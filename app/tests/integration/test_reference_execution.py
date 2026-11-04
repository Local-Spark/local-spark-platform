"""Real restricted admission/claims with synthetic transports and no supplier IO."""

from uuid import uuid4, uuid5

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_primary_place_types import JevPrimaryPlaceTypeMapper
from app.db.session import Database
from app.services.reference_execution_store import load_execution, record_output
from app.services.reference_search_admission import admit_provider_search
from app.services.reference_stage_guards import JevStageGuard, StageContext
from app.tests.integration.test_reference_places_budget_guard import _pilot
from app.tests.integration.test_reference_search_admission import _KEY, _business
from app.tests.unit.test_jev_primary_place_types import body

pytestmark = pytest.mark.integration


async def setup_mapping(admin, api, seeded, settings, database):
    tenant, actor, business, _, _ = await _business(admin, api, seeded, settings)
    pilot, _ = await _pilot(admin, cap=1000)
    admitted = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    tariff = "mapping-" + uuid4().hex
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:v,'jev','jev-model:jev-test-model',1,true)"""),
            {"v": tariff},
        )
    worker = Database(settings, correlator=True)
    state = await load_execution(worker, tenant, business, actor, admitted.search_id, admitted.event_id)
    effect = uuid5(admitted.search_id, "reference-jev-mapping-v1")
    context = StageContext(
        tenant,
        business,
        actor,
        admitted.search_id,
        effect,
        uuid5(effect, "request-event"),
        pilot,
        1,
        _KEY,
        "test-v1",
        tariff,
        "test-project",
        30,
        state.request_mac,
    )
    return worker, context, admitted


async def test_mapping_reserves_before_http_and_recovers_only_own_projection(admin, api, seeded, settings, database):
    worker, c, admitted = await setup_mapping(admin, api, seeded, settings, database)
    calls = []

    async def handler(request):
        calls.append(1)
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM reference_cost_reservations WHERE effect_id=:e"), {"e": c.effect}
                )
                == 1
            )
        return httpx.Response(200, json=body())

    guard = JevStageGuard(worker, c, "mapping")
    try:
        result = await JevPrimaryPlaceTypeMapper(
            _KEY, "jev-test-model", guard, enabled=True, transport=httpx.MockTransport(handler)
        ).map(("cafeteria",), None, c.effect)
        assert result.types == ("coffee_shop",)
        output = {"state": result.state, "types": list(result.types), "taxonomy_version": result.taxonomy_version}
        await record_output(worker, c.tenant, c.business, c.actor, c.effect, guard.execution_token(), "mapping", output)
        await record_output(worker, c.tenant, c.business, c.actor, c.effect, guard.execution_token(), "mapping", output)
        state = await load_execution(worker, c.tenant, c.business, c.actor, c.search, admitted.event_id)
        assert state.effect("jev", "mapping").output == output
        assert state.effect("jev", "mapping").state == "completed_filtered"
        assert calls == [1]
        with pytest.raises(DBAPIError, match="REFERENCE_OUTPUT_CONFLICT"):
            await record_output(
                worker,
                c.tenant,
                c.business,
                c.actor,
                c.effect,
                guard.execution_token(),
                "mapping",
                {**output, "types": ["bakery"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_OUTPUT_INVALID"):
            await record_output(worker, c.tenant, c.business, c.actor, c.effect, uuid4(), "mapping", output)
        with pytest.raises(DBAPIError):
            await load_execution(database, c.tenant, c.business, c.actor, c.search, admitted.event_id)
        with pytest.raises(DBAPIError):
            await load_execution(worker, seeded["t2"], c.business, seeded["a2"], c.search, admitted.event_id)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_provider_outputs")) == 1
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.provider_output_recorded'")
                )
                == 1
            )
            assert (
                await conn.scalar(
                    text("SELECT actual_usd_micros FROM reference_cost_reservations WHERE effect_id=:e"),
                    {"e": c.effect},
                )
                is None
            )
    finally:
        await worker.close()


@pytest.mark.usefixtures("historical_filtered_writer")
@pytest.mark.parametrize("actual", [None, 0, 7])
async def test_terminal_failure_allows_new_attempt_without_releasing_unknown_cost(admin, api, seeded, settings, actual):
    from uuid import UUID

    from app.adapters.apify_place_contacts import SubmittedPlaceContacts
    from app.services.reference_contacts_budget_guard import ContactsGuardContext
    from app.services.reference_contacts_runs import record_contacts_cost, record_contacts_run
    from app.tests.integration.test_reference_contacts_guard import _call, _revoke, _setup
    from app.tests.integration.test_reference_contacts_retry import _revoke_proof, _second

    google, worker, cycle, batch, candidate, p = await _setup(admin, api, seeded, settings)
    c = ContactsGuardContext(
        google.tenant,
        google.business,
        google.actor,
        cycle,
        batch["batch"],
        candidate,
        "fake-place",
        p["lookup"],
        p["effect"],
        p["event"],
        google.pilot,
        1,
        google.key,
        p["key"],
        p["tariff"],
        p["credential"],
        40,
        "1.2.3",
        "actor-id",
    )
    try:
        started = await _call(worker, google, p)
        token = UUID(started["executor_token"])
        run = SubmittedPlaceContacts(
            c.effect,
            c.place_id,
            "run-id",
            "dataset-id",
            "store-id",
            "queue-id",
            "build-id",
            c.build,
            c.provider_actor_id,
        )
        await record_contacts_run(worker, c, token, run)
        if actual is not None:
            await record_contacts_cost(worker, c, token, run, actual)
        second = await _second(admin, google, p)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)

        async def fail(status="FAILED", executor=token):
            async with worker.transaction(c.tenant, c.actor) as session:
                await session.scalar(
                    text("SELECT reference_contacts_terminal_failure(:business,:lookup,:effect,:token,:status)"),
                    {
                        "business": c.business,
                        "lookup": c.lookup,
                        "effect": c.effect,
                        "token": executor,
                        "status": status,
                    },
                )

        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_FAILURE_INVALID"):
            await fail("RUNNING")
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_FAILURE_INVALID"):
            await fail(executor=uuid4())
        await fail()
        await fail()
        assert (await _call(worker, google, second))["created"] is True
        async with admin.connect() as conn:
            reserved = await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots"))
            assert reserved == 140 + (40 if actual is None else actual)
            state = await conn.scalar(
                text("SELECT state FROM reference_cost_reservations WHERE effect_id=:e"), {"e": c.effect}
            )
            assert state == ("uncertain" if actual is None else "completed")
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM reference_contacts_failure_proofs WHERE reason='terminal_failed'")
                )
                == 1
            )
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)


async def test_retry_request_is_shared_owner_scoped_idempotent_and_keeps_source_identity(
    admin, api, seeded, settings, database
):

    worker, c, admitted = await setup_mapping(admin, api, seeded, settings, database)
    try:
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE reference_provider_searches SET execution_status='contacts_failed' WHERE id=:s"),
                {"s": c.search},
            )
            await conn.execute(
                text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:t,:a,'owner')"),
                {"t": c.tenant, "a": seeded["a2"]},
            )

        async def retry(actor, operation):
            async with database.transaction(c.tenant, actor) as session:
                return await session.scalar(
                    text("SELECT reference_request_execution_retry(:b,:s,:o)"),
                    {"b": c.business, "s": c.search, "o": operation},
                )

        operation = uuid4()
        first = await retry(seeded["a2"], operation)
        assert first == await retry(seeded["a2"], operation)
        assert first == {"search_id": str(c.search), "state": "pending"}
        with pytest.raises(DBAPIError, match="REFERENCE_RETRY_REQUEST_CONFLICT"):
            await retry(c.actor, operation)
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await retry(seeded["viewer"], uuid4())
        async with admin.connect() as conn:
            payload = await conn.scalar(
                text("SELECT payload FROM outbox_events WHERE event_type='reference.provider_retry_requested'")
            )
            assert payload["actor_id"] == str(c.actor)
            assert await conn.scalar(text("SELECT actor_id FROM reference_execution_retry_operations")) == seeded["a2"]
    finally:
        await worker.close()


async def runtime_case(admin, api, seeded, settings, database):
    from pydantic import SecretStr

    from app.schemas.reference_execution import ReferenceSearchStart
    from app.services.reference_search_start import ReferenceSearchStartService
    from app.tests.integration.test_reference_cost_accounting import _policy
    from app.workflows.contracts import BusinessEvent

    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    pilot, google_tariff = await _pilot(admin, cap=5_000_000)
    await _policy(admin, search=5_000_000, monthly=5_000_000, search_provider=5_000_000, monthly_provider=5_000_000)
    jev_tariff, apify_tariff = "jev-runtime-" + uuid4().hex, "apify-runtime-" + uuid4().hex
    async with admin.begin() as conn:
        for version, provider, charge in (
            (jev_tariff, "jev", "jev-model:jev-test-model"),
            (apify_tariff, "apify", "apify-place-contacts:1.2.3"),
        ):
            await conn.execute(
                text(
                    "INSERT INTO reference_provider_tariffs "
                    "(version,provider,field_mask,minimum_reserved_usd_micros,active) VALUES(:v,:p,:c,1,true)"
                ),
                {"v": version, "p": provider, "c": charge},
            )
    values = {
        "reference_discovery_execution_enabled": True,
        "reference_google_api_key": SecretStr("synthetic-google"),
        "reference_provider_hmac_key": _KEY,
        "reference_provider_key_version": "test-v1",
        "reference_google_credential_version": "google-v1",
        "reference_provider_pilot_id": pilot,
        "reference_google_tariff_version": google_tariff,
        "reference_google_reserved_usd_micros": 10,
        "typesafe_api_key": SecretStr("synthetic-jev"),
        "intent_ai_model": "jev-test-model",
        "reference_jev_tariff_version": jev_tariff,
        "reference_jev_credential_version": "jev-v1",
        "reference_jev_reserved_usd_micros": 10,
        "reference_apify_api_token": SecretStr("synthetic-apify"),
        "reference_apify_actor_id": "nwua9Gu5YrADL7ZDj",
        "reference_apify_actor_build": "1.2.3",
        "reference_apify_tariff_version": apify_tariff,
        "reference_apify_credential_version": "apify-v1",
        "reference_apify_reserved_usd_micros": 500_000,
    }
    for key, value in values.items():
        setattr(settings, key, value)
    operation = uuid4()
    admitted = await ReferenceSearchStartService(database, settings).start(
        tenant, business, actor, ReferenceSearchStart(operation_id=operation)
    )
    async with admin.connect() as conn:
        event_id = await conn.scalar(
            text("SELECT request_event_id FROM reference_provider_searches WHERE id=:s"), {"s": admitted.search_id}
        )
    event = BusinessEvent(str(event_id), str(tenant), str(business), str(actor), str(operation))
    return event, admitted, base, headers


def runtime_transports(calls, *, pending_once=False, terminal_once=False):
    import json

    from app.tests.unit.test_apify_place_contacts import metadata, pricing_payload
    from app.tests.unit.test_jev_primary_place_types import body as mapping_body
    from app.tests.unit.test_jev_reference_recommendations import answer as recommendation
    from app.tests.unit.test_jev_reference_similarity_levels import candidate as judgment
    from app.tests.unit.test_jev_reference_similarity_levels import level

    polls = 0

    def google(request):
        calls.append("google")
        assert json.loads(request.content)["includedPrimaryTypes"] == ["coffee_shop"]
        return httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "ChIJfixture",
                        "displayName": {"text": "Ephemeral bakery"},
                        "rating": 4.8,
                        "userRatingCount": 200,
                        "types": ["coffee_shop"],
                        "addressComponents": [
                            {"longText": "Avenida Distinta", "shortText": "Avenida Distinta", "types": ["route"]},
                            {"longText": "999", "shortText": "999", "types": ["street_number"]},
                            {"longText": "São Paulo", "shortText": "São Paulo", "types": ["locality"]},
                            {"longText": "São Paulo", "shortText": "SP", "types": ["administrative_area_level_1"]},
                            {"longText": "Brasil", "shortText": "BR", "types": ["country"]},
                        ],
                    }
                ]
            },
        )

    def jev(request):
        payload = json.loads(request.content)
        questions = payload["questions"]
        if "category" in questions:
            calls.append("mapping")
            result = mapping_body()
        elif "rank_1" in questions:
            calls.append("recommendation")
            result = recommendation(["candidate_0"], 1)
            assert payload["state"]["candidates"]["candidate_0"]["similarity_level"] == "high"
            assert payload["state"]["candidates"]["candidate_0"]["name"] is None
        else:
            calls.append("similarity")
            result = {
                "model": "jev-test",
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "answers": {"candidate_0": judgment(), "level_0": level()},
            }
        return httpx.Response(200, json=result)

    def apify(request):
        nonlocal polls
        path = request.url.path
        if path.endswith("/acts/nwua9Gu5YrADL7ZDj"):
            return httpx.Response(200, json=pricing_payload())
        if request.method == "POST":
            calls.append("apify-submit")
            return httpx.Response(
                201, json=metadata("READY", id="run-" + str(calls.count("apify-submit")), actId="nwua9Gu5YrADL7ZDj")
            )
        if "/actor-runs/" in path:
            polls += 1
            calls.append("apify-inspect")
            status = (
                "RUNNING" if pending_once and polls == 1 else "FAILED" if terminal_once and polls == 1 else "SUCCEEDED"
            )
            return httpx.Response(
                200, json=metadata(status, id=path.rsplit("/", 1)[1], actId="nwua9Gu5YrADL7ZDj", usageTotalUsd=0.000001)
            )
        calls.append("apify-dataset")
        return httpx.Response(
            200, json=[{"placeId": "ChIJfixture", "instagrams": ["https://www.instagram.com/fixture.cafe/"]}]
        )

    return httpx.MockTransport(google), httpx.MockTransport(jev), httpx.MockTransport(apify)


@pytest.mark.parametrize("pending_once,terminal_once", [(False, False), (True, False), (False, True)])
async def test_complete_runtime_reuses_outputs_and_runs_before_publishing(
    admin, api, seeded, settings, database, pending_once, terminal_once
):
    from app.services.reference_provider_execution import ReferenceProviderExecution

    event, admitted, base, headers = await runtime_case(admin, api, seeded, settings, database)
    worker = Database(settings, correlator=True)
    calls = []
    google, jev, apify = runtime_transports(calls, pending_once=pending_once, terminal_once=terminal_once)
    runner = ReferenceProviderExecution(
        worker, settings, google_transport=google, jev_transport=jev, apify_transport=apify
    )
    try:
        state = await runner.run(event)
        if pending_once or terminal_once:
            assert state == ("contacts_failed" if terminal_once else "contacts_pending")
            if terminal_once:
                requested = await api.post(
                    base + "/reference-results/searches/" + str(admitted.search_id) + "/retry",
                    headers=headers,
                    json={"operation_id": str(uuid4())},
                )
                assert requested.status_code == 200, requested.text
            state = await runner.run(event)
        assert state == "completed"
        assert await runner.run(event) == "completed"
        assert (
            calls.count("google")
            == calls.count("mapping")
            == calls.count("similarity")
            == calls.count("recommendation")
            == 1
        )
        assert calls.count("apify-submit") == (2 if terminal_once else 1)
        result = await api.get(base + "/reference-results", headers=headers)
        assert result.status_code == 200, result.text
        search = result.json()["searches"][0]
        assert search["published"] and search["execution_status"] == "completed"
        candidate = search["candidates"][0]
        assert candidate["instagram_handle"] == "fixture.cafe" and candidate["jev_recommendation_rank"] == 1
        async with admin.connect() as conn:
            for table in (
                "reference_provider_outputs",
                "reference_filtered_batch_candidates",
                "reference_similarity_snapshot_items",
            ):
                serialized = await conn.scalar(text(f"SELECT jsonb_agg(to_jsonb(t))::text FROM {table} t"))
                assert (
                    "Ephemeral bakery" not in serialized
                    and "userRatingCount" not in serialized
                    and "addressComponents" not in serialized
                )
    finally:
        await worker.close()


async def test_unmapped_segment_releases_radius_without_refunding_jev_or_calling_google(
    admin, api, seeded, settings, database
):
    from app.services.reference_provider_execution import ReferenceProviderExecution
    from app.tests.unit.test_jev_primary_place_types import body as mapping_body

    event, admitted, base, headers = await runtime_case(admin, api, seeded, settings, database)
    worker = Database(settings, correlator=True)
    calls = []

    def jev(_):
        calls.append("mapping")
        return httpx.Response(200, json=mapping_body(category="no_match"))

    forbidden = httpx.MockTransport(lambda _: pytest.fail("No provider other than mapping may run"))
    runner = ReferenceProviderExecution(
        worker, settings, google_transport=forbidden, jev_transport=httpx.MockTransport(jev), apify_transport=forbidden
    )
    try:
        assert await runner.run(event) == "type_mapping_unavailable"
        assert await runner.run(event) == "type_mapping_unavailable"
        assert calls == ["mapping"]
        snapshot = await api.get(base + "/reference-results", headers=headers)
        assert snapshot.status_code == 200, snapshot.text
        assert snapshot.json()["searches"][0]["execution_status"] == "type_mapping_unavailable"
        repeated = await api.post(
            base + "/reference-results/searches", headers=headers, json={"operation_id": str(uuid4())}
        )
        assert repeated.status_code == 200, repeated.text
        assert repeated.json()["search_id"] != str(admitted.search_id)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 10
            assert (
                await conn.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='google'")) == 0
            )
            assert (
                await conn.scalar(
                    text("SELECT radius_occupied FROM reference_provider_searches WHERE id=:s"),
                    {"s": admitted.search_id},
                )
                is False
            )
    finally:
        await worker.close()


async def test_all_empty_radii_advance_once_share_budget_and_allow_another_round(
    admin, api, seeded, settings, database
):
    from app.services.reference_provider_execution import ReferenceProviderExecution
    from app.tests.unit.test_jev_primary_place_types import body as mapping_body
    from app.workflows.contracts import BusinessEvent

    event, admitted, base, headers = await runtime_case(admin, api, seeded, settings, database)
    worker = Database(settings, correlator=True)
    radii = []

    def google(request):
        import json

        radii.append(json.loads(request.content)["locationRestriction"]["circle"]["radius"])
        return httpx.Response(200, json={"places": []})

    runner = ReferenceProviderExecution(
        worker,
        settings,
        google_transport=httpx.MockTransport(google),
        jev_transport=httpx.MockTransport(lambda _: httpx.Response(200, json=mapping_body())),
        apify_transport=httpx.MockTransport(lambda _: pytest.fail("Empty Google must not invoke Apify")),
    )
    try:
        for position in range(3):
            status = await runner.run(event)
            if position == 2:
                assert status == "completed"
                break
            assert status == "radius_successor"
            async with admin.connect() as conn:
                row = (
                    (
                        await conn.execute(
                            text("""SELECT id,request_event_id,operation_id,tenant_id,business_id,actor_id
                  FROM reference_provider_searches WHERE state='pending' AND execution_status='pending'
                  ORDER BY created_at DESC LIMIT 1""")
                        )
                    )
                    .mappings()
                    .one()
                )
            event = BusinessEvent(
                str(row["request_event_id"]),
                str(row["tenant_id"]),
                str(row["business_id"]),
                str(row["actor_id"]),
                str(row["operation_id"]),
            )
        assert radii == [5000, 20000, 50000]
        snapshot = await api.get(base + "/reference-results", headers=headers)
        assert snapshot.status_code == 200, snapshot.text
        data = snapshot.json()
        assert data["cycle_id"] is None and len(data["searches"]) == 3
        assert all(
            search["family_status"] == "empty_exhausted" and search["can_retry_family"] for search in data["searches"]
        )
        new = await api.post(base + "/reference-results/searches", headers=headers, json={"operation_id": str(uuid4())})
        assert new.status_code == 200, new.text
        assert new.json()["cycle_id"] != str(admitted.cycle_id)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 6
            assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()
