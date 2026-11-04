"""Admission and cycles are tested with synthetic business data and no HTTP providers."""

import asyncio
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_google_intent import create_google_intent, google_effect_id
from app.services.reference_places_budget_guard import PlacesGuardContext
from app.services.reference_search_admission import admit_provider_search
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.integration.test_reference_places_budget_guard import _pilot, _request
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration
_KEY = SecretStr("synthetic-reference-search-key-0123456789")


async def _business(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, headers, 0, local_scope(5))).status_code == 200
    address = await api.put(
        base + "/address",
        headers=headers,
        json={
            "operation_id": str(uuid4()),
            "expected_version": 0,
            "address": {"street": "Rua das Flores", "number": "123", "city": "São Paulo", "state_code": "SP"},
        },
    )
    assert address.status_code == 200
    return tenant, actor, business, base, headers


async def test_admission_is_idempotent_scoped_and_never_calls_providers(admin, api, seeded, settings, database):
    tenant, actor, business, _, _ = await _business(admin, api, seeded, settings)
    operation = uuid4()
    first, replay = await asyncio.gather(
        admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, operation, 1, 5),
        admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, operation, 1, 5),
    )
    assert first.search_id == replay.search_id and first.event_id == replay.event_id
    assert first.cycle_id == replay.cycle_id and {first.created, replay.created} == {True, False}
    with pytest.raises(DBAPIError, match="REFERENCE_RADIUS_ALREADY_SEARCHED"):
        await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    with pytest.raises(DBAPIError, match="REFERENCE_SEARCH_ADMISSION_CONFLICT"):
        await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, operation, 1, 20)
    with pytest.raises(DBAPIError, match="REFERENCE_SEARCH_ADMISSION_CONFLICT"):
        await admit_provider_search(database, _KEY, "test-v2", tenant, business, actor, operation, 1, 5)
    with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
        await admit_provider_search(database, _KEY, "test-v1", tenant, business, seeded["viewer"], uuid4(), 1, 5)
    with pytest.raises(DBAPIError):
        await admit_provider_search(database, _KEY, "test-v1", seeded["t2"], business, seeded["a2"], uuid4(), 1, 5)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_searches")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_effects")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
        payload = await connection.scalar(
            text("SELECT payload::text FROM outbox_events WHERE id=:event"), {"event": first.event_id}
        )
        assert "Café" not in payload and "-23.55" not in payload


async def test_unused_radius_and_new_cycle_follow_original_deadline(admin, api, seeded, settings, database):
    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    first = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE reference_real_cycles SET confirmed_at=clock_timestamp(),
              locked_until=clock_timestamp()+interval '6 months' WHERE id=:cycle"""),
            {"cycle": first.cycle_id},
        )
    assert (await save_scope(api, base, headers, 1, local_scope(20))).status_code == 200
    other = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 2, 20)
    assert other.cycle_id == first.cycle_id
    with pytest.raises(DBAPIError, match="REFERENCE_SEARCH_CONTEXT_INVALID"):
        await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE reference_real_cycles SET confirmed_at=clock_timestamp()-interval '7 months',
              locked_until=clock_timestamp()-interval '1 month' WHERE id=:cycle"""),
            {"cycle": first.cycle_id},
        )
    assert (await save_scope(api, base, headers, 2, local_scope(5))).status_code == 200
    renewed = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 3, 5)
    assert renewed.cycle_id != first.cycle_id


@pytest.mark.parametrize("state", ["stale", "failed", "cancelled", "uncertain"])
async def test_state_alone_does_not_release_a_radius(admin, api, seeded, settings, database, state):
    tenant, actor, business, _, _ = await _business(admin, api, seeded, settings)
    admitted = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_provider_searches SET state=:state WHERE id=:search"),
            {"state": state, "search": admitted.search_id},
        )
    with pytest.raises(DBAPIError, match="REFERENCE_RADIUS_ALREADY_SEARCHED"):
        await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)


async def test_unstarted_cancellation_is_idempotent_and_releases_radius(admin, api, seeded, settings, database):
    tenant, actor, business, _, _ = await _business(admin, api, seeded, settings)
    admitted = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    worker = Database(settings, correlator=True)
    operation = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text(
                "GRANT EXECUTE ON FUNCTION public.reference_cancel_unstarted_search(uuid,uuid,uuid) "
                "TO meu_braco_direito_correlator"
            )
        )

    async def cancel(op):
        async with worker.transaction(tenant, actor) as session:
            return await session.scalar(
                text("SELECT public.reference_cancel_unstarted_search(:b,:s,:o)"),
                {"b": business, "s": admitted.search_id, "o": op},
            )

    try:
        event = await cancel(operation)
        assert await cancel(operation) == event
        with pytest.raises(DBAPIError, match="REFERENCE_SEARCH_CANCELLATION_CONFLICT"):
            await cancel(uuid4())
        again = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
        assert again.cycle_id == admitted.cycle_id and again.search_id != admitted.search_id
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.provider_search_cancelled'")
                )
                == 1
            )
    finally:
        await worker.close()
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "REVOKE EXECUTE ON FUNCTION "
                    "public.reference_cancel_unstarted_search(uuid,uuid,uuid) "
                    "FROM meu_braco_direito_correlator"
                )
            )


async def test_cancellation_cannot_race_a_provider_intention(admin, api, seeded, settings, database):
    tenant, actor, business, _, _ = await _business(admin, api, seeded, settings)
    admitted = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    pilot, tariff = await _pilot(admin)
    worker = Database(settings, correlator=True)
    context = PlacesGuardContext(
        tenant=tenant,
        business=business,
        actor=actor,
        search=admitted.search_id,
        effect=google_effect_id(admitted.search_id),
        pilot=pilot,
        event=uuid4(),
        key=SecretStr("synthetic-reference-key-0123456789abcdef"),
        key_version="test-v1",
        tariff_version=tariff,
        credential_version="synthetic-project",
        context_version=1,
        reserved_usd_micros=1,
    )
    async with admin.begin() as connection:
        await connection.execute(
            text(
                "GRANT EXECUTE ON FUNCTION public.reference_cancel_unstarted_search(uuid,uuid,uuid) "
                "TO meu_braco_direito_correlator"
            )
        )

    async def cancel():
        async with worker.transaction(tenant, actor) as session:
            return await session.scalar(
                text("SELECT public.reference_cancel_unstarted_search(:b,:s,:o)"),
                {"b": business, "s": admitted.search_id, "o": uuid4()},
            )

    try:
        results = await asyncio.gather(
            cancel(), create_google_intent(worker, context, _request()), return_exceptions=True
        )
        assert sum(isinstance(value, DBAPIError) for value in results) == 1
        async with admin.connect() as connection:
            state = await connection.scalar(
                text("SELECT state FROM reference_provider_searches WHERE id=:id"), {"id": admitted.search_id}
            )
            effects = await connection.scalar(
                text("SELECT count(*) FROM reference_provider_effects WHERE search_id=:id"), {"id": admitted.search_id}
            )
            assert (state, effects) in (("cancelled", 0), ("pending", 1))
    finally:
        await worker.close()
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "REVOKE EXECUTE ON FUNCTION "
                    "public.reference_cancel_unstarted_search(uuid,uuid,uuid) "
                    "FROM meu_braco_direito_correlator"
                )
            )
