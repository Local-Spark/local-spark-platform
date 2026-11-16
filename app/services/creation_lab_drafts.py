"""Private drafts and resumable stage events; no provider calls or customer writes."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.creation_lab import LabDraft
from app.services.auth import AuthError
from app.services.creation_lab_access import require_lab_access
from app.services.motion_context import MotionContext

ZERO = UUID(int=0)


class CreationLabDrafts:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database
        self.cipher = MotionContext(settings)

    async def create(self, actor: UUID, body: LabDraft) -> dict[str, Any]:
        run_id = uuid5(actor, f"creation-lab:{body.operation_id}")
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, "admin.creation_lab.draft.create")
            fingerprint = self.cipher.fingerprint(body.model_dump(mode="json"))
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,119))"), {"key": str(run_id)}
            )
            existing = (
                (await session.execute(text("SELECT * FROM creation_lab_runs WHERE id=:id"), {"id": run_id}))
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != fingerprint:
                    raise AuthError("CREATION_LAB_OPERATION_CONFLICT", 409)
                return self.present(dict(existing))
            if not await session.scalar(
                text("SELECT 1 FROM businesses WHERE tenant_id=:tenant AND id=:business"),
                {"tenant": body.tenant_id, "business": body.business_id},
            ):
                raise AuthError("CREATION_LAB_BUSINESS_NOT_FOUND", 404)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO creation_lab_runs
                          (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,
                           instruction_ciphertext,budget_usd_micros,flow_version)
                          VALUES(:id,:actor,:tenant,:business,:operation,:hash,:format,:mode,:instruction,:budget,2)
                          RETURNING *"""),
                        {
                            "id": run_id,
                            "actor": actor,
                            "tenant": body.tenant_id,
                            "business": body.business_id,
                            "operation": body.operation_id,
                            "hash": fingerprint,
                            "format": body.format,
                            "mode": body.mode,
                            "instruction": self.cipher.seal({"instruction": body.instruction}),
                            "budget": body.budget_usd_micros,
                        },
                    )
                )
                .mappings()
                .one()
            )
            await session.execute(
                text("""INSERT INTO creation_lab_events(run_id,sequence,event_id,kind)
                  VALUES(:run,1,:event,'draft.created')"""),
                {"run": run_id, "event": uuid5(run_id, "draft.created")},
            )
            return self.present(dict(row))

    def present(self, row: dict[str, Any]) -> dict[str, Any]:
        fields = (
            "id",
            "tenant_id",
            "business_id",
            "format",
            "flow_version",
            "mode",
            "state",
            "budget_usd_micros",
            "created_at",
            "committed_usd_micros",
            "finished_at",
            "trace_expires_at",
            "failure_code",
            "parent_run_id",
            "rehearsal_id",
            "attempt_number",
        )
        return {key: row[key] for key in fields} | self.cipher.open(row["instruction_ciphertext"])

    async def get(self, actor: UUID, run: UUID) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, "admin.creation_lab.draft.read")
            row = (
                (await session.execute(text("SELECT * FROM creation_lab_runs WHERE id=:id"), {"id": run}))
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_RUN_NOT_FOUND", 404)
            result = self.present(dict(row))
            # Explain historical generic failures from existing evidence only.
            # Never rewrite their financial state or repeat the provider call.
            if row["failure_code"] == "CREATION_LAB_IMAGE_EXECUTION_FAILED":
                raw = await session.scalar(
                    text("""SELECT payload_ciphertext FROM creation_lab_trace
                  WHERE run_id=:run AND id=:trace AND (CAST(:expires AS timestamptz) IS NULL OR CAST(:expires AS timestamptz)>clock_timestamp())"""),
                    {
                        "run": run,
                        "trace": uuid5(uuid5(run, "editorial"), "raw-response"),
                        "expires": row["trace_expires_at"],
                    },
                )
                if raw:
                    value = self.cipher.open(raw)["value"]
                    if (
                        isinstance(value, dict)
                        and value.get("status") == "incomplete"
                        and value.get("incomplete_details") == {"reason": "max_output_tokens"}
                    ):
                        result["diagnostic_code"] = "EDITORIAL_OUTPUT_LIMIT_EXCEEDED"
            return result

    async def history(self, actor: UUID, tenant: UUID, business: UUID) -> list[dict[str, Any]]:
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, "admin.creation_lab.history.read")
            rows = (
                (
                    await session.execute(
                        text("""SELECT * FROM creation_lab_runs WHERE tenant_id=:tenant AND business_id=:business AND origin='lab'
                          ORDER BY created_at DESC,id DESC LIMIT 50"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [self.present(dict(row)) for row in rows]

    async def events(self, actor: UUID, run: UUID, after: int) -> list[dict[str, Any]]:
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, "admin.creation_lab.events.read")
            if not await session.scalar(text("SELECT 1 FROM creation_lab_runs WHERE id=:id"), {"id": run}):
                raise AuthError("CREATION_LAB_RUN_NOT_FOUND", 404)
            rows = (
                (
                    await session.execute(
                        text("""SELECT e.sequence,e.event_id,e.kind,e.trace_id,e.created_at,t.stage AS trace_stage,t.effect_id AS operation_id,
                          CASE WHEN t.slot='partial' AND (r.trace_expires_at IS NULL OR r.trace_expires_at>clock_timestamp()) THEN t.payload_ciphertext END AS partial_ciphertext
                          FROM creation_lab_events e JOIN creation_lab_runs r ON r.id=e.run_id
                          LEFT JOIN creation_lab_trace t ON t.id=e.trace_id
                          WHERE e.run_id=:run AND e.sequence>:after ORDER BY e.sequence LIMIT 100"""),
                        {"run": run, "after": after},
                    )
                )
                .mappings()
                .all()
            )
            events = []
            for row in rows:
                item = dict(row)
                value = item.pop("partial_ciphertext")
                if value:
                    partial = self.cipher.open(value)["value"]
                    item["partial_text"] = partial["text"]
                    item["operation_id"] = partial["operation_id"]
                events.append(item)
            return events
