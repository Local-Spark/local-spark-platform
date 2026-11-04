"""Versioned business terms, old clients and fake-search context snapshots."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services.outbox import claim_events
from app.tests.integration.test_reference_discovery import create_business, local_scope
from app.tests.unit.test_core import access_token
from app.workflows.reference_discovery_activities import ReferenceDiscoveryActivities

pytestmark = pytest.mark.integration


async def test_business_terms_old_clients_restore_and_idempotency(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    original = {"expected_version": 0, "operation_id": str(uuid4()), "preferences": {"tone": "friendly"}}
    first = await api.put(base, headers=owner, json=original)
    assert first.status_code == 200, first.text
    assert (await api.get(base, headers=other)).status_code == 403
    # Reproduce an authentic version stored before this optional field existed.
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_context_versions SET document=jsonb_set(document, '{preferences}',
          (document->'preferences')-'business_terms')
          WHERE tenant_id=:tenant AND business_id=:business AND version=1"""),
            {"tenant": tenant, "business": business},
        )
    assert (await api.get(base, headers=owner)).json()["preferences"]["business_terms"] == []
    assert (await api.put(base, headers=owner, json=original)).json()["version"] == 1
    set_terms = {
        "expected_version": 1,
        "operation_id": str(uuid4()),
        "preferences": {"business_terms": [" cafe\u0301 ", "Padaria"]},
    }
    assert (await api.put(base, headers=viewer, json=set_terms)).status_code == 403
    assert (
        await api.put(
            base, headers=owner, json={**set_terms, "preferences": {"business_terms": ["Café", "cafe\u0301"]}}
        )
    ).status_code == 422
    set_result = await api.put(base, headers=owner, json=set_terms)
    assert set_result.status_code == 200, set_result.text
    assert set_result.json()["preferences"]["business_terms"] == ["café", "Padaria"]
    assert (await api.put(base, headers=owner, json=set_terms)).json() == set_result.json()
    legacy_edit = {"expected_version": 2, "operation_id": str(uuid4()), "preferences": {"tone": "direct"}}
    changed = await api.put(base, headers=owner, json=legacy_edit)
    assert changed.status_code == 200, changed.text
    assert changed.json()["preferences"]["business_terms"] == ["café", "Padaria"]
    same_operation_clear = {**legacy_edit, "preferences": {"tone": "direct", "business_terms": []}}
    conflict = await api.put(base, headers=owner, json=same_operation_clear)
    assert conflict.status_code == 409 and conflict.json()["error_code"] == "CONTEXT_OPERATION_CONFLICT"
    restore_old = await api.post(
        base + "/restore",
        headers=owner,
        json={"expected_version": 3, "target_version": 1, "operation_id": str(uuid4())},
    )
    assert restore_old.status_code == 200, restore_old.text
    assert restore_old.json()["preferences"]["business_terms"] == ["café", "Padaria"]
    clear = await api.put(
        base,
        headers=owner,
        json={"expected_version": 4, "operation_id": str(uuid4()), "preferences": {"business_terms": []}},
    )
    assert clear.status_code == 200 and clear.json()["preferences"]["business_terms"] == []
    reset = await api.put(
        base,
        headers=owner,
        json={"expected_version": 5, "operation_id": str(uuid4()), "preferences": {"business_terms": ["Confeitaria"]}},
    )
    assert reset.status_code == 200
    restore_clear = await api.post(
        base + "/restore",
        headers=owner,
        json={"expected_version": 6, "target_version": 5, "operation_id": str(uuid4())},
    )
    assert restore_clear.status_code == 200 and restore_clear.json()["preferences"]["business_terms"] == []


async def test_terms_required_and_changes_blocked_only_during_search(
    admin, api, seeded, settings, database, relay_database
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    root = f"/api/v1/organizations/{tenant}/businesses/{business}"
    context_url = root + "/editorial-context"
    search_url = root + "/reference-discoveries"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    scope = local_scope(5)
    initial = await api.put(
        context_url,
        headers=owner,
        json={"expected_version": 0, "operation_id": str(uuid4()), "preferences": {"reference_search": scope}},
    )
    assert initial.status_code == 200
    missing = await api.post(search_url, headers=owner, json={"operation_id": str(uuid4())})
    assert missing.status_code == 409 and missing.json()["error_code"] == "REFERENCE_TERMS_REQUIRED"
    set_terms = await api.put(
        context_url,
        headers=owner,
        json={
            "expected_version": 1,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": scope, "business_terms": ["Café"]},
        },
    )
    assert set_terms.status_code == 200, set_terms.text
    search = await api.post(search_url, headers=owner, json={"operation_id": str(uuid4())})
    assert search.status_code == 200, search.text
    attempted_change = {
        "expected_version": 2,
        "operation_id": str(uuid4()),
        "preferences": {"reference_search": scope, "business_terms": ["Padaria"]},
    }
    blocked = await api.put(context_url, headers=owner, json=attempted_change)
    assert blocked.status_code == 409 and blocked.json()["error_code"] == "REFERENCE_SEARCH_IN_PROGRESS"
    unrelated = await api.put(
        context_url,
        headers=owner,
        json={
            "expected_version": 2,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": scope, "tone": "friendly"},
        },
    )
    assert unrelated.status_code == 200 and unrelated.json()["preferences"]["business_terms"] == ["Café"]
    events = await claim_events(relay_database, uuid4())
    assert len(events) == 1
    assert await ReferenceDiscoveryActivities(database, settings).simulate_discovery(events[0].event) == "simulated"
    change_after = await api.put(
        context_url,
        headers=owner,
        json={
            "expected_version": 3,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": scope, "business_terms": ["Padaria"]},
        },
    )
    assert change_after.status_code == 200, change_after.text


async def test_terms_update_and_search_admission_are_serialized(admin, api, seeded, settings, database, relay_database):
    import asyncio

    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    root = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    scope = local_scope(5)
    initial = await api.put(
        root + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 0,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": scope, "business_terms": ["Café"]},
        },
    )
    assert initial.status_code == 200
    update, search = await asyncio.gather(
        api.put(
            root + "/editorial-context",
            headers=owner,
            json={
                "expected_version": 1,
                "operation_id": str(uuid4()),
                "preferences": {"reference_search": scope, "business_terms": ["Padaria"]},
            },
        ),
        api.post(root + "/reference-discoveries", headers=owner, json={"operation_id": str(uuid4())}),
    )
    assert search.status_code == 200, search.text
    assert update.status_code in {200, 409}, update.text
    if update.status_code == 409:
        assert update.json()["error_code"] == "REFERENCE_SEARCH_IN_PROGRESS"
    async with admin.connect() as connection:
        row = (
            (
                await connection.execute(
                    text("""SELECT d.context_version,h.version AS current_version
          FROM reference_discoveries d JOIN business_context_heads h USING(tenant_id,business_id)
          WHERE d.tenant_id=:tenant AND d.business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one()
        )
        assert row["context_version"] == row["current_version"]
    events = await claim_events(relay_database, uuid4())
    assert len(events) == 1
    assert await ReferenceDiscoveryActivities(database, settings).simulate_discovery(events[0].event) == "simulated"


async def test_search_waits_for_already_deferred_context_change(admin, api, seeded, settings):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    root = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    initial = await api.put(
        root + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 0,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": local_scope(5), "business_terms": ["Café"]},
        },
    )
    assert initial.status_code == 200
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_visual_pending_changes
          (tenant_id,business_id,actor_id,operation_id,kind,resource_key,request_hash,payload,state)
          VALUES(:tenant,:business,:actor,:operation,'context_update','context',:digest,'{}'::jsonb,'pending')"""),
            {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4(), "digest": "a" * 64},
        )
    response = await api.post(root + "/reference-discoveries", headers=owner, json={"operation_id": str(uuid4())})
    assert response.status_code == 409 and response.json()["error_code"] == "REFERENCE_CONTEXT_CHANGE_PENDING"
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_discoveries")) == 0
