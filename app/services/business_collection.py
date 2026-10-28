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
from app.services.service_agreement_scope import accepted_agreement_sql

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
        fields["pending_activation"] = row["state"] == "pending"
        fields["pending_recovery"] = (
            row["state"] == "pending"
            and row["version"] == 0
            and row["upload_lease_until"] is None
            and bool(row.get("upload_single_attempt_confirmed", False))
        )
        fields["pending_cancelable"] = bool(row.get("pending_cancelable", False))
        fields["pending_uncertain"] = bool(row.get("pending_uncertain", False))
        fields["pending_quarantined"] = bool(row.get("pending_quarantined", False))
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
                        text("""SELECT *, (state='pending' AND version=0 AND
                      ((sha256 IS NULL AND upload_lease_until<clock_timestamp()) OR
                       (sha256 IS NOT NULL AND upload_owner IS NOT NULL AND
                        (upload_lease_until IS NULL OR upload_lease_until<clock_timestamp()))))
                      AS pending_cancelable,
                      (state='pending' AND version=0 AND sha256 IS NOT NULL AND upload_owner IS NOT NULL AND
                      (upload_lease_until<clock_timestamp() OR
                       (upload_lease_until IS NULL AND NOT upload_single_attempt_confirmed))) AS pending_uncertain,
                      (state='pending' AND version=0 AND sha256 IS NOT NULL AND upload_owner IS NULL
                      AND status='archived') AS pending_quarantined
                  FROM business_collection_photos WHERE tenant_id=:tenant
                  AND business_id=:business AND state IN ('ready','pending')
                  ORDER BY sort_order,created_at,id"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            pending = (
                (
                    await session.execute(
                        text("""SELECT resource_key,state,error_code FROM business_visual_pending_changes
                  WHERE tenant_id=:tenant AND business_id=:business AND state IN ('pending','failed')
                    AND resource_key LIKE 'photo:%'"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            by_resource = {row["resource_key"]: row for row in pending}
            photos = [self._present(row) for row in rows]
            for photo in photos:
                operation = by_resource.get(f"photo:{photo.id}")
                photo.pending_change = operation is not None and operation["state"] == "pending"
                photo.pending_change_error = (
                    operation["error_code"] if operation and operation["state"] == "failed" else None
                )
            return photos

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
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        photo = uuid5(NAMESPACE_URL, f"collection-photo/{tenant}/{business}/{body.operation_id}")
        key = f"business-collection/{tenant}/{business}/{photo}.png"
        upload_owner = uuid4()
        source = "whatsapp" if isinstance(body, CollectionPhotoPromotion) else "upload"
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
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
                await VisualPendingChanges.enqueue_in_session(
                    session,
                    tenant,
                    business,
                    actor,
                    body.operation_id,
                    "photo_create",
                    f"photo:{photo}",
                    digest,
                    {"photo_id": str(photo)},
                    reserve=True,
                )
            if row["request_hash"] != digest:
                raise AuthError("COLLECTION_PHOTO_OPERATION_CONFLICT", 409)
            if row["state"] in {"deleting", "deleted"}:
                raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
            if row["state"] == "pending" and row["version"] > 0:
                pending = await VisualPendingChanges.status_in_session(session, tenant, business, f"photo:{photo}")
                if pending is None:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
                receipt = self._present(row)
                receipt.pending_change = pending["status"] == "pending"
                receipt.pending_change_error = pending["error_code"] if pending["status"] == "failed" else None
                return {**row, "receipt": receipt}
            if (
                row["state"] == "pending"
                and row["version"] == 0
                and row.get("upload_lease_until") is None
                and row.get("upload_owner") is not None
                and row.get("sha256") is not None
            ):
                return {**row, "resume_finalize": True}
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
                    text(f"""SELECT a.object_key,a.mime_type,a.sha256 FROM whatsapp_material_assets a
              LEFT JOIN whatsapp_processing_consents c ON c.tenant_id=a.tenant_id AND c.business_id=a.business_id
              WHERE a.tenant_id=:tenant AND a.business_id=:business AND a.id=:material
                AND a.kind='image' AND a.object_key IS NOT NULL AND a.mime_type IN ('image/png','image/jpeg')
                AND a.delete_requested_at IS NULL AND (a.expires_at IS NULL OR a.expires_at>now())
                AND ({accepted_agreement_sql()} OR (c.tenant_id IS NOT NULL AND c.revoked_at IS NULL))"""),
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
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
            retired = await session.scalar(
                text("""UPDATE business_collection_photos SET state='deleting',delete_lease_until=NULL
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND actor_id=:actor
                    AND state='pending' AND version=0 AND upload_owner IS NOT NULL RETURNING id"""),
                {"tenant": tenant, "business": business, "id": photo, "actor": actor},
            )
            if retired is not None:
                await session.execute(
                    text("""UPDATE business_visual_pending_changes SET state='cancelled',finished_at=clock_timestamp()
                      WHERE tenant_id=:tenant AND business_id=:business AND resource_key=:resource
                        AND kind='photo_create' AND state='pending'"""),
                    {"tenant": tenant, "business": business, "resource": f"photo:{photo}"},
                )
                await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
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
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            recorded = await session.scalar(
                text("""UPDATE business_collection_photos SET sha256=:sha,source_sha256=:source_sha,
                  mime_type=:mime,size_bytes=:size,updated_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='pending'
                    AND version=0 AND upload_owner=:owner AND upload_lease_until>now() RETURNING id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": row["id"],
                    "owner": row["upload_owner"],
                    "sha": media.sha256,
                    "source_sha": source_sha,
                    "mime": media.mime_type,
                    "size": len(media.data),
                },
            )
        if recorded is None:
            raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
        put_task = asyncio.create_task(self.store.put(row["object_key"], media))
        finalize_task: asyncio.Task[CollectionPhoto] | None = None
        try:
            await asyncio.shield(put_task)
            finalize_task = asyncio.create_task(
                self._prepare_and_finalize(tenant, business, actor, body, row, media, digest, source_sha)
            )
            return await asyncio.shield(finalize_task)
        except (MaterialError, asyncio.CancelledError):
            # Cancelling the await cannot stop boto's worker thread. Wait for the
            # actual writer before deleting its key; repeated cancellation is safe.
            while not put_task.done():
                try:
                    await asyncio.shield(put_task)
                except (MaterialError, asyncio.CancelledError):
                    pass
            if finalize_task is not None:
                # The DB commit may already have succeeded. Drain its task but
                # never delete the object merely because the caller cancelled.
                while not finalize_task.done():
                    try:
                        await asyncio.shield(finalize_task)
                    except (Exception, asyncio.CancelledError):
                        pass
                if not finalize_task.cancelled():
                    finalize_task.exception()  # retrieve any failure without exposing private data
                raise
            # Even a later successful retry does not prove that an earlier
            # timed-out attempt cannot still finish. Never delete this key here.
            if not put_task.cancelled():
                put_task.exception()
            raise

    async def _prepare_and_finalize(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        body: CollectionPhotoUpload | CollectionPhotoPromotion,
        row: Any,
        media: FetchedMedia,
        digest: str,
        source_sha: str | None,
    ) -> CollectionPhoto:
        from app.services.visual_consent_gate import VisualConsentGate

        # Remove the automatic cleanup lease before attempting finalization.
        # A lost commit acknowledgement must not let a timer erase an object
        # that may already have become an active or staged photo.
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
            held = await session.scalar(
                text("""UPDATE business_collection_photos SET upload_lease_until=NULL,
                  upload_single_attempt_confirmed=:confirmed
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='pending'
                    AND upload_owner=:owner AND upload_lease_until>now() RETURNING id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": row["id"],
                    "owner": row["upload_owner"],
                    "confirmed": getattr(self.store, "single_attempt_put", False) is True,
                },
            )
        if held is None:
            # A previous request to storage may still be completing, even if
            # the latest put returned. Keep the intent private and recoverable.
            raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
        return await self._finalize_photo(tenant, business, actor, body.operation_id, row, media, digest, source_sha)

    async def _finalize_photo(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        row: Any,
        media: FetchedMedia,
        digest: str,
        source_sha: str | None = None,
    ) -> CollectionPhoto:
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        saved = None
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, row["id"], operation)
            current = await self._row(session, tenant, business, row["id"], lock=True)
            if current is None or current["operation_id"] != operation or current["request_hash"] != digest:
                raise AuthError("COLLECTION_PHOTO_OPERATION_CONFLICT", 409)
            if current["actor_id"] != actor:
                raise AuthError("COLLECTION_PHOTO_OWNER_REQUIRED", 403)
            if current["state"] == "ready":
                replay = await self._replay(session, tenant, business, row["id"], operation, digest)
                if replay is None:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
                return replay
            if current["state"] == "pending" and current["version"] > 0:
                pending = await VisualPendingChanges.status_in_session(session, tenant, business, f"photo:{row['id']}")
                if pending is None or pending["operation_id"] != operation:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
                saved = self._present(current)
                saved.pending_change = pending["status"] == "pending"
                saved.pending_change_error = pending["error_code"] if pending["status"] == "failed" else None
                return saved
            if current["state"] != "pending":
                # Delayed put after cleanup: persist compensation before attempting IO.
                await session.execute(
                    text("""UPDATE business_collection_photos SET state='deleting',delete_lease_until=NULL
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": row["id"]},
                )
            else:
                if (
                    current["version"] != 0
                    or current["upload_lease_until"] is not None
                    or current["upload_owner"] != row["upload_owner"]
                    or current["sha256"] != media.sha256
                    or current["mime_type"] != media.mime_type
                    or current["size_bytes"] != len(media.data)
                    or current["source_sha256"] != source_sha
                ):
                    raise AuthError("COLLECTION_PHOTO_RECOVERY_MISMATCH", 409)
                await self._destination(
                    session,
                    tenant,
                    business,
                    CollectionPhotoMetadata(
                        title=current["title"],
                        item_id=current["item_id"],
                        space_kind=current["space_kind"],
                        sort_order=current["sort_order"],
                    ),
                )
                if current["source"] == "whatsapp":
                    source = await self._source(session, tenant, business, current["source_material_id"])
                    if source["sha256"] != source_sha:
                        raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)
                await session.execute(
                    text("""UPDATE business_collection_photos SET version=1,
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
                await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
                pending = await VisualPendingChanges.status_in_session(session, tenant, business, f"photo:{row['id']}")
                if pending:
                    saved = self._present(await self._row(session, tenant, business, row["id"]))
                    saved.pending_change = pending["status"] == "pending"
                    saved.pending_change_error = pending["error_code"]
                else:
                    saved = await self._replay(session, tenant, business, row["id"], operation, digest)
        if saved is None:
            await self.reconcile(tenant, business, actor)
            raise AuthError("COLLECTION_PHOTO_RETIRED", 409)
        return saved

    @staticmethod
    async def _activate_staged_in_session(
        session: Any, tenant: UUID, business: UUID, actor: UUID, photo: UUID
    ) -> CollectionPhoto:
        """Activate an already-stored private image under the caller's business gate."""
        initial = await BusinessCollectionService._row(session, tenant, business, photo)
        if initial is None:
            raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
        await BusinessCollectionService._operation_guard(session, tenant, business, photo, initial["operation_id"])
        row = await BusinessCollectionService._row(session, tenant, business, photo, lock=True)
        if row is None or row["state"] != "pending" or row["version"] != 1 or row["upload_owner"] is not None:
            raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
        if row["actor_id"] != actor:
            raise AuthError("COLLECTION_PHOTO_OWNER_REQUIRED", 403)
        await BusinessCollectionService._destination(
            session,
            tenant,
            business,
            CollectionPhotoMetadata(
                title=row["title"], item_id=row["item_id"], space_kind=row["space_kind"], sort_order=row["sort_order"]
            ),
        )
        if row["source"] == "whatsapp":
            source = await BusinessCollectionService._source(session, tenant, business, row["source_material_id"])
            if source["sha256"] != row["source_sha256"]:
                raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)
        await session.execute(
            text("""UPDATE business_collection_photos SET state='ready',updated_at=now()
          WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='pending'"""),
            {"tenant": tenant, "business": business, "id": photo},
        )
        saved = BusinessCollectionService._present(
            await BusinessCollectionService._row(session, tenant, business, photo)
        )
        await BusinessCollectionService._version(
            session,
            tenant,
            business,
            actor,
            row["operation_id"],
            row["request_hash"],
            "promoted" if row["source"] == "whatsapp" else "uploaded",
            saved,
        )
        return saved

    async def upload(self, tenant: UUID, business: UUID, actor: UUID, body: CollectionPhotoUpload) -> CollectionPhoto:
        await self.reconcile(tenant, business, actor)
        digest = _digest(body.model_dump(mode="json"))
        row = await self._intent(tenant, business, actor, body, digest)
        if row.get("resume_finalize"):
            return await self.resume_upload(tenant, business, actor, row["id"])
        if row["state"] == "ready" or (row["state"] == "pending" and row["version"] > 0):
            return CollectionPhoto.model_validate(row["receipt"])
        try:
            raw = base64.b64decode(body.content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            await self._retire_upload(tenant, business, actor, row["id"])
            raise AuthError("COLLECTION_PHOTO_INVALID", 422) from exc
        try:
            media = await asyncio.to_thread(normalize_photo, raw, body.mime_type)
        except (AuthError, MaterialError, asyncio.CancelledError):
            await asyncio.shield(self._retire_upload(tenant, business, actor, row["id"]))
            raise
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
        if row.get("resume_finalize"):
            return await self.resume_upload(tenant, business, actor, row["id"])
        if row["state"] == "ready" or (row["state"] == "pending" and row["version"] > 0):
            return CollectionPhoto.model_validate(row["receipt"])
        try:
            async with self.database.transaction(tenant, actor) as session:
                await require_catalog_owner(session, tenant, business, actor)
                source = await self._source(session, tenant, business, body.material_id)
            raw = await self.store.get_image(source["object_key"])
            source_sha = hashlib.sha256(raw).hexdigest()
            if source_sha != source["sha256"]:
                raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)
            media = await asyncio.to_thread(normalize_photo, raw, source["mime_type"], 5 * 1024 * 1024)
        except (AuthError, MaterialError, asyncio.CancelledError):
            await asyncio.shield(self._retire_upload(tenant, business, actor, row["id"]))
            raise
        return await self._complete(tenant, business, actor, body, row, media, digest, source_sha)

    async def resume_upload(self, tenant: UUID, business: UUID, actor: UUID, photo: UUID) -> CollectionPhoto:
        """Recheck a private object after an unknown DB outcome; never overwrite or erase it."""
        from app.services.visual_pending_changes import VisualPendingChanges

        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            row = await self._row(session, tenant, business, photo)
            if row is None:
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            if row["actor_id"] != actor:
                raise AuthError("COLLECTION_PHOTO_OWNER_REQUIRED", 403)
            if row["state"] == "ready":
                saved = await self._replay(session, tenant, business, photo, row["operation_id"], row["request_hash"])
                if saved is None:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
                return saved
            if row["state"] == "pending" and row["version"] > 0:
                pending = await VisualPendingChanges.status_in_session(session, tenant, business, f"photo:{photo}")
                if pending is None or pending["operation_id"] != row["operation_id"]:
                    raise AuthError("COLLECTION_PHOTO_BUSY", 409)
                saved = self._present(row)
                saved.pending_change = pending["status"] == "pending"
                saved.pending_change_error = pending["error_code"] if pending["status"] == "failed" else None
                return saved
            if (
                row["state"] != "pending"
                or row["version"] != 0
                or row["upload_lease_until"] is not None
                or row["upload_owner"] is None
                or row["sha256"] is None
                or not row.get("upload_single_attempt_confirmed", False)
                or row["mime_type"] != "image/png"
                or not row["size_bytes"]
            ):
                raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
            persisted = dict(row)
        try:
            data = await self.store.get_image(persisted["object_key"], max_bytes=STORED_MAX_BYTES)
        except MaterialError as exc:
            raise AuthError("COLLECTION_PHOTO_RECOVERY_UNAVAILABLE", 409) from exc
        if len(data) != persisted["size_bytes"] or hashlib.sha256(data).hexdigest() != persisted["sha256"]:
            raise AuthError("COLLECTION_PHOTO_RECOVERY_MISMATCH", 409)
        media = FetchedMedia(data, "image/png", persisted["sha256"])
        task = asyncio.create_task(
            self._finalize_photo(
                tenant,
                business,
                actor,
                persisted["operation_id"],
                persisted,
                media,
                persisted["request_hash"],
                persisted["source_sha256"],
            )
        )
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            while not task.done():
                try:
                    await asyncio.shield(task)
                except (Exception, asyncio.CancelledError):
                    pass
            if not task.cancelled():
                task.exception()
            raise

    async def update(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        photo: UUID,
        body: CollectionPhotoUpdate,
    ) -> CollectionPhoto:
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        digest = _digest(body.model_dump(mode="json"))
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
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
            payload = {"photo_id": str(photo), "body": body.model_dump(mode="json")}
            if await VisualPendingChanges.enqueue_in_session(
                session, tenant, business, actor, body.operation_id, "photo_update", f"photo:{photo}", digest, payload
            ):
                pending = self._present(row)
                pending.pending_change = True
                return pending
            return await self._update_in_session(session, tenant, business, actor, photo, body)

    @staticmethod
    async def _update_in_session(
        session: Any, tenant: UUID, business: UUID, actor: UUID, photo: UUID, body: CollectionPhotoUpdate
    ) -> CollectionPhoto:
        digest = _digest(body.model_dump(mode="json"))
        await BusinessCollectionService._operation_guard(session, tenant, business, photo, body.operation_id)
        row = await BusinessCollectionService._row(session, tenant, business, photo, lock=True)
        if row is None:
            raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
        replay = await BusinessCollectionService._replay(session, tenant, business, photo, body.operation_id, digest)
        if replay is not None:
            return replay
        if row["state"] != "ready":
            raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
        if row["version"] != body.expected_version:
            raise AuthError("COLLECTION_PHOTO_VERSION_CONFLICT", 409)
        await BusinessCollectionService._destination(session, tenant, business, body, active=body.status == "active")
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
        saved = BusinessCollectionService._present(
            await BusinessCollectionService._row(session, tenant, business, photo)
        )
        await BusinessCollectionService._version(
            session, tenant, business, actor, body.operation_id, digest, "updated", saved
        )
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
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        digest = _digest({"action": "delete", "expected_version": expected_version})
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            await VisualConsentGate(self.database)._lock(session, tenant, business, actor)
            await self._operation_guard(session, tenant, business, photo, operation)
            row = await self._row(session, tenant, business, photo, lock=True)
            if row is None:
                raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
            replay = await self._replay(session, tenant, business, photo, operation, digest)
            if replay is None:
                if row["state"] == "pending" and row["version"] == 0 and expected_version == 0:
                    if row["actor_id"] != actor:
                        raise AuthError("COLLECTION_PHOTO_OWNER_REQUIRED", 403)
                    retired = await session.scalar(
                        text("""UPDATE business_collection_photos SET
                          state=CASE WHEN sha256 IS NOT NULL AND (upload_lease_until<clock_timestamp() OR
                                     (upload_lease_until IS NULL AND NOT upload_single_attempt_confirmed))
                                     THEN 'pending' ELSE 'deleting' END,
                          version=CASE WHEN sha256 IS NOT NULL AND (upload_lease_until<clock_timestamp() OR
                                       (upload_lease_until IS NULL AND NOT upload_single_attempt_confirmed))
                                       THEN 0 ELSE 1 END,
                          upload_owner=CASE WHEN sha256 IS NOT NULL AND (upload_lease_until<clock_timestamp() OR
                                            (upload_lease_until IS NULL AND NOT upload_single_attempt_confirmed))
                                            THEN NULL ELSE upload_owner END,
                          upload_quarantined=CASE WHEN sha256 IS NOT NULL AND
                            (upload_lease_until<clock_timestamp() OR
                             (upload_lease_until IS NULL AND NOT upload_single_attempt_confirmed))
                            THEN true ELSE false END,
                          status='archived',updated_at=now()
                          WHERE tenant_id=:tenant AND business_id=:business AND id=:id
                          AND state='pending' AND version=0 AND
                          ((sha256 IS NULL AND upload_lease_until<clock_timestamp()) OR
                           (sha256 IS NOT NULL AND upload_owner IS NOT NULL AND
                            (upload_lease_until IS NULL OR upload_lease_until<clock_timestamp())))
                          RETURNING state"""),
                        {"tenant": tenant, "business": business, "id": photo},
                    )
                    if retired is None:
                        raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
                    await session.execute(
                        text("""UPDATE business_visual_pending_changes SET state='cancelled',
                          finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business
                          AND resource_key=:resource AND kind='photo_create' AND state='pending'"""),
                        {"tenant": tenant, "business": business, "resource": f"photo:{photo}"},
                    )
                    saved = self._present(await self._row(session, tenant, business, photo))
                    if retired == "pending":
                        # The immutable receipt is versioned, but the tombstone
                        # remains version zero so it can never become an asset.
                        saved = saved.model_copy(update={"version": 1, "status": "deleted"})
                    await self._version(session, tenant, business, actor, operation, digest, "deleted", saved)
                    await VisualConsentGate._audit(session, tenant, business, actor, "visual.change_cancelled")
                    await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
                elif row["state"] == "pending" and row["version"] > 0:
                    pending = await VisualPendingChanges.status_in_session(session, tenant, business, f"photo:{photo}")
                    if pending is None or pending["status"] != "failed":
                        raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
                    if row["version"] != expected_version:
                        raise AuthError("COLLECTION_PHOTO_VERSION_CONFLICT", 409)
                    await session.execute(
                        text("""UPDATE business_visual_pending_changes SET state='cancelled',
                          finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business
                          AND resource_key=:resource AND kind='photo_create' AND state='failed'"""),
                        {"tenant": tenant, "business": business, "resource": f"photo:{photo}"},
                    )
                    await session.execute(
                        text("""UPDATE business_collection_photos SET state='deleting',status='archived',
                          version=version+1,updated_at=now() WHERE tenant_id=:tenant
                          AND business_id=:business AND id=:id AND state='pending'"""),
                        {"tenant": tenant, "business": business, "id": photo},
                    )
                    saved = self._present(await self._row(session, tenant, business, photo))
                    await self._version(session, tenant, business, actor, operation, digest, "deleted", saved)
                    await VisualConsentGate._audit(session, tenant, business, actor, "visual.change_cancelled")
                elif row["state"] != "ready":
                    raise AuthError("COLLECTION_PHOTO_NOT_READY", 409)
                else:
                    if row["version"] != expected_version:
                        raise AuthError("COLLECTION_PHOTO_VERSION_CONFLICT", 409)
                    payload = {
                        "photo_id": str(photo),
                        "operation_id": str(operation),
                        "expected_version": expected_version,
                    }
                    if await VisualPendingChanges.enqueue_in_session(
                        session, tenant, business, actor, operation, "photo_delete", f"photo:{photo}", digest, payload
                    ):
                        return CollectionPhotoDeletion(status="waiting_for_generation")
                    await self._delete_in_session(session, tenant, business, actor, photo, operation, expected_version)
        await self.reconcile(tenant, business, actor)
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            row = await self._row(session, tenant, business, photo)
            if row["state"] == "pending" and row["upload_owner"] is None and row["version"] == 0:
                return CollectionPhotoDeletion(status="quarantined")
            return CollectionPhotoDeletion(status="deleted" if row["state"] == "deleted" else "deleting")

    @staticmethod
    async def _delete_in_session(
        session: Any, tenant: UUID, business: UUID, actor: UUID, photo: UUID, operation: UUID, expected_version: int
    ) -> None:
        digest = _digest({"action": "delete", "expected_version": expected_version})
        await BusinessCollectionService._operation_guard(session, tenant, business, photo, operation)
        row = await BusinessCollectionService._row(session, tenant, business, photo, lock=True)
        if row is None:
            raise AuthError("COLLECTION_PHOTO_NOT_FOUND", 404)
        replay = await BusinessCollectionService._replay(session, tenant, business, photo, operation, digest)
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
            saved = BusinessCollectionService._present(
                await BusinessCollectionService._row(session, tenant, business, photo)
            )
            await BusinessCollectionService._version(
                session, tenant, business, actor, operation, digest, "deleted", saved
            )

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
                    AND state='deleting' AND (delete_lease_until IS NULL OR delete_lease_until<now())
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
