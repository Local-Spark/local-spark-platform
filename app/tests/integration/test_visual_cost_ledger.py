"""Atomic accounting uses the dedicated _test database, never a provider."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.session import Database
from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger

pytestmark = pytest.mark.integration


async def _business(admin, tenant):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
    return business


async def test_visual_cost_lifecycle_concurrency_and_tenant_rls(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    other_tenant, other_actor = seeded["t2"], seeded["a2"]
    business, other_business = await _business(admin, tenant), await _business(admin, other_tenant)
    configured = settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    worker_db, app_db = Database(configured, correlator=True), Database(configured)
    ledger = VisualCostLedger(configured, worker_db)

    async def reserve(op, amount=70):
        return await ledger.reserve(tenant, business, actor, op, "fake", "test", "a" * 64, amount)

    try:
        operation = uuid4()
        pair = await asyncio.gather(reserve(operation), reserve(operation))
        assert sorted(x.created for x in pair) == [False, True]
        assert pair[0].id == pair[1].id
        with pytest.raises(VisualCostError, match="OPERATION_CONFLICT"):
            await reserve(operation, 60)
        with pytest.raises(VisualCostError, match="BUDGET_EXCEEDED"):
            await reserve(uuid4(), 31)
        unknown = await ledger.finish(tenant, actor, pair[0].id, actual_usd_micros=None)
        assert unknown.state == "uncertain"
        assert (await ledger.finish(tenant, actor, pair[0].id, actual_usd_micros=None)).state == "uncertain"
        with pytest.raises(VisualCostError, match="BUDGET_EXCEEDED"):
            await reserve(uuid4(), 31)
        done = await ledger.finish(tenant, actor, pair[0].id, actual_usd_micros=20)
        assert done.state == "completed" and done.actual_usd_micros == 20
        assert (await ledger.finish(tenant, actor, pair[0].id, actual_usd_micros=20)).state == "completed"
        with pytest.raises(VisualCostError, match="OUTCOME_CONFLICT"):
            await ledger.finish(tenant, actor, pair[0].id, actual_usd_micros=None)
        second = await reserve(uuid4(), 80)
        await ledger.finish(tenant, actor, second.id, actual_usd_micros=95)
        with pytest.raises(VisualCostError, match="BUDGET_EXCEEDED"):
            await reserve(uuid4(), 1)
        other = await ledger.reserve(other_tenant, other_business, other_actor, operation, "fake", "test", "a" * 64, 90)
        assert other.created and other.id != pair[0].id
        with pytest.raises(VisualCostError, match="NOT_FOUND"):
            await ledger.finish(other_tenant, other_actor, pair[0].id, actual_usd_micros=None)
        async with worker_db.transaction(other_tenant, other_actor) as session:
            assert await session.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 1
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='over_reservation'")) == 1
            )
        with pytest.raises(ProgrammingError):
            async with app_db.transaction(tenant, actor) as session:
                await session.execute(text("SELECT * FROM visual_cost_reservations"))
    finally:
        await worker_db.close()
        await app_db.close()


async def test_budget_race_validation_and_disabled_default(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    worker_db = Database(settings, correlator=True)
    off = VisualCostLedger(settings, worker_db)
    ledger = VisualCostLedger(settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100}), worker_db)

    async def reserve(op, **overrides):
        params = {
            "tenant": tenant,
            "business": business,
            "actor": actor,
            "operation": op,
            "provider": "fake",
            "model": "test",
            "request_hash": "a" * 64,
            "reserved_usd_micros": 60,
        }
        params.update(overrides)
        return await ledger.reserve(**params)

    try:
        with pytest.raises(VisualCostError, match="DISABLED"):
            await off.reserve(tenant, business, actor, uuid4(), "fake", "test", "a" * 64, 10)
        for invalid in (
            {"provider": ""},
            {"model": ""},
            {"request_hash": "bad"},
            {"request_hash": "g" * 64},
            {"reserved_usd_micros": 0},
        ):
            with pytest.raises(VisualCostError, match="INVALID_RESERVATION"):
                await reserve(uuid4(), **invalid)
        with pytest.raises(VisualCostError, match="INVALID_ACTUAL_COST"):
            await ledger.finish(tenant, actor, uuid4(), actual_usd_micros=-1)
        outcomes = await asyncio.gather(reserve(uuid4()), reserve(uuid4()), return_exceptions=True)
        assert sum(not isinstance(x, Exception) for x in outcomes) == 1
        assert sum(isinstance(x, VisualCostError) and "EXCEEDED" in str(x) for x in outcomes) == 1
    finally:
        await worker_db.close()
