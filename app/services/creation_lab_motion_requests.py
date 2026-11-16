"""Administrative admission adapter for the productive motion orchestrator."""

from typing import Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.schemas.creation_lab import LabStart
from app.schemas.motion_preparation import MotionPreparation
from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.creation_lab_drafts import ZERO, CreationLabDrafts
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_motion_context import LabMotionContext
from app.services.motion_context import digest
from app.services.motion_requests import MotionRequestService


class LabMotionRequests(MotionRequestService):
    formats = {"reel"}

    def minimum_budget(self) -> int:
        return 2 * self.settings.motion_ai_reservation_usd_micros

    def __init__(self, settings: Settings, database: Database, run: UUID):
        from app.services.creation_lab_settings import lab_settings

        settings = lab_settings(settings)
        super().__init__(settings, database)
        self.run_id = run
        self.context = LabMotionContext(settings, run)
        self.execution = CreationLabExecution(settings, database)

    async def scope(self, session: AsyncSession, row: Any) -> None:
        if row["id"] != self.run_id:
            raise AuthError("CREATION_LAB_RUN_MISMATCH", 409)
        await session.execute(
            text("""SELECT set_config('app.tenant_id',:tenant,true),
          set_config('app.creation_lab_run_id',:run,true)"""),
            {"tenant": str(row["tenant_id"]), "run": str(self.run_id)},
        )

    async def admission_scope(self, session: AsyncSession, tenant: UUID, business: UUID) -> None:
        row = (
            (await session.execute(text("SELECT * FROM creation_lab_runs WHERE id=:run"), {"run": self.run_id}))
            .mappings()
            .one_or_none()
        )
        if row is None or (row["tenant_id"], row["business_id"]) != (tenant, business):
            raise AuthError("CREATION_LAB_RUN_MISMATCH", 409)
        await self.execution.guard(session, row["actor_id"], self.run_id, "admin.creation_lab.execution.admission")
        await self.scope(session, row)
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,48))"),
            {"key": f"visual-consent:{tenant}:{business}"},
        )

        from app.services.visual_pending_changes import VisualPendingChanges

        if await VisualPendingChanges.has_pending_in_session(session, tenant, business):
            raise AuthError("VISUAL_CHANGE_PENDING", 409)

    async def _admission(self, session: AsyncSession, tenant: UUID, business: UUID) -> None:
        await self.admission_scope(session, tenant, business)
        if not self.settings.motion_execution_ready(administrative=True) or not self.settings.motion_storyboard_enabled:
            raise AuthError("MOTION_EXECUTION_NOT_CONFIGURED", 409)
        if await self.gate._state(session, tenant, business) != "active":
            raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)

    async def normalized(self, session: AsyncSession, row: Any) -> dict[str, Any]:
        ciphertext = await session.scalar(
            text("SELECT payload_ciphertext FROM creation_lab_trace WHERE id=:id AND run_id=:run"),
            {"id": row["snapshot_trace_id"], "run": self.run_id},
        )
        if not ciphertext:
            raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
        snapshot = self.context.open(ciphertext)["value"]
        return dict(row) | {
            "operation_id": self.run_id,
            "snapshot_ciphertext": self.context.seal(snapshot),
            "source_asset_id": UUID(snapshot["request"]["source_asset_id"]),
            "max_corrections": snapshot["execution"]["max_corrections"],
        }

    async def start(self, actor: UUID, body: LabStart) -> dict[str, Any]:
        fingerprint = digest(body.model_dump(mode="json"))
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run_id, "admin.creation_lab.run.start")
            if row["start_hash"]:
                if row["start_hash"] != fingerprint:
                    raise AuthError("CREATION_LAB_START_CONFLICT", 409)
                return CreationLabDrafts(self.settings, self.database).present(dict(row))
            if row["state"] != "draft" or row["format"] not in self.formats:
                raise AuthError("CREATION_LAB_REEL_DRAFT_REQUIRED", 409)
            if row["format"] == "reel" and body.source_attachment_id is None:
                raise AuthError("CREATION_LAB_VIDEO_REQUIRED", 422)
            await self.scope(session, row)
            await self._admission(session, row["tenant_id"], row["business_id"])
            if (
                self.settings.creation_lab_budget_usd_micros
                and row["budget_usd_micros"] > self.settings.creation_lab_budget_usd_micros
            ):
                raise AuthError("CREATION_LAB_ADMIN_BUDGET_EXCEEDED", 409)
            committed = int(
                await session.scalar(
                    text("SELECT coalesce(sum(committed_usd_micros),0) FROM creation_lab_runs WHERE actor_id=:actor"),
                    {"actor": actor},
                )
                or 0
            )
            if (
                self.settings.creation_lab_budget_usd_micros
                and self.settings.creation_lab_budget_usd_micros - committed < self.minimum_budget()
            ):
                raise AuthError("CREATION_LAB_ADMIN_BUDGET_EXCEEDED", 409)
            if row["budget_usd_micros"] < self.minimum_budget():
                raise AuthError("MOTION_BUDGET_REQUIRED", 409)
            if await session.scalar(
                text("SELECT 1 FROM creation_lab_attachments WHERE run_id=:run AND state<>'ready' LIMIT 1"),
                {"run": self.run_id},
            ):
                raise AuthError("CREATION_LAB_UPLOAD_UNRESOLVED", 409)
            snapshot = await self.build_snapshot(session, row, body)
            snapshot["execution"]["request_budget"] = row["budget_usd_micros"]
            trace = uuid5(self.run_id, "snapshot")
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,'context','evidence',:payload)"""),
                {"id": trace, "run": self.run_id, "payload": self.context.seal({"value": snapshot})},
            )
            await session.execute(
                text("""UPDATE creation_lab_runs SET state='queued',start_hash=:hash,
              snapshot_trace_id=:trace,source_fingerprint=:fingerprint WHERE id=:run"""),
                {
                    "run": self.run_id,
                    "hash": fingerprint,
                    "trace": trace,
                    "fingerprint": self.context.fingerprint(snapshot),
                },
            )
            await self.execution.event(session, self.run_id, uuid5(self.run_id, "queued"), "run.queued", trace)
            await _event(session, row["tenant_id"], row["business_id"], actor, self.run_id, "creation_lab.requested")
        return await CreationLabDrafts(self.settings, self.database).get(actor, self.run_id)

    async def build_snapshot(self, session: AsyncSession, row: Any, body: LabStart) -> dict[str, Any]:
        message = self.context.open(row["instruction_ciphertext"])["instruction"]
        choices = await session.scalar(
            text("SELECT selection_ciphertext FROM creation_lab_collection_choices WHERE run_id=:run"),
            {"run": self.run_id},
        )
        photos = self.context.open(choices)["photos"] if choices else []
        preparation = MotionPreparation.model_validate(
            {
                "client_message": message,
                "decisions": [
                    {
                        "id": f"request-{i}",
                        "kind": "requirement",
                        "origin": "client",
                        "source_excerpt": message[i : i + 1000],
                        "interpretation": "Trecho literal do pedido; preservar seu sentido no planejamento.",
                        "scope": "request",
                    }
                    for i in range(0, len(message), 1000)
                ],
                "evidence": [
                    {
                        "id": "source-start",
                        "kind": "source",
                        "at_ms": [0],
                        "observation": "Vídeo anexado pelo administrador; conteúdo visual ainda será inspecionado pelo modelo.",
                        "intended_use": "Usar a fonte e os frames extraídos pelo fluxo produtivo para planejar a peça.",
                        "limitations": "Esta seleção inicial não representa aprovação estética nem análise do movimento.",
                    }
                ],
            }
        )
        request = MotionRequest(
            operation_id=self.run_id,
            instruction=message,
            source_asset_id=body.source_attachment_id,
            storyboard=True,
            review_checkpoints=True,
            propose_direction=True,
            preparation=preparation,
            collection_photo_ids=tuple(UUID(p["id"]) for p in photos),
        )
        snapshot = await self.context.capture(session, row["tenant_id"], row["business_id"], request)
        return snapshot

    async def current(self, session: AsyncSession, row: Any) -> None:
        await self.scope(session, row)
        await self._admission(session, row["tenant_id"], row["business_id"])
        snapshot = self.context.open(row["snapshot_ciphertext"])
        current = await self.context.capture(
            session,
            row["tenant_id"],
            row["business_id"],
            MotionRequest.model_validate(snapshot["request"]),
            previous=snapshot,
        )
        current["execution"]["request_budget"] = row["budget_usd_micros"]
        if self.context.fingerprint(current) != row["source_fingerprint"]:
            raise AuthError("MOTION_CONTEXT_CHANGED", 409)

    async def locked_running(self, session: AsyncSession, row: dict[str, Any], token: UUID) -> Any:
        current = await self.execution.guard(
            session, row["actor_id"], self.run_id, "admin.creation_lab.execution.authorize"
        )
        self.execution.fence(current, token)
        normalized = await self.normalized(session, current)
        await self.current(session, normalized)
        return normalized

    async def begin(
        self, tenant: UUID, business: UUID, actor: UUID, operation: UUID, event_id: UUID
    ) -> tuple[dict[str, Any], UUID] | None:
        if operation != self.run_id or event_id != uuid5(operation, "motion.requested"):
            raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run_id, "admin.creation_lab.execution.begin")
            if (row["tenant_id"], row["business_id"]) != (tenant, business):
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            if row["state"] != "queued":
                return None
            normalized = await self.normalized(session, row)
            await self.current(session, normalized)
            token = uuid4()
            await session.execute(
                text(
                    "UPDATE creation_lab_runs SET state='running',execution_token=:token,execution_event_id=:event WHERE id=:run"
                ),
                {"run": self.run_id, "token": token, "event": event_id},
            )
            await self.execution.event(session, self.run_id, uuid5(self.run_id, "started"), "run.started")
            return normalized, token
