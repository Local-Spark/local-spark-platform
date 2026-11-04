"""Local simulation: durable intent, owner isolation, replay and stale context."""

import asyncio
import os
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

from app.services.outbox import claim_events, dispatch_once
from app.tests.unit.test_core import access_token
from app.workflows.reference_discovery import ReferenceDiscoveryWorkflow
from app.workflows.reference_discovery_activities import ReferenceDiscoveryActivities
from app.workflows.reference_selection import ReferenceSelectionWorkflow
from app.workflows.reference_selection_activities import ReferenceSelectionActivities

pytestmark = pytest.mark.integration


async def create_business(admin, tenant):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    return business


def local_scope(radius=5):
    return {
        "scope": "local",
        "radius_km": radius,
        "origin": {
            "method": "device",
            "coordinates": {"latitude": -23.55, "longitude": -46.63, "accuracy_m": 30, "confirmed": True},
        },
    }


async def save_scope(api, base, headers, version, scope):
    return await api.put(
        base + "/editorial-context",
        headers=headers,
        json={
            "operation_id": str(uuid4()),
            "expected_version": version,
            "preferences": {"reference_search": scope, "business_terms": ["Café"]},
        },
    )


async def test_fake_discovery_replay_and_owner_isolation(admin, api, seeded, settings, database, relay_database):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    body = {"operation_id": str(uuid4())}
    url = base + "/reference-discoveries"
    assert (await api.post(url, headers=owner, json=body)).status_code == 503
    settings.reference_discovery_mode = "fake"
    assert (await api.post(url, headers=viewer, json=body)).status_code == 403
    assert (await api.post(url, headers=other, json=body)).status_code == 403
    assert (await api.post(url, headers=owner, json=body)).json()[
        "error_code"
    ] == "REFERENCE_SEARCH_PREFERENCE_REQUIRED"
    saved = await save_scope(api, base, owner, 0, local_scope())
    assert saved.status_code == 200, saved.text
    first = await api.post(url, headers=owner, json=body)
    assert first.status_code == 200, first.text
    assert first.json()["state"] == "pending" and first.json()["mode"] == "fake"
    fixture_url = url + "/" + first.json()["id"] + "/fixtures"
    assert (await api.get(fixture_url, headers=owner)).json() == []
    assert (await api.post(url, headers=owner, json=body)).json() == first.json()
    assert (await api.get(url + "/" + first.json()["id"], headers=other)).status_code == 403
    assert (await api.get(fixture_url, headers=other)).status_code == 403
    assert (await api.get(url + "/" + str(uuid4()), headers=owner)).status_code == 404
    claims = await claim_events(relay_database, uuid4())
    assert len(claims) == 1 and claims[0].event_type == "reference.search_requested"
    activity = ReferenceDiscoveryActivities(database, settings)
    with pytest.raises(ApplicationError):
        await activity.simulate_discovery(replace(claims[0].event, business_id=str(uuid4())))
    assert await activity.simulate_discovery(claims[0].event) == "simulated"
    assert await activity.simulate_discovery(claims[0].event) == "simulated"
    result = (await api.get(url + "/" + first.json()["id"], headers=owner)).json()
    assert result["state"] == "simulated" and result["completed_at"] is not None
    assert "candidates" not in result
    fixtures = (await api.get(fixture_url, headers=owner)).json()
    assert [item["fixture_number"] for item in fixtures] == [1, 2, 3]
    assert all(item["mode"] == "fake" and item["discovery_id"] == first.json()["id"] for item in fixtures)
    assert all(
        item["similarity"] == "scripted_suitable" and item["fixture_version"] == "synthetic-v1" for item in fixtures
    )
    assert [item["reputation_score"] for item in fixtures] == ["9.42", "8.97", "8.62"]
    assert [item["reputation_status"] for item in fixtures] == ["scored", "scored", "scored"]
    assert len({item["id"] for item in fixtures}) == 3
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_discoveries")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM reference_discovery_candidates")) == 3
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.search_requested'"))
            == 1
        )
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.search_simulated'"))
            == 1
        )
        assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 1
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_discoveries")) == 0
        assert await session.scalar(text("SELECT count(*) FROM reference_discovery_candidates")) == 0


async def test_changed_preference_marks_stale_and_manual_needs_geocoding(
    admin, api, seeded, settings, database, relay_database
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope())).status_code == 200
    url = base + "/reference-discoveries"
    first = await api.post(url, headers=owner, json={"operation_id": str(uuid4())})
    assert first.status_code == 200, first.text
    manual = {
        "scope": "local",
        "radius_km": 5,
        "origin": {"method": "manual", "address": {"city": "Rio", "state_code": "RJ"}},
    }
    assert (await save_scope(api, base, owner, 1, manual)).status_code == 200
    assert (await api.post(url, headers=owner, json={"operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "REFERENCE_ORIGIN_REQUIRES_GEOCODING"
    claims = await claim_events(relay_database, uuid4())
    assert len(claims) == 1
    assert await ReferenceDiscoveryActivities(database, settings).simulate_discovery(claims[0].event) == "stale"
    assert (await api.get(url + "/" + first.json()["id"], headers=owner)).json()["state"] == "stale"
    assert (await api.get(url + "/" + first.json()["id"] + "/fixtures", headers=owner)).json() == []
    assert (await save_scope(api, base, owner, 2, local_scope(5))).status_code == 200
    assert (await api.post(url, headers=owner, json={"operation_id": str(uuid4())})).status_code == 200


async def test_concurrent_replay_produces_one_durable_intent(admin, api, seeded, settings):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope())).status_code == 200
    body = {"operation_id": str(uuid4())}
    responses = await asyncio.gather(
        *(api.post(base + "/reference-discoveries", headers=owner, json=body) for _ in range(2))
    )
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_discoveries")) == 1
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type='reference.search_requested'")
            )
            == 1
        )


@pytest.mark.temporal
async def test_real_temporal_workflow_consumes_simulated_request(
    admin, api, seeded, settings, database, relay_database
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope())).status_code == 200
    requested = await api.post(base + "/reference-discoveries", headers=owner, json={"operation_id": str(uuid4())})
    assert requested.status_code == 200
    async with admin.connect() as connection:
        event_id = await connection.scalar(
            text("SELECT id FROM outbox_events WHERE event_type='reference.search_requested'")
        )
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    queue = f"test-reference-discovery-{uuid4()}"
    config = settings.model_copy(update={"temporal_task_queue": queue})
    activities = ReferenceDiscoveryActivities(database, settings)
    selections = ReferenceSelectionActivities(database)
    async with Worker(
        client,
        task_queue=queue,
        workflows=[ReferenceDiscoveryWorkflow, ReferenceSelectionWorkflow],
        activities=[activities.simulate_discovery, activities.fail_discovery, selections.record_selection],
    ):
        assert await dispatch_once(relay_database, client, config, uuid4()) == 1
        handle = client.get_workflow_handle(f"reference-discovery/{tenant}/{event_id}")
        assert await handle.result() == "simulated"
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE outbox_events SET state='pending', available_at=now()"))
        assert await dispatch_once(relay_database, client, config, uuid4()) == 1
        fixtures = (
            await api.get(base + "/reference-discoveries/" + requested.json()["id"] + "/fixtures", headers=owner)
        ).json()
        selection = await api.post(
            base + "/reference-discoveries/fixture-selection",
            headers=owner,
            json={"operation_id": str(uuid4()), "candidate_ids": [fixtures[0]["id"]]},
        )
        assert selection.status_code == 200, selection.text
        async with admin.connect() as connection:
            selection_event = await connection.scalar(
                text("SELECT id FROM outbox_events WHERE event_type='reference.selection_confirmed'")
            )
        assert await dispatch_once(relay_database, client, config, uuid4()) == 1
        selection_handle = client.get_workflow_handle(f"reference-selection/{tenant}/{selection_event}")
        assert await selection_handle.result() == "recorded"
    result = (await api.get(base + "/reference-discoveries/" + requested.json()["id"], headers=owner)).json()
    assert result["state"] == "simulated"
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 2
