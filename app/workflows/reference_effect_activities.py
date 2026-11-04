"""Fixture-only Temporal activities, with no outbound transport."""

import hmac
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.config import Settings
from app.db.session import Database
from app.services.reference_cost_guard import ReferenceCostError, ReferenceCostGuard
from app.services.reference_effect_simulation import fixture_mac
from app.workflows.contracts import BusinessEvent


class ReferenceEffectActivities:
    def __init__(self, database: Database, settings: Settings, worker_database: Database | None) -> None:
        self.database, self.settings, self.worker_database = database, settings, worker_database

    def _worker(self) -> Database:
        if self.worker_database is None:
            raise ApplicationError("Restricted worker database required", type="ReferenceWorkerUnavailable")
        return self.worker_database

    async def _check_event(self, session: Any, event: BusinessEvent, event_type: str) -> None:
        payload = await session.scalar(
            text("""SELECT payload FROM outbox_events
          WHERE id=:id AND tenant_id=:tenant AND event_type=:type"""),
            {"id": UUID(event.event_id), "tenant": UUID(event.tenant_id), "type": event_type},
        )
        if payload != {
            "business_id": event.business_id,
            "actor_id": event.actor_id,
            "operation_id": event.operation_id,
        }:
            raise ApplicationError("Event does not match intent", type="ReferenceEventInvalid", non_retryable=True)

    @activity.defn(name="simulate_reference_effect")
    async def simulate_effect(self, event: BusinessEvent) -> str:
        worker = self._worker()
        tenant, actor, business, effect = map(
            UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
        )
        async with worker.transaction(tenant, actor) as session:
            await self._check_event(session, event, "reference.effect_requested")
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM reference_simulated_effects
              WHERE tenant_id=:tenant AND actor_id=:actor AND business_id=:business AND id=:effect"""),
                        {"tenant": tenant, "actor": actor, "business": business, "effect": effect},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise ApplicationError("Effect intent unavailable", type="ReferenceEffectInvalid", non_retryable=True)
            expected = fixture_mac(
                self.settings,
                tenant,
                business,
                actor,
                row["discovery_id"],
                effect,
                row["fixture"],
                row["provider"],
                row["reserved_usd_micros"],
            )
            if not hmac.compare_digest(expected, row["request_mac"]):
                # This attempt makes no new claim. An earlier lost attempt may
                # already hold budget until the configured key is restored.
                raise ApplicationError("Effect fingerprint mismatch", type="ReferenceKeyMismatch")
            if row["state"] != "pending":
                return str(row["state"])
        guard = ReferenceCostGuard(worker)
        try:
            claim = await guard.claim(
                tenant,
                business,
                actor,
                row["discovery_id"],
                effect,
                row["provider"],
                expected,
                row["reserved_usd_micros"],
            )
        except ReferenceCostError as error:
            if str(error) not in {"REFERENCE_OWNER_INACTIVE", "REFERENCE_DISCOVERY_NOT_PENDING"}:
                raise
            return await self._complete(event, "cancelled")
        # A retry after a committed claim never repeats even this local fake effect.
        # There is deliberately no external I/O or model call in this activity.
        state = "simulated" if claim.created else "uncertain"
        await guard.finish(tenant, actor, claim.id, actual_usd_micros=None)
        return await self._complete(event, state)

    async def _complete(self, event: BusinessEvent, state: str) -> str:
        worker = self._worker()
        tenant, actor, business, effect = map(
            UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
        )
        async with worker.transaction(tenant, actor) as session:
            await self._check_event(session, event, "reference.effect_requested")
            current = await session.scalar(
                text("""UPDATE reference_simulated_effects SET state=:state
              WHERE tenant_id=:tenant AND actor_id=:actor AND business_id=:business AND id=:effect AND state='pending'
              RETURNING state"""),
                {"state": state, "tenant": tenant, "actor": actor, "business": business, "effect": effect},
            )
            if current is None:
                current = await session.scalar(
                    text("""SELECT state FROM reference_simulated_effects
                  WHERE tenant_id=:tenant AND actor_id=:actor AND business_id=:business AND id=:effect"""),
                    {"tenant": tenant, "actor": actor, "business": business, "effect": effect},
                )
                if current is None:
                    raise ApplicationError(
                        "Effect intent unavailable", type="ReferenceEffectInvalid", non_retryable=True
                    )
                return str(current)
            await session.execute(
                text("INSERT INTO processed_events(tenant_id,event_id) VALUES(:tenant,:event)"),
                {"tenant": tenant, "event": UUID(event.event_id)},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:effect,:action,:business)"""),
                {
                    "tenant": tenant,
                    "actor": actor,
                    "effect": effect,
                    "action": f"reference.effect_{state}",
                    "business": business,
                },
            )
            await session.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(gen_random_uuid(),:tenant,'reference.effect_completed',CAST(:payload AS jsonb))"""),
                {
                    "tenant": tenant,
                    "payload": json.dumps(
                        {"business_id": str(business), "actor_id": str(actor), "operation_id": str(effect)}
                    ),
                },
            )
            return str(current)

    async def _project(self, event: BusinessEvent, event_type: str, source: str, target: str) -> str:
        worker = self._worker()
        tenant, actor, business, effect = map(
            UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
        )
        async with worker.transaction(tenant, actor) as session:
            await self._check_event(session, event, event_type)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,72))"),
                {"key": f"{tenant}:{effect}"},
            )
            key_column = "id" if source == "reference_simulated_effects" else "effect_id"
            state = await session.scalar(
                text(f"""SELECT state FROM {source}
              WHERE tenant_id=:tenant AND actor_id=:actor AND business_id=:business AND {key_column}=:effect"""),
                {"tenant": tenant, "actor": actor, "business": business, "effect": effect},
            )
            if state is None:
                raise ApplicationError("Effect state unavailable", type="ReferenceEffectInvalid", non_retryable=True)
            inserted = await session.scalar(
                text("""INSERT INTO processed_events(tenant_id,event_id)
              VALUES(:tenant,:event) ON CONFLICT DO NOTHING RETURNING event_id"""),
                {"tenant": tenant, "event": UUID(event.event_id)},
            )
            if inserted is not None:
                await session.execute(
                    text(f"""INSERT INTO {target}(tenant_id,actor_id,business_id,effect_id,state)
                  VALUES(:tenant,:actor,:business,:effect,:state) ON CONFLICT(tenant_id,effect_id)
                  DO UPDATE SET state=excluded.state,updated_at=clock_timestamp()"""),
                    {"tenant": tenant, "actor": actor, "business": business, "effect": effect, "state": state},
                )
            return str(state)

    @activity.defn(name="project_reference_effect")
    async def project_effect(self, event: BusinessEvent) -> str:
        return await self._project(
            event, "reference.effect_completed", "reference_simulated_effects", "reference_effect_projection"
        )

    @activity.defn(name="project_reference_cost")
    async def project_cost(self, event: BusinessEvent) -> str:
        return await self._project(
            event, "reference.cost_changed", "reference_cost_reservations", "reference_cost_projection"
        )
