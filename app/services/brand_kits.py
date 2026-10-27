"""Versioned owner kit selection and private, approved business logos."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.core.config import Settings
from app.db.session import Database
from app.schemas.brand_kits import (
    BrandKitCatalog,
    BrandKitCatalogItem,
    BrandKitConfirmRequest,
    BrandKitDraftRequest,
    BrandKitFormats,
    BrandKitLogoRead,
    BrandKitLogoUpload,
    BrandKitLogoUrl,
    BrandKitOptions,
    BrandKitOverrides,
    BrandKitPalette,
    BrandKitState,
    BrandKitVersion,
    FeedLayout,
    ReelCoverLayout,
    StoryLayout,
)
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService

KIT_ID = "cafe-pausas"
KIT_VERSION = 1
MANIFEST = Path(__file__).resolve().parents[2] / "catalog/kits/cafe-pausas/v1/manifest.json"
LOGO_MAX_BYTES = 2 * 1024 * 1024
LOGO_MAX_PIXELS = 16_000_000
LOGO_MAX_SIDE = 4096
LOGO_MAX_STORED_BYTES = 4 * 1024 * 1024
logger = logging.getLogger("meu_braco_direito.brand_kits")


def _digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def _manifest() -> dict[str, Any]:
    document = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    if document["kit_id"] != KIT_ID or document["version"] != KIT_VERSION:
        raise RuntimeError("Brand kit manifest identity does not match deployed catalog")
    media = {item["path"] for item in document["media"]}
    if any(
        source not in media or source.startswith("assets/post-")
        for source in document["editor"]["preview_sources"].values()
    ):
        raise RuntimeError("Brand kit editor sources must be clean registered media")
    return document


def kit_commercially_available() -> bool:
    return str(_manifest()["status"]) == "approved"


def _default_overrides(business_name: str, manifest: dict[str, Any]) -> BrandKitOverrides:
    return BrandKitOverrides(
        palette=BrandKitPalette(
            primary=manifest["palette"]["forest"],
            background=manifest["palette"]["cream"],
            accent=manifest["palette"]["caramel"],
        ),
        heading_font=manifest["fonts"]["heading"],
        body_font=manifest["fonts"]["body"],
        brand_name=business_name,
        tagline="",
        cta="Saiba mais",
        formats=BrandKitFormats(
            feed=FeedLayout(layout="photo_focus", image_position="center"),
            story=StoryLayout(layout="photo_focus", image_position="center"),
            reel_cover=ReelCoverLayout(layout="photo_focus", image_position="center"),
        ),
    )


def _normalize_logo(body: BrandKitLogoUpload) -> tuple[FetchedMedia, str]:
    try:
        raw = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AuthError("BRAND_KIT_LOGO_INVALID", 422) from exc
    if not raw or len(raw) > LOGO_MAX_BYTES:
        raise AuthError("BRAND_KIT_LOGO_SIZE", 422)
    raw_digest = hashlib.sha256(raw).hexdigest()
    try:
        with Image.open(io.BytesIO(raw)) as picture:
            if (
                picture.width > LOGO_MAX_SIDE
                or picture.height > LOGO_MAX_SIDE
                or picture.width * picture.height > LOGO_MAX_PIXELS
                or Image.MIME.get(picture.format or "") != body.mime_type
            ):
                raise AuthError("BRAND_KIT_LOGO_INVALID", 422)
            picture.verify()
        with Image.open(io.BytesIO(raw)) as picture:
            oriented = ImageOps.exif_transpose(picture)
            prepared = oriented.convert("RGBA" if "A" in oriented.getbands() else "RGB")
            prepared.info.clear()
            output = io.BytesIO()
            prepared.save(output, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise AuthError("BRAND_KIT_LOGO_INVALID", 422) from exc
    normalized = output.getvalue()
    if len(normalized) > LOGO_MAX_STORED_BYTES:
        raise AuthError("BRAND_KIT_LOGO_SIZE", 422)
    return FetchedMedia(normalized, "image/png", hashlib.sha256(normalized).hexdigest()), raw_digest


class BrandKitService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

    @staticmethod
    async def _owner(session: Any, tenant: UUID, business: UUID, actor: UUID) -> None:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)

    @staticmethod
    async def _business_name(session: Any, tenant: UUID, business: UUID) -> str:
        name = await session.scalar(
            text("SELECT name FROM businesses WHERE tenant_id=:tenant AND id=:business"),
            {"tenant": tenant, "business": business},
        )
        if not isinstance(name, str):
            raise AuthError("BUSINESS_NOT_FOUND", 404)
        return name

    @property
    def _selectable(self) -> bool:
        return self.settings.environment in {"development", "testing"} or kit_commercially_available()

    async def catalog(self, tenant: UUID, business: UUID, actor: UUID) -> BrandKitCatalog:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            name = await self._business_name(session, tenant, business)
        manifest = _manifest()
        options = BrandKitOptions.model_validate(
            {
                "fonts": manifest["editor"]["fonts"],
                "layouts": manifest["editor"]["layouts"],
                "image_positions": manifest["editor"]["image_positions"],
            }
        )
        sources = {
            key: f"/brand-kits/{KIT_ID}/v{KIT_VERSION}/{value.removeprefix('assets/')}"
            for key, value in manifest["editor"]["preview_sources"].items()
        }
        return BrandKitCatalog(
            kits=[
                BrandKitCatalogItem(
                    kit_id=KIT_ID,
                    kit_version=KIT_VERSION,
                    status=manifest["status"],
                    selectable=self._selectable,
                    segment=manifest["segment"],
                    preview_images=sources,
                    default_overrides=_default_overrides(name, manifest),
                    options=options,
                )
            ]
        )

    @staticmethod
    def _version(row: Any) -> BrandKitVersion:
        return BrandKitVersion.model_validate(
            {
                "version": row["version"],
                "state": row["state"],
                "kit_id": row["document"]["kit_id"],
                "kit_version": row["document"]["kit_version"],
                "overrides": row["document"]["overrides"],
                "created_at": row["created_at"],
            }
        )

    @staticmethod
    async def _state(session: Any, tenant: UUID, business: UUID) -> BrandKitState:
        head = (
            (
                await session.execute(
                    text("""SELECT version,confirmed_version FROM business_brand_kit_heads
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one_or_none()
        )
        if head is None:
            return BrandKitState(head_version=0)
        rows = (
            (
                await session.execute(
                    text("""SELECT version,state,document,created_at FROM business_brand_kit_versions
                      WHERE tenant_id=:tenant AND business_id=:business
                        AND version IN (:head,:confirmed)"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "head": head["version"],
                        "confirmed": head["confirmed_version"] or -1,
                    },
                )
            )
            .mappings()
            .all()
        )
        versions = {row["version"]: BrandKitService._version(row) for row in rows}
        latest = versions.get(head["version"])
        return BrandKitState(
            head_version=head["version"],
            confirmed=versions.get(head["confirmed_version"]),
            draft=latest if latest is not None and latest.state == "draft" else None,
        )

    async def read(self, tenant: UUID, business: UUID, actor: UUID) -> BrandKitState:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            return await self._state(session, tenant, business)

    async def history(self, tenant: UUID, business: UUID, actor: UUID) -> list[BrandKitVersion]:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT version,state,document,created_at FROM business_brand_kit_versions
                          WHERE tenant_id=:tenant AND business_id=:business
                          ORDER BY version DESC LIMIT 30"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [self._version(row) for row in rows]

    @staticmethod
    async def _replay(session: Any, tenant: UUID, business: UUID, operation: UUID, digest: str) -> BrandKitState | None:
        row = (
            (
                await session.execute(
                    text("""SELECT request_hash,response FROM business_brand_kit_versions
                      WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                    {"tenant": tenant, "business": business, "operation": operation},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["request_hash"] != digest:
            raise AuthError("BRAND_KIT_OPERATION_CONFLICT", 409)
        if row["response"] is None:
            raise AuthError("BRAND_KIT_OPERATION_INCOMPLETE", 409)
        return BrandKitState.model_validate(row["response"])

    @staticmethod
    async def _save_response(session: Any, tenant: UUID, business: UUID, version: int, state: BrandKitState) -> None:
        await session.execute(
            text("""UPDATE business_brand_kit_versions SET response=CAST(:response AS jsonb)
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
            {
                "tenant": tenant,
                "business": business,
                "version": version,
                "response": json.dumps(state.model_dump(mode="json"), ensure_ascii=False),
            },
        )

    @staticmethod
    async def _record(
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        action: str,
        version: int | None = None,
    ) -> None:
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,:action,:business)"""),
            {"tenant": tenant, "actor": actor, "operation": operation, "action": action, "business": business},
        )
        event_id = uuid5(NAMESPACE_URL, f"brand-kit/{tenant}/{business}/{operation}/{action}")
        await session.execute(
            text("""INSERT INTO outbox_events
              (id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,'brand_kit.changed',CAST(:payload AS jsonb))"""),
            {
                "id": event_id,
                "tenant": tenant,
                "payload": json.dumps(
                    {
                        "business_id": str(business),
                        "actor_id": str(actor),
                        "operation_id": str(operation),
                    }
                ),
            },
        )

    async def draft(self, tenant: UUID, business: UUID, actor: UUID, body: BrandKitDraftRequest) -> BrandKitState:
        digest = _digest(body.model_dump(mode="json"))
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            replay = await self._replay(session, tenant, business, body.operation_id, digest)
            if replay is not None:
                return replay
            if not self._selectable:
                raise AuthError("BRAND_KIT_NOT_SELECTABLE", 409)
            if body.overrides.logo_asset_id is not None and not await session.scalar(
                text("""SELECT 1 FROM business_brand_kit_logos
                  WHERE id=:logo AND tenant_id=:tenant AND business_id=:business AND state='ready'"""),
                {"logo": body.overrides.logo_asset_id, "tenant": tenant, "business": business},
            ):
                raise AuthError("BRAND_KIT_LOGO_NOT_FOUND", 409)
            await session.execute(
                text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id)
                  VALUES(:tenant,:business) ON CONFLICT DO NOTHING"""),
                {"tenant": tenant, "business": business},
            )
            version = await session.scalar(
                text("""UPDATE business_brand_kit_heads SET version=version+1
                  WHERE tenant_id=:tenant AND business_id=:business AND version=:expected
                  RETURNING version"""),
                {"tenant": tenant, "business": business, "expected": body.expected_version},
            )
            if version is None:
                replay = await self._replay(session, tenant, business, body.operation_id, digest)
                if replay is not None:
                    return replay
                raise AuthError("BRAND_KIT_VERSION_CONFLICT", 409)
            document = {
                "kit_id": body.kit_id,
                "kit_version": body.kit_version,
                "overrides": body.overrides.model_dump(mode="json"),
            }
            await session.execute(
                text("""INSERT INTO business_brand_kit_versions
                  (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
                  VALUES(:tenant,:business,:version,:operation,:actor,:digest,'draft',CAST(:document AS jsonb))"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "version": version,
                    "operation": body.operation_id,
                    "actor": actor,
                    "digest": digest,
                    "document": json.dumps(document, ensure_ascii=False),
                },
            )
            await self._record(session, tenant, business, actor, body.operation_id, "brand_kit.draft_saved", version)
            state = await self._state(session, tenant, business)
            await self._save_response(session, tenant, business, version, state)
            return state

    async def confirm(self, tenant: UUID, business: UUID, actor: UUID, body: BrandKitConfirmRequest) -> BrandKitState:
        digest = _digest(body.model_dump(mode="json"))
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            replay = await self._replay(session, tenant, business, body.operation_id, digest)
            if replay is not None:
                return replay
            if not self._selectable:
                raise AuthError("BRAND_KIT_NOT_SELECTABLE", 409)
            draft = (
                (
                    await session.execute(
                        text("""SELECT state,document FROM business_brand_kit_versions
                          WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
                        {"tenant": tenant, "business": business, "version": body.expected_version},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if draft is None or draft["state"] != "draft":
                raise AuthError("BRAND_KIT_DRAFT_REQUIRED", 409)
            version = await session.scalar(
                text("""UPDATE business_brand_kit_heads
                  SET version=version+1,confirmed_version=version+1
                  WHERE tenant_id=:tenant AND business_id=:business AND version=:expected
                  RETURNING version"""),
                {"tenant": tenant, "business": business, "expected": body.expected_version},
            )
            if version is None:
                replay = await self._replay(session, tenant, business, body.operation_id, digest)
                if replay is not None:
                    return replay
                raise AuthError("BRAND_KIT_VERSION_CONFLICT", 409)
            await session.execute(
                text("""INSERT INTO business_brand_kit_versions
                  (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
                  VALUES(:tenant,:business,:version,:operation,:actor,:digest,'confirmed',CAST(:document AS jsonb))"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "version": version,
                    "operation": body.operation_id,
                    "actor": actor,
                    "digest": digest,
                    "document": json.dumps(draft["document"], ensure_ascii=False),
                },
            )
            await self._record(session, tenant, business, actor, body.operation_id, "brand_kit.confirmed", version)
            state = await self._state(session, tenant, business)
            await self._save_response(session, tenant, business, version, state)
            return state

    @staticmethod
    async def _logo_row(session: Any, tenant: UUID, business: UUID, operation: UUID) -> Any:
        return (
            (
                await session.execute(
                    text("""SELECT id,request_hash,object_key,mime_type,state FROM business_brand_kit_logos
                      WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                    {"tenant": tenant, "business": business, "operation": operation},
                )
            )
            .mappings()
            .one_or_none()
        )

    async def upload_logo(
        self, tenant: UUID, business: UUID, actor: UUID, body: BrandKitLogoUpload
    ) -> BrandKitLogoRead:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            if not self._selectable:
                raise AuthError("BRAND_KIT_NOT_SELECTABLE", 409)
        await self.reconcile_pending_logos(tenant, business, actor)
        media, raw_digest = await asyncio.to_thread(_normalize_logo, body)
        digest = _digest({"sha256": raw_digest, "mime_type": body.mime_type, "rights_confirmed": True})
        logo_id = uuid5(NAMESPACE_URL, f"brand-kit-logo/{tenant}/{business}/{body.operation_id}")
        key = f"brand-kit-logos/{tenant}/{business}/{logo_id}.png"
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            replay = await self._logo_row(session, tenant, business, body.operation_id)
            if replay is not None:
                if replay["request_hash"] != digest:
                    raise AuthError("BRAND_KIT_OPERATION_CONFLICT", 409)
                if replay["state"] == "deleting":
                    raise AuthError("BRAND_KIT_LOGO_EXPIRED", 409)
                logo_id, key = replay["id"], replay["object_key"]
                ready = replay["state"] == "ready"
            else:
                inserted = await session.scalar(
                    text("""INSERT INTO business_brand_kit_logos
                      (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,
                       sha256,mime_type,size_bytes,state,rights_scope)
                      VALUES(:id,:tenant,:business,:operation,:actor,:digest,:key,:sha,'image/png',
                             :size,'pending','business_brand_confirmed')
                      ON CONFLICT DO NOTHING RETURNING id"""),
                    {
                        "id": logo_id,
                        "tenant": tenant,
                        "business": business,
                        "operation": body.operation_id,
                        "actor": actor,
                        "digest": digest,
                        "key": key,
                        "sha": media.sha256,
                        "size": len(media.data),
                    },
                )
                if inserted is None:
                    replay = await self._logo_row(session, tenant, business, body.operation_id)
                    if replay is None or replay["request_hash"] != digest:
                        raise AuthError("BRAND_KIT_OPERATION_CONFLICT", 409)
                    if replay["state"] == "deleting":
                        raise AuthError("BRAND_KIT_LOGO_EXPIRED", 409)
                    logo_id, key = replay["id"], replay["object_key"]
                    ready = replay["state"] == "ready"
                else:
                    ready = False
            if not ready:
                reserved = await session.scalar(
                    text("""UPDATE business_brand_kit_logos
                      SET upload_lease_until=clock_timestamp()+interval '10 minutes'
                      WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                        AND request_hash=:digest AND state='pending' RETURNING id"""),
                    {"id": logo_id, "tenant": tenant, "business": business, "digest": digest},
                )
                if reserved is None:
                    raise AuthError("BRAND_KIT_LOGO_EXPIRED", 409)
        if ready:
            return BrandKitLogoRead(id=logo_id, preview_url=await self.store.signed_url(key, "image/png"))
        await self.store.put(key, media)
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            changed = await session.scalar(
                text("""UPDATE business_brand_kit_logos SET state='ready'
                  WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                    AND request_hash=:digest AND state='pending' RETURNING id"""),
                {"id": logo_id, "tenant": tenant, "business": business, "digest": digest},
            )
            if changed is not None:
                await self._record(session, tenant, business, actor, body.operation_id, "brand_kit.logo_uploaded")
            elif not await session.scalar(
                text("""SELECT 1 FROM business_brand_kit_logos WHERE id=:id AND tenant_id=:tenant
                  AND business_id=:business AND request_hash=:digest AND state='ready'"""),
                {"id": logo_id, "tenant": tenant, "business": business, "digest": digest},
            ):
                raise AuthError("BRAND_KIT_LOGO_NOT_READY", 409)
        return BrandKitLogoRead(id=logo_id, preview_url=await self.store.signed_url(key, "image/png"))

    async def logo_url(self, tenant: UUID, business: UUID, actor: UUID, logo_id: UUID) -> BrandKitLogoUrl:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT object_key,mime_type FROM business_brand_kit_logos
                          WHERE id=:id AND tenant_id=:tenant AND business_id=:business AND state='ready'"""),
                        {"id": logo_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("BRAND_KIT_LOGO_NOT_FOUND", 404)
            key, mime = row["object_key"], row["mime_type"]
        return BrandKitLogoUrl(url=await self.store.signed_url(key, mime))

    async def reconcile_pending_logos(self, tenant: UUID, business: UUID, actor: UUID, limit: int = 10) -> int:
        """Owner-scoped cleanup; no cross-tenant reconciler credential is granted."""
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""WITH candidates AS (
                          SELECT id FROM business_brand_kit_logos
                          WHERE tenant_id=:tenant AND business_id=:business
                            AND ((state='pending' AND created_at<now()-interval '1 hour'
                              AND upload_lease_until<clock_timestamp())
                              OR (state='deleting' AND delete_lease_until<now()))
                          ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                          UPDATE business_brand_kit_logos l SET state='deleting',
                            delete_owner=:actor,delete_lease_until=now()+interval '60 seconds',
                            delete_fencing_token=l.delete_fencing_token+1
                          FROM candidates c WHERE l.id=c.id
                          RETURNING l.id,l.object_key,l.delete_fencing_token"""),
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
                    deleted = await session.scalar(
                        text("""DELETE FROM business_brand_kit_logos
                          WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                            AND state='deleting' AND delete_owner=:actor
                            AND delete_fencing_token=:fence AND delete_lease_until>now()
                          RETURNING id"""),
                        {
                            "id": row["id"],
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "fence": row["delete_fencing_token"],
                        },
                    )
                    if deleted is not None:
                        await session.execute(
                            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                              VALUES(:tenant,:actor,:operation,'brand_kit.logo_reconciled',:business)"""),
                            {
                                "tenant": tenant,
                                "actor": actor,
                                "operation": row["id"],
                                "business": business,
                            },
                        )
                        removed += 1
            except MaterialError:
                logger.warning("brand_kit.logo_reconcile_retry", extra={"logo_id": str(row["id"])})
        return removed
