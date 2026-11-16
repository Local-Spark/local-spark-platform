"""Private material readers for the productive motion snapshot builder."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.auth import AuthError
from app.services.motion_context import MotionContext
from app.services.reference_generation_context import ReferenceGenerationSnapshot, read_generation_snapshot


class LabMotionContext(MotionContext):
    def __init__(self, settings: Settings, run: UUID):
        super().__init__(settings)
        self.run_id = run

    def select_default_photos(self) -> bool:
        return False

    async def source(self, session: AsyncSession, tenant: UUID, business: UUID, identifier: UUID) -> Any:
        return (
            (
                await session.execute(
                    text("""SELECT a.id,a.kind,a.object_key,a.mime_type,
          a.byte_size AS size_bytes,a.sha256 FROM creation_lab_attachments a
          JOIN creation_lab_runs r ON r.id=a.run_id
          WHERE r.id=:run AND r.tenant_id=:tenant AND r.business_id=:business AND a.id=:id
          AND a.state='ready' AND a.rights_confirmed AND a.kind='video' AND a.mime_type='video/mp4'"""),
                    {"run": self.run_id, "tenant": tenant, "business": business, "id": identifier},
                )
            )
            .mappings()
            .one_or_none()
        )

    async def photo(self, session: AsyncSession, tenant: UUID, business: UUID, identifier: UUID) -> Any:
        selected = await session.scalar(
            text("SELECT selection_ciphertext FROM creation_lab_collection_choices WHERE run_id=:run"),
            {"run": self.run_id},
        )
        choices = self.open(selected)["photos"] if selected else []
        expected = next((item for item in choices if item["id"] == str(identifier)), None)
        if expected is None:
            raise AuthError("CREATION_LAB_PHOTO_NOT_SELECTED", 409)
        # SELECT-only administrative scope: a row-lock would require customer UPDATE privileges.
        photo = (
            (
                await session.execute(
                    text("""SELECT id,version,title,item_id,space_kind,object_key,mime_type,size_bytes,sha256
          FROM business_collection_photos WHERE tenant_id=:tenant AND business_id=:business AND id=:id
          AND state='ready' AND status='active' AND rights_scope='business_collection_confirmed'
          AND delete_owner IS NULL AND delete_lease_until IS NULL"""),
                    {"tenant": tenant, "business": business, "id": identifier},
                )
            )
            .mappings()
            .one_or_none()
        )
        if photo is None or photo["version"] != expected["version"] or photo["sha256"] != expected["sha256"]:
            raise AuthError("CREATION_LAB_COLLECTION_CHANGED", 409)
        return photo

    async def references(self, session: AsyncSession, business: UUID) -> ReferenceGenerationSnapshot:
        return read_generation_snapshot(
            await session.scalar(text("SELECT creation_lab_reference_context(:business)"), {"business": business})
        )

    async def capture(self, session, tenant, business, request, *, previous=None):
        snapshot = await super().capture(session, tenant, business, request, previous=previous)
        rows = (
            (
                await session.execute(
                    text("""SELECT id,kind,object_key,mime_type,byte_size,sha256,name_ciphertext
          FROM creation_lab_attachments WHERE run_id=:run AND id<>:source AND state='ready' AND rights_confirmed ORDER BY id"""),
                    {"run": self.run_id, "source": request.source_asset_id},
                )
            )
            .mappings()
            .all()
        )
        photos = list(snapshot.get("collection_photos", []))
        for row in rows:
            if row["kind"] != "image" or row["mime_type"] not in {"image/png", "image/jpeg"}:
                raise AuthError("CREATION_LAB_REEL_MATERIAL_TYPE_UNSUPPORTED", 409)
            photos.append(
                {
                    "id": str(row["id"]),
                    "version": 1,
                    "title": self.open(row["name_ciphertext"])["name"],
                    "item_id": None,
                    "space_kind": None,
                    "object_key": row["object_key"],
                    "mime_type": row["mime_type"],
                    "size_bytes": row["byte_size"],
                    "sha256": row["sha256"],
                    "origin": "creation_lab_upload",
                }
            )
        if len(photos) > 4:
            raise AuthError("MOTION_COLLECTION_PHOTO_LIMIT", 409)
        if photos:
            snapshot["collection_photos"] = photos
        return snapshot
