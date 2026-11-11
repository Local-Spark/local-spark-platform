"""At-least-once relay with durable claims, lease recovery and fencing."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid5

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


async def claim_events(
    database: Database,
    owner_id: UUID,
    limit: int = 20,
    *,
    include_fixture_effects: bool = False,
    include_geocoding: bool = False,
    include_provider_discovery: bool = False,
    include_learning: bool = False,
    include_motion: bool = False,
) -> list[ClaimedEvent]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""
          WITH candidates AS (
            SELECT id FROM outbox_events
            WHERE (event_type IN ('business.created','brand_kit.changed','reference.search_requested',
                                 'reference.selection_confirmed') OR
                   (:include_geocoding AND event_type='business.address_geocode_requested') OR
                   (:include_motion AND event_type IN ('motion.requested','motion.storyboard_approved')) OR
                   (:include_learning AND event_type='reference.learning_requested') OR
                   (:include_providers AND event_type IN ('reference.provider_search_requested',
                     'reference.search_reviewed','reference.provider_retry_requested')) OR
                   (:include_fixtures AND event_type IN ('reference.effect_requested','reference.cost_changed',
                                                          'reference.effect_completed'))) AND (
              (state='pending' AND available_at <= clock_timestamp())
               OR (state='leased' AND lease_until <= clock_timestamp()))
            ORDER BY available_at,id LIMIT :limit FOR UPDATE SKIP LOCKED
          )
          UPDATE outbox_events e SET state='leased', owner_id=:owner,
            lease_until=clock_timestamp()+interval '60 seconds',
            fencing_token=e.fencing_token+1, attempts=e.attempts+1
          FROM candidates c WHERE e.id=c.id
          RETURNING e.id,e.tenant_id,e.event_type,e.payload,e.fencing_token
        """),
                    {
                        "limit": limit,
                        "owner": owner_id,
                        "include_fixtures": include_fixture_effects,
                        "include_geocoding": include_geocoding,
                        "include_providers": include_provider_discovery,
                        "include_learning": include_learning,
                        "include_motion": include_motion,
                    },
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
    if getattr(settings, "motion_execution_ready", lambda: False)():
        items = await claim_events(
            database,
            owner_id,
            limit=5,
            include_motion=True,
            include_learning=getattr(settings, "reference_learning_ready", lambda: False)(),
            include_provider_discovery=getattr(settings, "reference_discovery_ready", lambda: False)(),
            include_geocoding=getattr(settings, "reference_geocoding_ready", lambda: False)(),
            include_fixture_effects=getattr(settings, "reference_discovery_mode", "disabled") == "fake",
        )
    elif getattr(settings, "reference_learning_ready", lambda: False)():
        items = await claim_events(
            database,
            owner_id,
            limit=5,
            include_learning=True,
            include_provider_discovery=getattr(settings, "reference_discovery_ready", lambda: False)(),
            include_geocoding=getattr(settings, "reference_geocoding_ready", lambda: False)(),
            include_fixture_effects=getattr(settings, "reference_discovery_mode", "disabled") == "fake",
        )
    elif getattr(settings, "reference_discovery_ready", lambda: False)():
        items = await claim_events(
            database,
            owner_id,
            limit=5,
            include_provider_discovery=True,
            include_geocoding=getattr(settings, "reference_geocoding_ready", lambda: False)(),
            include_fixture_effects=getattr(settings, "reference_discovery_mode", "disabled") == "fake",
        )
    elif getattr(settings, "reference_geocoding_ready", lambda: False)():
        items = await claim_events(
            database,
            owner_id,
            limit=5,
            include_geocoding=True,
            include_fixture_effects=getattr(settings, "reference_discovery_mode", "disabled") == "fake",
        )
    elif getattr(settings, "reference_discovery_mode", "disabled") == "fake":
        items = await claim_events(database, owner_id, limit=5, include_fixture_effects=True)
    else:
        items = await claim_events(database, owner_id, limit=5)
    for item in items:
        event = item.event
        success = True
        try:
            if item.event_type in ("reference.search_reviewed", "reference.provider_retry_requested"):
                search = uuid5(
                    UUID(event.operation_id), f"reference-provider-search-v1:{event.tenant_id}:{event.business_id}"
                )
                handle = client.get_workflow_handle(f"reference-provider-search/{event.tenant_id}/{search}")
                await handle.signal("resume", rpc_timeout=timedelta(seconds=5))
            else:
                await _start_workflow(client, settings, item)
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            success = False
            logger.warning(
                "outbox.dispatch.retry", extra={"event_id": event.event_id, "error_code": "TEMPORAL_UNAVAILABLE"}
            )
        if not await finish_event(database, item, owner_id, success=success):
            logger.warning("outbox.lease_lost", extra={"event_id": event.event_id})
    return len(items)


async def _start_workflow(client: Client, settings: Settings, item: ClaimedEvent) -> None:
    event = item.event
    workflow_type = {
        "business.created": "BusinessCreatedWorkflow",
        "motion.requested": "MotionProductionWorkflow",
        "motion.storyboard_approved": "MotionProductionWorkflow",
        "reference.provider_search_requested": "ReferenceProviderDiscoveryWorkflow",
        "reference.learning_requested": "ReferenceLearningWorkflow",
        "business.address_geocode_requested": "BusinessGeocodingWorkflow",
        "brand_kit.changed": "BrandKitChangedWorkflow",
        "reference.search_requested": "ReferenceDiscoveryWorkflow",
        "reference.selection_confirmed": "ReferenceSelectionWorkflow",
        "reference.effect_requested": "ReferenceEffectWorkflow",
        "reference.cost_changed": "ReferenceCostProjectionWorkflow",
        "reference.effect_completed": "ReferenceEffectProjectionWorkflow",
    }[item.event_type]
    workflow_id = {
        "business.created": "business-created",
        "motion.requested": "motion-production",
        "motion.storyboard_approved": "motion-storyboard-approved",
        "reference.provider_search_requested": "reference-provider-search",
        "reference.learning_requested": "reference-learning",
        "business.address_geocode_requested": "business-geocoding",
        "brand_kit.changed": "brand-kit-changed",
        "reference.search_requested": "reference-discovery",
        "reference.selection_confirmed": "reference-selection",
        "reference.effect_requested": "reference-effect",
        "reference.cost_changed": "reference-cost-projection",
        "reference.effect_completed": "reference-effect-projection",
    }[item.event_type]
    identity = (
        str(uuid5(UUID(event.operation_id), f"reference-provider-search-v1:{event.tenant_id}:{event.business_id}"))
        if item.event_type == "reference.provider_search_requested"
        else event.operation_id
        if item.event_type == "reference.learning_requested"
        else event.event_id
    )
    await client.start_workflow(
        workflow_type,
        event,
        id=f"{workflow_id}/{event.tenant_id}/{identity}",
        task_queue=settings.temporal_task_queue,
        id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
        rpc_timeout=timedelta(seconds=5),
    )
