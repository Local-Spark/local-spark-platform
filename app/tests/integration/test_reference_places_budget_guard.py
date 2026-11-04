"""Closed mock effects against the dedicated test ledger; no network."""

import asyncio
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.google_places import PLACES_FIELD_MASK, GooglePlacesNearby, PlacesChargeableRequest, PlacesError
from app.db.session import Database
from app.services.reference_places_budget_guard import (
    DatabasePlacesBudgetGuard,
    PlacesGuardContext,
    PlacesGuardStateError,
)
from app.services.reference_places_request_mac import places_request_mac
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration
_MASK = PLACES_FIELD_MASK


def _request(*, max_results=10):
    request = httpx.Request(
        "POST",
        "https://places.googleapis.com/v1/places:searchNearby",
        json={
            "includedTypes": ["restaurant"],
            "maxResultCount": max_results,
            "languageCode": "pt-BR",
            "locationRestriction": {"circle": {"center": {"latitude": 1.0, "longitude": 1.0}, "radius": 5000}},
        },
    )
    return PlacesChargeableRequest("POST", str(request.url), _MASK, request.content, SecretStr("synthetic-key"))


async def _intent(admin, api, settings, tenant, actor, pilot, tariff, *, amount=60, field_mask=_MASK, max_results=10):
    business, search, effect, event = await create_business(admin, tenant), uuid4(), uuid4(), uuid4()
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, headers, 0, local_scope(5))).status_code == 200
    context = PlacesGuardContext(
        tenant=tenant,
        business=business,
        actor=actor,
        search=search,
        effect=effect,
        pilot=pilot,
        event=event,
        context_version=1,
        key=SecretStr("synthetic-reference-key-0123456789abcdef"),
        key_version="test-key-v1",
        tariff_version=tariff,
        credential_version="synthetic-project-v1",
        reserved_usd_micros=amount,
    )
    mac = places_request_mac(
        context.key,
        key_version=context.key_version,
        tariff_version=context.tariff_version,
        credential_version=context.credential_version,
        tenant=tenant,
        business=business,
        actor=actor,
        search=search,
        effect=effect,
        pilot=pilot,
        context_version=context.context_version,
        reserved_usd_micros=amount,
        request=_request(max_results=max_results),
    )
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_searches
          (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state)
          VALUES(:id,:tenant,:business,:actor,:op,1,:mac,'pending')"""),
            {"id": search, "tenant": tenant, "business": business, "actor": actor, "op": uuid4(), "mac": mac},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,
           tariff_version,credential_version,field_mask,reserved_usd_micros,state)
          VALUES(:id,:tenant,:business,:actor,:search,:pilot,'google',:mac,:key,:tariff,:credential,:mask,:amount,'pending')"""),
            {
                "id": effect,
                "tenant": tenant,
                "business": business,
                "actor": actor,
                "search": search,
                "pilot": pilot,
                "mac": mac,
                "key": context.key_version,
                "tariff": tariff,
                "credential": context.credential_version,
                "mask": field_mask,
                "amount": amount,
            },
        )
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:id,:tenant,'reference.provider_effect_requested',jsonb_build_object(
            'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
            'operation_id',CAST(:effect AS text)))"""),
            {"id": event, "tenant": tenant, "business": str(business), "actor": str(actor), "effect": str(effect)},
        )
    return context


async def _pilot(admin, *, cap=100, minimum=1, tariff_active=True, pilot_active=True):
    pilot, tariff = uuid4(), "synthetic-" + uuid4().hex
    async with admin.begin() as connection:
        # `admin` is guarded by the integration fixture to use only `_test`.
        await connection.execute(text("DELETE FROM reference_cost_monthly"))
        await connection.execute(text("DELETE FROM reference_provider_pilots"))
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:version,'google',:mask,:minimum,:active)"""),
            {"version": tariff, "mask": _MASK, "minimum": minimum, "active": tariff_active},
        )
        await connection.execute(
            text("INSERT INTO reference_provider_pilots(id,cap_usd_micros,active) VALUES(:id,:cap,:active)"),
            {"id": pilot, "cap": cap, "active": pilot_active},
        )
    await _policy(admin, search=1000, monthly=1000, search_provider=1000, monthly_provider=1000)
    return pilot, tariff


async def test_mock_http_claim_commits_before_io_and_replay_does_not_disturb_executor(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    started, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def handler(request):
        calls.append(request.url.host)
        async with admin.begin() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_provider_effects WHERE id=:id FOR UPDATE NOWAIT"),
                    {"id": context.effect},
                )
                == "running"
            )
        started.set()
        await release.wait()
        return httpx.Response(200, json={"places": [{"id": "synthetic-id", "rating": 4.8, "userRatingCount": 20}]})

    def adapter():
        return GooglePlacesNearby(
            SecretStr("synthetic-key"),
            DatabasePlacesBudgetGuard(worker, context),
            enabled=True,
            transport=httpx.MockTransport(handler),
        )

    try:
        pending = asyncio.create_task(adapter().search("restaurant", 1, 1, 5, context.effect))
        await asyncio.wait_for(started.wait(), timeout=3)
        with pytest.raises(PlacesError, match="PLACES_BUDGET_UNAVAILABLE"):
            await adapter().search("restaurant", 1, 1, 5, context.effect)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "running"
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
        release.set()
        result = await asyncio.wait_for(pending, timeout=3)
        assert [item.place_id for item in result] == ["synthetic-id"] and calls == ["places.googleapis.com"]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_cost_reservations")) == "claimed"
    finally:
        release.set()
        await worker.close()


async def test_uncertain_response_keeps_fenced_reservation_and_replay_never_resends(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    guard = DatabasePlacesBudgetGuard(worker, context)

    def fail(request):
        raise httpx.ConnectError("sensitive provider detail", request=request)

    try:
        provider = GooglePlacesNearby(
            SecretStr("synthetic-key"), guard, enabled=True, transport=httpx.MockTransport(fail)
        )
        with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN") as error:
            await provider.search("restaurant", 1, 1, 5, context.effect)
        assert "sensitive provider detail" not in str(error.value)
        await guard.uncertain()
        replay = DatabasePlacesBudgetGuard(worker, context)
        assert await replay.claim(context.effect, _request()) is False
        with pytest.raises(PlacesGuardStateError, match="PLACES_EXECUTOR_NOT_CLAIMED"):
            await replay.uncertain()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "uncertain"
            reservation = await connection.scalar(text("SELECT id FROM reference_cost_reservations"))
            assert await connection.scalar(text("SELECT state FROM reference_cost_reservations")) == "uncertain"
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_FENCE_REQUIRED"):
            async with worker.transaction(context.tenant, context.actor) as session:
                await session.scalar(text("SELECT public.reference_cost_finish(:id,NULL)"), {"id": reservation})
    finally:
        await worker.close()


async def test_single_pilot_cap_is_shared_across_tenants_and_claims(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin, cap=100)
    first = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    second = await _intent(admin, api, settings, seeded["t2"], seeded["a2"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        results = await asyncio.gather(
            DatabasePlacesBudgetGuard(worker, first).claim(first.effect, _request()),
            DatabasePlacesBudgetGuard(worker, second).claim(second.effect, _request()),
            return_exceptions=True,
        )
        assert sum(result is True for result in results) == 1
        assert (
            sum(
                isinstance(result, DBAPIError) and "REFERENCE_PILOT_BUDGET_EXCEEDED" in str(result)
                for result in results
            )
            == 1
        )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
        with pytest.raises(DBAPIError):
            async with admin.begin() as connection:
                await connection.execute(
                    text("INSERT INTO reference_provider_pilots(id,cap_usd_micros) VALUES(:id,100)"), {"id": uuid4()}
                )
    finally:
        await worker.close()


async def test_intent_mac_tariff_and_pilot_must_match_before_claim(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin, minimum=61)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        for altered in (
            replace(context, credential_version="another-project"),
            replace(context, event=uuid4()),
        ):
            with pytest.raises(DBAPIError):
                await DatabasePlacesBudgetGuard(worker, altered).claim(altered.effect, _request())
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_INTENT_INVALID"):
            await DatabasePlacesBudgetGuard(worker, context).claim(
                context.effect, replace(_request(), credential=SecretStr("different-synthetic-key"))
            )
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_TARIFF_INVALID"):
            await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request())
        guard = DatabasePlacesBudgetGuard(worker, context)
        assert await guard.claim(uuid4(), _request()) is False
        with pytest.raises(PlacesGuardStateError):
            await guard.uncertain()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "pending"
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()


@pytest.mark.parametrize("disabled", ["tariff", "pilot", "policy", "search", "membership"])
async def test_no_new_claim_after_policy_or_owner_revocation(admin, api, seeded, settings, disabled):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    commands = {
        "tariff": ("UPDATE reference_provider_tariffs SET active=false WHERE version=:tariff", {"tariff": tariff}),
        "pilot": ("UPDATE reference_provider_pilots SET active=false WHERE id=:pilot", {"pilot": pilot}),
        "policy": ("UPDATE reference_cost_policy_head SET policy_id=NULL", {}),
        "search": ("UPDATE reference_provider_searches SET state='stale' WHERE id=:id", {"id": context.search}),
        "membership": (
            "UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor",
            {"tenant": context.tenant, "actor": context.actor},
        ),
    }
    sql, params = commands[disabled]
    async with admin.begin() as connection:
        await connection.execute(text(sql), params)
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError):
            await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request())
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "pending"
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
    finally:
        await worker.close()


async def test_tariff_revocation_committed_while_waiting_prevents_claim(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_tariffs SET active=false WHERE version=:version"), {"version": tariff}
            )
            claim = asyncio.create_task(DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()))
            await asyncio.sleep(0.15)
            assert not claim.done()
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_TARIFF_INVALID"):
            await asyncio.wait_for(claim, 3)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()


async def test_reservation_must_satisfy_global_monthly_budget(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    await _policy(admin, search=1000, monthly=50, search_provider=1000, monthly_provider=1000)
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_MONTHLY_BUDGET_EXCEEDED"):
            await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request())
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
    finally:
        await worker.close()


async def test_pilot_cap_survives_calendar_month_change(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin, cap=100)
    first = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    second = await _intent(admin, api, settings, seeded["t2"], seeded["a2"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, first).claim(first.effect, _request()) is True
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE reference_cost_monthly SET month=month-interval '1 month'"))
        with pytest.raises(DBAPIError, match="REFERENCE_PILOT_BUDGET_EXCEEDED"):
            await DatabasePlacesBudgetGuard(worker, second).claim(second.effect, _request())
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()


async def test_intent_field_mask_cannot_diverge_from_signed_request(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff, field_mask="places.id")
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_INTENT_INVALID"):
            await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request())
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()


async def test_direct_claim_has_a_durable_reservation(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()) is True
    finally:
        await worker.close()


async def test_empty_response_commits_once_and_replay_recovers_without_new_http(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    requests = []

    def empty(request):
        requests.append(request.method)
        return httpx.Response(200, json={"places": []})

    def adapter(guard):
        return GooglePlacesNearby(SecretStr("synthetic-key"), guard, enabled=True, transport=httpx.MockTransport(empty))

    try:
        guard = DatabasePlacesBudgetGuard(worker, context)
        assert await adapter(guard).search("restaurant", 1, 1, 5, context.effect) == ()
        # The original executor may retry the committed outcome without duplicating events.
        await guard.complete_empty()
        assert (
            await adapter(DatabasePlacesBudgetGuard(worker, context)).search("restaurant", 1, 1, 5, context.effect)
            == ()
        )
        assert requests == ["POST"]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "completed_empty"
            assert await connection.scalar(text("SELECT state FROM reference_cost_reservations")) == "uncertain"
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM outbox_events WHERE event_type='reference.provider_effect_completed'")
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.provider_empty_completed'")
                )
                == 1
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_provider_results")) == 0
    finally:
        await worker.close()


@pytest.mark.parametrize("commit_before_loss", [False, True])
async def test_lost_empty_commit_confirmation_never_resends(admin, api, seeded, settings, commit_before_loss):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    guard = DatabasePlacesBudgetGuard(worker, context)
    original = guard.complete_empty

    async def lost_confirmation():
        if commit_before_loss:
            await original()
        raise ConnectionError("synthetic lost acknowledgement")

    guard.complete_empty = lost_confirmation
    calls = []

    def empty(request):
        calls.append(request.method)
        return httpx.Response(200, json={"places": []})

    try:
        provider = GooglePlacesNearby(
            SecretStr("synthetic-key"), guard, enabled=True, transport=httpx.MockTransport(empty)
        )
        with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN"):
            await provider.search("restaurant", 1, 1, 5, context.effect)
        retry = GooglePlacesNearby(
            SecretStr("synthetic-key"),
            DatabasePlacesBudgetGuard(worker, context),
            enabled=True,
            transport=httpx.MockTransport(empty),
        )
        if commit_before_loss:
            assert await retry.search("restaurant", 1, 1, 5, context.effect) == ()
        else:
            with pytest.raises(PlacesError, match="PLACES_BUDGET_UNAVAILABLE"):
                await retry.search("restaurant", 1, 1, 5, context.effect)
        assert calls == ["POST"]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == (
                "completed_empty" if commit_before_loss else "uncertain"
            )
    finally:
        await worker.close()


async def test_empty_completion_requires_original_event_and_executor_token(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    try:
        guard = DatabasePlacesBudgetGuard(worker, context)
        with pytest.raises(PlacesGuardStateError, match="PLACES_EXECUTOR_NOT_CLAIMED"):
            await guard.complete_empty()
        assert await guard.claim(context.effect, _request()) is True
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_FENCE_INVALID"):
            async with worker.transaction(context.tenant, context.actor) as session:
                await session.scalar(
                    text("SELECT public.reference_provider_complete_empty(:effect,:event,:token)"),
                    {"effect": context.effect, "event": context.event, "token": uuid4()},
                )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM reference_provider_effects")) == "running"
            assert await connection.scalar(text("SELECT state FROM reference_cost_reservations")) == "claimed"
    finally:
        await worker.close()
