"""Private material uploads with committed one-shot claims and authenticated reads."""

import hashlib
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.material_media import MAX_BYTES, MIME_TYPES, FetchedMedia, MaterialError, MaterialStore, inspect_media
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creation_lab_access import require_lab_access
from app.services.creation_lab_drafts import ZERO
from app.services.motion_context import MotionContext


class CreationLabAttachments:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database
        self.cipher, self.store = MotionContext(settings), MaterialStore(settings)

    async def authorize(self, actor: UUID, run: UUID, action: str) -> None:
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, action)

    async def guard(self, session: AsyncSession, actor: UUID, run: UUID, action: str) -> None:
        await require_lab_access(session, self.settings, actor, action)
        if not await session.scalar(text("SELECT 1 FROM creation_lab_runs WHERE id=:run"), {"run": run}):
            raise AuthError("CREATION_LAB_RUN_NOT_FOUND", 404)

    def present(self, row: Any) -> dict[str, Any]:
        fields = ("id", "run_id", "kind", "mime_type", "sha256", "byte_size", "state", "created_at")
        return {key: row[key] for key in fields} | self.cipher.open(row["name_ciphertext"])

    @staticmethod
    def media_kind(mime: str) -> str:
        for kind, accepted in MIME_TYPES.items():
            if mime in accepted:
                return kind
        raise AuthError("CREATION_LAB_MEDIA_TYPE_UNSUPPORTED", 415)

    @staticmethod
    async def event(session: AsyncSession, run: UUID, operation: UUID, state: str) -> None:
        # All attachment writers serialize before assigning a sequence.
        await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)})
        await session.execute(
            text("""INSERT INTO creation_lab_events(run_id,sequence,event_id,kind)
              SELECT :run,coalesce(max(sequence),0)+1,:event,:kind
              FROM creation_lab_events WHERE run_id=:run"""),
            {"run": run, "event": uuid5(operation, f"attachment.{state}"), "kind": f"attachment.{state}"},
        )

    async def upload(
        self, actor: UUID, run: UUID, operation: UUID, name: str, mime: str, data: bytes
    ) -> dict[str, Any]:
        kind = self.media_kind(mime)
        if not 0 < len(data) <= MAX_BYTES[kind]:
            raise AuthError("CREATION_LAB_MEDIA_TOO_LARGE", 413)
        if not self.settings.material_storage_bucket:
            raise AuthError("MATERIAL_STORAGE_NOT_CONFIGURED", 409)
        media = FetchedMedia(data, mime, hashlib.sha256(data).hexdigest())
        identifier = uuid5(run, f"attachment:{operation}")
        fingerprint = self.cipher.fingerprint({"name": name, "mime": mime, "sha256": media.sha256})
        await self.authorize(actor, run, "admin.creation_lab.attachment.prepare")
        try:
            await inspect_media(media, kind)
        except MaterialError as exc:
            raise AuthError(exc.code, 503 if exc.retryable else 422) from None
        key = f"creation-lab/{actor}/{run}/{identifier}"
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, "admin.creation_lab.attachment.claim")
            await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)})
            state = await session.scalar(text("SELECT state FROM creation_lab_runs WHERE id=:run"), {"run": run})
            existing = (
                (await session.execute(text("SELECT * FROM creation_lab_attachments WHERE id=:id"), {"id": identifier}))
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != fingerprint:
                    raise AuthError("CREATION_LAB_OPERATION_CONFLICT", 409)
                # A repeated request never repeats an upload, even after an ambiguous timeout.
                return self.present(existing)
            if state != "draft":
                raise AuthError("CREATION_LAB_DRAFT_REQUIRED", 409)
            count, size = (
                await session.execute(
                    text("SELECT count(*),coalesce(sum(byte_size),0) FROM creation_lab_attachments WHERE run_id=:run"),
                    {"run": run},
                )
            ).one()
            if count >= 8 or size + len(data) > 100 * 1024 * 1024:
                raise AuthError("CREATION_LAB_ATTACHMENT_LIMIT", 409)
            await session.execute(
                text("""INSERT INTO creation_lab_attachments
                  (id,run_id,operation_id,request_hash,name_ciphertext,object_key,kind,mime_type,
                   sha256,byte_size,rights_confirmed,state)
                  VALUES(:id,:run,:operation,:hash,:name,:key,:kind,:mime,:sha,:size,true,'uploading')"""),
                {
                    "id": identifier,
                    "run": run,
                    "operation": operation,
                    "hash": fingerprint,
                    "name": self.cipher.seal({"name": name}),
                    "key": key,
                    "kind": kind,
                    "mime": mime,
                    "sha": media.sha256,
                    "size": len(data),
                },
            )
            await self.event(session, run, identifier, "uploading")
        outcome = "ready"
        try:
            await self.store.put(key, media)
        except Exception:
            outcome = "uncertain"
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, "admin.creation_lab.attachment.finish")
            row = (
                (
                    await session.execute(
                        text("""UPDATE creation_lab_attachments SET state=:state
                      WHERE id=:id AND state='uploading' RETURNING *"""),
                        {"id": identifier, "state": outcome},
                    )
                )
                .mappings()
                .one()
            )
            await self.event(session, run, identifier, outcome)
            return self.present(row)

    async def list(self, actor: UUID, run: UUID) -> list[dict[str, Any]]:
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, "admin.creation_lab.attachments.read")
            rows = (
                (
                    await session.execute(
                        text("SELECT * FROM creation_lab_attachments WHERE run_id=:run ORDER BY created_at,id"),
                        {"run": run},
                    )
                )
                .mappings()
                .all()
            )
            return [self.present(row) for row in rows]

    async def download(self, actor: UUID, run: UUID, identifier: UUID) -> tuple[dict[str, Any], bytes]:
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, "admin.creation_lab.attachment.download")
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM creation_lab_attachments WHERE run_id=:run AND id=:id"),
                        {"run": run, "id": identifier},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_ATTACHMENT_NOT_FOUND", 404)
            if row["state"] != "ready":
                raise AuthError("CREATION_LAB_ATTACHMENT_NOT_READY", 409)
            metadata, key = self.present(row), row["object_key"]
        try:
            fetch = {"image": self.store.get_image, "audio": self.store.get_audio, "video": self.store.get_video}
            data = await fetch[metadata["kind"]](key)
        except MaterialError as exc:
            raise AuthError(exc.code, 503) from None
        if len(data) != metadata["byte_size"] or hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise AuthError("CREATION_LAB_ATTACHMENT_CHANGED", 409)
        # Storage IO never holds database locks; recheck revocation before releasing bytes.
        await self.authorize(actor, run, "admin.creation_lab.attachment.release")
        return metadata, data
