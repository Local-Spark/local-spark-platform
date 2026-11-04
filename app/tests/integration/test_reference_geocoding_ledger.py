"""Inactive manual-origin reservations share the same fenced pilot."""

import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.google_geocoding import GeocodingChargeableRequest
from app.db.session import Database
from app.services.reference_geocoding_budget_guard import (
    DatabaseGeocodingBudgetGuard,
    GeocodingGuardContext,
    GeocodingGuardError,
)
from app.services.reference_geocoding_request_mac import geocoding_request_mac
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot, _request

pytestmark = pytest.mark.integration

_SIGNATURE = "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"
_CLAIM = text("""SELECT public.reference_geocode_claim(:business,:effect,:event,:origin,:pilot,:mac,
  :key,:tariff,:credential,:class,:amount,:context)""")


async def _setup(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin, cap=100)
    parent = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    geocode_tariff = "geocode-test-" + uuid4().hex
    async with admin.begin() as connection:
        assert not await connection.scalar(
            text(f"""SELECT has_function_privilege('meu_braco_direito_correlator',
          'public.reference_geocode_claim({_SIGNATURE})','EXECUTE')""")
        )
        await connection.execute(
            text(
                f"GRANT EXECUTE ON FUNCTION public.reference_geocode_claim({_SIGNATURE}), "
                "public.reference_geocode_uncertain(uuid,uuid) TO meu_braco_direito_correlator"
            )
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:v,'google','geocode-v4:results.placeId,results.location',1,true)"""),
            {"v": geocode_tariff},
        )
    return parent, geocode_tariff


async def _effect(admin, parent, tariff, *, effect=None, event=None, origin=None, mac="a" * 64):
    effect, event, origin = effect or uuid4(), event or uuid4(), origin or uuid4()
    values = {
        "business": parent.business,
        "effect": effect,
        "event": event,
        "origin": origin,
        "pilot": parent.pilot,
        "mac": mac,
        "key": "test-key",
        "tariff": tariff,
        "credential": "test-credential",
        "class": "geocode-v4:results.placeId,results.location",
        "amount": 40,
        "context": 1,
    }
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_geocode_origins
          (id,tenant_id,business_id,actor_id,context_version) VALUES(:origin,:tenant,:business,:actor,1)"""),
            {**values, "tenant": parent.tenant, "actor": parent.actor},
        )
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
            text("""INSERT INTO reference_geocode_effects
          (id,tenant_id,business_id,actor_id,origin_id,pilot_id,event_id,request_mac,key_version,tariff_version,
           credential_version,charge_class,reserved_usd_micros,state)
          VALUES(:effect,:tenant,:business,:actor,:origin,:pilot,:event,:mac,:key,:tariff,:credential,:class,:amount,'pending')"""),
            {**values, "tenant": parent.tenant, "actor": parent.actor},
        )
    return values


async def _claim(worker, parent, values):
    async with worker.transaction(parent.tenant, parent.actor) as session:
        return await session.scalar(_CLAIM, values)


async def _revoke(admin):
    async with admin.begin() as connection:
        await connection.execute(
            text(
                f"REVOKE EXECUTE ON FUNCTION public.reference_geocode_claim({_SIGNATURE}), "
                "public.reference_geocode_uncertain(uuid,uuid) FROM meu_braco_direito_correlator"
            )
        )


async def test_geocode_shares_budget_and_holds_uncertain_cost(admin, api, seeded, settings):
    parent, tariff = await _setup(admin, api, seeded, settings)
    values = await _effect(admin, parent, tariff)
    worker = Database(settings, correlator=True)
    try:
        assert await DatabasePlacesBudgetGuard(worker, parent).claim(parent.effect, _request()) is True
        first = await _claim(worker, parent, values)
        assert first["created"] is True and (await _claim(worker, parent, values))["created"] is False
        with pytest.raises(DBAPIError, match="REFERENCE_GEOCODE_FENCE_INVALID"):
            async with worker.transaction(parent.tenant, parent.actor) as session:
                await session.execute(
                    text("SELECT public.reference_geocode_uncertain(:effect,:token)"),
                    {"effect": values["effect"], "token": uuid4()},
                )
        async with worker.transaction(parent.tenant, parent.actor) as session:
            await session.execute(
                text("SELECT public.reference_geocode_uncertain(:effect,:token)"),
                {"effect": values["effect"], "token": UUID(first["executor_token"])},
            )
        assert (await _claim(worker, parent, values))["state"] == "uncertain"
        async with admin.connect() as connection:
            reservation = await connection.scalar(
                text("SELECT id FROM reference_cost_reservations WHERE effect_id=:id"), {"id": values["effect"]}
            )
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_FENCE_REQUIRED"):
            async with worker.transaction(parent.tenant, parent.actor) as session:
                await session.scalar(text("SELECT public.reference_cost_finish(:id,NULL)"), {"id": reservation})
    finally:
        await worker.close()
        await _revoke(admin)


async def test_geocode_races_cannot_exceed_pilot(admin, api, seeded, settings):
    parent, tariff = await _setup(admin, api, seeded, settings)
    first, second = await _effect(admin, parent, tariff), await _effect(admin, parent, tariff)
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


async def test_geocode_checks_context_event_monthly_and_tenant(admin, api, seeded, settings):
    parent, tariff = await _setup(admin, api, seeded, settings)
    values = await _effect(admin, parent, tariff)
    worker = Database(settings, correlator=True)
    try:
        for changed in ({"context": 2}, {"event": uuid4()}, {"mac": "b" * 64}):
            with pytest.raises(DBAPIError, match="REFERENCE_GEOCODE_INTENT_INVALID"):
                await _claim(worker, parent, {**values, **changed})
        with pytest.raises(DBAPIError, match="REFERENCE_GEOCODE_INTENT_INVALID"):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_CLAIM, values)
        await _policy(admin, search=1000, monthly=39, search_provider=1000, monthly_provider=1000)
        with pytest.raises(DBAPIError, match="REFERENCE_MONTHLY_BUDGET_EXCEEDED"):
            await _claim(worker, parent, values)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()
        await _revoke(admin)


async def test_geocode_guard_binds_exact_address_mask_and_actual_credential(admin, api, seeded, settings):
    parent, tariff = await _setup(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    context = GeocodingGuardContext(
        tenant=parent.tenant,
        business=parent.business,
        actor=parent.actor,
        origin=uuid4(),
        effect=uuid4(),
        event=uuid4(),
        pilot=parent.pilot,
        context_version=1,
        key=parent.key,
        key_version="test-key",
        tariff_version=tariff,
        credential_version="test-credential",
        reserved_usd_micros=40,
    )
    request = httpx.Request(
        "GET",
        "https://geocode.googleapis.com/v4/geocode/address",
        params={"address.addressLines": "Rua Fictícia 10", "address.regionCode": "BR", "languageCode": "pt-BR"},
    )
    binding = GeocodingChargeableRequest(
        "GET", str(request.url), "results.placeId,results.location", SecretStr("synthetic-google-key")
    )
    mac = geocoding_request_mac(
        context.key,
        key_version=context.key_version,
        tariff_version=context.tariff_version,
        credential_version=context.credential_version,
        tenant=context.tenant,
        business=context.business,
        actor=context.actor,
        origin=context.origin,
        effect=context.effect,
        pilot=context.pilot,
        context_version=context.context_version,
        reserved_usd_micros=context.reserved_usd_micros,
        request=binding,
    )
    await _effect(admin, parent, tariff, effect=context.effect, event=context.event, origin=context.origin, mac=mac)
    guard = DatabaseGeocodingBudgetGuard(worker, context)
    try:
        assert await guard.claim(uuid4(), binding) is False
        with pytest.raises(GeocodingGuardError, match="GEOCODING_EXECUTOR_NOT_CLAIMED"):
            await guard.uncertain()
        for changed in (
            replace(binding, credential=SecretStr("other-key")),
            replace(binding, url=binding.url.replace("Fict", "Outro")),
        ):
            with pytest.raises(DBAPIError, match="REFERENCE_GEOCODE_INTENT_INVALID"):
                await DatabaseGeocodingBudgetGuard(worker, context).claim(context.effect, changed)
        assert await guard.claim(context.effect, binding) is True
        assert await guard.claim(context.effect, binding) is False
        await guard.uncertain()
        assert await DatabaseGeocodingBudgetGuard(worker, context).claim(context.effect, binding) is False
    finally:
        await worker.close()
        await _revoke(admin)
