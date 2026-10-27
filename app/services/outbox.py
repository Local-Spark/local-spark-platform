"""At-least-once relay with durable claims, lease recovery and fencing."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import text
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core.config import Settings
from app.db.session import Database
from app.workflows.contracts import BusinessEvent

logger = logging.getLogger("meu_braco_direito.relay")


@dataclass(frozen=True)
class ClaimedEvent:
    event: BusinessEvent
    fencing_token: int
    event_type: str = "business.created"


async def claim_events(database: Database, owner_id: UUID, limit: int = 20) -> list[ClaimedEvent]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""
          WITH candidates AS (
            SELECT id FROM outbox_events
            WHERE (state='pending' AND available_at <= clock_timestamp())
               OR (state='leased' AND lease_until <= clock_timestamp())
            ORDER BY available_at,id LIMIT :limit FOR UPDATE SKIP LOCKED
          )
          UPDATE outbox_events e SET state='leased', owner_id=:owner,
            lease_until=clock_timestamp()+interval '60 seconds',
            fencing_token=e.fencing_token+1, attempts=e.attempts+1
          FROM candidates c WHERE e.id=c.id
          RETURNING e.id,e.tenant_id,e.event_type,e.payload,e.fencing_token
        """),
                    {"limit": limit, "owner": owner_id},
                )
            )
            .mappings()
            .all()
        )
        return [
            ClaimedEvent(
                BusinessEvent(
                    event_id=str(row["id"]),
                    tenant_id=str(row["tenant_id"]),
                    **row["payload"],
                ),
                row["fencing_token"],
                row["event_type"],
            )
            for row in rows
        ]


async def finish_event(database: Database, item: ClaimedEvent, owner_id: UUID, *, success: bool) -> bool:
    async with database.sessions() as session, session.begin():
        result = await session.scalar(
            text("""
          UPDATE outbox_events SET
            state=CASE WHEN :success THEN 'delivered' WHEN attempts>=5 THEN 'failed' ELSE 'pending' END,
            delivered_at=CASE WHEN :success THEN clock_timestamp() ELSE NULL END,
            available_at=clock_timestamp()+interval '30 seconds', lease_until=NULL, owner_id=NULL
          WHERE id=:id AND state='leased' AND owner_id=:owner AND fencing_token=:token
            AND lease_until > clock_timestamp() RETURNING id
        """),
            {"success": success, "id": UUID(item.event.event_id), "owner": owner_id, "token": item.fencing_token},
        )
        return result is not None


async def dispatch_once(database: Database, client: Client, settings: Settings, owner_id: UUID) -> int:
    items = await claim_events(database, owner_id, limit=5)
    for item in items:
        event = item.event
        success = True
        try:
            workflow_type = {
                "business.created": "BusinessCreatedWorkflow",
                "brand_kit.changed": "BrandKitChangedWorkflow",
            }[item.event_type]
            workflow_id = {
                "business.created": "business-created",
                "brand_kit.changed": "brand-kit-changed",
            }[item.event_type]
            await client.start_workflow(
                workflow_type,
                event,
                id=f"{workflow_id}/{event.tenant_id}/{event.event_id}",
                task_queue=settings.temporal_task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass  # Accepted before a relay crash; never start a second execution.
        except Exception:
            success = False
            logger.warning(
                "outbox.dispatch.retry", extra={"event_id": event.event_id, "error_code": "TEMPORAL_UNAVAILABLE"}
            )
        if not await finish_event(database, item, owner_id, success=success):
            logger.warning("outbox.lease_lost", extra={"event_id": event.event_id})
    return len(items)
