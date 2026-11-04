"""Mock-only Jev claims linked to a live, budgeted Places executor."""

import asyncio
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.google_places import GooglePlacesNearby
from app.adapters.jev_reference_similarity import (
    JevReferenceSimilarity,
    SimilarityCandidate,
    SimilarityError,
    SimilarityInput,
)
from app.db.session import Database
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard, JevGuardContext, JevGuardStateError
from app.services.reference_jev_intent import JevIntentError, create_jev_intent, jev_effect_id
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot

pytestmark = pytest.mark.integration


class _Capture:
    def __init__(self):
        self.request = None

    async def claim(self, operation, request):
        self.request = request
        return False

    async def uncertain(self):
        raise AssertionError("no effect was admitted")


async def _jev_intent(admin, worker, parent, parent_token, similarity_input, *, amount=40, create=True):
    effect, event, tariff = jev_effect_id(parent.effect), uuid4(), "jev-test-" + uuid4().hex
    capture = _Capture()
    with pytest.raises(SimilarityError, match="SIMILARITY_BUDGET_UNAVAILABLE"):
        await JevReferenceSimilarity(
            SecretStr("synthetic-jev-key"),
            "jev-test-model",
            capture,
            enabled=True,
            transport=httpx.MockTransport(lambda _: pytest.fail("effect before claim")),
        ).classify(similarity_input, effect)
    request = capture.request
    context = JevGuardContext(
        tenant=parent.tenant,
        business=parent.business,
        actor=parent.actor,
        search=parent.search,
        effect=effect,
        pilot=parent.pilot,
        event=event,
        key=parent.key,
        key_version=parent.key_version,
        tariff_version=tariff,
        credential_version="synthetic-jev-project",
        reserved_usd_micros=amount,
        parent_google_effect=parent.effect,
        parent_executor_token=parent_token,
        source_batch_mac="a" * 64,
        context_version=1,
    )
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
              (version,provider,field_mask,minimum_reserved_usd_micros,active)
              VALUES(:version,'jev','jev-model:jev-test-model',1,true)"""),
            {"version": tariff},
        )
    if create:
        context = await create_jev_intent(worker, context, parent.event, request)
    return context, request


async def _google_started(admin, api, seeded, settings, *, cap=100):
    pilot, tariff = await _pilot(admin, cap=cap)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff)
    worker = Database(settings, correlator=True)
    guard = DatabasePlacesBudgetGuard(worker, context)
    provider = GooglePlacesNearby(
        SecretStr("synthetic-key"),
        guard,
        enabled=True,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"places": [{"id": "fixture-place", "displayName": {"text": "fake"}}]})
        ),
    )
    await provider.search("restaurant", 1, 1, 5, context.effect)
    return context, guard, worker


def _body():
    return {
        "model": "jev-test-model",
        "usage": {"input_tokens": 5, "output_tokens": 0},
        "answers": {
            "candidate_0": {
                "type": "choice",
                "choice": "match",
                "confidence": 0.9,
                "probabilities": {"match": 0.9, "no_match": 0.05, "uncertain": 0.05},
            }
        },
    }


async def test_intent_is_fenced_atomic_idempotent_and_contains_no_raw_input(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "private fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data, create=False)
    try:
        for bad, event in (
            (replace(context, parent_executor_token=uuid4()), parent.event),
            (context, uuid4()),
            (replace(context, context_version=2), parent.event),
        ):
            with pytest.raises(DBAPIError):
                await create_jev_intent(worker, bad, event, request)
        with pytest.raises(JevIntentError, match="JEV_EFFECT_ID_INVALID"):
            await create_jev_intent(worker, replace(context, effect=uuid4()), parent.event, request)
        first = await create_jev_intent(worker, context, parent.event, request)
        replay = await create_jev_intent(worker, replace(context, event=uuid4()), parent.event, request)
        assert replay.event == first.event == context.event
        for bad in (
            replace(context, source_batch_mac="b" * 64),
            replace(context, reserved_usd_micros=context.reserved_usd_micros + 1),
        ):
            with pytest.raises(DBAPIError):
                await create_jev_intent(worker, bad, parent.event, request)
        async with admin.connect() as connection:
            parent_batch = await connection.scalar(
                text("SELECT source_batch_mac FROM reference_provider_effects WHERE id=:id"), {"id": parent.effect}
            )
            assert parent_batch == context.source_batch_mac
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.jev_intent_created'")
                )
                == 1
            )
            payload = await connection.scalar(
                text("SELECT payload::text FROM outbox_events WHERE id=:id"), {"id": context.event}
            )
            assert "private fixture" not in payload and "synthetic-jev-key" not in payload
    finally:
        await worker.close()


async def test_intent_rejects_revoked_owner_before_creation_but_allows_replay(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data, create=False)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await create_jev_intent(worker, context, parent.event, request)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        await create_jev_intent(worker, context, parent.event, request)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": context.tenant, "actor": context.actor},
            )
        assert (await create_jev_intent(worker, context, parent.event, request)).event == context.event
    finally:
        await worker.close()


async def test_concurrent_intent_creation_converges_on_one_event(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data, create=False)
    try:
        outcomes = await asyncio.gather(
            create_jev_intent(worker, context, parent.event, request),
            create_jev_intent(worker, replace(context, event=uuid4()), parent.event, request),
        )
        assert outcomes[0].event == outcomes[1].event
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.jev_intent_created'")
                )
                == 1
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='jev'"))
                == 1
            )
    finally:
        await worker.close()


@pytest.mark.parametrize("failure", ["parent", "tariff", "search"])
async def test_intent_failure_is_atomic_and_parent_remains_unbound(admin, api, seeded, settings, failure):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data, create=False)
    try:
        if failure == "parent":
            await google.uncertain()
        else:
            statement, params = (
                ("UPDATE reference_provider_tariffs SET active=false WHERE version=:value", context.tariff_version)
                if failure == "tariff"
                else ("UPDATE reference_provider_searches SET state='stale' WHERE id=:value", context.search)
            )
            async with admin.begin() as connection:
                await connection.execute(text(statement), {"value": params})
        with pytest.raises(DBAPIError):
            await create_jev_intent(worker, context, parent.event, request)
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT source_batch_mac FROM reference_provider_effects WHERE id=:id"), {"id": parent.effect}
                )
                is None
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='jev'"))
                == 0
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM outbox_events WHERE id=:id"), {"id": context.event})
                == 0
            )
    finally:
        await worker.close()


async def test_parent_batch_tampering_cannot_admit_jev_and_worker_cannot_change_it(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    try:
        with pytest.raises(DBAPIError):
            async with worker.transaction(context.tenant, context.actor) as session:
                await session.execute(
                    text("UPDATE reference_provider_effects SET source_batch_mac=:mac WHERE id=:id"),
                    {"id": parent.effect, "mac": "b" * 64},
                )
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_effects SET source_batch_mac=:mac WHERE id=:id"),
                {"id": parent.effect, "mac": "b" * 64},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_JEV_PARENT_INVALID"):
            await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()


async def test_mock_jev_claim_is_fenced_to_google_and_shares_pilot_budget(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fake place", ("cafe",)),))
    context, _ = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    jev = DatabaseJevBudgetGuard(worker, context)
    calls = []

    def reply(request):
        calls.append(json.loads(request.content)["model"])
        return httpx.Response(200, json=_body())

    try:
        result = await JevReferenceSimilarity(
            SecretStr("synthetic-jev-key"), "jev-test-model", jev, enabled=True, transport=httpx.MockTransport(reply)
        ).classify(input_data, context.effect)
        assert result.judgments[0].choice == "match" and calls == ["jev-test-model"]
        assert jev.execution_token() != google.execution_token()
        replay = DatabaseJevBudgetGuard(worker, context)
        with pytest.raises(SimilarityError, match="SIMILARITY_BUDGET_UNAVAILABLE"):
            await JevReferenceSimilarity(
                SecretStr("synthetic-jev-key"),
                "jev-test-model",
                replay,
                enabled=True,
                transport=httpx.MockTransport(lambda _: pytest.fail("duplicate effect")),
            ).classify(input_data, context.effect)
        with pytest.raises(JevGuardStateError, match="JEV_EXECUTOR_NOT_CLAIMED"):
            replay.execution_token()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 2
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE state='running'"))
                == 2
            )
    finally:
        await worker.close()


async def test_jev_claim_rejects_wrong_parent_fence_batch_context_and_key(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fake place", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    try:
        for changes in (
            {"parent_executor_token": uuid4()},
            {"source_batch_mac": "b" * 64},
            {"context_version": 2},
            {"parent_google_effect": uuid4()},
            {"credential_version": "other-project"},
        ):
            bad = replace(context, **changes)
            with pytest.raises(DBAPIError):
                await DatabaseJevBudgetGuard(worker, bad).claim(bad.effect, request)
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_INTENT_INVALID"):
            await DatabaseJevBudgetGuard(worker, context).claim(
                context.effect, replace(request, credential=SecretStr("different-synthetic-jev-key"))
            )
        guard = DatabaseJevBudgetGuard(worker, context)
        assert await guard.claim(uuid4(), request) is False
        with pytest.raises(JevGuardStateError, match="JEV_EXECUTOR_NOT_CLAIMED"):
            await guard.uncertain()
        async with worker.transaction(context.tenant, context.actor) as session:
            # The generic entry point cannot bypass the Jev parent checks.
            with pytest.raises(DBAPIError):
                await session.scalar(
                    text("""SELECT public.reference_provider_claim(
                  NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)""")
                )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()


async def test_uncertain_parent_blocks_new_jev_effect(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fake place", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    try:
        await google.uncertain()
        with pytest.raises(DBAPIError, match="REFERENCE_JEV_PARENT_INVALID"):
            await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
    finally:
        await worker.close()


async def test_shared_pilot_budget_rejects_jev_after_google_reservation(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings, cap=99)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fake place", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_PILOT_BUDGET_EXCEEDED"):
            await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
    finally:
        await worker.close()


async def test_uncertain_jev_is_not_retried_and_retains_both_reservations(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fake place", ("cafe",)),))
    context, _ = await _jev_intent(admin, worker, parent, google.execution_token(), input_data)
    guard = DatabaseJevBudgetGuard(worker, context)

    def timeout(request):
        raise httpx.ReadTimeout("private input detail", request=request)

    try:
        with pytest.raises(SimilarityError, match="SIMILARITY_RESULT_UNCERTAIN") as error:
            await JevReferenceSimilarity(
                SecretStr("synthetic-jev-key"),
                "jev-test-model",
                guard,
                enabled=True,
                transport=httpx.MockTransport(timeout),
            ).classify(input_data, context.effect)
        assert "private input detail" not in str(error.value)
        await guard.uncertain()
        with pytest.raises(SimilarityError, match="SIMILARITY_BUDGET_UNAVAILABLE"):
            await JevReferenceSimilarity(
                SecretStr("synthetic-jev-key"),
                "jev-test-model",
                DatabaseJevBudgetGuard(worker, context),
                enabled=True,
                transport=httpx.MockTransport(lambda _: pytest.fail("duplicate effect")),
            ).classify(input_data, context.effect)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_provider_effects WHERE id=:id"), {"id": context.effect}
                )
                == "uncertain"
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 2
    finally:
        await worker.close()
