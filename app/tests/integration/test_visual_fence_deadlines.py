"""Lock waits cannot extend a visual lease or its creation window."""

import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_cost_ledger import VisualCostError
from app.services.visual_provider_execution import VisualSubmissionClaims
from app.tests.integration.test_visual_attempts import preview
from app.tests.integration.test_visual_cost_ledger import _business
from app.tests.integration.test_visual_provider_submission import _setup

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "effect,lock",
    [("reserve", "preview"), ("reserve", "ledger"), ("reserve", "global"), ("claim", "preview"), ("claim", "ledger")],
)
@pytest.mark.parametrize("deadline", ["dispatch_lease_until", "expires_at"])
async def test_visual_deadline_expiring_while_waiting_for_lock_rejects_effect(
    admin, seeded, settings, monkeypatch, effect, lock, deadline
):
    if effect == "claim":
        cfg, database, identity, prepared, attempt = await _setup(admin, seeded, settings)
        tenant, actor, item = identity.tenant, identity.actor, identity.preview

        async def execute():
            return await VisualSubmissionClaims(database).claim(
                identity, attempt.reservation.id, prepared.request.model, prepared.context.proposal_id
            )

    else:
        tenant, actor = seeded["t1"], seeded["a1"]
        business = await _business(admin, tenant)
        item = await preview(admin, tenant, business, actor)
        cfg = settings.model_copy(
            update={"visual_ai_monthly_budget_usd_micros": 100, "visual_ai_global_monthly_budget_usd_micros": 100}
        )
        database = Database(cfg, correlator=True)

        async def execute():
            return await VisualAttemptService(cfg, database).reserve(
                tenant,
                business,
                actor,
                item,
                1,
                uuid4(),
                "openai" if lock == "global" else "fake",
                "synthetic",
                "a" * 64,
                70,
            )

    entered = asyncio.Event()
    transaction_started = None
    original_transaction = database.transaction

    @asynccontextmanager
    async def observed_transaction(*args):
        nonlocal transaction_started
        async with original_transaction(*args) as session:
            transaction_started = await session.scalar(text("SELECT transaction_timestamp()"))
            entered.set()
            yield session

    monkeypatch.setattr(database, "transaction", observed_transaction)
    task = None
    try:
        # Commit this update before taking the test's blocking lock. In the
        # ledger case the worker must be able to acquire its own preview lock.
        async with admin.begin() as connection:
            if lock == "global":
                await connection.execute(
                    text("""INSERT INTO visual_global_monthly_budget(month)
                      VALUES(date_trunc('month',clock_timestamp() AT TIME ZONE 'UTC')::date)""")
                )
            expiry = await connection.scalar(
                text(f"""UPDATE media_previews SET {deadline}=clock_timestamp()+interval '0.25 second'
                  WHERE id=:id RETURNING {deadline}"""),
                {"id": item},
            )
        async with admin.begin() as holder:
            if lock == "preview":
                await holder.execute(text("SELECT id FROM media_previews WHERE id=:id FOR UPDATE"), {"id": item})
            elif lock == "ledger":
                await holder.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 31))"), {"key": str(tenant)}
                )
            else:
                await holder.execute(text("SELECT month FROM visual_global_monthly_budget FOR UPDATE"))
            task = asyncio.create_task(execute())
            await asyncio.wait_for(entered.wait(), 5)
            assert transaction_started < expiry
            await asyncio.sleep(0.3)
            assert not task.done()
            assert await holder.scalar(text("SELECT clock_timestamp()>:expiry"), {"expiry": expiry})
        if effect == "claim":
            assert await asyncio.wait_for(task, 5) is False
        else:
            with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
                await asyncio.wait_for(task, 5)
        async with admin.connect() as connection:
            count = await connection.scalar(
                text("SELECT count(*) FROM visual_ai_attempts WHERE preview_id=:id"), {"id": item}
            )
            assert count == int(effect == "claim")
            states = (
                (
                    await connection.execute(
                        text("""SELECT state FROM visual_cost_reservations WHERE tenant_id=:tenant"""),
                        {"tenant": tenant},
                    )
                )
                .scalars()
                .all()
            )
            assert states == (["submitted"] if effect == "claim" else [])
            if lock == "global":
                assert (
                    await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 0
                )
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 0
            )
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await database.close()
