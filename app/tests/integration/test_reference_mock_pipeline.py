"""End-to-end fixture-only pipeline, using the restricted cost ledger."""

import asyncio
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services import reference_mock_pipeline as pipeline
from app.tests.integration.test_reference_jev_budget_guard import _body
from app.tests.integration.test_reference_places_budget_guard import _intent, _pilot

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def allow_draft_only_for_isolated_test(admin):
    writer = (
        "public.reference_filtered_commit_with_similarity("
        "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb,jsonb)"
    )
    reader = "public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid)"
    async with admin.begin() as connection:
        for signature in (writer, reader):
            assert not await connection.scalar(
                text("SELECT has_function_privilege('meu_braco_direito_correlator',:sig,'EXECUTE')"), {"sig": signature}
            )
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {signature} TO meu_braco_direito_correlator"))
    try:
        yield
    finally:
        async with admin.begin() as connection:
            for signature in (writer, reader):
                await connection.execute(
                    text(f"REVOKE EXECUTE ON FUNCTION {signature} FROM meu_braco_direito_correlator")
                )


async def _setup(admin, api, seeded, settings):
    pilot, tariff = await _pilot(admin)
    context = await _intent(admin, api, settings, seeded["t1"], seeded["a1"], pilot, tariff, max_results=20)
    jev_tariff = "jev-test-" + uuid4().hex
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:v,'jev','jev-model:jev-test-model',1,true)"""),
            {"v": jev_tariff},
        )
    inputs = pipeline.MockPipelineInput(
        google=context,
        context_version=1,
        place_type="restaurant",
        latitude=1,
        longitude=1,
        radius_km=5,
        business_terms=("cafe",),
        business_description="private business",
        google_key=SecretStr("synthetic-key"),
        jev_key=SecretStr("synthetic-jev-key"),
        jev_model="jev-test-model",
        jev_tariff_version=jev_tariff,
        jev_credential_version="test-jev-project",
        jev_reserved_usd_micros=40,
    )
    # Shared fixture predates the exact request-event link required by recovery.
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_provider_effects SET request_event_id=:event WHERE id=:effect"),
            {"event": context.event, "effect": context.effect},
        )
    return inputs, Database(settings, correlator=True)


def _transports(calls):
    def google(request):
        calls.append("google")
        assert json.loads(request.content)["maxResultCount"] == 20
        return httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "fixture-place",
                        "displayName": {"text": "private name"},
                        "rating": 4.8,
                        "userRatingCount": 200,
                        "types": ["cafe"],
                    }
                ]
            },
        )

    def jev(request):
        calls.append("jev")
        result = _body()
        result["answers"]["level_0"] = {
            "type": "choice",
            "choice": "high",
            "probabilities": {"high": 0.7, "medium": 0.1, "low": 0.1, "unknown": 0.1},
        }
        return httpx.Response(200, json=result)

    return httpx.MockTransport(google), httpx.MockTransport(jev)


@pytest.mark.parametrize("lose_ack", [False, True])
async def test_pipeline_commits_sanitized_batch_and_recovers_without_resending(
    admin, api, seeded, settings, monkeypatch, lose_ack
):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []
    google, jev = _transports(calls)
    if lose_ack:
        original = pipeline.commit_leveled_batch

        async def lost(*args, **kwargs):
            await original(*args, **kwargs)
            raise ConnectionError("private details")

        monkeypatch.setattr(pipeline, "commit_leveled_batch", lost)
    try:
        result = await pipeline.run_mock_reference_pipeline(worker, inputs, google_transport=google, jev_transport=jev)
        replay = await pipeline.run_mock_reference_pipeline(worker, inputs, google_transport=google, jev_transport=jev)
        assert result == replay and result.state == "filtered" and result.batch_id is not None
        assert calls == ["google", "jev"]
        for changed in (
            replace(inputs, latitude=2),
            replace(inputs, google_key=SecretStr("different-key")),
            replace(inputs, google=replace(inputs.google, context_version=2)),
        ):
            with pytest.raises(pipeline.ReferenceMockPipelineError):
                await pipeline.run_mock_reference_pipeline(worker, changed, google_transport=google, jev_transport=jev)
        assert calls == ["google", "jev"]
        async with admin.connect() as connection:
            rows = (
                await connection.execute(
                    text("SELECT place_id,reputation_score FROM reference_filtered_batch_candidates")
                )
            ).all()
            assert len(rows) == 1 and rows[0].place_id == "fixture-place" and rows[0].reputation_score > 0
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
            events = (await connection.execute(text("SELECT payload FROM outbox_events"))).scalars().all()
            serialized = json.dumps(events)
            assert "private name" not in serialized and "private business" not in serialized
            assert "synthetic-key" not in serialized and "fixture-place" not in serialized
    finally:
        await worker.close()


async def test_pipeline_jev_timeout_keeps_cost_and_does_not_retry(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []
    google, _ = _transports(calls)

    def failure(request):
        calls.append("jev")
        raise httpx.ReadTimeout("private details", request=request)

    jev = httpx.MockTransport(failure)
    try:
        for _ in range(2):
            with pytest.raises(pipeline.ReferenceMockPipelineError, match="REFERENCE_MOCK_PIPELINE_INCOMPLETE"):
                await pipeline.run_mock_reference_pipeline(worker, inputs, google_transport=google, jev_transport=jev)
        assert calls == ["google", "jev"]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE state='uncertain'"))
                == 2
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
    finally:
        await worker.close()


async def test_concurrent_pipeline_claim_never_sends_twice(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []
    google, jev = _transports(calls)
    try:

        async def run():
            try:
                return await pipeline.run_mock_reference_pipeline(
                    worker, inputs, google_transport=google, jev_transport=jev
                )
            except pipeline.ReferenceMockPipelineError:
                return None

        results = await asyncio.gather(run(), run())
        assert any(result is not None and result.state == "filtered" for result in results)
        assert calls == ["google", "jev"]
        assert (await run()).state == "filtered"
    finally:
        await worker.close()


async def test_missing_similarity_evidence_never_fabricates_jev_fence(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []

    def google(request):
        calls.append("google")
        return httpx.Response(200, json={"places": [{"id": "fixture-place", "rating": 4, "userRatingCount": 10}]})

    def jev(request):
        pytest.fail("no candidate can be evaluated")

    try:
        with pytest.raises(pipeline.ReferenceMockPipelineError, match="REFERENCE_MOCK_PIPELINE_INCOMPLETE"):
            await pipeline.run_mock_reference_pipeline(
                worker, inputs, google_transport=httpx.MockTransport(google), jev_transport=httpx.MockTransport(jev)
            )
        assert calls == ["google"]
        async with admin.connect() as connection:
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='jev'"))
                == 0
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 60
    finally:
        await worker.close()


async def test_empty_google_result_recovers_without_jev(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []

    def google(request):
        calls.append("google")
        return httpx.Response(200, json={"places": []})

    def jev(request):
        pytest.fail("empty Google result does not call Jev")

    try:
        for _ in range(2):
            result = await pipeline.run_mock_reference_pipeline(
                worker, inputs, google_transport=httpx.MockTransport(google), jev_transport=httpx.MockTransport(jev)
            )
            assert result.state == "empty" and result.batch_id is None
        assert calls == ["google"]
    finally:
        await worker.close()


async def test_recovery_only_exposes_own_result_to_worker(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    app = Database(settings)
    calls = []
    google, jev = _transports(calls)
    statement = text("SELECT public.reference_filtered_recovery(:business,:search,:effect,:event)")
    params = {
        "business": inputs.google.business,
        "search": inputs.google.search,
        "effect": inputs.google.effect,
        "event": inputs.google.event,
    }
    try:
        result = await pipeline.run_mock_reference_pipeline(worker, inputs, google_transport=google, jev_transport=jev)
        async with worker.transaction(inputs.google.tenant, inputs.google.actor) as session:
            recovered = await session.scalar(statement, params)
            assert recovered == {"state": "filtered", "batch_id": str(result.batch_id)}
        for context, values in (
            ((inputs.google.tenant, seeded["a2"]), params),
            ((inputs.google.tenant, inputs.google.actor), {**params, "event": uuid4()}),
        ):
            with pytest.raises(DBAPIError):
                async with worker.transaction(*context) as session:
                    await session.scalar(statement, values)
        with pytest.raises(DBAPIError):
            async with app.transaction(inputs.google.tenant, inputs.google.actor) as session:
                await session.scalar(statement, params)
    finally:
        await worker.close()
        await app.close()


async def test_unknown_similarity_is_stored_but_not_ranked_or_requeried(admin, api, seeded, settings):
    inputs, worker = await _setup(admin, api, seeded, settings)
    calls = []
    google, _ = _transports(calls)

    def jev(request):
        calls.append("jev")
        result = _body()
        result["answers"]["level_0"] = {
            "type": "choice",
            "choice": "unknown",
            "probabilities": {"high": 0.1, "medium": 0.1, "low": 0.1, "unknown": 0.7},
        }
        return httpx.Response(200, json=result)

    try:
        result = await pipeline.run_mock_reference_pipeline(
            worker, inputs, google_transport=google, jev_transport=httpx.MockTransport(jev)
        )
        replay = await pipeline.run_mock_reference_pipeline(
            worker, inputs, google_transport=google, jev_transport=httpx.MockTransport(jev)
        )
        assert result == replay and result.state == "filtered"
        assert calls == ["google", "jev"]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batch_candidates")) == 0
            row = (
                await connection.execute(
                    text("SELECT judgment,similarity_level FROM reference_similarity_snapshot_items")
                )
            ).one()
            assert tuple(row) == ("match", "unknown")
    finally:
        await worker.close()
