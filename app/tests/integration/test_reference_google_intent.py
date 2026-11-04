"""Admit mock-only Google intents without provider calls or customer content."""

import asyncio
from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_google_intent import GoogleIntentError, create_google_intent, google_effect_id
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot, _request

pytestmark = pytest.mark.integration


async def _parent(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    original = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM reference_provider_effects WHERE id=:id"), {"id": original.effect})
        await connection.execute(text("DELETE FROM outbox_events WHERE id=:id"), {"id": original.event})
    return replace(original, effect=google_effect_id(original.search))


async def test_google_intent_is_atomic_private_and_idempotent(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        first, second = await asyncio.gather(
            create_google_intent(worker, context, _request()),
            create_google_intent(worker, replace(context, event=uuid4()), _request()),
        )
        assert first.event == second.event
        async with admin.connect() as connection:
            row = (
                await connection.execute(
                    text("SELECT state,request_event_id FROM reference_provider_effects WHERE id=:id"),
                    {"id": context.effect},
                )
            ).one()
            assert row.state == "pending" and row.request_event_id == first.event
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.google_intent_created'")
                )
                == 1
            )
            payload = await connection.scalar(
                text("SELECT payload::text FROM outbox_events WHERE id=:id"), {"id": first.event}
            )
            assert "synthetic-key" not in payload and "restaurant" not in payload
        for changed in (
            replace(context, reserved_usd_micros=context.reserved_usd_micros + 1),
            replace(context, context_version=context.context_version + 1),
            replace(context, pilot=uuid4()),
        ):
            with pytest.raises(DBAPIError):
                await create_google_intent(worker, changed, _request())
        with pytest.raises(DBAPIError, match="REFERENCE_GOOGLE_INTENT_CONFLICT"):
            await create_google_intent(worker, context, replace(_request(), credential=SecretStr("another-key")))
        with pytest.raises(GoogleIntentError, match="GOOGLE_EFFECT_ID_INVALID"):
            await create_google_intent(worker, replace(context, effect=uuid4()), _request())
    finally:
        await worker.close()


async def test_google_intent_cannot_bypass_role_or_duplicate_a_search(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    app = Database(settings)
    try:
        await create_google_intent(worker, context, _request())
        async with app.transaction(context.tenant, context.actor) as session:
            with pytest.raises(DBAPIError):
                await session.execute(
                    text(
                        "SELECT public.reference_google_intent(NULL,NULL,NULL,NULL,NULL,"
                        "NULL,NULL,NULL,NULL,NULL,NULL,NULL)"
                    )
                )
        async with admin.begin() as connection:
            with pytest.raises(DBAPIError):
                await connection.execute(
                    text("""INSERT INTO reference_provider_effects
                      (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,
                       tariff_version,credential_version,field_mask,reserved_usd_micros,state)
                      SELECT :id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,
                        tariff_version,credential_version,field_mask,reserved_usd_micros,state
                      FROM reference_provider_effects WHERE id=:original"""),
                    {"id": uuid4(), "original": context.effect},
                )
    finally:
        await worker.close()
        await app.close()


async def test_google_intent_requires_owner_and_matching_parent(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_SEARCH_INACTIVE"):
            await create_google_intent(worker, replace(context, context_version=2), _request())
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await create_google_intent(worker, context, _request())
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        first = await create_google_intent(worker, context, _request())
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        assert (await create_google_intent(worker, replace(context, event=uuid4()), _request())).event == first.event
    finally:
        await worker.close()
