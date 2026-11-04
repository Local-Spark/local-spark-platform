"""Inactive feed claim prototype shares the same fenced pilot ledger."""

import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.apify_instagram_feed import ApifyInstagramFeed
from app.db.session import Database
from app.services.reference_feed_budget_guard import DatabaseFeedBudgetGuard, FeedGuardContext, FeedGuardError
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot, _request

pytestmark = pytest.mark.integration

_CLAIM = text("""SELECT public.reference_feed_claim(:business,:effect,:event,:window,:pilot,:mac,
  :key,:tariff,:credential,:build,:amount)""")


async def _fixture(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin, cap=100)
    parent = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    reference, window = uuid4(), uuid4()
    feed_tariff = "feed-test-" + uuid4().hex
    async with admin.begin() as connection:
        allowed = await connection.scalar(
            text("""SELECT has_function_privilege('meu_braco_direito_correlator',
          'public.reference_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint)','EXECUTE')""")
        )
        assert allowed is False
        await connection.execute(
            text("""GRANT EXECUTE ON FUNCTION
          public.reference_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint),
          public.reference_feed_uncertain(uuid,uuid) TO meu_braco_direito_correlator""")
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:v,'apify','apify-instagram-feed:1.2.3',1,true)"""),
            {"v": feed_tariff},
        )
        await connection.execute(
            text("""INSERT INTO owner_references(id,tenant_id,business_id,actor_id,instagram_handle)
          VALUES(:ref,:tenant,:business,:actor,'fixture_profile')"""),
            {"ref": reference, "tenant": parent.tenant, "business": parent.business, "actor": parent.actor},
        )
        await connection.execute(
            text("""INSERT INTO reference_feed_windows
          (id,tenant_id,business_id,actor_id,owner_reference_id,association_version)
          VALUES(:window,:tenant,:business,:actor,:ref,1)"""),
            {
                "window": window,
                "tenant": parent.tenant,
                "business": parent.business,
                "actor": parent.actor,
                "ref": reference,
            },
        )
    return parent, window, reference, feed_tariff


async def _effect(admin, parent, window, tariff, *, amount=40, effect=None, event=None, mac="a" * 64):
    effect, event = effect or uuid4(), event or uuid4()
    values = {
        "business": parent.business,
        "effect": effect,
        "event": event,
        "window": window,
        "pilot": parent.pilot,
        "mac": mac,
        "key": "test-key",
        "tariff": tariff,
        "credential": "test-credential",
        "build": "1.2.3",
        "amount": amount,
    }
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:event,:tenant,'reference.provider_effect_requested',jsonb_build_object(
            'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
            'operation_id',CAST(:effect AS text)))"""),
            {
                **values,
                "tenant": parent.tenant,
                "business": str(parent.business),
                "actor": str(parent.actor),
                "effect": str(effect),
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_feed_effects
          (id,tenant_id,business_id,actor_id,window_id,pilot_id,event_id,request_mac,key_version,tariff_version,
           credential_version,actor_build,reserved_usd_micros,state)
          VALUES(:effect,:tenant,:business,:actor,:window,:pilot,:event,:mac,:key,:tariff,:credential,:build,:amount,'pending')"""),
            {**values, "tenant": parent.tenant, "actor": parent.actor},
        )
    return values


async def _claim(worker, parent, values):
    async with worker.transaction(parent.tenant, parent.actor) as session:
        return await session.scalar(_CLAIM, values)


async def _revoke(admin):
    async with admin.begin() as connection:
        await connection.execute(
            text("""REVOKE EXECUTE ON FUNCTION
          public.reference_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint)
          FROM meu_braco_direito_correlator""")
        )


async def test_feed_and_google_share_cap_and_fenced_uncertainty(admin, api, seeded, settings):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    values = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, parent).claim(parent.effect, _request()) is True
        first = await _claim(worker, parent, values)
        assert first["created"] is True
        assert (await _claim(worker, parent, values))["created"] is False
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_FENCE_INVALID"):
            async with worker.transaction(parent.tenant, parent.actor) as session:
                await session.execute(
                    text("SELECT public.reference_feed_uncertain(:effect,:token)"),
                    {"effect": values["effect"], "token": uuid4()},
                )
        async with worker.transaction(parent.tenant, parent.actor) as session:
            await session.execute(
                text("SELECT public.reference_feed_uncertain(:effect,:token)"),
                {"effect": values["effect"], "token": UUID(first["executor_token"])},
            )
        assert (await _claim(worker, parent, values))["state"] == "uncertain"
        async with admin.connect() as connection:
            reservation = await connection.scalar(
                text("SELECT id FROM reference_cost_reservations WHERE effect_id=:id"), {"id": values["effect"]}
            )
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE id=:id"), {"id": reservation}
                )
                == "uncertain"
            )
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_FENCE_REQUIRED"):
            async with worker.transaction(parent.tenant, parent.actor) as session:
                await session.scalar(text("SELECT public.reference_cost_finish(:id,NULL)"), {"id": reservation})
    finally:
        await worker.close()
        await _revoke(admin)


async def test_feed_concurrent_claims_cannot_exceed_shared_cap(admin, api, seeded, settings):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    first, second = await _effect(admin, parent, window, tariff), await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, parent).claim(parent.effect, _request()) is True
        outcomes = await asyncio.gather(
            _claim(worker, parent, first), _claim(worker, parent, second), return_exceptions=True
        )
        assert sum(isinstance(x, dict) and x["created"] for x in outcomes) == 1
        assert sum(isinstance(x, DBAPIError) and "REFERENCE_PILOT_BUDGET_EXCEEDED" in str(x) for x in outcomes) == 1
    finally:
        await worker.close()
        await _revoke(admin)


@pytest.mark.parametrize("changed", ["mac", "event", "actor_build", "amount", "removed_reference", "tariff", "owner"])
async def test_feed_rejects_unverified_or_revoked_inputs_before_reserving(admin, api, seeded, settings, changed):
    parent, window, reference, tariff = await _fixture(admin, api, seeded, settings)
    values = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        if changed in {"mac", "event", "actor_build", "amount"}:
            key, value = {
                "mac": ("mac", "b" * 64),
                "event": ("event", uuid4()),
                "actor_build": ("build", "1.2.4"),
                "amount": ("amount", 1),
            }[changed]
            values[key] = value
        else:
            statement, params = {
                "removed_reference": ("UPDATE owner_references SET removed_at=now() WHERE id=:id", {"id": reference}),
                "tariff": ("UPDATE reference_provider_tariffs SET active=false WHERE version=:id", {"id": tariff}),
                "owner": (
                    "UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor",
                    {"tenant": parent.tenant, "actor": parent.actor},
                ),
            }[changed]
            async with admin.begin() as connection:
                await connection.execute(text(statement), params)
        with pytest.raises(DBAPIError):
            await _claim(worker, parent, values)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
    finally:
        await worker.close()
        await _revoke(admin)


async def test_feed_enforces_monthly_limit_and_tenant_isolation(admin, api, seeded, settings):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    values = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        await _policy(admin, search=1000, monthly=39, search_provider=1000, monthly_provider=1000)
        with pytest.raises(DBAPIError, match="REFERENCE_MONTHLY_BUDGET_EXCEEDED"):
            await _claim(worker, parent, values)
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_INTENT_INVALID"):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_CLAIM, values)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()
        await _revoke(admin)


async def test_feed_rejects_duplicate_event_even_with_identical_payload(admin, api, seeded, settings):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    values = await _effect(admin, parent, window, tariff)
    duplicate = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          SELECT :new,tenant_id,event_type,payload FROM outbox_events WHERE id=:original"""),
            {"new": duplicate, "original": values["event"]},
        )
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_INTENT_INVALID"):
            await _claim(worker, parent, {**values, "event": duplicate})
        assert (await _claim(worker, parent, values))["created"] is True
    finally:
        await worker.close()
        await _revoke(admin)


async def test_feed_guard_binds_actual_request_and_rejects_replay(admin, api, seeded, settings):
    parent, window, reference, tariff = await _fixture(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    context = FeedGuardContext(
        tenant=parent.tenant,
        business=parent.business,
        actor=parent.actor,
        reference=reference,
        association_version=1,
        analysis_window=window,
        search=None,
        selection=None,
        effect=uuid4(),
        event=uuid4(),
        pilot=parent.pilot,
        key=parent.key,
        key_version="test-key",
        tariff_version=tariff,
        credential_version="test-credential",
        reserved_usd_micros=40,
        profile="fixture_profile",
        build="1.2.3",
    )
    token = SecretStr("synthetic-apify-key")
    request = ApifyInstagramFeed._request(
        "POST",
        "https://api.apify.com/v2/acts/apify~instagram-scraper/runs",
        token,
        params={
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.00004",
            "maxItems": "20",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        },
        body={
            "directUrls": ["https://www.instagram.com/fixture_profile/"],
            "resultsType": "posts",
            "resultsLimit": 20,
        },
    )
    binding = ApifyInstagramFeed._bind(request, token)
    guard = DatabaseFeedBudgetGuard(worker, context)
    mac = guard._request_mac(binding)
    await _effect(admin, parent, window, tariff, effect=context.effect, event=context.event, mac=mac)
    try:
        assert await guard.claim_submission(uuid4(), binding) is False
        with pytest.raises(FeedGuardError, match="FEED_EXECUTOR_FENCE_INVALID"):
            await guard.submission_uncertain(context.effect, binding)
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_INTENT_INVALID"):
            await DatabaseFeedBudgetGuard(worker, context).claim_submission(
                context.effect, replace(binding, credential=SecretStr("another-key"))
            )
        assert await guard.claim_submission(context.effect, binding) is True
        assert await guard.claim_submission(context.effect, binding) is False
        with pytest.raises(FeedGuardError, match="FEED_EXECUTOR_FENCE_INVALID"):
            await guard.submission_uncertain(uuid4(), binding)
        await guard.submission_uncertain(context.effect, binding)
        assert await DatabaseFeedBudgetGuard(worker, context).claim_submission(context.effect, binding) is False
        assert await guard.claim_inspection(uuid4(), None) is False
        with pytest.raises(FeedGuardError, match="FEED_INSPECTION_DISABLED"):
            await guard.inspection_uncertain(uuid4(), None)
    finally:
        await worker.close()
        await _revoke(admin)
