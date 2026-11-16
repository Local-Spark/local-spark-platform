"""Dispatch authenticated private events into the productive motion stages."""

from dataclasses import replace
from uuid import UUID, uuid5

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_images import LabImageRequests, LabImageRunner
from app.services.creation_lab_motion_requests import LabMotionRequests
from app.services.creation_lab_motion_output import LabMotionOrchestrator
from app.services.motion_runtime import build_motion_runner
from app.workflows.contracts import BusinessEvent


class CreationLabRunner:
    def __init__(self, settings: Settings, database: Database):
        from app.services.creation_lab_settings import lab_settings

        self.settings, self.database = lab_settings(settings), database

    async def run(self, event: BusinessEvent) -> str:
        run, actor = UUID(event.operation_id), UUID(event.actor_id)
        requests = LabMotionRequests(self.settings, self.database, run)
        async with self.database.transaction(ZERO, actor) as session:
            row = await requests.execution.guard(session, actor, run, "admin.creation_lab.execution.dispatch")
            if str(row["tenant_id"]) != event.tenant_id or str(row["business_id"]) != event.business_id:
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            await requests.scope(session, row)
            kind = await session.scalar(
                text("""SELECT event_type FROM outbox_events WHERE id=:event AND tenant_id=:tenant
              AND payload->>'actor_id'=:actor AND payload->>'business_id'=:business AND payload->>'operation_id'=:run"""),
                {
                    "event": UUID(event.event_id),
                    "tenant": row["tenant_id"],
                    "actor": str(actor),
                    "business": event.business_id,
                    "run": str(run),
                },
            )
            if kind not in {
                "creation_lab.requested",
                "creation_lab.plan_approved",
                "creation_lab.render_approved",
                "creation_lab.storyboard_approved",
                "creation_lab.catalog_approved",
                "creation_lab.editorial_approved",
            } or UUID(event.event_id) != uuid5(run, kind):
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            format = row["format"]
        translated = replace(event, event_id=str(uuid5(run, kind.replace("creation_lab.", "motion."))))
        if format in {"photo", "story"}:
            if kind not in {
                "creation_lab.requested",
                "creation_lab.catalog_approved",
                "creation_lab.editorial_approved",
            }:
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            return await LabImageRunner(LabImageRequests(self.settings, self.database, run)).run(
                translated, kind.split(".")[1]
            )
        if kind not in {
            "creation_lab.requested",
            "creation_lab.plan_approved",
            "creation_lab.render_approved",
            "creation_lab.storyboard_approved",
        }:
            raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
        productive = build_motion_runner(
            self.settings, self.database, self.database, requests=requests, administrative=True
        )
        return await LabMotionOrchestrator(productive, run).run(translated)

    async def fail(self, event: BusinessEvent) -> None:
        requests = LabMotionRequests(self.settings, self.database, UUID(event.operation_id))
        async with self.database.transaction(ZERO, UUID(event.actor_id)) as session:
            row = await requests.execution.guard(
                session, UUID(event.actor_id), requests.run_id, "admin.creation_lab.execution.failure"
            )
            if str(row["tenant_id"]) != event.tenant_id or str(row["business_id"]) != event.business_id:
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            await requests.scope(session, row)
            kind = await session.scalar(
                text(
                    "SELECT event_type FROM outbox_events WHERE id=:id AND tenant_id=:tenant AND payload->>'operation_id'=:run AND payload->>'actor_id'=:actor"
                ),
                {
                    "id": UUID(event.event_id),
                    "tenant": row["tenant_id"],
                    "run": str(requests.run_id),
                    "actor": event.actor_id,
                },
            )
            if not kind or not kind.startswith("creation_lab.") or UUID(event.event_id) != uuid5(requests.run_id, kind):
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            owns_stage = row["execution_event_id"] == uuid5(requests.run_id, kind.replace("creation_lab.", "motion."))
            if row["finished_at"] is None and (
                (row["state"] == "queued" and kind == "creation_lab.requested")
                or (row["state"] == "running" and owns_stage)
            ):
                await requests.execution.finish_locked(session, row, "failed", "CREATION_LAB_EXECUTION_INTERRUPTED")
