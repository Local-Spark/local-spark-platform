"""Owner-only, versioned editorial context survives concurrent edits and replays."""

import asyncio
from uuid import uuid4

from sqlalchemy import text

from app.tests.unit.test_core import access_token


async def test_context_owner_history_restore_and_conflicts(admin, api, seeded, settings):
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
    assert (await api.get(base, headers=owner)).json() == {
        "facts": [],
        "preferences": {"goal": None, "tone": None, "avoided_topics": [], "posts_per_week": None},
        "version": 0,
        "updated_at": None,
        "hypotheses": [],
    }
    assert (await api.get(base, headers=viewer)).status_code == 403
    assert (await api.get(base, headers=other)).status_code == 403
    assert (await api.get(base + "/versions/1", headers=owner)).status_code == 404
    assert (await api.get(base + "/history", headers=owner)).json() == []

    payload = {
        "operation_id": str(uuid4()),
        "expected_version": 0,
        "facts": [
            {
                "id": str(uuid4()),
                "kind": "offer",
                "statement": "Combo de sexta",
                "source_detail": "Informado pelo dono",
                "valid_until": "2026-12-31",
            }
        ],
        "preferences": {"goal": "sales", "tone": "friendly", "avoided_topics": ["Política"], "posts_per_week": 3},
    }
    invalid = {**payload, "facts": [{**payload["facts"][0], "valid_until": None}]}
    assert (await api.put(base, headers=owner, json=invalid)).status_code == 422
    assert (await api.put(base, headers=viewer, json=payload)).status_code == 403
    created = await api.put(base, headers=owner, json=payload)
    assert created.status_code == 200, created.text
    assert created.json()["version"] == 1
    assert created.json()["facts"][0]["statement"] == "Combo de sexta"
    assert (await api.put(base, headers=owner, json=payload)).json() == created.json()
    assert (await api.put(base, headers=owner, json={**payload, "facts": []})).json()[
        "error_code"
    ] == "CONTEXT_OPERATION_CONFLICT"
    assert (await api.put(base, headers=owner, json={**payload, "operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "CONTEXT_VERSION_CONFLICT"
    assert (await api.get(base + "/versions/1", headers=owner)).json() == created.json()
    assert (await api.get(base + "/history", headers=owner)).json()[0]["version"] == 1

    revised = {
        **payload,
        "operation_id": str(uuid4()),
        "expected_version": 1,
        "facts": [],
        "preferences": {"goal": "appointments", "tone": "direct", "posts_per_week": 2},
    }
    second = await api.put(base, headers=owner, json=revised)
    assert second.json()["version"] == 2
    assert second.json()["facts"] == []
    restore = {"operation_id": str(uuid4()), "expected_version": 2, "target_version": 1}
    restored = await api.post(base + "/restore", headers=owner, json=restore)
    assert restored.json()["version"] == 3
    assert restored.json()["facts"] == created.json()["facts"]
    assert (await api.post(base + "/restore", headers=owner, json=restore)).json() == restored.json()
    assert (await api.post(base + "/restore", headers=owner, json={**restore, "target_version": 2})).json()[
        "error_code"
    ] == "CONTEXT_OPERATION_CONFLICT"
    assert (
        await api.post(
            base + "/restore", headers=owner, json={**restore, "operation_id": str(uuid4()), "target_version": 99}
        )
    ).status_code == 404
    assert (await api.post(base + "/restore", headers=owner, json={**restore, "operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "CONTEXT_VERSION_CONFLICT"
    assert [item["version"] for item in (await api.get(base + "/history", headers=owner)).json()] == [3, 2, 1]
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_context_versions")) == 3
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='editorial.context_updated'"))
            == 3
        )


async def test_context_cas_and_tenant_rls(admin, api, database, seeded, settings):
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
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    first, second = await asyncio.gather(
        *[
            api.put(
                base,
                headers=headers,
                json={"operation_id": str(uuid4()), "expected_version": 0, "facts": [], "preferences": {"goal": goal}},
            )
            for goal in ("sales", "awareness")
        ]
    )
    assert sorted([first.status_code, second.status_code]) == [200, 409]
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_context_versions")) == 0
