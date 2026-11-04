"""Simulation activity. It never calls a provider or emits candidate profiles."""

from uuid import UUID, uuid5

from sqlalchemy import text
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.config import Settings
from app.db.session import Database
from app.services.reference_cycles import lock_reference_head
from app.services.reference_recovery import owner_is_active, recover_revoked
from app.services.reference_reputation import EXPERIMENTAL_PENALIZED_VERSION
from app.services.reference_simulated_candidates import SIMULATED_FIXTURE_VERSION, simulated_candidates
from app.workflows.contracts import BusinessEvent


class ReferenceDiscoveryActivities:
    def __init__(self, database: Database, settings: Settings, recovery_database: Database | None = None) -> None:
        self.database = database
        self.settings = settings
        self.recovery_database = recovery_database

    @activity.defn(name="simulate_reference_discovery")
    async def simulate_discovery(self, event: BusinessEvent) -> str:
        try:
            return await self._perform(event)
        except _RevokedOwner:
            return await recover_revoked(self.recovery_database, event, "search")

    @activity.defn(name="fail_reference_simulation")
    async def fail_discovery(self, event: BusinessEvent) -> str:
        try:
            return await self._perform(event, force_stale=True)
        except _RevokedOwner:
            return await recover_revoked(self.recovery_database, event, "search")

    async def _perform(self, event: BusinessEvent, *, force_stale: bool = False) -> str:
        tenant, actor, business, operation = map(
            UUID, (event.tenant_id, event.actor_id, event.business_id, event.operation_id)
        )
        async with self.database.transaction(tenant, actor) as session:
            payload = await session.scalar(
                text("""SELECT payload FROM outbox_events
              WHERE id=:id AND tenant_id=:tenant AND event_type='reference.search_requested'"""),
                {"id": UUID(event.event_id), "tenant": tenant},
            )
            if payload != {
                "business_id": event.business_id,
                "actor_id": event.actor_id,
                "operation_id": event.operation_id,
            }:
                raise ApplicationError("Event does not match durable intent", type="InvalidEvent", non_retryable=True)
            if not await owner_is_active(session, tenant, actor):
                raise _RevokedOwner
            head = await lock_reference_head(session, tenant, business)
            row = (
                (
                    await session.execute(
                        text("""SELECT d.id,d.state,d.context_version,d.category,d.preference,d.cycle_id,
              h.version,v.document,snapshot.document AS snapshot_document,p.category AS current_category
              FROM reference_discoveries d
              JOIN business_context_heads h ON (h.tenant_id,h.business_id)=(d.tenant_id,d.business_id)
              JOIN business_context_versions v
                ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
              JOIN business_context_versions snapshot
                ON (snapshot.tenant_id,snapshot.business_id,snapshot.version)=
                   (d.tenant_id,d.business_id,d.context_version)
              JOIN business_profiles p ON (p.tenant_id,p.business_id)=(d.tenant_id,d.business_id)
              WHERE d.tenant_id=:tenant AND d.business_id=:business AND d.actor_id=:actor AND d.operation_id=:operation
              FOR UPDATE OF d FOR SHARE OF h,p"""),
                        {"tenant": tenant, "business": business, "actor": actor, "operation": operation},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise ApplicationError("Discovery intent unavailable", type="InvalidEvent", non_retryable=True)
            if row["state"] != "pending":
                return str(row["state"])
            processed = await session.scalar(
                text("""INSERT INTO processed_events(tenant_id,event_id)
                  VALUES(:tenant,:event) ON CONFLICT DO NOTHING RETURNING event_id"""),
                {"tenant": tenant, "event": UUID(event.event_id)},
            )
            if processed is None:
                raise ApplicationError(
                    "Processed event has no terminal discovery", type="InvalidEvent", non_retryable=True
                )
            current = row["document"].get("preferences", {}).get("reference_search")
            current_terms = row["document"].get("preferences", {}).get("business_terms", [])
            snapshot_terms = row["snapshot_document"].get("preferences", {}).get("business_terms", [])
            state = (
                "simulated"
                if not force_stale
                and self.settings.reference_discovery_mode == "fake"
                and current == row["preference"]
                and row["category"] == row["current_category"]
                and current_terms == snapshot_terms
                and head["cycle_id"] == row["cycle_id"]
                else "stale"
            )
            if state == "simulated":
                for candidate in simulated_candidates():
                    fixture_number = candidate.number
                    canonical = uuid5(row["cycle_id"] or row["id"], f"simulated-reference-{fixture_number}")
                    await session.execute(
                        text("""INSERT INTO reference_discovery_candidates
                          (id,tenant_id,business_id,discovery_id,fixture_number,canonical_id,selected,
                           reputation_score_snapshot,reputation_formula_version,reputation_fixture_version)
                          SELECT :id,:tenant,:business,:discovery,:number,:canonical,
                            EXISTS(SELECT 1 FROM reference_discovery_candidates
                              WHERE tenant_id=:tenant AND business_id=:business
                                AND canonical_id=:canonical AND selected=true),
                            :score,:formula_version,:fixture_version"""),
                        {
                            "id": uuid5(row["id"], f"simulated-reference-{fixture_number}"),
                            "tenant": tenant,
                            "business": business,
                            "discovery": row["id"],
                            "number": fixture_number,
                            "canonical": canonical,
                            "score": candidate.ordering_score,
                            "formula_version": EXPERIMENTAL_PENALIZED_VERSION,
                            "fixture_version": SIMULATED_FIXTURE_VERSION,
                        },
                    )
            await session.execute(
                text("""UPDATE reference_discoveries SET state=:state,completed_at=now()
              WHERE id=:id AND tenant_id=:tenant"""),
                {"state": state, "id": row["id"], "tenant": tenant},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,:action,:business)"""),
                {
                    "tenant": tenant,
                    "actor": actor,
                    "operation": operation,
                    "action": f"reference.search_{state}",
                    "business": business,
                },
            )
            return state


class _RevokedOwner(Exception):
    pass
