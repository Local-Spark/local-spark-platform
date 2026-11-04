"""Simulated cycle limits, confirmation, overlap and expiry with real RLS."""

import asyncio
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.services.outbox import claim_events, finish_event
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token
from app.workflows.reference_discovery_activities import ReferenceDiscoveryActivities
from app.workflows.reference_selection_activities import ReferenceSelectionActivities

pytestmark = pytest.mark.integration


async def complete_events(database, relay_database):
    relay = uuid4()
    events = await claim_events(relay_database, relay)
    for event in events:
        if event.event_type == "reference.search_requested":
            await ReferenceDiscoveryActivities(
                database, SimpleNamespace(reference_discovery_mode="fake")
            ).simulate_discovery(event.event)
        elif event.event_type == "reference.selection_confirmed":
            await ReferenceSelectionActivities(database).record_selection(event.event)
        assert await finish_event(relay_database, event, relay, success=True)


async def search(api, base, owner, database, relay_database):
    operation = str(uuid4())
    url = base + "/reference-discoveries"
    response = await api.post(url, headers=owner, json={"operation_id": operation})
    assert response.status_code == 200, response.text
    await complete_events(database, relay_database)
    fixtures = await api.get(url + "/" + response.json()["id"] + "/fixtures", headers=owner)
    assert fixtures.status_code == 200, fixtures.text
    return response.json(), fixtures.json(), operation


async def test_limits_dedup_lock_swap_expiry_and_preserved_selection(
    admin, api, seeded, settings, database, relay_database
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    url = base + "/reference-discoveries"
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    found5, candidates5, op5 = await search(api, base, owner, database, relay_database)
    assert len(candidates5) == 3 and all(c["mode"] == "fake" for c in candidates5)
    assert (await api.post(url, headers=owner, json={"operation_id": op5})).json()["id"] == found5["id"]
    blocked5 = await api.post(url, headers=owner, json={"operation_id": str(uuid4())})
    assert blocked5.json()["error_code"] == "REFERENCE_RADIUS_ALREADY_SEARCHED"
    assert (await save_scope(api, base, owner, 1, local_scope(20))).status_code == 200
    found20, candidates20, _ = await search(api, base, owner, database, relay_database)
    assert [c["canonical_id"] for c in candidates5] == [c["canonical_id"] for c in candidates20]
    for index in range(4):
        manual = await api.post(
            base + "/references",
            headers=owner,
            json={"operation_id": str(uuid4()), "instagram": f"@manual{index}"},
        )
        assert manual.status_code == 200, manual.text
    selection_url = url + "/fixture-selection"
    empty = (await api.get(selection_url, headers=owner)).json()
    assert empty == {"candidate_ids": [], "locked_until": None, "mode": "fake"}
    duplicate_entity = {"operation_id": str(uuid4()), "candidate_ids": [candidates5[0]["id"], candidates20[0]["id"]]}
    assert (await api.post(selection_url, headers=owner, json=duplicate_entity)).json()[
        "error_code"
    ] == "REFERENCE_SELECTION_DUPLICATE_ENTITY"
    assert (await api.post(selection_url, headers=other, json=duplicate_entity)).status_code == 403
    chosen = {
        "operation_id": str(uuid4()),
        "candidate_ids": [candidates5[0]["id"], candidates20[1]["id"], candidates5[2]["id"]],
    }
    confirmed = await api.post(selection_url, headers=owner, json=chosen)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["mode"] == "fake"
    current = (await api.get(selection_url, headers=owner)).json()
    assert len(current["candidate_ids"]) == 3 and current["locked_until"] == confirmed.json()["locked_until"]
    assert len((await api.get(base + "/references", headers=owner)).json()) == 4
    assert (await api.post(selection_url, headers=owner, json=chosen)).json() == confirmed.json()
    conflict = {**chosen, "candidate_ids": [candidates5[0]["id"]]}
    assert (await api.post(selection_url, headers=owner, json=conflict)).json()[
        "error_code"
    ] == "REFERENCE_SELECTION_OPERATION_CONFLICT"
    assert (
        await api.post(
            selection_url, headers=owner, json={"operation_id": str(uuid4()), "candidate_ids": [str(uuid4())]}
        )
    ).json()["error_code"] == "REFERENCE_SELECTION_INVALID_CANDIDATE"
    assert (
        await api.post(
            selection_url,
            headers=owner,
            json={"operation_id": str(uuid4()), "candidate_ids": [candidates5[0]["id"]] * 2},
        )
    ).status_code == 422
    assert (await save_scope(api, base, owner, 2, local_scope(50))).status_code == 200
    changed_terms = await api.put(
        base + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 3,
            "operation_id": str(uuid4()),
            "preferences": {"reference_search": local_scope(50), "business_terms": ["Padaria"]},
        },
    )
    assert changed_terms.status_code == 200, changed_terms.text
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_profiles SET category='Bakery' WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
    # A new radius remains available even after a selection starts the clock.
    found50_before_expiry, candidates50, op50 = await search(api, base, owner, database, relay_database)
    assert all(candidate["selected"] for candidate in candidates50)
    assert (await api.post(url, headers=owner, json={"operation_id": op50})).json()["id"] == found50_before_expiry["id"]
    assert (await api.get(selection_url, headers=owner)).json()["locked_until"] == confirmed.json()["locked_until"]
    mixed = await api.post(
        selection_url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "candidate_ids": [candidates5[0]["id"], candidates20[1]["id"], candidates50[2]["id"]],
        },
    )
    assert mixed.status_code == 200, mixed.text
    assert mixed.json()["locked_until"] == confirmed.json()["locked_until"]
    candidate_entities = {c["id"]: c["canonical_id"] for c in candidates5 + candidates20 + candidates50}
    current_ids = (await api.get(selection_url, headers=owner)).json()["candidate_ids"]
    assert {candidate_entities[value] for value in current_ids} == {
        candidate_entities[value] for value in mixed.json()["candidate_ids"]
    }
    # Changing the point or business segment cannot unlock an already used radius.
    moved = local_scope(50)
    moved["origin"]["coordinates"]["longitude"] = -46.65
    assert (await save_scope(api, base, owner, 4, moved)).status_code == 200
    assert (await api.post(url, headers=owner, json={"operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "REFERENCE_RADIUS_ALREADY_SEARCHED"
    swapped = await api.post(
        selection_url, headers=owner, json={"operation_id": str(uuid4()), "candidate_ids": [candidates5[1]["id"]]}
    )
    assert swapped.status_code == 200, swapped.text
    assert swapped.json()["locked_until"] == confirmed.json()["locked_until"]
    old_rows = (await api.get(url + "/" + found5["id"] + "/fixtures", headers=owner)).json()
    assert [r["selected"] for r in old_rows] == [False, True, False]
    async with admin.begin() as connection:
        assert await connection.scalar(
            text("SELECT locked_until = confirmed_at + interval '6 months' FROM reference_search_cycles")
        )
        await connection.execute(
            text(
                "UPDATE reference_search_cycles SET confirmed_at=now()-interval '7 months', "
                "locked_until=now()-interval '1 month'"
            )
        )
    found50, fresh, _ = await search(api, base, owner, database, relay_database)
    previous = (await api.get(selection_url, headers=owner)).json()
    assert len(previous["candidate_ids"]) == 1 and previous["locked_until"] is None
    assert len((await api.get(url, headers=owner)).json()) == 4
    preserved = (await api.get(url + "/" + found5["id"] + "/fixtures", headers=owner)).json()
    assert [r["selected"] for r in preserved] == [False, True, False]
    assert fresh[0]["canonical_id"] != candidates5[0]["canonical_id"]

    # Model the same business appearing in the fresh results and the previous
    # selection: fixture canonical IDs otherwise deliberately differ per cycle.
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_discovery_candidates SET canonical_id=:canonical WHERE id=:candidate"),
            {"canonical": UUID(candidates5[1]["canonical_id"]), "candidate": UUID(fresh[0]["id"])},
        )
    duplicate = await api.post(
        selection_url,
        headers=owner,
        json={"operation_id": str(uuid4()), "candidate_ids": [candidates5[1]["id"], fresh[0]["id"]]},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error_code"] == "REFERENCE_SELECTION_DUPLICATE_ENTITY"
    old_unselected = await api.post(
        selection_url,
        headers=owner,
        json={"operation_id": str(uuid4()), "candidate_ids": [candidates5[0]["id"], fresh[1]["id"]]},
    )
    assert old_unselected.status_code == 409
    assert old_unselected.json()["error_code"] == "REFERENCE_SELECTION_INVALID_CANDIDATE"
    mixed_payload = {
        "operation_id": str(uuid4()),
        "candidate_ids": [candidates5[1]["id"], fresh[1]["id"]],
    }
    new_confirmation = await api.post(selection_url, headers=owner, json=mixed_payload)
    assert new_confirmation.status_code == 200, new_confirmation.text
    assert (await api.post(selection_url, headers=owner, json=mixed_payload)).json() == new_confirmation.json()
    assert [r["selected"] for r in (await api.get(url + "/" + found5["id"] + "/fixtures", headers=owner)).json()] == [
        False,
        True,
        False,
    ]
    assert [r["selected"] for r in (await api.get(url + "/" + found50["id"] + "/fixtures", headers=owner)).json()] == [
        True,
        True,
        False,
    ]
    retained_ids = (await api.get(selection_url, headers=owner)).json()["candidate_ids"]
    all_entities = {c["id"]: c["canonical_id"] for c in candidates5 + candidates20 + candidates50 + fresh}
    all_entities[fresh[0]["id"]] = candidates5[1]["canonical_id"]
    assert {all_entities[value] for value in retained_ids} == {
        candidates5[1]["canonical_id"],
        fresh[1]["canonical_id"],
    }


async def test_concurrent_same_radius_is_reserved_once(admin, api, seeded, settings):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    url = base + "/reference-discoveries"
    results = await asyncio.gather(
        *(api.post(url, headers=owner, json={"operation_id": str(uuid4())}) for _ in range(2))
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    assert [r.json().get("error_code") for r in results if r.status_code == 409] == [
        "REFERENCE_RADIUS_ALREADY_SEARCHED"
    ]
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_search_cycles")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM reference_discoveries")) == 1


async def test_search_waiting_for_lock_rechecks_expiry_after_the_wait(
    admin, api, seeded, settings, database, relay_database
):
    from app.services.reference_cycles import reserve_simulated_radius

    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    _, candidates, _ = await search(api, base, owner, database, relay_database)
    selected = await api.post(
        base + "/reference-discoveries/fixture-selection",
        headers=owner,
        json={"operation_id": str(uuid4()), "candidate_ids": [candidates[0]["id"]]},
    )
    assert selected.status_code == 200, selected.text
    started = asyncio.Event()

    async def reserve():
        async with database.transaction(tenant, actor) as session:
            # Establish the transaction timestamp while the old cycle is live.
            await session.scalar(text("SELECT now()"))
            started.set()
            return await reserve_simulated_radius(session, tenant, business, 5)

    async with admin.begin() as connection:
        old_cycle = await connection.scalar(
            text("""SELECT cycle_id FROM reference_search_heads
                    WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
            {"tenant": tenant, "business": business},
        )
        waiting = asyncio.create_task(reserve())
        await asyncio.wait_for(started.wait(), timeout=2)
        await connection.execute(
            text("""UPDATE reference_search_cycles SET
                confirmed_at=clock_timestamp()+interval '0.5 second'-interval '6 months',
                locked_until=clock_timestamp()+interval '0.5 second'
                WHERE id=:id"""),
            {"id": old_cycle},
        )
        await connection.execute(text("SELECT pg_sleep(0.6)"))
        assert not waiting.done()
    assert await asyncio.wait_for(waiting, timeout=2) != old_cycle


async def test_confirmation_waiting_for_lock_starts_six_months_after_wait(
    admin, api, seeded, settings, database, relay_database, monkeypatch
):
    from app.schemas.reference_discovery import FixtureSelectionRequest
    from app.services import reference_cycles

    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    _, candidates, _ = await search(api, base, owner, database, relay_database)
    started = asyncio.Event()
    original = reference_cycles.lock_reference_head

    async def observed_lock(*args):
        started.set()
        return await original(*args)

    monkeypatch.setattr(reference_cycles, "lock_reference_head", observed_lock)
    service = reference_cycles.FixtureSelectionService(settings, database)
    payload = FixtureSelectionRequest(operation_id=uuid4(), candidate_ids=[candidates[0]["id"]])
    async with admin.begin() as connection:
        await connection.scalar(
            text("""SELECT cycle_id FROM reference_search_heads
                    WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
            {"tenant": tenant, "business": business},
        )
        waiting = asyncio.create_task(service.confirm(tenant, business, actor, payload))
        await asyncio.wait_for(started.wait(), timeout=2)
        await connection.execute(text("SELECT pg_sleep(0.1)"))
        assert not waiting.done()
        before_unlock = await connection.scalar(text("SELECT clock_timestamp()"))
    await asyncio.wait_for(waiting, timeout=2)
    async with admin.connect() as connection:
        confirmed, six_months = (
            await connection.execute(
                text("""SELECT confirmed_at, locked_until = confirmed_at + interval '6 months'
                        FROM reference_search_cycles WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
        ).one()
    assert confirmed >= before_unlock
    assert six_months


async def test_revoked_owner_pending_radius_is_recovered_with_scoped_worker(
    admin, api, seeded, settings, database, relay_database
):
    from app.db.session import Database

    settings.reference_discovery_mode = "fake"
    tenant, actor, successor = seeded["t1"], seeded["a1"], seeded["a2"]
    business = await create_business(admin, tenant)
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": tenant, "actor": successor},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    successor_headers = {"Authorization": f"Bearer {access_token(settings, successor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    requested = await api.post(base + "/reference-discoveries", headers=owner, json={"operation_id": str(uuid4())})
    assert requested.status_code == 200
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": actor},
        )
    worker = Database(settings, correlator=True)
    try:
        claims = await claim_events(relay_database, uuid4())
        assert len(claims) == 1
        activity = ReferenceDiscoveryActivities(database, settings, worker)
        assert await activity.simulate_discovery(claims[0].event) == "stale"
        assert await activity.simulate_discovery(claims[0].event) == "stale"
        assert await activity.fail_discovery(claims[0].event) == "stale"
        async with worker.transaction(seeded["t2"], actor) as session:
            assert await session.scalar(text("SELECT count(*) FROM reference_discoveries")) == 0
        async with worker.transaction(tenant, successor) as session:
            assert await session.scalar(text("SELECT count(*) FROM reference_discoveries")) == 0
        recovered = await api.post(
            base + "/reference-discoveries", headers=successor_headers, json={"operation_id": str(uuid4())}
        )
        assert recovered.status_code == 200, recovered.text
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_discoveries WHERE state='stale'")) == 1
            assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 1
    finally:
        await worker.close()


async def test_revoked_owner_selection_event_is_acknowledged_without_changing_lock(
    admin, api, seeded, settings, database, relay_database
):
    from app.db.session import Database

    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    _, fixtures, _ = await search(api, base, owner, database, relay_database)
    selected = await api.post(
        base + "/reference-discoveries/fixture-selection",
        headers=owner,
        json={"operation_id": str(uuid4()), "candidate_ids": [fixtures[0]["id"]]},
    )
    assert selected.status_code == 200
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": actor},
        )
    worker = Database(settings, correlator=True)
    try:
        claims = await claim_events(relay_database, uuid4())
        assert len(claims) == 1 and claims[0].event_type == "reference.selection_confirmed"
        activity = ReferenceSelectionActivities(database, worker)
        assert await activity.record_selection(claims[0].event) == "recorded"
        assert await activity.record_selection(claims[0].event) == "recorded"
        async with admin.connect() as connection:
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_discovery_candidates WHERE selected=true"))
                == 1
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_search_cycles WHERE locked_until>now()"))
                == 1
            )
            assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 2
    finally:
        await worker.close()


async def test_known_fake_failure_and_disabled_mode_release_the_radius(
    admin, api, seeded, settings, database, relay_database
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    url = base + "/reference-discoveries"
    first = await api.post(url, headers=owner, json={"operation_id": str(uuid4())})
    assert first.status_code == 200
    relay = uuid4()
    claims = await claim_events(relay_database, relay)
    assert len(claims) == 1
    activity = ReferenceDiscoveryActivities(database, settings)
    assert await activity.fail_discovery(claims[0].event) == "stale"
    assert await activity.fail_discovery(claims[0].event) == "stale"
    assert await finish_event(relay_database, claims[0], relay, success=True)
    retry = await api.post(url, headers=owner, json={"operation_id": str(uuid4())})
    assert retry.status_code == 200, retry.text
    relay2 = uuid4()
    claims = await claim_events(relay_database, relay2)
    assert len(claims) == 1
    settings.reference_discovery_mode = "disabled"
    assert await activity.simulate_discovery(claims[0].event) == "stale"
    assert await finish_event(relay_database, claims[0], relay2, success=True)
    settings.reference_discovery_mode = "fake"
    assert (await api.post(url, headers=owner, json={"operation_id": str(uuid4())})).status_code == 200
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_discovery_candidates")) == 0
