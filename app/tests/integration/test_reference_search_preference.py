"""Persist reference scope through the existing owner-only, versioned context."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.tests.unit.test_core import access_token


async def test_reference_scope_version_replay_and_access(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
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
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    scope = {
        "scope": "local",
        "radius_km": 5,
        "origin": {"method": "manual", "address": {"city": "Curitiba", "state_code": "PR"}},
    }
    payload = {"operation_id": str(uuid4()), "expected_version": 0, "preferences": {"reference_search": scope}}
    assert (await api.put(base, headers=viewer, json=payload)).status_code == 403
    assert (await api.put(base, headers=other, json=payload)).status_code == 403
    saved = await api.put(base, headers=owner, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["preferences"]["reference_search"]["origin"]["coordinates"] is None
    assert (await api.put(base, headers=owner, json=payload)).json() == saved.json()
    changed = {**payload, "preferences": {"reference_search": {**scope, "radius_km": 10}}}
    assert (await api.put(base, headers=owner, json=changed)).json()["error_code"] == "CONTEXT_OPERATION_CONFLICT"
    stale = {**changed, "operation_id": str(uuid4())}
    assert (await api.put(base, headers=owner, json=stale)).json()["error_code"] == "CONTEXT_VERSION_CONFLICT"
    national = {
        "operation_id": str(uuid4()),
        "expected_version": 1,
        "preferences": {"reference_search": {"scope": "national"}},
    }
    rejected = await api.put(base, headers=owner, json=national)
    assert rejected.status_code == 422
    assert rejected.json()["error_code"] == "REFERENCE_SEARCH_NOT_SUPPORTED"
    updated = {
        **national,
        "operation_id": str(uuid4()),
        "preferences": {"reference_search": {**scope, "radius_km": 20}},
    }
    assert (await api.put(base, headers=owner, json=updated)).json()["version"] == 2
    assert (await api.get(base + "/versions/1", headers=owner)).json() == saved.json()
    assert (await api.get(base, headers=other)).status_code == 403
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_context_versions")) == 2
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='editorial.context_updated'"))
            == 2
        )


async def seed_legacy_context(admin, tenant, business, actor, scope):
    import json

    from app.schemas.editorial_context import ContextUpdate
    from app.services.editorial_context import _digest

    operation = uuid4()
    payload = ContextUpdate.model_validate(
        {"expected_version": 0, "operation_id": operation, "preferences": {"reference_search": scope}}
    )
    document = payload.model_dump(mode="json", exclude={"expected_version", "operation_id"})
    document["preferences"].pop("business_terms")
    document["preferences"].pop("business_characteristics")
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_context_heads(tenant_id,business_id,version)
              VALUES(:tenant,:business,1)"""),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,1,:operation,:actor,:digest,CAST(:document AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "operation": operation,
                "actor": actor,
                "digest": _digest(payload),
                "document": json.dumps(document),
            },
        )
    original = payload.model_dump(mode="json")
    original["preferences"].pop("business_terms")
    original["preferences"].pop("business_characteristics")
    return original


@pytest.mark.parametrize(
    "scope",
    [
        {"scope": "national"},
        {
            "scope": "local",
            "radius_km": 10,
            "origin": {"method": "manual", "address": {"city": "Rio", "state_code": "RJ"}},
        },
    ],
)
async def test_legacy_scope_survives_unrelated_changes_and_replay(admin, api, seeded, settings, scope):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles(tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    original = await seed_legacy_context(admin, tenant, business, actor, scope)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    replay = await api.put(base, headers=owner, json=original)
    assert replay.status_code == 200, replay.text
    assert replay.json()["preferences"]["reference_search"]["scope"] == scope["scope"]
    changed_replay = {
        **original,
        "preferences": {**original["preferences"], "business_characteristics": None},
    }
    conflict = await api.put(base, headers=owner, json=changed_replay)
    assert conflict.status_code == 409 and conflict.json()["error_code"] == "CONTEXT_OPERATION_CONFLICT"
    unrelated = {"expected_version": 1, "operation_id": str(uuid4()), "preferences": {"tone": "friendly"}}
    assert (await api.put(base, headers=viewer, json=unrelated)).status_code == 403
    updated = await api.put(base, headers=owner, json=unrelated)
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == 2
    assert updated.json()["preferences"]["tone"] == "friendly"
    assert updated.json()["preferences"]["reference_search"] == replay.json()["preferences"]["reference_search"]
    assert (await api.put(base, headers=owner, json=unrelated)).json() == updated.json()
    restore = {"expected_version": 2, "target_version": 1, "operation_id": str(uuid4())}
    assert (await api.post(base + "/restore", headers=owner, json=restore)).json()["version"] == 3
    allowed = {
        "scope": "local",
        "radius_km": 20,
        "origin": {"method": "manual", "address": {"city": "Rio", "state_code": "RJ"}},
    }
    transition = {"expected_version": 3, "operation_id": str(uuid4()), "preferences": {"reference_search": allowed}}
    accepted = await api.put(base, headers=owner, json=transition)
    assert accepted.status_code == 200 and accepted.json()["version"] == 4
    restore_legacy = {"expected_version": 4, "target_version": 1, "operation_id": str(uuid4())}
    rejected = await api.post(base + "/restore", headers=owner, json=restore_legacy)
    assert rejected.status_code == 422 and rejected.json()["error_code"] == "REFERENCE_SEARCH_NOT_SUPPORTED"
    other_legacy = {"expected_version": 4, "operation_id": str(uuid4()), "preferences": {"reference_search": scope}}
    assert (await api.put(base, headers=owner, json=other_legacy)).json()[
        "error_code"
    ] == "REFERENCE_SEARCH_NOT_SUPPORTED"
    remove = {"expected_version": 4, "operation_id": str(uuid4()), "preferences": {"reference_search": None}}
    cleared = await api.put(base, headers=owner, json=remove)
    assert cleared.status_code == 200 and cleared.json()["preferences"]["reference_search"] is None
