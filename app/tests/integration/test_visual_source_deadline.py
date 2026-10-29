"""A source-validity window cannot be extended by waiting for claim locks."""

import asyncio
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text

from app.services.visual_provider_execution import VisualSubmissionClaims
from app.tests.integration.test_visual_provider_submission import _setup

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("lock", ["commercial", "ledger"])
async def test_source_deadline_after_owner_proof_expires_during_claim_lock_wait(
    admin, seeded, settings, monkeypatch, lock
):
    cfg, worker, identity, prepared, attempt = await _setup(admin, seeded, settings)
    entered = asyncio.Event()
    original = worker.transaction

    @asynccontextmanager
    async def observed(*args):
        async with original(*args) as session:
            entered.set()
            yield session

    monkeypatch.setattr(worker, "transaction", observed)
    task = None
    try:
        async with admin.begin() as connection:
            # This timestamp represents a source deadline obtained by the owner
            # proof. The persisted preview and lease remain valid for minutes.
            admitted_at, deadline = (
                await connection.execute(text("SELECT clock_timestamp(),clock_timestamp()+interval '0.3 second'"))
            ).one()
            if lock == "commercial":
                from app.services.billing import lock_commercial_change

                await lock_commercial_change(connection, identity.tenant)
            else:
                await connection.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key,31))"),
                    {"key": str(identity.tenant)},
                )
            task = asyncio.create_task(
                VisualSubmissionClaims(worker).claim(
                    identity,
                    attempt.reservation.id,
                    prepared.request.model,
                    prepared.context.proposal_id,
                    admitted_at=admitted_at,
                    source_valid_until=deadline,
                )
            )
            await asyncio.wait_for(entered.wait(), 5)
            await asyncio.sleep(0.35)
            assert not task.done()
            assert await connection.scalar(text("SELECT clock_timestamp()>:deadline"), {"deadline": deadline})
        assert await asyncio.wait_for(task, 5) is False
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "submitted"
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 0
            )
            assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await worker.close()
