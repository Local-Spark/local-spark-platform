import asyncio
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.services.reference_search_admission import admit_provider_search
from app.tests.integration.test_reference_jev_budget_guard import _google_started
from app.tests.integration.test_reference_places_budget_guard import _request
from app.tests.integration.test_reference_real_selection import _confirm, _result, _seed
from app.tests.integration.test_reference_search_admission import _KEY, _business

pytestmark = pytest.mark.integration


async def test_shared_read_and_selection_without_transfer_of_paid_effects(admin, seeded, database, api, settings):
    tenant, business, first, cycle = await _seed(admin, seeded)
    result, candidates, places = await _result(admin, tenant, business, first, cycle, 5, places=[uuid4(), uuid4()])
    hidden_result, hidden_candidates, hidden_places = await _result(
        admin, tenant, business, first, cycle, 20, published=False, places=[places[0], uuid4()]
    )
    async with admin.begin() as conn:
        for rid, candidate, handle in (
            (result, candidates[0], "public_profile"),
            (hidden_result, hidden_candidates[0], "private_profile"),
        ):
            await conn.execute(
                text("""INSERT INTO reference_provider_profile_options
                (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
                VALUES(:t,:b,:r,:c,:h,1,'apify','unverified')"""),
                {"t": tenant, "b": business, "r": rid, "c": candidate, "h": handle},
            )
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": tenant, "a": seeded["viewer"]},
        )
    second = seeded["viewer"]
    operation = uuid4()
    a = await _confirm(admin, tenant, business, first, operation, [result], [candidates[0]])
    async with database.transaction(tenant, second) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_real_published_results")) == 1
        assert await session.scalar(text("SELECT count(*) FROM reference_real_selected")) == 1
        assert (await session.execute(text("SELECT id FROM reference_provider_results"))).scalars().all() == [result]
        assert set(
            (await session.execute(text("SELECT id FROM reference_provider_result_candidates"))).scalars()
        ) == set(candidates)
        assert set((await session.execute(text("SELECT id FROM reference_provider_places"))).scalars()) == set(places)
        assert (
            await session.execute(text("SELECT instagram_handle FROM reference_provider_profile_options"))
        ).scalars().all() == ["public_profile"]
    b = await _confirm(admin, tenant, business, second, uuid4(), [result], [candidates[1]])
    assert a["locked_until"] == b["locked_until"]
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_OPERATION_CONFLICT"):
        await _confirm(admin, tenant, business, second, operation, [result], [candidates[0]])
    async with database.transaction(tenant, first) as session:
        assert await session.scalar(text("SELECT candidate_id FROM reference_real_selected")) == candidates[1]
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_real_published_results")) == 0
        assert await session.scalar(text("SELECT count(*) FROM reference_real_selected")) == 0
    async with admin.connect() as conn:
        assert not await conn.scalar(
            text(
                "SELECT has_function_privilege('meu_braco_direito_app', "
                "'public.reference_confirm_real_selection(uuid,uuid,uuid[],uuid[])', 'EXECUTE')"
            )
        )
        rows = (
            (await conn.execute(text("SELECT actor_id FROM reference_real_selection_operations ORDER BY created_at")))
            .scalars()
            .all()
        )
        assert rows == [first, second]
        assert (
            await conn.scalar(
                text("SELECT actor_id FROM reference_provider_searches WHERE business_id=:b"), {"b": business}
            )
            == first
        )
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, second) as session:
            await session.execute(
                text("SELECT reference_confirm_real_selection(:b,:o,:r,:c)"),
                {"b": business, "o": uuid4(), "r": [result], "c": [candidates[0]]},
            )


async def test_other_owner_cannot_take_paid_effect(admin, seeded, api, settings):
    second = seeded["viewer"]
    first = seeded["a1"]
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": seeded["t1"], "a": second},
        )
    parent, original_guard, worker = await _google_started(admin, api, seeded, settings)
    try:
        impostor = DatabasePlacesBudgetGuard(worker, replace(parent, actor=second))
        with pytest.raises(DBAPIError):
            await impostor.claim(parent.effect, _request())
        async with admin.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT actor_id,state FROM reference_provider_effects WHERE id=:e"), {"e": parent.effect}
                )
            ).one()
            assert row.actor_id == first and row.state == "running"
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM reference_cost_reservations WHERE effect_id=:e"), {"e": parent.effect}
                )
                == 1
            )
    finally:
        await worker.close()


async def test_distinct_owners_cannot_admit_same_radius(admin, seeded, database, api, settings):
    second = seeded["viewer"]
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": seeded["t1"], "a": second},
        )
    t2, actor2, business2, _, _ = await _business(admin, api, seeded, settings)
    outcomes = await asyncio.gather(
        *[
            admit_provider_search(database, _KEY, "test-v1", t2, business2, owner, uuid4(), 1, 5)
            for owner in (actor2, second)
        ],
        return_exceptions=True,
    )
    assert sum(not isinstance(outcome, Exception) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, DBAPIError) for outcome in outcomes) == 1
    async with admin.connect() as conn:
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM reference_provider_searches WHERE business_id=:b"), {"b": business2}
            )
            == 1
        )
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM reference_provider_effects WHERE business_id=:b"), {"b": business2}
            )
            == 0
        )
