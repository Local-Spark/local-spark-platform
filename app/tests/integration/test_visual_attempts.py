"""Atomic fenced reservations against PostgreSQL and restricted worker role."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_cost_ledger import VisualCostError
from app.tests.integration.test_visual_cost_ledger import _business

pytestmark = pytest.mark.integration


async def preview(admin, tenant, business, actor):
    identifier = uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO media_previews
              (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,
               render_key,context_version,fact_ids,state,dispatch_fence,dispatch_lease_until,expires_at)
              VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:render,0,'[]'::jsonb,
                'rendering',1,now()+interval '3 minutes',now()+interval '1 hour')"""),
            {
                "id": identifier,
                "tenant": tenant,
                "business": business,
                "proposal": uuid4(),
                "actor": actor,
                "operation": uuid4(),
                "hash": "c" * 64,
                "render": identifier.hex * 2,
            },
        )
    return identifier


async def test_same_preview_concurrent_replay_and_fence_are_safe(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    item, operation = await preview(admin, tenant, business, actor), uuid4()
    cfg = settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    database = Database(cfg, correlator=True)
    service = VisualAttemptService(cfg, database)
    args = (tenant, business, actor, item, 1, operation, "fake", "synthetic", "a" * 64, 70)
    try:
        one, two = await asyncio.gather(service.reserve(*args), service.reserve(*args))
        assert sorted((one.created, two.created)) == [False, True]
        assert one.reservation.id == two.reservation.id
        with pytest.raises(VisualCostError, match="VISUAL_ATTEMPT_CONFLICT"):
            await service.reserve(*(args[:5] + (uuid4(),) + args[6:]))
        with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
            await service.reserve(*(args[:4] + (2,) + args[5:]))
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_ai_attempts WHERE tenant_id=:t"), {"t": tenant})
                == 1
            )
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant}
                )
                == 1
            )
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
    finally:
        await database.close()


async def test_two_previews_cannot_both_spend_last_budget(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    first, second = await preview(admin, tenant, business, actor), await preview(admin, tenant, business, actor)
    cfg = settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    database = Database(cfg, correlator=True)
    service = VisualAttemptService(cfg, database)
    try:

        async def reserve(item):
            return await service.reserve(tenant, business, actor, item, 1, uuid4(), "fake", "synthetic", "a" * 64, 70)

        results = await asyncio.gather(reserve(first), reserve(second), return_exceptions=True)
        assert sum(not isinstance(value, Exception) for value in results) == 1
        error = next(value for value in results if isinstance(value, Exception))
        assert isinstance(error, VisualCostError) and str(error) == "VISUAL_BUDGET_EXCEEDED"
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_ai_attempts WHERE tenant_id=:t"), {"t": tenant})
                == 1
            )
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant}
                )
                == 1
            )
    finally:
        await database.close()
