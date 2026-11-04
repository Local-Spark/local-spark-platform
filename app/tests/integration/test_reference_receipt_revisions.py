"""Authenticated late receipts adjust only their delta; no provider POST is used."""

import asyncio
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.reference_contacts_runs import record_contacts_cost, record_contacts_run
from app.services.reference_post_analysis_guard import record_feed_terminal_cost
from app.tests.integration.test_reference_contacts_runs import started_contacts as started_contacts
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_post_ledger import complete, fixture

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]


async def receipt(worker, c, amount, *, token=None):
    await record_feed_terminal_cost(
        worker, c.tenant, c.actor, c.business, c.parent_feed_effect, token or c.parent_feed_token, amount
    )


async def test_feed_revisions_keep_exact_history_and_concurrent_replay_is_once(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await receipt(worker, c, 7)
        await asyncio.gather(receipt(worker, c, 18), receipt(worker, c, 18))
        await receipt(worker, c, None)
        with pytest.raises(DBAPIError, match="RECEIPT_CONFLICT"):
            await receipt(worker, c, 17)
        with pytest.raises(DBAPIError, match="FENCE_INVALID"):
            await receipt(worker, c, 19, token=uuid4())
        async with admin.connect() as conn:
            rows = (
                await conn.execute(
                    text("""SELECT previous_usd_micros,reported_usd_micros,
              reserved_usd_micros,block_reason FROM reference_apify_cost_receipts ORDER BY observed_at""")
                )
            ).all()
            assert [tuple(row) for row in rows] == [(None, 7, 40, None), (7, 18, 40, None)]
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 18
            assert await conn.scalar(text("SELECT actual_usd_micros FROM reference_cost_reservations")) == 18
            assert (
                await conn.scalar(
                    text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='all'")
                )
                == 0
            )
            assert (
                await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.apify_cost_revised'"))
                == 1
            )
        async with worker.transaction(c.tenant, c.actor) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.scalar(text("SELECT count(*) FROM reference_apify_cost_receipts"))
        async with worker.transaction(c.tenant, c.actor) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.scalar(
                    text("SELECT reference_apply_apify_receipt(:b,:e,:r,20)"),
                    {"b": c.business, "e": c.parent_feed_effect, "r": uuid4()},
                )
    finally:
        await worker.close()


async def test_contacts_revisions_share_the_same_accounting_and_preserve_fences(admin, seeded, started_contacts):
    worker, c, token, run = started_contacts
    await record_contacts_run(worker, c, token, run)
    await record_contacts_cost(worker, c, token, run, 7)
    await asyncio.gather(
        record_contacts_cost(worker, c, token, run, 18), record_contacts_cost(worker, c, token, run, 18)
    )
    for bad in (replace(c, actor=seeded["viewer"]), replace(c, tenant=seeded["t2"], actor=seeded["a2"])):
        with pytest.raises(DBAPIError):
            await record_contacts_cost(worker, bad, token, run, 20)
    with pytest.raises(DBAPIError, match="FENCE_INVALID"):
        await record_contacts_cost(worker, c, uuid4(), run, 20)
    with pytest.raises(DBAPIError, match="RECEIPT_CONFLICT"):
        await record_contacts_cost(worker, c, token, run, 17)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 118
        assert await conn.scalar(text("SELECT reported_cost_usd_micros FROM reference_contacts_runs")) == 18
        assert await conn.scalar(text("SELECT count(*) FROM reference_apify_cost_receipts")) == 2
        assert (
            await conn.scalar(text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='all'"))
            == 100
        )


@pytest.mark.parametrize("late", [False, True])
async def test_over_reservation_is_recorded_and_blocks_new_admission(admin, api, seeded, settings, late):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        if late:
            await receipt(worker, c, 7)
        await receipt(worker, c, 41)
        await receipt(worker, c, 41)
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, c)
        async with admin.connect() as conn:
            pilot = (
                await conn.execute(
                    text("SELECT cap_usd_micros,reserved_usd_micros,active FROM reference_provider_pilots")
                )
            ).one()
            assert tuple(pilot) == (100, 41, False)
            assert await conn.scalar(text("SELECT actual_usd_micros FROM reference_cost_reservations")) == 41
            assert (
                await conn.scalar(
                    text("SELECT block_reason FROM reference_apify_cost_receipts WHERE reported_usd_micros=41")
                )
                == "reservation"
            )
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 0
    finally:
        await worker.close()


async def test_contacts_can_report_an_overrun_without_bypassing_the_guard(admin, started_contacts):
    worker, c, token, run = started_contacts
    await record_contacts_run(worker, c, token, run)
    await record_contacts_cost(worker, c, token, run, 41)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT reported_cost_usd_micros FROM reference_contacts_runs")) == 41
        assert await conn.scalar(text("SELECT active FROM reference_provider_pilots")) is False
        assert await conn.scalar(text("SELECT block_reason FROM reference_apify_cost_receipts")) == "reservation"


async def test_racing_new_claim_and_true_correction_never_hide_overcap_cost(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await receipt(worker, c, 10)
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE reference_provider_pilots SET cap_usd_micros=40"))
        spend = replace(c, reserved_usd_micros=30)
        corrected, claimed = await asyncio.gather(
            receipt(worker, c, 35), complete(worker, spend), return_exceptions=True
        )
        assert corrected is None
        accepted = isinstance(claimed, tuple)
        async with admin.connect() as conn:
            pilot = (
                await conn.execute(
                    text("SELECT cap_usd_micros,reserved_usd_micros,active FROM reference_provider_pilots")
                )
            ).one()
            assert tuple(pilot) == (40, 65 if accepted else 35, not accepted)
            assert (
                await conn.scalar(
                    text("SELECT actual_usd_micros FROM reference_cost_reservations WHERE provider='apify'")
                )
                == 35
            )
            assert await conn.scalar(
                text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='all'")
            ) == (30 if accepted else 0)
    finally:
        await worker.close()


async def test_reused_headroom_does_not_prevent_recording_a_true_overcap_receipt(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await receipt(worker, c, 10)
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE reference_provider_pilots SET cap_usd_micros=40"))
        await complete(worker, replace(c, reserved_usd_micros=30))
        await receipt(worker, c, 35)
        async with admin.connect() as conn:
            pilot = (
                await conn.execute(
                    text("SELECT cap_usd_micros,reserved_usd_micros,active FROM reference_provider_pilots")
                )
            ).one()
            assert tuple(pilot) == (40, 65, False)
            assert (
                await conn.scalar(
                    text("SELECT block_reason FROM reference_apify_cost_receipts WHERE reported_usd_micros=35")
                )
                == "pilot"
            )
            assert (
                await conn.scalar(
                    text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='all'")
                )
                == 30
            )
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, replace(c, effect=uuid4(), sample_mac="d" * 64, caption_mac="f" * 64))
    finally:
        await worker.close()


@pytest.mark.parametrize("limit", ["monthly", "provider_monthly", "search", "provider_search"])
async def test_true_cost_over_policy_is_saved_before_pilot_is_blocked(admin, api, seeded, settings, limit):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await receipt(worker, c, 7)
        values = {"search": 1000, "monthly": 1000, "search_provider": 1000, "monthly_provider": 1000}
        values[
            {
                "monthly": "monthly",
                "provider_monthly": "monthly_provider",
                "search": "search",
                "provider_search": "search_provider",
            }[limit]
        ] = 20
        await _policy(admin, **values)
        await receipt(worker, c, 35)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT actual_usd_micros FROM reference_cost_reservations")) == 35
            assert await conn.scalar(text("SELECT active FROM reference_provider_pilots")) is False
            assert (
                await conn.scalar(
                    text("SELECT block_reason FROM reference_apify_cost_receipts WHERE reported_usd_micros=35")
                )
                == limit
            )
    finally:
        await worker.close()


async def test_inconsistent_aggregate_rolls_back_revision_and_keeps_prior_receipt(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await receipt(worker, c, 7)
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE reference_cost_monthly SET committed_usd_micros=6 WHERE provider='apify'"))
        with pytest.raises(DBAPIError, match="MONTHLY_INCONSISTENT"):
            await receipt(worker, c, 18)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT actual_usd_micros FROM reference_cost_reservations")) == 7
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 7
            assert await conn.scalar(text("SELECT count(*) FROM reference_apify_cost_receipts")) == 1
    finally:
        await worker.close()
