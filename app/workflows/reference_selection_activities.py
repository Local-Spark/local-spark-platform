"""Record consumption of the durable selection; never access a real profile."""

from uuid import UUID

from sqlalchemy import text
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.db.session import Database
from app.services.reference_recovery import owner_is_active, recover_revoked
from app.workflows.contracts import BusinessEvent


class ReferenceSelectionActivities:
    def __init__(self, database: Database, recovery_database: Database | None = None) -> None:
        self.database = database
        self.recovery_database = recovery_database

    @activity.defn(name="record_reference_fixture_selection")
    async def record_selection(self, event: BusinessEvent) -> str:
        try:
            return await self._perform(event)
        except _RevokedOwner:
            return await recover_revoked(self.recovery_database, event, "selection")

    async def _perform(self, event: BusinessEvent) -> str:
        tenant, actor, business, operation = map(
            UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
        )
        async with self.database.transaction(tenant, actor) as session:
            stored = await session.scalar(
                text("""SELECT payload FROM outbox_events
              WHERE id=:event AND tenant_id=:tenant AND event_type='reference.selection_confirmed'"""),
                {"event": UUID(event.event_id), "tenant": tenant},
            )
            if stored != {
                "business_id": event.business_id,
                "actor_id": event.actor_id,
                "operation_id": event.operation_id,
            }:
                raise ApplicationError("Event does not match durable intent", type="InvalidEvent", non_retryable=True)
            if not await owner_is_active(session, tenant, actor):
                raise _RevokedOwner
            exists = await session.scalar(
                text("""SELECT 1 FROM reference_selection_operations
              WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND operation_id=:operation"""),
                {"tenant": tenant, "business": business, "actor": actor, "operation": operation},
            )
            if exists is None:
                raise ApplicationError("Selection intent unavailable", type="InvalidEvent", non_retryable=True)
            inserted = await session.scalar(
                text("""INSERT INTO processed_events(tenant_id,event_id)
              VALUES(:tenant,:event) ON CONFLICT DO NOTHING RETURNING event_id"""),
                {"tenant": tenant, "event": UUID(event.event_id)},
            )
            return "recorded" if inserted is not None else "duplicate"


class _RevokedOwner(Exception):
    pass
