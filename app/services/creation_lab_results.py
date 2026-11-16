"""Authenticated private results and version-bound feedback; never publishes."""

import hashlib
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.material_media import MaterialError, MaterialStore
from app.core.config import Settings
from app.db.session import Database
from app.schemas.creation_lab import LabFeedback
from app.services.auth import AuthError
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_execution import CreationLabExecution


class CreationLabResults:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.execution = CreationLabExecution(settings, database)
        self.database, self.store = database, MaterialStore(settings)

    async def list(self, actor: UUID, run: UUID) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as session:
            state = await self.execution.guard(session, actor, run, "admin.creation_lab.results.read")
            versions = (
                (
                    await session.execute(
                        text("""SELECT v.id,v.run_id,r.attempt_number,v.number,v.sha256,v.mime_type,v.size_bytes,v.selected,
              v.review_verdict,v.copy_ciphertext,v.created_at,
              EXISTS(SELECT 1 FROM creation_lab_approvals a WHERE a.version_id=v.id) AS approved
              FROM creation_lab_versions v
              JOIN creation_lab_runs r ON r.id=v.run_id
              WHERE coalesce(r.rehearsal_id,r.id)=:root AND r.tenant_id=:tenant AND r.business_id=:business
              ORDER BY r.attempt_number,v.number"""),
                        {
                            "root": state["rehearsal_id"] or run,
                            "tenant": state["tenant_id"],
                            "business": state["business_id"],
                        },
                    )
                )
                .mappings()
                .all()
            )
            feedback = (
                (
                    await session.execute(
                        text("""SELECT f.id,f.version_id,f.note_ciphertext,f.timestamp_ms,f.created_at
              FROM creation_lab_feedback f JOIN creation_lab_runs r ON r.id=f.run_id
              WHERE coalesce(r.rehearsal_id,r.id)=:root AND r.tenant_id=:tenant AND r.business_id=:business
              ORDER BY f.created_at,f.id LIMIT 5000"""),
                        {
                            "root": state["rehearsal_id"] or run,
                            "tenant": state["tenant_id"],
                            "business": state["business_id"],
                        },
                    )
                )
                .mappings()
                .all()
            )
            return {
                "state": state["state"],
                "trace_expires_at": state["trace_expires_at"],
                "versions": [
                    {k: v for k, v in item.items() if k != "copy_ciphertext"}
                    | {"copy": self.execution.cipher.open(item["copy_ciphertext"]) if item["copy_ciphertext"] else None}
                    for item in versions
                ],
                "feedback": [
                    {
                        "id": item["id"],
                        "version_id": item["version_id"],
                        "timestamp_ms": item["timestamp_ms"],
                        "created_at": item["created_at"],
                        **self.execution.cipher.open(item["note_ciphertext"]),
                    }
                    for item in feedback
                ],
            }

    async def feedback(self, actor: UUID, run: UUID, body: LabFeedback) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, run, "admin.creation_lab.feedback.create")
            fingerprint = self.execution.cipher.fingerprint(body.model_dump(mode="json"))
            identifier = uuid5(run, f"feedback:{body.operation_id}")
            previous = await session.scalar(
                text("SELECT request_hash FROM creation_lab_feedback WHERE id=:id"), {"id": identifier}
            )
            if previous is not None:
                if previous != fingerprint:
                    raise AuthError("CREATION_LAB_OPERATION_CONFLICT", 409)
                return {"id": identifier}
            mime = await session.scalar(
                text("SELECT mime_type FROM creation_lab_versions WHERE id=:id AND run_id=:run"),
                {"id": body.version_id, "run": run},
            )
            if mime is None:
                raise AuthError("CREATION_LAB_VERSION_NOT_FOUND", 404)
            if body.timestamp_ms is not None and mime != "video/mp4":
                raise AuthError("CREATION_LAB_VIDEO_TIMESTAMP_REQUIRED", 422)
            if (
                int(
                    await session.scalar(
                        text("SELECT count(*) FROM creation_lab_feedback WHERE run_id=:run"), {"run": run}
                    )
                    or 0
                )
                >= 500
            ):
                raise AuthError("CREATION_LAB_FEEDBACK_LIMIT", 409)
            await session.execute(
                text("""INSERT INTO creation_lab_feedback
              (id,run_id,version_id,operation_id,request_hash,note_ciphertext,timestamp_ms)
              VALUES(:id,:run,:version,:operation,:hash,:note,:timestamp)"""),
                {
                    "id": identifier,
                    "run": run,
                    "version": body.version_id,
                    "operation": body.operation_id,
                    "hash": fingerprint,
                    "note": self.execution.cipher.seal({"note": body.note}),
                    "timestamp": body.timestamp_ms,
                },
            )
            await self.execution.event(session, run, uuid5(identifier, "recorded"), "feedback.recorded")
            return {"id": identifier}

    async def download(self, actor: UUID, run: UUID, version: UUID) -> tuple[str, bytes]:
        async with self.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, run, "admin.creation_lab.result.download")
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM creation_lab_versions WHERE run_id=:run AND id=:id"),
                        {"run": run, "id": version},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_VERSION_NOT_FOUND", 404)
            metadata = dict(row)
        try:
            data = (
                await self.store.get_video(metadata["object_key"])
                if metadata["mime_type"] == "video/mp4"
                else await self.store.get_motion_payload(metadata["object_key"])
            )
        except MaterialError as exc:
            raise AuthError(exc.code, 503) from None
        if len(data) != metadata["size_bytes"] or hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise AuthError("CREATION_LAB_RESULT_CHANGED", 409)
        async with self.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, run, "admin.creation_lab.result.release")
        return metadata["mime_type"], data
