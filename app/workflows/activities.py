from uuid import UUID

from sqlalchemy import text
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.db.session import Database
from app.workflows.contracts import BusinessEvent


class FoundationActivities:
    def __init__(self, database: Database) -> None:
        self.database = database

    @activity.defn
    async def record_business_created(self, event: BusinessEvent) -> str:
        tenant, actor = UUID(event.tenant_id), UUID(event.actor_id)
        async with self.database.transaction(tenant, actor) as session:
            payload = await session.scalar(
                text("SELECT payload FROM outbox_events WHERE id=:id AND tenant_id=:tenant"),
                {"id": UUID(event.event_id), "tenant": tenant},
            )
            expected = {
                "business_id": event.business_id,
                "actor_id": event.actor_id,
                "operation_id": event.operation_id,
            }
            if payload != expected:
                raise ApplicationError("Event does not match durable intent", type="InvalidEvent", non_retryable=True)
            inserted = await session.scalar(
                text("""INSERT INTO processed_events(tenant_id,event_id) VALUES (:tenant,:id)
                  ON CONFLICT DO NOTHING RETURNING event_id"""),
                {"tenant": tenant, "id": UUID(event.event_id)},
            )
            if inserted is None:
                return "duplicate"
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                   VALUES (:tenant,:actor,:operation,'workflow.business_registered',:resource)"""),
                {
                    "tenant": tenant,
                    "actor": actor,
                    "operation": UUID(event.operation_id),
                    "resource": UUID(event.business_id),
                },
            )
            return "recorded"

    @activity.defn
    async def record_brand_kit_changed(self, event: BusinessEvent) -> str:
        tenant, actor = UUID(event.tenant_id), UUID(event.actor_id)
        async with self.database.transaction(tenant, actor) as session:
            row = (
                (
                    await session.execute(
                        text("""SELECT event_type,payload FROM outbox_events
                          WHERE id=:id AND tenant_id=:tenant"""),
                        {"id": UUID(event.event_id), "tenant": tenant},
                    )
                )
                .mappings()
                .one_or_none()
            )
            expected = {
                "business_id": event.business_id,
                "actor_id": event.actor_id,
                "operation_id": event.operation_id,
            }
            if row is None or row["event_type"] != "brand_kit.changed" or row["payload"] != expected:
                raise ApplicationError("Event does not match durable intent", type="InvalidEvent", non_retryable=True)
            inserted = await session.scalar(
                text("""INSERT INTO processed_events(tenant_id,event_id) VALUES (:tenant,:id)
                  ON CONFLICT DO NOTHING RETURNING event_id"""),
                {"tenant": tenant, "id": UUID(event.event_id)},
            )
            return "recorded" if inserted is not None else "duplicate"
