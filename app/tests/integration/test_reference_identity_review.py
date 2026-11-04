"""Own-listing decisions and empty-radius recovery use only synthetic fixtures."""

import asyncio
import json
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_context_loader import load_search_context
from app.services.reference_empty_search import advance_empty_search
from app.services.reference_google_intent import create_google_intent, google_effect_id
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard, PlacesGuardContext
from app.services.reference_search_admission import admit_provider_search
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _linked
from app.tests.integration.test_reference_places_budget_guard import _pilot, _request
from app.tests.integration.test_reference_search_admission import _KEY, _business
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration
_ATOMIC = text("""SELECT public.reference_filtered_commit_with_identity(
 :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
 :source,:context,CAST(:candidates AS jsonb),CAST(:judgments AS jsonb),CAST(:match AS jsonb))""")


async def _own_setup(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    values = _params(google, jev, gg, jg, candidate)
    base = f"/api/v1/organizations/{google.tenant}/businesses/{google.business}"
    headers = {"Authorization": f"Bearer {access_token(settings, google.actor)}"}
    assert (
        await api.put(
            base + "/address",
            headers=headers,
            json={
                "operation_id": str(uuid4()),
                "expected_version": 0,
                "address": {"street": "Rua Ficticia", "number": "10", "city": "São Paulo", "state_code": "SP"},
            },
        )
    ).status_code == 200
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE reference_provider_effects SET request_event_id=:e WHERE id=:g"),
            {"e": google.event, "g": google.effect},
        )
        await conn.execute(text("SELECT set_config('app.tenant_id',:v,true)"), {"v": str(google.tenant)})
        await conn.execute(text("SELECT set_config('app.actor_id',:v,true)"), {"v": str(google.actor)})
        own = await conn.scalar(text("SELECT reference_prepare_business_identity(:b)"), {"b": google.business})
        await conn.execute(
            text("""UPDATE reference_provider_searches SET business_name=:name,business_row_version=:row,
          business_address_version=:address,business_location_version=:location,
          business_identity_mac=:mac WHERE id=:s"""),
            {
                "name": own["name"],
                "row": own["row_version"],
                "address": own["address_version"],
                "location": own["location_version"],
                "mac": "f" * 64,
                "s": google.search,
            },
        )
    values["judgments"] = json.dumps(
        [{"candidate_id": str(candidate), "judgment": "match", "similarity_level": "high"}]
    )
    return google, worker, values, candidate, base, headers


async def _commit_match(worker, google, values, match):
    async with worker.transaction(google.tenant, google.actor) as session:
        return await session.scalar(_ATOMIC, values | {"match": json.dumps(match)})


async def test_own_review_is_atomic_and_shared_owners_can_confirm(admin, api, seeded, settings):
    google, worker, values, candidate, base, headers = await _own_setup(admin, api, seeded, settings)
    route = base + f"/reference-results/searches/{google.search}/own-business-review"
    try:
        assert (await api.get(route, headers=headers)).json()["status"] == "pending"
        with pytest.raises(DBAPIError, match="REFERENCE_OWN_MATCH_INVALID"):
            await _commit_match(worker, google, values, {"status": "identified", "place_ids": []})
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
        match = {"status": "review", "place_ids": ["fake-place", "excluded-by-similarity"]}
        assert await _commit_match(worker, google, values, match) == values["batch"]
        assert await _commit_match(worker, google, values, match) == values["batch"]
        pending = (await api.get(route, headers=headers)).json()
        assert pending["status"] == "awaiting_confirmation" and pending["candidates"] == [{"place_id": "fake-place"}]
        async with worker.transaction(google.tenant, google.actor) as session:
            with pytest.raises(DBAPIError, match="REFERENCE_OWN_REVIEW_REQUIRED"):
                await session.scalar(
                    text("SELECT reference_prepare_shortlist(:b,:s,:batch,:op,:ids)"),
                    {
                        "b": google.business,
                        "s": google.search,
                        "batch": values["batch"],
                        "op": uuid4(),
                        "ids": [candidate],
                    },
                )
        second = seeded["viewer"]
        second_headers = {"Authorization": f"Bearer {access_token(settings, second)}"}
        assert (await api.get(route, headers=second_headers)).status_code == 403
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
                {"t": google.tenant, "a": second},
            )
        assert (await api.get(route, headers=second_headers)).json() == pending
        payload = {"operation_id": str(uuid4()), "place_id": "fake-place"}
        confirmed = await api.post(route, headers=second_headers, json=payload)
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["excluded_place_id"] == "fake-place"
        assert confirmed.json()["candidates"] == []
        assert (await api.post(route, headers=second_headers, json=payload)).json() == confirmed.json()
        assert (await api.post(route, headers=headers, json=payload)).status_code == 409
        async with admin.connect() as conn:
            event = await conn.scalar(
                text("SELECT payload FROM outbox_events WHERE event_type='reference.search_reviewed'")
            )
            assert event["actor_id"] == str(google.actor)
            assert (
                await conn.scalar(
                    text("SELECT actor_id FROM audit_events WHERE action='reference.own_business_review_confirmed'")
                )
                == second
            )
        async with worker.transaction(google.tenant, google.actor) as session:
            assert (
                await session.scalar(
                    text("SELECT reference_prepare_shortlist(:b,:s,:batch,:op,:ids)"),
                    {"b": google.business, "s": google.search, "batch": values["batch"], "op": uuid4(), "ids": []},
                )
                is not None
            )
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": google.tenant, "a": second},
            )
        assert (await api.get(route, headers=second_headers)).status_code == 403
    finally:
        await worker.close()


@pytest.mark.parametrize(
    "match,excluded",
    [
        ({"status": "absent", "place_ids": []}, None),
        ({"status": "identified", "place_ids": ["fake-place"]}, "fake-place"),
        ({"status": "review", "place_ids": ["not-eligible"]}, None),
    ],
)
async def test_automatic_own_match_resolves_without_customer_step(admin, api, seeded, settings, match, excluded):
    google, worker, values, candidate, base, headers = await _own_setup(admin, api, seeded, settings)
    try:
        await _commit_match(worker, google, values, match)
        data = (
            await api.get(base + f"/reference-results/searches/{google.search}/own-business-review", headers=headers)
        ).json()
        assert data["status"] == "resolved" and data["excluded_place_id"] == excluded and data["candidates"] == []
        async with worker.transaction(google.tenant, google.actor) as session:
            await session.scalar(
                text("SELECT reference_prepare_shortlist(:b,:s,:batch,:op,:ids)"),
                {
                    "b": google.business,
                    "s": google.search,
                    "batch": values["batch"],
                    "op": uuid4(),
                    "ids": [] if excluded else [candidate],
                },
            )
    finally:
        await worker.close()


async def _empty(worker, tenant, business, actor, search, pilot, tariff, amount=1, context_version=1):
    context = PlacesGuardContext(
        tenant,
        business,
        actor,
        search,
        google_effect_id(search),
        pilot,
        uuid4(),
        context_version,
        _KEY,
        "test-v1",
        tariff,
        "synthetic-project",
        amount,
    )
    context = await create_google_intent(worker, context, _request())
    guard = DatabasePlacesBudgetGuard(worker, context)
    assert await guard.claim(context.effect, _request())
    await guard.complete_empty()


async def _family(database, tenant, actor, business, search):
    async with database.transaction(tenant, actor) as session:
        return await session.scalar(text("SELECT reference_read_search_family(:b,:s)"), {"b": business, "s": search})


async def test_empty_radius_chain_is_durable_budgeted_and_reopens_only_unconfirmed_round(
    admin, api, seeded, settings, database
):
    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    initial = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    worker = Database(settings, correlator=True)
    pilot, tariff = await _pilot(admin, cap=100)
    try:
        await _empty(worker, tenant, business, actor, initial.search_id, pilot, tariff)
        first, replay = await asyncio.gather(
            *[
                advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, initial.search_id)
                for _ in range(2)
            ]
        )
        assert first == replay and first.state == "scheduled"
        family = await _family(database, tenant, actor, business, initial.search_id)
        assert family == {
            "family_root_id": str(initial.search_id),
            "family_current_search_id": str(first.next_search_id),
            "family_status": "pending",
            "can_retry_family": False,
        }
        async with admin.connect() as conn:
            event = await conn.scalar(
                text("SELECT request_event_id FROM reference_provider_searches WHERE id=:s"),
                {"s": first.next_search_id},
            )
        loaded = await load_search_context(
            worker, {"test-v1": _KEY}, tenant, business, actor, first.next_search_id, event
        )
        assert loaded.radius_km == 20
        await _empty(worker, tenant, business, actor, first.next_search_id, pilot, tariff)
        second = await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, first.next_search_id)
        assert second.state == "scheduled"
        await _policy(admin, search=2, monthly=1000, search_provider=100, monthly_provider=1000)
        with pytest.raises(DBAPIError, match="REFERENCE_SEARCH_BUDGET_EXCEEDED"):
            await _empty(worker, tenant, business, actor, second.next_search_id, pilot, tariff)
        await _policy(admin, search=100, monthly=1000, search_provider=100, monthly_provider=1000)
        await _empty(worker, tenant, business, actor, second.next_search_id, pilot, tariff)
        final = await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, second.next_search_id)
        assert final.state == "exhausted" and final.result_id is not None
        assert (
            await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, second.next_search_id) == final
        )
        family = await _family(database, tenant, actor, business, initial.search_id)
        assert family["family_status"] == "empty_exhausted" and family["can_retry_family"] is True
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT cycle_id FROM reference_real_heads WHERE business_id=:b"), {"b": business}
                )
                is None
            )
            assert await conn.scalar(text("SELECT count(*) FROM reference_provider_results")) == 1
            assert await conn.scalar(text("SELECT count(*) FROM reference_cycle_reviews")) == 0
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 3
            assert (
                await conn.scalar(
                    text(
                        "SELECT document#>>'{preferences,reference_search,radius_km}' "
                        "FROM business_context_versions WHERE business_id=:b AND version=1"
                    ),
                    {"b": business},
                )
                == "5.0"
            )
        next_round = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
        assert next_round.cycle_id != initial.cycle_id
        assert (await _family(database, tenant, actor, business, initial.search_id))["can_retry_family"] is False
    finally:
        await worker.close()


async def test_shared_cached_empty_radius_is_not_queried_or_charged_again(admin, api, seeded, settings, database):
    from app.tests.integration.test_reference_discovery import local_scope, save_scope

    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    other = seeded["viewer"]
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"), {"t": tenant, "a": other}
        )
    assert (await save_scope(api, base, headers, 1, local_scope(20))).status_code == 200
    cached = await admit_provider_search(database, _KEY, "test-v1", tenant, business, other, uuid4(), 2, 20)
    worker = Database(settings, correlator=True)
    pilot, tariff = await _pilot(admin, cap=100)
    try:
        await _empty(worker, tenant, business, other, cached.search_id, pilot, tariff, context_version=2)
        assert (await save_scope(api, base, headers, 2, local_scope(5))).status_code == 200
        root = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 3, 5)
        await _empty(worker, tenant, business, actor, root.search_id, pilot, tariff, context_version=3)
        next_step = await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, root.search_id)
        assert next_step.state == "scheduled"
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT radius_km FROM reference_provider_searches WHERE id=:s"),
                    {"s": next_step.next_search_id},
                )
                == 50
            )
            assert await conn.scalar(text("SELECT count(*) FROM reference_provider_searches")) == 3
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 2
            assert (
                await conn.execute(text("SELECT kind FROM reference_radius_expansions ORDER BY created_at"))
            ).scalars().all() == ["cached", "scheduled"]
        await _empty(worker, tenant, business, actor, next_step.next_search_id, pilot, tariff, context_version=3)
        final = await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, next_step.next_search_id)
        assert final.state == "exhausted"
        family = await _family(database, tenant, other, business, root.search_id)
        assert family["family_current_search_id"] == str(next_step.next_search_id)
        assert family["can_retry_family"] is True
        # Other owners can read lifecycle metadata but never borrow a paid executor token.
        async with worker.transaction(tenant, other) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.scalar(
                    text("SELECT executor_token FROM reference_provider_effects WHERE search_id=:s"),
                    {"s": root.search_id},
                )
    finally:
        await worker.close()


async def test_confirmed_cycle_is_not_released_by_empty_unused_radius(admin, api, seeded, settings, database):
    from app.tests.integration.test_reference_discovery import local_scope, save_scope

    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    assert (await save_scope(api, base, headers, 1, local_scope(50))).status_code == 200
    initial = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 2, 50)
    async with admin.begin() as conn:
        await conn.execute(
            text(
                "UPDATE reference_real_cycles SET confirmed_at=now(),locked_until=now()+interval '6 months' WHERE id=:c"
            ),
            {"c": initial.cycle_id},
        )
    worker = Database(settings, correlator=True)
    pilot, tariff = await _pilot(admin)
    try:
        await _empty(worker, tenant, business, actor, initial.search_id, pilot, tariff, context_version=2)
        final = await advance_empty_search(worker, _KEY, "test-v1", tenant, business, actor, initial.search_id)
        assert final.state == "exhausted"
        assert (await _family(database, tenant, actor, business, initial.search_id))["can_retry_family"] is False
        with pytest.raises(DBAPIError, match="REFERENCE_RADIUS_ALREADY_SEARCHED"):
            await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 2, 50)
    finally:
        await worker.close()


async def test_none_is_explicit_and_stale_business_identity_blocks_confirmation(admin, api, seeded, settings):
    google, worker, values, candidate, base, headers = await _own_setup(admin, api, seeded, settings)
    route = base + f"/reference-results/searches/{google.search}/own-business-review"
    try:
        await _commit_match(worker, google, values, {"status": "review", "place_ids": ["fake-place"]})
        payload = {"operation_id": str(uuid4()), "place_id": None}
        assert (await api.post(route, headers=headers, json=payload | {"place_id": "unknown"})).status_code == 409
        async with admin.begin() as conn:
            name = await conn.scalar(text("SELECT name FROM businesses WHERE id=:b"), {"b": google.business})
            await conn.execute(
                text("UPDATE businesses SET name='Changed own name' WHERE id=:b"), {"b": google.business}
            )
        assert (await api.post(route, headers=headers, json=payload)).status_code == 409
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE businesses SET name=:n WHERE id=:b"), {"n": name, "b": google.business})
        confirmed = await api.post(route, headers=headers, json=payload)
        assert confirmed.status_code == 200
        assert confirmed.json()["excluded_place_id"] is None
        async with worker.transaction(google.tenant, google.actor) as session:
            await session.scalar(
                text("SELECT reference_prepare_shortlist(:b,:s,:batch,:op,:ids)"),
                {"b": google.business, "s": google.search, "batch": values["batch"], "op": uuid4(), "ids": [candidate]},
            )
    finally:
        await worker.close()
