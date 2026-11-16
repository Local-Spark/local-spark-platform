"""Pin collection versions privately; selection never changes customer materials."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.creation_lab import LabCollectionSelection
from app.services.auth import AuthError
from app.services.creation_lab_context import CreationLabContext
from app.services.motion_context import MotionContext


class CreationLabCollection:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.context = CreationLabContext(settings, database)
        self.cipher = MotionContext(settings)

    async def select(self, actor: UUID, run: UUID, body: LabCollectionSelection) -> dict[str, Any]:
        async with self.context.scope(actor, run, "admin.creation_lab.collection.select") as (session, row):
            await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)})
            fingerprint = self.cipher.fingerprint([str(item) for item in body.photo_ids])
            previous = await session.scalar(
                text("SELECT request_hash FROM creation_lab_collection_changes WHERE run_id=:run AND operation_id=:op"),
                {"run": run, "op": body.operation_id},
            )
            if previous is not None:
                if previous != fingerprint:
                    raise AuthError("CREATION_LAB_OPERATION_CONFLICT", 409)
                return {"operation_id": body.operation_id, "replayed": True}
            if await session.scalar(text("SELECT state FROM creation_lab_runs WHERE id=:run"), {"run": run}) != "draft":
                raise AuthError("CREATION_LAB_DRAFT_REQUIRED", 409)
            choices = []
            for identifier in body.photo_ids:
                photo = (
                    (
                        await session.execute(
                            text("""SELECT id,version,title,sha256 FROM business_collection_photos
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id
                        AND state='ready' AND status='active' AND rights_scope='business_collection_confirmed'
                        AND delete_owner IS NULL AND delete_lease_until IS NULL AND sha256 IS NOT NULL"""),
                            {"tenant": row["tenant_id"], "business": row["business_id"], "id": identifier},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if photo is None:
                    raise AuthError("CREATION_LAB_COLLECTION_PHOTO_UNAVAILABLE", 409)
                choices.append(dict(photo))
            await session.execute(
                text("""INSERT INTO creation_lab_collection_choices(run_id,selection_ciphertext)
                  VALUES(:run,:selection) ON CONFLICT(run_id) DO UPDATE
                  SET selection_ciphertext=excluded.selection_ciphertext,updated_at=clock_timestamp()"""),
                {"run": run, "selection": self.cipher.seal({"photos": choices})},
            )
            await session.execute(
                text("""INSERT INTO creation_lab_collection_changes(run_id,operation_id,request_hash)
                  VALUES(:run,:op,:hash)"""),
                {"run": run, "op": body.operation_id, "hash": fingerprint},
            )
            await session.execute(
                text("""INSERT INTO creation_lab_events(run_id,sequence,event_id,kind)
                  SELECT :run,coalesce(max(sequence),0)+1,:event,'collection.selected'
                  FROM creation_lab_events WHERE run_id=:run"""),
                {"run": run, "event": uuid5(run, f"collection:{body.operation_id}")},
            )
            return {"operation_id": body.operation_id, "replayed": False}
