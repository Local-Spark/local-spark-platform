"""Fixture-only effect integration: no public service or customer data."""

import asyncio
import os
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

from app.db.session import Database
from app.services.auth import AuthError
from app.services.outbox import dispatch_once
from app.services.reference_cost_guard import ReferenceCostError, ReferenceCostGuard
from app.services.reference_effect_simulation import ReferenceEffectSimulationService, fixture_mac
from app.tests.integration.test_reference_cost_accounting import _discovery, _policy
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_discovery_activities import ReferenceDiscoveryActivities
from app.workflows.reference_effect import (
    ReferenceCostProjectionWorkflow,
    ReferenceEffectProjectionWorkflow,
    ReferenceEffectWorkflow,
)
from app.workflows.reference_effect_activities import ReferenceEffectActivities

pytestmark = pytest.mark.integration


async def _event(admin, tenant, kind):
    async with admin.connect() as connection:
        row = (
            (
                await connection.execute(
                    text("""SELECT id,payload FROM outbox_events
          WHERE tenant_id=:tenant AND event_type=:kind ORDER BY created_at DESC LIMIT 1"""),
                    {"tenant": tenant, "kind": kind},
                )
            )
            .mappings()
            .one()
        )
    return BusinessEvent(event_id=str(row["id"]), tenant_id=str(tenant), **row["payload"])


async def _setup(admin, seeded, settings):
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM reference_cost_monthly"))
    await _policy(admin)
    settings.reference_discovery_mode = "fake"
    settings.reference_fixture_hmac_key = SecretStr("synthetic-reference-fixture-key-only")
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Test','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    app_db, worker = Database(settings), Database(settings, correlator=True)
    return tenant, actor, business, discovery, app_db, worker


async def test_fixture_effect_end_to_end_replay_and_projections(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        service = ReferenceEffectSimulationService(settings, app_db)
        effect = await service.request(tenant, business, actor, discovery, "fixture_place_1")
        assert effect == await service.request(tenant, business, actor, discovery, "fixture_place_1")
        with pytest.raises(AuthError, match="REFERENCE_FIXTURE_INVALID"):
            await service.request(tenant, business, actor, discovery, "real-place-id")
        event = await _event(admin, tenant, "reference.effect_requested")
        activities = ReferenceEffectActivities(app_db, settings, worker)
        assert await activities.simulate_effect(event) == "simulated"
        assert await activities.simulate_effect(event) == "simulated"
        assert await activities._complete(event, "uncertain") == "simulated"
        finished = await _event(admin, tenant, "reference.effect_completed")
        assert await activities.project_effect(finished) == "simulated"
        assert await activities.project_effect(finished) == "simulated"
        async with admin.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        text("""SELECT id,payload FROM outbox_events
              WHERE tenant_id=:tenant AND event_type='reference.cost_changed' ORDER BY created_at"""),
                        {"tenant": tenant},
                    )
                )
                .mappings()
                .all()
            )
        assert len(rows) == 2
        cost_events = [BusinessEvent(event_id=str(row["id"]), tenant_id=str(tenant), **row["payload"]) for row in rows]
        assert await asyncio.gather(*(activities.project_cost(item) for item in reversed(cost_events))) == [
            "uncertain",
            "uncertain",
        ]
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_projection WHERE effect_id=:id"), {"id": effect}
                )
                == "uncertain"
            )
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_effect_projection WHERE effect_id=:id"), {"id": effect}
                )
                == "simulated"
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
            assert (
                await connection.scalar(
                    text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='all'")
                )
                == 1
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_effect_can_follow_existing_simulated_discovery(admin, seeded, settings, api):
    tenant, actor = seeded["t1"], seeded["a1"]
    settings.reference_discovery_mode = "fake"
    settings.reference_fixture_hmac_key = SecretStr("synthetic-reference-fixture-key-only")
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM reference_cost_monthly"))
    await _policy(admin)
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope())).status_code == 200
    response = await api.post(base + "/reference-discoveries", headers=owner, json={"operation_id": str(uuid4())})
    assert response.status_code == 200
    discovery = UUID(response.json()["id"])
    app_db, worker = Database(settings), Database(settings, correlator=True)
    try:
        await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_profile_1"
        )
        earlier_effect_event = await _event(admin, tenant, "reference.effect_requested")
        search_event = await _event(admin, tenant, "reference.search_requested")
        assert (
            await ReferenceDiscoveryActivities(app_db, settings, worker).simulate_discovery(search_event) == "simulated"
        )
        assert (
            await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(earlier_effect_event)
            == "simulated"
        )
        await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        effect_event = await _event(admin, tenant, "reference.effect_requested")
        assert await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(effect_event) == "simulated"
    finally:
        await app_db.close()
        await worker.close()


async def test_revocation_before_claim_cancels_without_cost(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_profile_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": actor},
            )
        assert await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(event) == "cancelled"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_simulated_effects WHERE id=:id"), {"id": effect}
                )
                == "cancelled"
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_discovery_stale_before_claim_cancels_without_cost(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_discoveries SET state='stale' WHERE id=:id"), {"id": discovery}
            )
        assert await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(event) == "cancelled"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_simulated_effects WHERE id=:id"), {"id": effect}
                )
                == "cancelled"
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_jev_fixture_obeys_its_provider_limit(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        await _policy(admin, search=100, monthly=100, search_provider=1, monthly_provider=1)
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_jev_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        assert await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(event) == "simulated"
        with pytest.raises(ReferenceCostError, match="SEARCH_PROVIDER_BUDGET_EXCEEDED"):
            await ReferenceCostGuard(worker).claim(tenant, business, actor, discovery, uuid4(), "jev", "a" * 64, 1)
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT provider FROM reference_cost_reservations WHERE effect_id=:id"), {"id": effect}
                )
                == "jev"
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_lost_claim_never_runs_effect_again(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        async with admin.connect() as connection:
            mac = await connection.scalar(
                text("SELECT request_mac FROM reference_simulated_effects WHERE id=:id"), {"id": effect}
            )
        claim = await ReferenceCostGuard(worker).claim(tenant, business, actor, discovery, effect, "google", mac, 1)
        assert claim.created
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": actor},
            )
        assert await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(event) == "uncertain"
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE id=:id"), {"id": claim.id}
                )
                == "uncertain"
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_changed_or_missing_hmac_fails_before_claim(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        settings.reference_fixture_hmac_key = SecretStr("another-synthetic-reference-key-only")
        with pytest.raises(ApplicationError, match="fingerprint mismatch") as rejected:
            await ReferenceEffectActivities(app_db, settings, worker).simulate_effect(event)
        assert not rejected.value.non_retryable
        with pytest.raises(AuthError, match="REFERENCE_EFFECT_CONFLICT"):
            await ReferenceEffectSimulationService(settings, app_db).request(
                tenant, business, actor, discovery, "fixture_place_1"
            )
        settings.reference_fixture_hmac_key = None
        with pytest.raises(AuthError, match="REFERENCE_FIXTURE_KEY_REQUIRED"):
            await ReferenceEffectSimulationService(settings, app_db).request(
                tenant, business, actor, discovery, "fixture_place_1"
            )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_simulated_effects WHERE id=:id"), {"id": effect}
                )
                == "pending"
            )
    finally:
        await app_db.close()
        await worker.close()


async def test_fixture_fail_closed_and_hmac_binds_inputs(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    effect = uuid4()
    try:
        args = (tenant, business, actor, discovery, effect, "fixture_place_1", "google", 1)
        digest = fixture_mac(settings, *args)
        assert digest != fixture_mac(
            settings, tenant, business, actor, discovery, uuid4(), "fixture_place_1", "google", 1
        )
        for fixture, provider, amount in (("fixture_place_1", "apify", 1), ("fixture_place_1", "google", 2)):
            with pytest.raises(AuthError, match="REFERENCE_FIXTURE_INVALID"):
                fixture_mac(settings, tenant, business, actor, discovery, effect, fixture, provider, amount)
        settings.reference_fixture_hmac_key = SecretStr("short")
        with pytest.raises(AuthError, match="REFERENCE_FIXTURE_KEY_REQUIRED"):
            fixture_mac(settings, *args)
        settings.reference_discovery_mode = "disabled"
        with pytest.raises(AuthError, match="REFERENCE_FIXTURE_DISABLED"):
            fixture_mac(settings, *args)
        settings.reference_discovery_mode = "fake"
        settings.environment = "production"
        with pytest.raises(AuthError, match="REFERENCE_FIXTURE_DISABLED"):
            fixture_mac(settings, *args)
    finally:
        await app_db.close()
        await worker.close()


async def test_invalid_event_stale_request_and_missing_effect_fail_closed(admin, seeded, settings):
    from dataclasses import replace

    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    service = ReferenceEffectSimulationService(settings, app_db)
    activities = ReferenceEffectActivities(app_db, settings, worker)
    try:
        with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_NOT_PENDING"):
            await service.request(tenant, business, actor, uuid4(), "fixture_place_1")
        effect = await service.request(tenant, business, actor, discovery, "fixture_place_1")
        event = await _event(admin, tenant, "reference.effect_requested")
        with pytest.raises(ApplicationError, match="Event does not match intent"):
            await activities.simulate_effect(replace(event, business_id=str(uuid4())))
        with pytest.raises(ApplicationError, match="Restricted worker database required"):
            await ReferenceEffectActivities(app_db, settings, None).simulate_effect(event)
        async with admin.begin() as connection:
            await connection.execute(text("DELETE FROM reference_simulated_effects WHERE id=:id"), {"id": effect})
        with pytest.raises(ApplicationError, match="Effect intent unavailable"):
            await activities.simulate_effect(event)
        with pytest.raises(ApplicationError, match="Effect intent unavailable"):
            await activities._complete(event, "cancelled")
    finally:
        await app_db.close()
        await worker.close()


async def test_budget_disabled_retries_and_projection_without_reservation_fails(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    activities = ReferenceEffectActivities(app_db, settings, worker)
    try:
        await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=NULL"))
        with pytest.raises(ReferenceCostError, match="BUDGET_DISABLED"):
            await activities.simulate_effect(event)
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              SELECT gen_random_uuid(),tenant_id,'reference.cost_changed',payload FROM outbox_events WHERE id=:id"""),
                {"id": UUID(event.event_id)},
            )
        cost_event = await _event(admin, tenant, "reference.cost_changed")
        with pytest.raises(ApplicationError, match="Effect state unavailable"):
            await activities.project_cost(cost_event)
    finally:
        await app_db.close()
        await worker.close()


async def test_downgrade_guard_fails_closed_without_rls_bypass(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker = await _setup(admin, seeded, settings)
    try:
        await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        with pytest.raises(DBAPIError, match="row-level security"):
            async with worker.transaction(tenant, actor) as session:
                await session.execute(text("SET LOCAL row_security=off"))
                await session.scalar(text("SELECT EXISTS(SELECT 1 FROM reference_simulated_effects)"))
    finally:
        await app_db.close()
        await worker.close()


@pytest.mark.temporal
async def test_real_temporal_dispatches_fixture_effect_and_projections(admin, seeded, settings):
    tenant, actor, business, discovery, app_db, worker_db = await _setup(admin, seeded, settings)
    relay = Database(settings, relay=True)
    settings.temporal_task_queue = f"reference-fixture-{uuid4()}"
    activities = ReferenceEffectActivities(app_db, settings, worker_db)
    try:
        effect = await ReferenceEffectSimulationService(settings, app_db).request(
            tenant, business, actor, discovery, "fixture_place_1"
        )
        event = await _event(admin, tenant, "reference.effect_requested")
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE outbox_events SET state='delivered',delivered_at=clock_timestamp()
              WHERE tenant_id=:tenant AND event_type='reference.search_requested'"""),
                {"tenant": tenant},
            )
        client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
        async with Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[ReferenceEffectWorkflow, ReferenceCostProjectionWorkflow, ReferenceEffectProjectionWorkflow],
            activities=[activities.simulate_effect, activities.project_cost, activities.project_effect],
        ):
            assert await dispatch_once(relay, client, settings, uuid4()) == 1
            result = await asyncio.wait_for(
                client.get_workflow_handle(f"reference-effect/{tenant}/{event.event_id}").result(), timeout=15
            )
            assert result == "simulated"
            assert await dispatch_once(relay, client, settings, uuid4()) == 3
            async with admin.connect() as connection:
                rows = (
                    await connection.execute(
                        text("""SELECT id,event_type FROM outbox_events
                  WHERE tenant_id=:tenant AND event_type IN ('reference.cost_changed','reference.effect_completed')"""),
                        {"tenant": tenant},
                    )
                ).all()
            for event_id, kind in rows:
                prefix = (
                    "reference-cost-projection" if kind == "reference.cost_changed" else "reference-effect-projection"
                )
                await asyncio.wait_for(client.get_workflow_handle(f"{prefix}/{tenant}/{event_id}").result(), timeout=15)
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_effect_projection WHERE effect_id=:id"), {"id": effect}
                )
                == "simulated"
            )
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_projection WHERE effect_id=:id"), {"id": effect}
                )
                == "uncertain"
            )
    finally:
        await relay.close()
        await app_db.close()
        await worker_db.close()
