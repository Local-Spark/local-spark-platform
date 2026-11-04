"""Recover a revoked owner's fake operation via a narrowly scoped RLS worker role."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from temporalio.exceptions import ApplicationError

from app.db.session import Database
from app.workflows.contracts import BusinessEvent


async def owner_is_active(session: Any, tenant: UUID, actor: UUID) -> bool:
    return bool(
        await session.scalar(
            text("""SELECT 1 FROM memberships
      WHERE tenant_id=:tenant AND actor_id=:actor AND role='owner' AND active"""),
            {"tenant": tenant, "actor": actor},
        )
    )


async def recover_revoked(database: Database | None, event: BusinessEvent, kind: str) -> str:
    if database is None:
        raise ApplicationError("Recovery database unavailable", type="RecoveryUnavailable")
    tenant, actor, business, operation = map(
        UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
    )
    event_id = UUID(event.event_id)
    event_type = "reference.search_requested" if kind == "search" else "reference.selection_confirmed"
    async with database.transaction(tenant, actor) as session:
        payload = await session.scalar(
            text("""SELECT payload FROM outbox_events
          WHERE id=:event AND tenant_id=:tenant AND event_type=:event_type"""),
            {"event": event_id, "tenant": tenant, "event_type": event_type},
        )
        if payload != {
            "business_id": event.business_id,
            "actor_id": event.actor_id,
            "operation_id": event.operation_id,
        }:
            raise ApplicationError("Event does not match durable intent", type="InvalidEvent", non_retryable=True)
        if await owner_is_active(session, tenant, actor):
            raise ApplicationError("Owner access restored; retry normally", type="OwnerRestored")
        if kind == "search":
            state = await session.scalar(
                text("""UPDATE reference_discoveries SET state='stale',completed_at=now()
              WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND operation_id=:operation
                AND state='pending' RETURNING state"""),
                {"tenant": tenant, "business": business, "actor": actor, "operation": operation},
            )
            if state is None:
                state = await session.scalar(
                    text("""SELECT state FROM reference_discoveries
                  WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND operation_id=:operation"""),
                    {"tenant": tenant, "business": business, "actor": actor, "operation": operation},
                )
            if state is None:
                raise ApplicationError("Discovery intent unavailable", type="InvalidEvent", non_retryable=True)
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'reference.search_stale',:business) ON CONFLICT DO NOTHING"""),
                {"tenant": tenant, "actor": actor, "operation": operation, "business": business},
            )
        else:
            exists = await session.scalar(
                text("""SELECT 1 FROM reference_selection_operations
              WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND operation_id=:operation"""),
                {"tenant": tenant, "business": business, "actor": actor, "operation": operation},
            )
            if exists is None:
                raise ApplicationError("Selection intent unavailable", type="InvalidEvent", non_retryable=True)
            state = "recorded"
        await session.execute(
            text("""INSERT INTO processed_events(tenant_id,event_id)
          VALUES(:tenant,:event) ON CONFLICT DO NOTHING"""),
            {"tenant": tenant, "event": event_id},
        )
        return str(state)
