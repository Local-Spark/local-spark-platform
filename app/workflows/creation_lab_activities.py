"""Restricted cleanup capability; never deletes original materials or final pieces."""

from uuid import UUID

from sqlalchemy import text
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.config import Settings
from app.db.session import Database
from app.workflows.contracts import BusinessEvent
from app.services.creation_lab_drafts import ZERO


class CreationLabActivities:
    def __init__(self, database: Database) -> None:
        self.database = database

    @activity.defn(name="expire_creation_lab_trace")
    async def expire_trace(self, identifier: str) -> int:
        run = UUID(identifier)
        async with self.database.transaction(ZERO, ZERO) as session:
            return int(await session.scalar(text("SELECT creation_lab_expire_trace(:run)"), {"run": run}))


class CreationLabProductionActivities:
    def __init__(self, settings: Settings, database: Database):
        from app.services.creation_lab_runner import CreationLabRunner

        self.runner = CreationLabRunner(settings, database)

    @activity.defn(name="run_creation_lab_production")
    async def run(self, event: BusinessEvent) -> str:
        try:
            return await self.runner.run(event)
        except Exception:
            # Temporal history contains identities and stable errors, never provider payloads.
            raise ApplicationError("CREATION_LAB_EXECUTION_FAILED", non_retryable=True) from None

    @activity.defn(name="fail_creation_lab_production")
    async def fail(self, event: BusinessEvent) -> None:
        await self.runner.fail(event)
