"""Owner-managed durable photos; object IO runs outside database transactions."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import io
import json
import logging
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.core.config import Settings
from app.db.session import Database
from app.schemas.business_collection import (
    CollectionPhoto,
    CollectionPhotoDeletion,
    CollectionPhotoMetadata,
    CollectionPhotoPromotion,
    CollectionPhotoUpdate,
    CollectionPhotoUpload,
    CollectionPhotoUrl,
    CollectionPhotoVersion,
)
from app.services.auth import AuthError
from app.services.business_catalog import audit_catalog_change, require_catalog_owner

logger = logging.getLogger("meu_braco_direito.collection")
UPLOAD_MAX_BYTES = 2 * 1024 * 1024
STORED_MAX_BYTES = 8 * 1024 * 1024
PHOTO_FIELDS = """id,version,title,item_id,space_kind,sort_order,status,source,
  source_material_id,mime_type,sha256,source_sha256,size_bytes,created_at,updated_at"""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def normalize_photo(data: bytes, mime: str, limit: int = UPLOAD_MAX_BYTES) -> FetchedMedia:
    if not data or len(data) > limit:
        raise AuthError("COLLECTION_PHOTO_SIZE", 422)
    try:
        with Image.open(io.BytesIO(data)) as image:
            if (
                image.width * image.height > 16_000_000
                or max(image.size) > 8192
                or Image.MIME.get(image.format or "") != mime
                or getattr(image, "n_frames", 1) != 1
            ):
                raise AuthError("COLLECTION_PHOTO_INVALID", 422)
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            oriented = ImageOps.exif_transpose(image)
            prepared = oriented.convert("RGBA" if "A" in oriented.getbands() else "RGB")
            prepared.info.clear()
            output = io.BytesIO()
            prepared.save(output, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise AuthError("COLLECTION_PHOTO_INVALID", 422) from exc
    normalized = output.getvalue()
    if len(normalized) > STORED_MAX_BYTES:
        raise AuthError("COLLECTION_PHOTO_SIZE", 422)
    return FetchedMedia(normalized, "image/png", hashlib.sha256(normalized).hexdigest())


class BusinessCollectionService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.database = database
        self.store = store or MaterialStore(settings)

    @staticmethod
    async def _destination(
        session: Any, tenant: UUID, business: UUID, body: CollectionPhotoMetadata, *, active: bool = True
    ) -> None:
        if body.item_id is not None and not await session.scalar(
            text("""SELECT 1 FROM business_offerings WHERE tenant_id=:tenant AND business_id=:business
              AND id=:item AND (NOT :active OR state='active')"""),
            {"tenant": tenant, "business": business, "item": body.item_id, "active": active},
        ):
            raise AuthError("COLLECTION_ITEM_NOT_ACTIVE", 409)

    @staticmethod
    async def _row(session: Any, tenant: UUID, business: UUID, photo: UUID, *, lock: bool = False) -> Any:
        return (
            (
                await session.execute(
                    text(
                        """SELECT * FROM business_collection_photos
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""
                        + (" FOR UPDATE" if lock else "")
                    ),
                    {"tenant": tenant, "business": business, "id": photo},
                )
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _present(row: Any) -> CollectionPhoto:
        fields = {name: row[name] for name in PHOTO_FIELDS.replace("\n", "").replace(" ", "").split(",")}
        if row["state"] in {"deleting", "deleted"}:
            fields["status"] = "deleted"
        return CollectionPhoto.model_validate(fields)

    @staticmethod
    async def _operation_guard(
        session: Any,
        tenant: UUID,
        business: UUID,
        photo: UUID,
        operation: UUID,
    ) -> None:
        # Serialize the durable operation identity, including calls against different photos.
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope,0))"),
            {"scope": f"collection/{tenant}/{operation}"},
        )
        prior = (
            (
                await session.execute(
                    text("""SELECT business_id,id FROM business_collection_photos
              WHERE tenant_id=:tenant AND operation_id=:op UNION ALL
              SELECT business_id,photo_id AS id FROM business_collection_photo_versions
              WHERE tenant_id=:tenant AND operation_id=:op"""),
                    {"tenant": tenant, "op": operation},
                )
            )
            .mappings()
            .all()
        )
        if any(row["business_id"] != business or row["id"] != photo for row in prior):
            raise AuthError("COLLECTION_PHOTO_OPERATION_CONFLICT", 409)

    @staticmethod
    async def _replay(
        session: Any, tenant: UUID, business: UUID, photo: UUID, operation: UUID, digest: str
    ) -> CollectionPhoto | None:
        row = (
            (
                await session.execute(
                    text("""SELECT request_hash,document FROM business_collection_photo_versions
                      WHERE tenant_id=:tenant AND business_id=:business AND photo_id=:photo AND operation_id=:op"""),
                    {"tenant": tenant, "business": business, "photo": photo, "op": operation},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is not None and row["request_hash"] != digest:
            raise AuthError("COLLECTION_PHOTO_OPERATION_CONFLICT", 409)
        return None if row is None else CollectionPhoto.model_validate(row["document"])

    @staticmethod
    async def _version(
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        digest: str,
        action: str,
        photo: CollectionPhoto,
    ) -> None:
        await session.execute(
            text("""INSERT INTO business_collection_photo_versions
              (tenant_id,business_id,photo_id,version,operation_id,actor_id,request_hash,action,document)
              VALUES(:tenant,:business,:photo,:version,:op,:actor,:hash,:action,CAST(:doc AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "photo": photo.id,
                "version": photo.version,
                "op": operation,
                "actor": actor,
                "hash": digest,
                "action": action,
                "doc": photo.model_dump_json(),
            },
        )
        await audit_catalog_change(session, tenant, business, actor, operation, f"collection.photo_{action}")

    async def list_photos(self, tenant: UUID, business: UUID, actor: UUID) -> list[CollectionPhoto]:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT * FROM business_collection_photos WHERE tenant_id=:tenant
                  AND business_id=:business AND state='ready' ORDER BY sort_order,created_at,id"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [self._present(row) for row in rows]

    async def history(self, tenant: UUID, business: UUID, actor: UUID, photo: UUID) -> list[CollectionPhotoVersion]:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            if await self._row(session, tenant, business, photo) is None:
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            rows = (
                (
                    await session.execute(
                        text("""SELECT version,action,document,created_at FROM business_collection_photo_versions
                  WHERE tenant_id=:tenant AND business_id=:business AND photo_id=:photo ORDER BY version DESC"""),
                        {"tenant": tenant, "business": business, "photo": photo},
                    )
                )
                .mappings()
                .all()
            )
            return [
                CollectionPhotoVersion(
                    version=row["version"],
                    action=row["action"],
                    photo=CollectionPhoto.model_validate(row["document"]),
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def _intent(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        body: CollectionPhotoUpload | CollectionPhotoPromotion,
        digest: str,
    ) -> Any:
        photo = uuid5(NAMESPACE_URL, f"collection-photo/{tenant}/{business}/{body.operation_id}")
        key = f"business-collection/{tenant}/{business}/{photo}.png"
        upload_owner = uuid4()
        source = "whatsapp" if isinstance(body, CollectionPhotoPromotion) else "upload"
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, photo, body.operation_id)
            row = await self._row(session, tenant, business, photo)
            if row is None:
                await self._destination(session, tenant, business, body)
                await session.execute(
                    text("""INSERT INTO business_collection_photos
                      (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,
                       title,item_id,space_kind,sort_order,source,source_material_id,rights_scope,upload_owner,upload_lease_until)
                      VALUES(:id,:tenant,:business,:op,:actor,:hash,:key,:title,:item,:space,:sort,:source,:material,
                             'business_collection_confirmed',:upload_owner,now()+interval '10 minutes')
                      ON CONFLICT DO NOTHING"""),
                    {
                        "id": photo,
                        "tenant": tenant,
                        "business": business,
                        "op": body.operation_id,
                        "actor": actor,
                        "hash": digest,
                        "key": key,
                        "title": body.title,
                        "item": body.item_id,
                        "space": body.space_kind,
                        "sort": body.sort_order,
                        "source": source,
                        "upload_owner": upload_owner,
                        "material": body.material_id if isinstance(body, CollectionPhotoPromotion) else None,
                    },
                )
                row = await self._row(session, tenant, business, photo)
            if row["request_hash"] != digest:
                raise AuthError("COLLECTION_PHOTO_OPERATION_CONFLICT", 409)
            if row["state"] in {"deleting", "deleted"}:
                raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
            if row["state"] == "pending":
                renewed = await session.scalar(
                    text("""UPDATE business_collection_photos SET upload_lease_until=now()+interval '10 minutes'
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='pending'
                        AND upload_owner=:owner
                        AND upload_lease_until>now() RETURNING id"""),
                    {"tenant": tenant, "business": business, "id": photo, "owner": upload_owner},
                )
                if renewed is None:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
            if row["state"] == "ready":
                return {
                    **row,
                    "receipt": await self._replay(session, tenant, business, photo, body.operation_id, digest),
                }
            return row

    @staticmethod
    async def _source(session: Any, tenant: UUID, business: UUID, material: UUID) -> Any:
        row = (
            (
                await session.execute(
                    text("""SELECT a.object_key,a.mime_type,a.sha256 FROM whatsapp_material_assets a
              JOIN whatsapp_processing_consents c ON c.tenant_id=a.tenant_id AND c.business_id=a.business_id
              WHERE a.tenant_id=:tenant AND a.business_id=:business AND a.id=:material
                AND a.kind='image' AND a.object_key IS NOT NULL AND a.mime_type IN ('image/png','image/jpeg')
                AND a.delete_requested_at IS NULL AND a.expires_at>now() AND c.revoked_at IS NULL"""),
                    {"tenant": tenant, "business": business, "material": material},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)
        return row

    async def _retire_upload(self, tenant: UUID, business: UUID, actor: UUID, photo: UUID) -> None:
        """Compensate an ambiguous put, including a key recreated after old cleanup."""
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await session.execute(
                text("""UPDATE business_collection_photos SET state='deleting',delete_lease_until=NULL
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": photo},
            )
        await self.reconcile(tenant, business, actor)

    async def _complete(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        body: CollectionPhotoUpload | CollectionPhotoPromotion,
        row: Any,
        media: FetchedMedia,
        digest: str,
        source_sha: str | None = None,
    ) -> CollectionPhoto:
        put_task = asyncio.create_task(self.store.put(row["object_key"], media))
        try:
            await asyncio.shield(put_task)
            return await self._finalize_photo(tenant, business, actor, body, row, media, digest, source_sha)
        except (MaterialError, asyncio.CancelledError):
            # Cancelling the await cannot stop boto's worker thread. Wait for the
            # actual writer before deleting its key; repeated cancellation is safe.
            while not put_task.done():
                try:
                    await asyncio.shield(put_task)
                except (MaterialError, asyncio.CancelledError):
                    pass
            await asyncio.shield(self._retire_upload(tenant, business, actor, row["id"]))
            raise

    async def _finalize_photo(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        body: CollectionPhotoUpload | CollectionPhotoPromotion,
        row: Any,
        media: FetchedMedia,
        digest: str,
        source_sha: str | None = None,
    ) -> CollectionPhoto:
        saved = None
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, row["id"], body.operation_id)
            current = await self._row(session, tenant, business, row["id"], lock=True)
            if current["state"] != "pending":
                # Delayed put after cleanup: persist compensation before attempting IO.
                await session.execute(
                    text("""UPDATE business_collection_photos SET state='deleting',delete_lease_until=NULL
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": row["id"]},
                )
            else:
                await self._destination(session, tenant, business, body)
                if isinstance(body, CollectionPhotoPromotion):
                    await self._source(session, tenant, business, body.material_id)
                await session.execute(
                    text("""UPDATE business_collection_photos SET state='ready',version=1,
                      sha256=:sha,source_sha256=:source_sha,mime_type=:mime,size_bytes=:size,
                      updated_at=now(),upload_owner=NULL,upload_lease_until=NULL
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "id": row["id"],
                        "sha": media.sha256,
                        "source_sha": source_sha,
                        "mime": media.mime_type,
                        "size": len(media.data),
                    },
                )
                saved = self._present(await self._row(session, tenant, business, row["id"]))
                await self._version(
                    session,
                    tenant,
                    business,
                    actor,
                    body.operation_id,
                    digest,
                    "promoted" if isinstance(body, CollectionPhotoPromotion) else "uploaded",
                    saved,
                )
        if saved is None:
            await self.reconcile(tenant, business, actor)
            raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
        return saved

    async def upload(self, tenant: UUID, business: UUID, actor: UUID, body: CollectionPhotoUpload) -> CollectionPhoto:
        await self.reconcile(tenant, business, actor)
        digest = _digest(body.model_dump(mode="json"))
        row = await self._intent(tenant, business, actor, body, digest)
        if row["state"] == "ready":
            return CollectionPhoto.model_validate(row["receipt"])
        try:
            raw = base64.b64decode(body.content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise AuthError("COLLECTION_PHOTO_INVALID", 422) from exc
        media = await asyncio.to_thread(normalize_photo, raw, body.mime_type)
        return await self._complete(tenant, business, actor, body, row, media, digest)

    async def promote(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        body: CollectionPhotoPromotion,
    ) -> CollectionPhoto:
        await self.reconcile(tenant, business, actor)
        digest = _digest(body.model_dump(mode="json"))
        row = await self._intent(tenant, business, actor, body, digest)
        if row["state"] == "ready":
            return CollectionPhoto.model_validate(row["receipt"])
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            source = await self._source(session, tenant, business, body.material_id)
        raw = await self.store.get_image(source["object_key"])
        source_sha = hashlib.sha256(raw).hexdigest()
        if source_sha != source["sha256"]:
            raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)
        media = await asyncio.to_thread(normalize_photo, raw, source["mime_type"], 5 * 1024 * 1024)
        return await self._complete(tenant, business, actor, body, row, media, digest, source_sha)

    async def update(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        photo: UUID,
        body: CollectionPhotoUpdate,
    ) -> CollectionPhoto:
        digest = _digest(body.model_dump(mode="json"))
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, photo, body.operation_id)
            row = await self._row(session, tenant, business, photo, lock=True)
            if row is None:
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            replay = await self._replay(session, tenant, business, photo, body.operation_id, digest)
            if replay is not None:
                return replay
            if row["state"] != "ready":
                raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
            if row["version"] != body.expected_version:
                raise AuthError("COLLECTION_PHOTO_VERSION_CONFLICT", 409)
            await self._destination(session, tenant, business, body, active=body.status == "active")
            await session.execute(
                text("""UPDATE business_collection_photos SET title=:title,item_id=:item,
                  space_kind=:space,sort_order=:sort,status=:status,version=version+1,updated_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": photo,
                    "title": body.title,
                    "item": body.item_id,
                    "space": body.space_kind,
                    "sort": body.sort_order,
                    "status": body.status,
                },
            )
            saved = self._present(await self._row(session, tenant, business, photo))
            await self._version(session, tenant, business, actor, body.operation_id, digest, "updated", saved)
            return saved

    async def url(self, tenant: UUID, business: UUID, actor: UUID, photo: UUID) -> CollectionPhotoUrl:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            row = await self._row(session, tenant, business, photo)
            if row is None or row["state"] != "ready":
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            key, mime = row["object_key"], row["mime_type"]
        return CollectionPhotoUrl(url=await self.store.signed_url(key, mime))

    async def delete(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        photo: UUID,
        operation: UUID,
        expected_version: int,
    ) -> CollectionPhotoDeletion:
        digest = _digest({"action": "delete", "expected_version": expected_version})
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, photo, operation)
            row = await self._row(session, tenant, business, photo, lock=True)
            if row is None:
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            replay = await self._replay(session, tenant, business, photo, operation, digest)
            if replay is None:
                if row["state"] != "ready":
                    raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
                if row["version"] != expected_version:
                    raise AuthError("COLLECTION_PHOTO_VERSION_CONFLICT", 409)
                await session.execute(
                    text("""UPDATE business_collection_photos SET state='deleting',status='archived',
                      version=version+1,updated_at=now()
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": photo},
                )
                saved = self._present(await self._row(session, tenant, business, photo))
                await self._version(session, tenant, business, actor, operation, digest, "deleted", saved)
        await self.reconcile(tenant, business, actor)
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            row = await self._row(session, tenant, business, photo)
            return CollectionPhotoDeletion(status="deleted" if row["state"] == "deleted" else "deleting")

    async def removals(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, int]:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            count = await session.scalar(
                text("""SELECT count(*) FROM business_collection_photos
                  WHERE tenant_id=:tenant AND business_id=:business AND state='deleting'"""),
                {"tenant": tenant, "business": business},
            )
            return {"pending": int(count)}

    async def reconcile(self, tenant: UUID, business: UUID, actor: UUID, limit: int = 20) -> int:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""WITH candidates AS (
                  SELECT id FROM business_collection_photos WHERE tenant_id=:tenant AND business_id=:business
                    AND ((state='pending' AND created_at<now()-interval '1 hour' AND upload_lease_until<now())
                      OR (state='deleting' AND (delete_lease_until IS NULL OR delete_lease_until<now())))
                  ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                  UPDATE business_collection_photos p SET state='deleting',delete_owner=:actor,
                    delete_lease_until=now()+interval '60 seconds',delete_fencing_token=p.delete_fencing_token+1
                  FROM candidates c WHERE p.id=c.id AND p.tenant_id=:tenant AND p.business_id=:business
                  RETURNING p.id,p.object_key,p.delete_fencing_token"""),
                        {"tenant": tenant, "business": business, "actor": actor, "limit": limit},
                    )
                )
                .mappings()
                .all()
            )
        removed = 0
        for row in rows:
            try:
                await self.store.delete(row["object_key"])
                async with self.database.transaction(tenant, actor) as session:
                    await require_catalog_owner(session, tenant, business, actor)
                    changed = await session.scalar(
                        text("""UPDATE business_collection_photos SET state='deleted',updated_at=now()
                          WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='deleting'
                            AND delete_owner=:actor AND delete_fencing_token=:fence AND delete_lease_until>now()
                          RETURNING id"""),
                        {
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "id": row["id"],
                            "fence": row["delete_fencing_token"],
                        },
                    )
                    if changed is not None:
                        await audit_catalog_change(
                            session,
                            tenant,
                            business,
                            actor,
                            uuid5(row["id"], f"cleanup/{row['delete_fencing_token']}"),
                            "collection.photo_object_removed",
                        )
                        removed += 1
            except MaterialError:
                logger.warning("collection.photo_cleanup_retry", extra={"photo_id": str(row["id"])})
        return removed
