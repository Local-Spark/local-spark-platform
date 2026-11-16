"""Private lab approvals, deliberately never projected into publishable pieces."""

from uuid import UUID, uuid5

from sqlalchemy import bindparam, text

from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.creation_lab_access import require_lab_access
from app.services.creation_lab_execution import CreationLabExecution


class LabPieceApprovalService:
    def __init__(self, settings, database):
        self.settings, self.database = settings, database
        self.execution = CreationLabExecution(settings, database)

    async def approve(self, actor, run, body):
        async with self.database.transaction(UUID(int=0), actor) as s:
            await require_lab_access(s, self.settings, actor, "admin.creation_lab.piece.approve")
            row = await self.execution.guard(s, actor, run, "admin.creation_lab.piece.approve")
            if row["origin"] != "lab" or row["state"] != "completed":
                raise AuthError("LAB_COMPLETED_PIECE_REQUIRED", 409)
            await s.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,134))"),
                {"key": f"{actor}:{body.operation_id}"},
            )
            await s.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,133))"), {"key": str(body.version_id)}
            )
            valid = await s.scalar(
                text("SELECT 1 FROM creation_lab_versions WHERE run_id=:r AND id=:v AND sha256=:sha"),
                {"r": run, "v": body.version_id, "sha": body.sha256},
            )
            if not valid:
                raise AuthError("CREATION_LAB_RESULT_CHANGED", 409)
            prior = (
                (
                    await s.execute(
                        text("SELECT * FROM creation_lab_approvals WHERE actor_id=:a AND operation_id=:op"),
                        {"a": actor, "op": body.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if prior and (prior["run_id"], prior["version_id"], prior["sha256"]) != (run, body.version_id, body.sha256):
                raise AuthError("LAB_APPROVAL_OPERATION_CONFLICT", 409)
            inserted = await s.scalar(
                text("""INSERT INTO creation_lab_approvals(version_id,run_id,actor_id,operation_id,sha256)
              VALUES(:v,:r,:a,:op,:sha) ON CONFLICT(version_id) DO NOTHING RETURNING version_id"""),
                {"v": body.version_id, "r": run, "a": actor, "op": body.operation_id, "sha": body.sha256},
            )
            if inserted:
                await s.execute(text("SELECT set_config('app.tenant_id',:t,true)"), {"t": str(row["tenant_id"])})
                await _event(
                    s,
                    row["tenant_id"],
                    row["business_id"],
                    actor,
                    uuid5(body.version_id, "lab-approved"),
                    "creation_lab.piece_approved",
                )
            return {"version_id": body.version_id, "approved": True}

    async def list(self, actor, tenant, business):
        async with self.database.transaction(UUID(int=0), actor) as s:
            await require_lab_access(s, self.settings, actor, "admin.creation_lab.approved.list")
            rows = (
                (
                    await s.execute(
                        text("""SELECT v.id,v.run_id,v.number,v.sha256,v.mime_type,v.selected,v.review_verdict,
              r.attempt_number,a.created_at AS approved_at,v.copy_ciphertext,
              root.instruction_ciphertext AS original_message_ciphertext FROM creation_lab_approvals a
              JOIN creation_lab_versions v ON v.id=a.version_id AND v.run_id=a.run_id
              JOIN creation_lab_runs r ON r.id=a.run_id
              LEFT JOIN creation_lab_runs root ON root.id=coalesce(r.rehearsal_id,r.id)
                AND root.tenant_id=r.tenant_id AND root.business_id=r.business_id AND root.origin='lab'
              WHERE r.tenant_id=:t AND r.business_id=:b AND r.origin='lab' AND a.actor_id=:a
              ORDER BY a.created_at DESC LIMIT 100"""),
                        {"t": tenant, "b": business, "a": actor},
                    )
                )
                .mappings()
                .all()
            )
            feedback_by_version = {}
            if rows:
                feedback = (
                    (
                        await s.execute(
                            text("""SELECT f.id,f.version_id,f.timestamp_ms,f.created_at,f.note_ciphertext
                  FROM creation_lab_feedback f
                  JOIN creation_lab_approvals a ON a.version_id=f.version_id AND a.run_id=f.run_id
                  WHERE a.actor_id=:actor AND f.version_id IN :versions
                  ORDER BY f.created_at,f.id""").bindparams(bindparam("versions", expanding=True)),
                            {"actor": actor, "versions": [r["id"] for r in rows]},
                        )
                    )
                    .mappings()
                    .all()
                )
                for item in feedback:
                    feedback_by_version.setdefault(item["version_id"], []).append(
                        {k: v for k, v in item.items() if k != "note_ciphertext"}
                        | self.execution.cipher.open(item["note_ciphertext"])
                    )
            return [
                {k: v for k, v in r.items() if k not in {"copy_ciphertext", "original_message_ciphertext"}}
                | {
                    "copy": self.execution.cipher.open(r["copy_ciphertext"]) if r["copy_ciphertext"] else None,
                    "original_message": (
                        self.execution.cipher.open(r["original_message_ciphertext"])["instruction"]
                        if r["original_message_ciphertext"]
                        else None
                    ),
                    "is_test": True,
                    "approved": True,
                    "feedback": feedback_by_version.get(r["id"], []),
                }
                for r in rows
            ]
