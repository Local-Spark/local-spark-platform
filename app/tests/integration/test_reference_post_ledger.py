import asyncio
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_reference_post_analysis import JevReferencePostAnalysis
from app.services.reference_post_analysis_guard import DatabasePostAnalysisGuard, PostGuardContext, load_post_analysis
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.unit.test_jev_reference_post_analysis import response_for

pytestmark = pytest.mark.integration


async def fixture(admin, api, seeded, settings):
    from app.tests.integration.test_reference_learning import canonical_feed_fixture

    worker, window, parent, token, run = await canonical_feed_fixture(admin, api, seeded, settings)
    jev_tariff = "post-test-" + uuid4().hex
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs(version,provider,field_mask,
          minimum_reserved_usd_micros,active) VALUES(:v,'jev','jev-model:jev-1.14.0',1,true)"""),
            {"v": jev_tariff},
        )
    context = PostGuardContext(
        window.tenant,
        window.business,
        window.actor,
        window.window,
        window.reference,
        window.association_version,
        parent.effect,
        token,
        uuid4(),
        "b" * 64,
        parent.pilot,
        parent.key,
        "key-v1",
        jev_tariff,
        "cred-v1",
        5,
        caption_mac="e" * 64,
    )
    return worker, context


def model(guard):
    return JevReferencePostAnalysis(
        SecretStr("fake"),
        "jev-1.14.0",
        guard,
        enabled=True,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=response_for(r))),
    )


async def complete(worker, c):
    guard = DatabasePostAnalysisGuard(worker, c)
    result = await model(guard).analyze(caption="fixture caption", image=None, operation_id=c.effect)
    await guard.record(result)
    return guard, result


async def test_claim_record_replay_recovery_never_persists_inputs(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        assert await load_post_analysis(worker, c.tenant, c.actor, c.business, c.window, c.sample_mac) is None
        guard, result = await complete(worker, c)
        await guard.record(result)
        saved = await load_post_analysis(worker, c.tenant, c.actor, c.business, c.window, c.sample_mac)
        assert dict(saved.choices) == dict(result.choices)
        await guard.uncertain()  # Completed result is never changed by a late failure callback.
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await model(DatabasePostAnalysisGuard(worker, c)).analyze(
                caption="fixture caption", image=None, operation_id=c.effect
            )
        async with admin.connect() as conn:
            row = (await conn.execute(text("SELECT * FROM reference_post_effects"))).mappings().one()
            assert row["state"] == "completed" and row["input_tokens"] == 123
            assert "fixture caption" not in json.dumps(dict(row), default=str)
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 45
            r = (
                await conn.execute(
                    text("SELECT state,actual_usd_micros FROM reference_cost_reservations WHERE provider='jev'")
                )
            ).one()
            assert tuple(r) == ("claimed", None)
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.post_patterns_recorded'")
                )
                == 1
            )
        async with worker.transaction(c.tenant, c.actor) as sess:
            with pytest.raises(DBAPIError, match="permission denied"):
                await sess.execute(text("SELECT * FROM reference_post_effects"))
    finally:
        await worker.close()


async def test_fences_invalid_patterns_and_revoked_selection_keep_reservation(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        guard = DatabasePostAnalysisGuard(worker, c)
        result = await model(guard).analyze(caption="fixture caption", image=None, operation_id=c.effect)
        with pytest.raises(DBAPIError, match="RESULT_INVALID"):
            await guard.record(replace(result, choices=(("tone", "private caption"),)))
        async with worker.transaction(c.tenant, c.actor) as sess:
            with pytest.raises(DBAPIError, match="FENCE_INVALID"):
                await sess.execute(
                    text("SELECT reference_post_uncertain(:b,:e,:token)"),
                    {"b": c.business, "e": c.effect, "token": uuid4()},
                )
        await guard.uncertain()
        await guard.uncertain()
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE owner_references SET removed_at=now() WHERE id=:id"), {"id": c.reference})
        with pytest.raises(DBAPIError, match="REFERENCE_INVALID"):
            await guard.record(result)
        with pytest.raises(DBAPIError, match="REFERENCE_INVALID"):
            await load_post_analysis(worker, c.tenant, c.actor, c.business, c.window, c.sample_mac)
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT state FROM reference_cost_reservations WHERE provider='jev'"))
                == "uncertain"
            )
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 45
    finally:
        await worker.close()


async def test_concurrent_claims_share_all_provider_cap_and_monthly_budget(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE reference_provider_pilots SET cap_usd_micros=45"))
        other = replace(c, effect=uuid4(), sample_mac="c" * 64, caption_mac="f" * 64)
        outcomes = await asyncio.gather(complete(worker, c), complete(worker, other), return_exceptions=True)
        assert sum(isinstance(v, tuple) for v in outcomes) == 1
        assert sum(isinstance(v, Exception) for v in outcomes) == 1
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 45
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 1
        await _policy(admin, search=1000, monthly=44, search_provider=1000, monthly_provider=1000)
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE reference_provider_pilots SET cap_usd_micros=100"))
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, replace(c, effect=uuid4(), sample_mac="d" * 64))
    finally:
        await worker.close()


@pytest.mark.parametrize("change", ["token", "version", "reference", "actor", "tenant", "tariff", "window"])
async def test_wrong_parent_or_authority_never_spends(admin, api, seeded, settings, change):
    worker, c = await fixture(admin, api, seeded, settings)
    modifications = {
        "token": {"parent_feed_token": uuid4()},
        "version": {"association_version": 2},
        "reference": {"reference": uuid4()},
        "actor": {"actor": seeded["viewer"]},
        "tenant": {"tenant": seeded["t2"], "actor": seeded["a2"]},
        "tariff": {"tariff_version": "missing"},
        "window": {"window": uuid4()},
    }
    try:
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, replace(c, **modifications[change]))
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 40
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 0
    finally:
        await worker.close()


@pytest.mark.parametrize("limit", ["window_total", "window_jev", "monthly_jev"])
async def test_independent_limits_include_held_costs(admin, api, seeded, settings, limit):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await _policy(
            admin,
            search=44 if limit == "window_total" else 1000,
            monthly=1000,
            search_provider=4 if limit == "window_jev" else 1000,
            monthly_provider=4 if limit == "monthly_jev" else 1000,
        )
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, c)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 40
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 0
    finally:
        await worker.close()


async def test_conflicting_completed_result_and_input_cannot_replace_saved_patterns(admin, api, seeded, settings):
    worker, c = await fixture(admin, api, seeded, settings)
    try:
        guard, result = await complete(worker, c)
        with pytest.raises(DBAPIError, match="RESULT_CONFLICT"):
            await guard.record(replace(result, choices=(("tone", "professional"),)))
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await model(DatabasePostAnalysisGuard(worker, c)).analyze(
                caption="changed fixture", image=None, operation_id=c.effect
            )
        saved = await load_post_analysis(worker, c.tenant, c.actor, c.business, c.window, c.sample_mac)
        assert dict(saved.choices) == dict(result.choices)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 45
    finally:
        await worker.close()


async def test_downgrade_refuses_to_destroy_costs_and_results(admin, api, seeded, settings):
    import importlib.util
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    worker, c = await fixture(admin, api, seeded, settings)
    try:
        await complete(worker, c)
        path = Path(__file__).resolve().parents[3] / "migrations/versions/0109_reference_post_analysis.py"
        spec = importlib.util.spec_from_file_location("migration_for_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def downgrade(conn):
            with Operations.context(MigrationContext.configure(conn)):
                module.downgrade()

        with pytest.raises(DBAPIError, match="FORWARD_RECOVERY"):
            async with admin.begin() as conn:
                await conn.run_sync(downgrade)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 1
    finally:
        await worker.close()


@pytest.mark.parametrize("actual", [None, 0, 7, 40])
async def test_terminal_feed_cost_reconciles_once_without_guessing_zero(admin, api, seeded, settings, actual):
    from app.services.reference_post_analysis_guard import record_feed_terminal_cost

    worker, c = await fixture(admin, api, seeded, settings)

    async def receipt(amount, token=None):
        await record_feed_terminal_cost(
            worker, c.tenant, c.actor, c.business, c.parent_feed_effect, token or c.parent_feed_token, amount
        )

    try:
        with pytest.raises(DBAPIError, match="FENCE_INVALID"):
            await receipt(actual, uuid4())
        await receipt(actual)
        await receipt(actual)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == (
                40 if actual is None else actual
            )
            r = (
                await conn.execute(
                    text("SELECT state,actual_usd_micros FROM reference_cost_reservations WHERE provider='apify'")
                )
            ).one()
            assert tuple(r) == (("uncertain", None) if actual is None else ("completed", actual))
            assert (
                await conn.scalar(
                    text(
                        "SELECT count(*) FROM audit_events WHERE action IN "
                        "('reference.feed_cost_uncertain','reference.feed_cost_reported')"
                    )
                )
                == 1
            )
        if actual is not None:
            await receipt(None)
            if actual:
                with pytest.raises(DBAPIError, match="RECEIPT_CONFLICT"):
                    await receipt(actual - 1)
            else:
                await receipt(1)
        else:
            await receipt(7)
            async with admin.connect() as conn:
                assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 7
        # Completing Apify cost does not close the feed, so Jev can claim the same window.
        await complete(worker, c)
    finally:
        await worker.close()


async def test_bad_feed_receipt_and_counter_inconsistency_roll_back(admin, api, seeded, settings):
    from app.services.reference_post_analysis_guard import record_feed_terminal_cost

    worker, c = await fixture(admin, api, seeded, settings)

    async def receipt(amount):
        await record_feed_terminal_cost(
            worker, c.tenant, c.actor, c.business, c.parent_feed_effect, c.parent_feed_token, amount
        )

    try:
        for amount in (-1, 1_000_000_000_001):
            with pytest.raises(DBAPIError, match="RECEIPT_INVALID"):
                await receipt(amount)
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE reference_cost_monthly SET outstanding_usd_micros=0 WHERE provider='apify'")
            )
        with pytest.raises(DBAPIError, match="MONTHLY_INCONSISTENT"):
            await receipt(7)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 40
            assert await conn.scalar(text("SELECT reported_cost_usd_micros FROM reference_feed_resources")) is None
    finally:
        await worker.close()


async def test_uncertain_caption_anchor_survives_image_list_changes(admin, api, seeded, settings):
    from app.services.reference_post_analysis_guard import caption_claimed, load_post_sample

    worker, c = await fixture(admin, api, seeded, settings)
    try:
        assert not await caption_claimed(worker, c.tenant, c.actor, c.business, c.window, c.caption_mac)
        guard = DatabasePostAnalysisGuard(worker, c)
        await model(guard).analyze(caption="fixture caption", image=None, operation_id=c.effect)
        await guard.uncertain()
        assert await caption_claimed(worker, c.tenant, c.actor, c.business, c.window, c.caption_mac)
        sample = await load_post_sample(worker, c.tenant, c.actor, c.business, c.window, c.sample_mac)
        assert sample.state == "uncertain" and sample.includes_caption and sample.result is None
        with pytest.raises(Exception, match="BUDGET_UNAVAILABLE"):
            await complete(worker, replace(c, effect=uuid4(), sample_mac="f" * 64))
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 1
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 45
    finally:
        await worker.close()


async def test_caption_reader_recovers_finished_pattern_by_anchor_after_images_change(admin, api, seeded, settings):
    from app.services.reference_post_analysis_guard import load_caption_sample

    worker, c = await fixture(admin, api, seeded, settings)
    try:
        assert await load_caption_sample(worker, c.tenant, c.actor, c.business, c.window, c.caption_mac) is None
        guard, result = await complete(worker, c)
        saved = await load_caption_sample(worker, c.tenant, c.actor, c.business, c.window, c.caption_mac)
        assert saved.state == "completed" and saved.includes_caption
        assert dict(saved.result.choices) == dict(result.choices)
    finally:
        await worker.close()
