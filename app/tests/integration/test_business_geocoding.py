"""Address resolution crosses the real ledger with an HTTP transport fake only."""

from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.google_geocoding import GEOCODING_FIELD_MASK, GeocodingError
from app.db.session import Database
from app.schemas.business_address import BusinessAddressWrite
from app.schemas.business_geocoding import GeocodeConfirmation, GeocodeRequest
from app.services.auth import AuthError
from app.services.business_address import BusinessAddressService
from app.services.business_geocoding import BusinessGeocodingRunner, BusinessGeocodingService
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.integration.test_reference_places_budget_guard import _pilot
from app.tests.unit.test_core import access_token
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


async def setup(admin, api, database, settings, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, headers, 0, local_scope())).status_code == 200
    await BusinessAddressService(database).save(
        tenant,
        business,
        actor,
        BusinessAddressWrite(
            operation_id=uuid4(),
            expected_version=0,
            address={"street": "Rua das Flores", "number": "123", "city": "São Paulo", "state_code": "SP"},
        ),
    )
    pilot, _ = await _pilot(admin, cap=100)
    tariff = "geocode-" + uuid4().hex
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:version,'google',:mask,10,true)"""),
            {"version": tariff, "mask": "geocode-v4:" + GEOCODING_FIELD_MASK},
        )
    await _policy(admin, search=100, monthly=100, search_provider=100, monthly_provider=100)
    for key, value in dict(
        reference_geocoding_enabled=True,
        reference_google_api_key=SecretStr("synthetic-google"),
        reference_provider_hmac_key=SecretStr("synthetic-reference-key-0123456789abcdef"),
        reference_provider_key_version="test-v1",
        reference_google_credential_version="test-v1",
        reference_provider_pilot_id=pilot,
        reference_geocoding_tariff_version=tariff,
        reference_geocoding_reserved_usd_micros=10,
    ).items():
        setattr(settings, key, value)
    return tenant, business, actor, base, headers


def result(*, number="123", latitude=-23.5):
    return {
        "placeId": "only-geocode-address-id",
        "formattedAddress": "provider formatted address must not persist",
        "location": {"latitude": latitude, "longitude": -46.6},
        "granularity": "ROOFTOP",
        "postalAddress": {"regionCode": "BR"},
        "addressComponents": [
            {"longText": "Rua das Flores", "types": ["route"]},
            {"longText": number, "types": ["street_number"]},
            {"longText": "São Paulo", "types": ["locality"]},
            {"longText": "São Paulo", "shortText": "SP", "types": ["administrative_area_level_1"]},
        ],
    }


async def event_for(admin, tenant, business, actor):
    async with admin.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT id,event_id FROM business_address_geocodes "
                    "WHERE tenant_id=:tenant AND business_id=:business"
                ),
                {"tenant": tenant, "business": business},
            )
        ).one()
    return BusinessEvent(
        tenant_id=str(tenant),
        business_id=str(business),
        actor_id=str(actor),
        operation_id=str(row.id),
        event_id=str(row.event_id),
    )


async def test_geocode_api_automatic_match_costed_once_and_private(admin, api, database, settings, seeded):
    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    path = base + "/address/geocoding"
    assert (await api.get(path, headers=headers)).json()["status"] == "unrequested"
    payload = {"operation_id": str(uuid4()), "address_version": 1}
    requested = await api.post(path, headers=headers, json=payload)
    assert requested.status_code == 202, requested.text
    assert requested.json()["status"] == "pending"
    assert (await api.post(path, headers=headers, json=payload)).json() == requested.json()
    assert (
        await api.post(path, headers=headers, json={**payload, "operation_id": str(uuid4())})
    ).json() == requested.json()
    event = await event_for(admin, t, b, a)
    worker = Database(settings, correlator=True)
    calls = []

    async def transport(request):
        calls.append(request)
        # Verify the reservation committed before transport, with no lock held by the runner.
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
        return httpx.Response(200, json={"results": [result()]})

    try:
        runner = BusinessGeocodingRunner(worker, settings, transport=httpx.MockTransport(transport))
        assert await runner.run(event) == "resolved"
        assert await runner.run(event) == "resolved"
        assert len(calls) == 1
        read = (await api.get(path, headers=headers)).json()
        assert read["status"] == "resolved" and read["coordinates"]["latitude"] == -23.5 and read["candidates"] == []
        async with admin.connect() as conn:
            data = await conn.scalar(text("SELECT row_to_json(g)::text FROM business_address_geocodes g"))
            assert "provider formatted" not in data and "only-geocode-address-id" not in data
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 10
            assert await conn.scalar(text("SELECT state FROM reference_cost_reservations")) == "uncertain"
            events = (
                (
                    await conn.execute(
                        text("SELECT payload::text FROM outbox_events WHERE event_type LIKE 'business.address_%'")
                    )
                )
                .scalars()
                .all()
            )
            assert all("Flores" not in item and "-23.5" not in item for item in events)
    finally:
        await worker.close()


async def test_geocode_ambiguous_confirmed_by_shared_owner_without_requery(admin, api, database, settings, seeded):
    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    event = await event_for(admin, t, b, a)
    worker = Database(settings, correlator=True)
    try:
        assert (
            await BusinessGeocodingRunner(
                worker,
                settings,
                transport=httpx.MockTransport(
                    lambda _: httpx.Response(200, json={"results": [result(), result(number="124", latitude=-23.6)]})
                ),
            ).run(event)
            == "confirmation_required"
        )
    finally:
        await worker.close()
    second = seeded["a2"]
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": t, "actor": second},
        )
    read = await service.read(t, b, second)
    assert read.coordinates is None and len(read.candidates) == 2
    payload = GeocodeConfirmation(
        operation_id=uuid4(), address_version=1, geocode_id=read.geocode_id, candidate_id=read.candidates[1].id
    )
    response = await api.post(
        base + "/address/geocoding/confirm",
        headers={"Authorization": f"Bearer {access_token(settings, second)}"},
        json=payload.model_dump(mode="json"),
    )
    assert response.status_code == 200, response.text
    confirmed = await service.confirm(t, b, second, payload)
    assert confirmed.status == "resolved" and confirmed.coordinates.latitude == -23.6
    assert await service.confirm(t, b, second, payload) == confirmed
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_OPERATION_CONFLICT"):
        await service.confirm(t, b, second, payload.model_copy(update={"candidate_id": read.candidates[0].id}))


async def test_geocode_fail_closed_disabled_stale_budget_and_unavailable(admin, api, database, settings, seeded):
    from app.tests.integration.test_business_address import payload

    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    settings.reference_geocoding_enabled = False
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_GEOCODE_DISABLED"):
        await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    settings.reference_geocoding_enabled = True
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_VERSION_CONFLICT"):
        await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=9))
    await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    event = await event_for(admin, t, b, a)
    worker = Database(settings, correlator=True)
    calls = []
    runner = BusinessGeocodingRunner(
        worker, settings, transport=httpx.MockTransport(lambda request: calls.append(request))
    )
    try:
        await _policy(admin, search=9, monthly=100, search_provider=100, monthly_provider=100)
        with pytest.raises(GeocodingError, match="GEOCODING_BUDGET_UNAVAILABLE"):
            await runner.run(event)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
        await _policy(admin, search=100, monthly=100, search_provider=100, monthly_provider=100)
        await BusinessAddressService(database).save(t, b, a, payload(1, "456"))
        with pytest.raises(GeocodingError, match="GEOCODING_BUDGET_UNAVAILABLE"):
            await runner.run(event)
        assert not calls
    finally:
        await worker.close()


@pytest.mark.parametrize(
    "response,status", [(httpx.Response(200, json={"results": []}), "not_found"), (httpx.Response(503), "uncertain")]
)
async def test_geocode_empty_or_uncertain_retries_never_dispatch_twice(
    admin, api, database, settings, seeded, response, status
):
    t, b, a, _, _ = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    worker = Database(settings, correlator=True)
    calls = []

    def handler(request):
        calls.append(request)
        return response

    try:
        event = await event_for(admin, t, b, a)
        runner = BusinessGeocodingRunner(worker, settings, transport=httpx.MockTransport(handler))
        assert await runner.run(event) == status
        assert await runner.run(event) == status
        assert (await service.read(t, b, a)).status == status
        assert len(calls) == 1
    finally:
        await worker.close()


async def test_geocode_binding_drift_and_lost_commit_are_visible_without_repeat(admin, api, database, settings, seeded):
    from app.schemas.business_address import ShopAddress
    from app.services.reference_geocoding_budget_guard import DatabaseGeocodingBudgetGuard, GeocodingGuardContext

    t, b, a, _, _ = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    worker = Database(settings, correlator=True)
    event = await event_for(admin, t, b, a)
    try:
        runner = BusinessGeocodingRunner(
            worker, settings, transport=httpx.MockTransport(lambda _: pytest.fail("no network expected"))
        )
        settings.reference_google_credential_version = "other"
        with pytest.raises(GeocodingError, match="GEOCODING_CONFIGURATION_CHANGED"):
            await runner.run(event)
        settings.reference_google_credential_version = "test-v1"
        original = settings.reference_google_api_key
        settings.reference_google_api_key = SecretStr("changed-credential")
        with pytest.raises(GeocodingError, match="GEOCODING_BINDING_INVALID"):
            await runner.run(event)
        settings.reference_google_api_key = original
        async with worker.transaction(t, a) as session:
            row = await session.scalar(
                text("SELECT public.business_address_geocode_load(:b,:id,:event)"),
                {"b": b, "id": UUID(event.operation_id), "event": UUID(event.event_id)},
            )
        context = GeocodingGuardContext(
            tenant=t,
            business=b,
            actor=a,
            origin=UUID(row["origin_id"]),
            effect=UUID(row["effect_id"]),
            event=UUID(row["effect_event_id"]),
            pilot=UUID(row["pilot_id"]),
            context_version=1,
            key=settings.reference_provider_hmac_key,
            key_version="test-v1",
            tariff_version=row["tariff_version"],
            credential_version="test-v1",
            reserved_usd_micros=10,
        )
        guard = DatabaseGeocodingBudgetGuard(worker, context, shop_address=True)
        from app.services.business_geocoding import _request

        assert await guard.claim(context.effect, _request(ShopAddress.model_validate(row["address"]), original))
        assert await runner.run(event) == "uncertain"
        assert (await service.read(t, b, a)).status == "uncertain"
    finally:
        await worker.close()


async def test_saved_manual_origin_is_reused_and_counted_in_search_budget(admin, api, database, settings, seeded):
    from app.services.reference_business_identity import load_business_identity
    from app.services.reference_context_loader import load_search_context
    from app.services.reference_search_admission import admit_provider_search

    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    worker = Database(settings, correlator=True)
    try:
        event = await event_for(admin, t, b, a)
        assert (
            await BusinessGeocodingRunner(
                worker,
                settings,
                transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"results": [result()]})),
            ).run(event)
            == "resolved"
        )
        own = await BusinessAddressService(database).read(t, b, a)
        scope = {
            "scope": "local",
            "radius_km": 5,
            "origin": {"method": "manual", "address": own.address.model_dump(mode="json", exclude_none=True)},
        }
        assert (await save_scope(api, base, headers, 1, scope)).status_code == 200
        search = await admit_provider_search(
            database, settings.reference_provider_hmac_key, "test-v1", t, b, a, uuid4(), 2, 5
        )
        loaded = await load_search_context(
            worker, {"test-v1": settings.reference_provider_hmac_key}, t, b, a, search.search_id, search.event_id
        )
        assert loaded.latitude == -23.5 and loaded.longitude == -46.6
        identity = await load_business_identity(
            worker, {"test-v1": settings.reference_provider_hmac_key}, t, b, a, search.search_id
        )
        assert identity.name == "Test" and identity.address == own.address
        from app.services.reference_business_identity_mac import BusinessIdentityBindingError

        for keys in ({}, {"test-v1": SecretStr("wrong-reference-key-0123456789abcdef")}):
            with pytest.raises(BusinessIdentityBindingError, match="REFERENCE_BUSINESS_IDENTITY_INVALID"):
                await load_business_identity(worker, keys, t, b, a, search.search_id)
        assert "Flores" not in repr(identity)
        async with admin.begin() as conn:
            await conn.execute(text("SET LOCAL ROLE meu_braco_direito_reference_ledger"))
            await conn.execute(
                text("SELECT set_config('app.tenant_id',:tenant,true),set_config('app.actor_id',:actor,true)"),
                {"tenant": str(t), "actor": str(a)},
            )
            usage = (
                await conn.execute(
                    text("SELECT * FROM public.reference_search_cost_usage(:business,:search,'google')"),
                    {"business": b, "search": search.search_id},
                )
            ).one()
            assert usage.total_used == 10 and usage.provider_used == 10
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE businesses SET name='Renamed' WHERE id=:b"), {"b": b})
        from sqlalchemy.exc import DBAPIError

        with pytest.raises(DBAPIError, match="REFERENCE_BUSINESS_IDENTITY_STALE"):
            await load_business_identity(
                worker, {"test-v1": settings.reference_provider_hmac_key}, t, b, a, search.search_id
            )
    finally:
        await worker.close()


async def test_geocode_outbox_runs_temporal_with_identifier_only_payload(
    admin, api, database, settings, seeded, relay_database
):
    import os

    from temporalio.client import Client
    from temporalio.worker import Worker

    from app.services.outbox import dispatch_once
    from app.workflows.business_geocoding import BusinessGeocodingWorkflow
    from app.workflows.business_geocoding_activities import BusinessGeocodingActivities

    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    await BusinessGeocodingService(database, settings).request(
        t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1)
    )
    event = await event_for(admin, t, b, a)
    worker_db = Database(settings, correlator=True)
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    settings.temporal_task_queue = "address-geocode-" + uuid4().hex
    activities = BusinessGeocodingActivities(
        BusinessGeocodingRunner(
            worker_db,
            settings,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"results": [result()]})),
        )
    )
    try:
        async with Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[BusinessGeocodingWorkflow],
            activities=[activities.resolve],
        ):
            assert await dispatch_once(relay_database, client, settings, uuid4()) == 1
            handle = client.get_workflow_handle(f"business-geocoding/{t}/{event.event_id}")
            assert await handle.result() == "resolved"
            history = await handle.fetch_history()
            serialized = str(history)
            assert "Rua das Flores" not in serialized and "provider formatted" not in serialized
    finally:
        await worker_db.close()


async def test_geocode_configuration_context_and_conflicting_actor_errors_are_stable(
    admin, api, database, settings, seeded
):
    from app.tests.integration.test_business_address import payload, setup_shop

    t, b, a, base, headers = await setup(admin, api, database, settings, seeded)
    service = BusinessGeocodingService(database, settings)
    empty_t, empty, empty_a = await setup_shop(admin, {**seeded, "t1": seeded["t2"], "a1": seeded["a2"]})
    assert (await service.read(empty_t, empty, empty_a)).address_version == 0
    await BusinessAddressService(database).save(empty_t, empty, empty_a, payload())
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_CONTEXT_REQUIRED"):
        await service.request(empty_t, empty, empty_a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    pilot = settings.reference_provider_pilot_id
    settings.reference_provider_pilot_id = uuid4()
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_GEOCODE_UNAVAILABLE"):
        await service.request(t, b, a, GeocodeRequest(operation_id=uuid4(), address_version=1))
    settings.reference_provider_pilot_id = pilot
    request = GeocodeRequest(operation_id=uuid4(), address_version=1)
    await service.request(t, b, a, request)
    second = seeded["a2"]
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": t, "actor": second},
        )
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_OPERATION_CONFLICT"):
        await service.request(t, b, second, request)
    worker = Database(settings, correlator=True)
    settings.reference_geocoding_enabled = False
    try:
        with pytest.raises(GeocodingError, match="GEOCODING_DISABLED"):
            await BusinessGeocodingRunner(worker, settings).run(await event_for(admin, t, b, a))
    finally:
        await worker.close()
