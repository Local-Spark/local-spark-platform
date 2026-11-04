"""A shared search cannot spend the per-search allowance once per owner."""

from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot, _request

pytestmark = pytest.mark.integration


async def _setup(admin, api, settings, seeded):
    pilot, tariff = await _pilot(admin, cap=1000)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff, amount=60)
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:t,:a,'owner')"),
            {"t": context.tenant, "a": seeded["a2"]},
        )
    return context


async def _prior(admin, ctx, actor, *, provider="google", amount=50, actual=None):
    async with admin.begin() as conn:
        policy = await conn.scalar(text("SELECT policy_id FROM reference_cost_policy_head"))
        await conn.execute(
            text("""INSERT INTO reference_cost_reservations
          (id,tenant_id,business_id,actor_id,provider_search_id,pilot_id,effect_id,request_hash,
           provider,month,reserved_usd_micros,actual_usd_micros,state,policy_id)
          VALUES(:id,:tenant,:business,:actor,:search,:pilot,:effect,:hash,:provider,
            date_trunc('month',now() AT TIME ZONE 'UTC')::date,:amount,:actual,:state,:policy)"""),
            {
                "id": uuid4(),
                "tenant": ctx.tenant,
                "business": ctx.business,
                "actor": actor,
                "search": ctx.search,
                "pilot": ctx.pilot,
                "effect": uuid4(),
                "hash": "a" * 64,
                "provider": provider,
                "amount": amount,
                "actual": actual,
                "state": "completed" if actual is not None else "uncertain",
                "policy": policy,
            },
        )


@pytest.mark.parametrize(
    "provider,total,per_provider,error",
    [
        ("apify", 100, 1000, "REFERENCE_SEARCH_BUDGET_EXCEEDED"),
        ("google", 1000, 100, "REFERENCE_SEARCH_PROVIDER_BUDGET_EXCEEDED"),
    ],
)
async def test_other_owner_reservation_counts_before_a_provider_request(
    admin, api, settings, seeded, provider, total, per_provider, error
):
    ctx = await _setup(admin, api, settings, seeded)
    await _policy(admin, search=total, monthly=1000, search_provider=per_provider, monthly_provider=1000)
    await _prior(admin, ctx, seeded["a2"], provider=provider)
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError, match=error):
            await DatabasePlacesBudgetGuard(worker, ctx).claim(ctx.effect, _request())
        async with worker.transaction(ctx.tenant, ctx.actor) as session:
            # The sum does not grant access to another executor's ledger rows.
            assert await session.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT state FROM reference_provider_effects WHERE id=:id"), {"id": ctx.effect})
                == "pending"
            )
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()


async def test_completed_actual_cost_and_exact_boundary_are_counted(admin, api, settings, seeded):
    ctx = await _setup(admin, api, settings, seeded)
    await _policy(admin, search=100, monthly=1000, search_provider=100, monthly_provider=1000)
    await _prior(admin, ctx, seeded["a2"], amount=95, actual=40)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, ctx).claim(ctx.effect, _request()) is True
        assert await DatabasePlacesBudgetGuard(worker, ctx).claim(ctx.effect, _request()) is False
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 2
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()


@pytest.mark.parametrize("scope", ["other_tenant", "other_search"])
async def test_other_search_costs_do_not_consume_this_search(admin, api, settings, seeded, scope):
    ctx = await _setup(admin, api, settings, seeded)
    if scope == "other_tenant":
        other = await _intent(admin, api, settings, seeded["t2"], seeded["a2"], ctx.pilot, ctx.tariff_version)
    else:
        other = replace(ctx, search=uuid4())
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO reference_provider_searches
                  (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state)
                  VALUES(:id,:tenant,:business,:actor,:operation,1,:mac,'pending')"""),
                {
                    "id": other.search,
                    "tenant": ctx.tenant,
                    "business": ctx.business,
                    "actor": ctx.actor,
                    "operation": uuid4(),
                    "mac": "b" * 64,
                },
            )
    await _policy(admin, search=60, monthly=1000, search_provider=60, monthly_provider=1000)
    await _prior(admin, other, seeded["a2"], amount=60)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, ctx).claim(ctx.effect, _request()) is True
        async with worker.transaction(ctx.tenant, ctx.actor) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.execute(
                    text("SELECT * FROM reference_search_cost_usage(:business,:search,'google')"),
                    {"business": ctx.business, "search": ctx.search},
                )
    finally:
        await worker.close()
