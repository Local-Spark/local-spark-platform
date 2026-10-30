"""Read only the authorized image references selected by a validated briefing.

This service prepares in-memory provider inputs; it does not reserve money,
authorize a provider call, or persist a visual generation attempt. The caller
must bind the returned fingerprint to the durable attempt and revalidate before
and after every external effect.
"""

import asyncio
import hashlib
import io
from dataclasses import dataclass, field
from typing import Any, cast
from uuid import UUID

from PIL import Image
from sqlalchemy import text

from app.adapters.material_media import MaterialStore
from app.adapters.visual_ai import VisualReference
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.business_collection import normalize_photo
from app.services.editorial_briefings import EditorialBriefingService
from app.services.visual_context import VisualContextService, VisualContextSnapshot

_MAX_PROVIDER_BYTES = 5 * 1024 * 1024
_MAX_PROVIDER_PIXELS = 12_000_000


@dataclass(frozen=True)
class VisualReferenceSource:
    kind: str
    id: UUID
    version: int
    source_sha256: str
    normalized_sha256: str
    catalog_id: str | None = None
    asset_path: str | None = None


@dataclass(frozen=True)
class VisualReferenceBundle:
    context: VisualContextSnapshot
    sources: tuple[VisualReferenceSource, ...]
    references: tuple[VisualReference, ...] = field(repr=False)


class VisualReferenceService:
    """Prepare the submitted image and up to one item and one space photo."""

    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

    async def load(
        self, tenant: UUID, business: UUID, actor: UUID, proposal: UUID, *, candidate: bool = False
    ) -> VisualReferenceBundle:
        capture = VisualContextService(self.settings, self.database)
        before = await capture.capture(tenant, business, actor, proposal, candidate=candidate)
        params: dict[str, Any] = {"tenant": tenant, "business": business}
        selected: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        # Only the server's stored briefing is used; never trust client-supplied
        # object keys or a client-supplied snapshot. No storage I/O in the txn.
        async with self.database.transaction(tenant, actor) as session:
            status, catalog = await EditorialBriefingService(self.settings, self.database).read_valid(
                session, tenant, business, actor, before.briefing_id
            )
            if status != "prepared" or catalog is None:
                raise AuthError("VISUAL_BRIEFING_CHANGED", 409)
            source_result = await session.execute(
                text("""SELECT id,kind,object_key,mime_type,sha256 FROM whatsapp_material_assets
                  WHERE id=:source AND tenant_id=:tenant AND business_id=:business
                    AND delete_requested_at IS NULL AND (expires_at IS NULL OR expires_at>now())"""),
                {**params, "source": before.source_asset_id},
            )
            original = source_result.mappings().one_or_none()
            if original is None:
                raise AuthError("VISUAL_SOURCE_CHANGED", 409)
            if original["kind"] == "image":
                if (
                    not original["object_key"]
                    or not original["sha256"]
                    or original["mime_type"] not in {"image/jpeg", "image/png"}
                ):
                    raise AuthError("VISUAL_SOURCE_NOT_READY", 409)
                selected.append(
                    (
                        "source_photo",
                        {"id": str(before.source_asset_id), "version": 1, "sha256": original["sha256"]},
                        dict(original),
                    )
                )
            for kind in ("item_photo", "space_photo"):
                photo = cast(dict[str, Any] | None, catalog[kind])
                if photo is None:
                    continue
                result = await session.execute(
                    text("""SELECT object_key,mime_type FROM business_collection_photos
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id
                        AND version=:version AND sha256=:sha AND state='ready' AND status='active'
                        AND rights_scope='business_collection_confirmed'"""),
                    {**params, "id": UUID(photo["id"]), "version": photo["version"], "sha": photo["sha256"]},
                )
                found = result.mappings().one_or_none()
                if found is None:
                    raise AuthError("VISUAL_REFERENCE_CHANGED", 409)
                selected.append((kind, photo, dict(found)))
        references: list[VisualReference] = []
        sources: list[VisualReferenceSource] = []
        for kind, photo, row in selected:
            raw = await self.store.get_image(row["object_key"])
            if hashlib.sha256(raw).hexdigest() != photo["sha256"]:
                raise AuthError("VISUAL_REFERENCE_HASH_MISMATCH", 409)
            # EXIF orientation is applied and all metadata removed; do not
            # mutate the private original or treat its bytes as provider input.
            normalized = await asyncio.to_thread(normalize_photo, raw, row["mime_type"], _MAX_PROVIDER_BYTES)
            with Image.open(io.BytesIO(normalized.data)) as image:
                if (
                    len(normalized.data) > _MAX_PROVIDER_BYTES
                    or image.width > 4096
                    or image.height > 4096
                    or image.width * image.height > _MAX_PROVIDER_PIXELS
                ):
                    raise AuthError("VISUAL_REFERENCE_TOO_LARGE", 422)
            references.append(VisualReference(normalized.data, normalized.mime_type))
            sources.append(
                VisualReferenceSource(kind, UUID(photo["id"]), photo["version"], photo["sha256"], normalized.sha256)
            )
        after = await capture.capture(tenant, business, actor, proposal, candidate=candidate)
        if before != after:
            raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
        return VisualReferenceBundle(before, tuple(sources), tuple(references))
