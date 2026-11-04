"""Canonical owner selection through real guards and only synthetic HTTP."""

import io
import json
from uuid import UUID, uuid4

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.services.reference_learning_execution import ReferenceLearningExecution
from app.tests.integration.test_reference_cost_accounting import _policy
from app.tests.integration.test_reference_learning import canonical_learning_fixture
from app.tests.integration.test_reference_places_budget_guard import _pilot
from app.tests.unit.test_reference_learning_wiring import configured

pytestmark = pytest.mark.integration


async def learning_settings(admin, settings):
    pilot, _ = await _pilot(admin, cap=1_000_000)
    await _policy(admin, search=1_000_000, monthly=1_000_000, search_provider=1_000_000, monthly_provider=1_000_000)
    feed_tariff, jev_tariff = "feed-" + uuid4().hex, "jev-" + uuid4().hex
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs
            (version,provider,field_mask,minimum_reserved_usd_micros,active)
            VALUES(:feed,'apify','apify-instagram-feed:1.2.3',1,true),
                  (:jev,'jev','jev-model:jev-test-model',1,true)"""),
            {"feed": feed_tariff, "jev": jev_tariff},
        )
    return configured(
        settings,
        correlator_database_url=settings.correlator_database_url,
        reference_provider_pilot_id=pilot,
        reference_provider_key_version="test-v1",
        reference_provider_hmac_key=SecretStr("synthetic-key-longer-than-32-bytes-for-feed"),
        reference_feed_tariff_version=feed_tariff,
        reference_jev_tariff_version=jev_tariff,
        intent_ai_model="jev-test-model",
    )


async def policy_version(connection, jev_limit):
    identity = uuid4()
    await connection.execute(
        text("""INSERT INTO reference_cost_policies(id,timezone,per_search,monthly_total)
            VALUES(:id,'UTC',1000000,1000000)"""),
        {"id": identity},
    )
    for provider in ("google", "apify", "jev"):
        await connection.execute(
            text("""INSERT INTO reference_cost_policy_providers(policy_id,provider,per_search,monthly_total)
                VALUES(:id,:provider,:limit,1000000)"""),
            {"id": identity, "provider": provider, "limit": jev_limit if provider == "jev" else 1000000},
        )
    await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=:id"), {"id": identity})


@pytest.mark.parametrize("pending_first,pause_for_budget", [(False, False), (True, False), (False, True)])
async def test_acceptance_collection_analysis_snapshot_and_next_window(
    admin, api, seeded, settings, database, pending_first, pause_for_budget
):
    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    settings = await learning_settings(admin, settings)
    calls = []
    pending = pending_first
    expected_status = "completed" if pause_for_budget else "partial"
    if pause_for_budget:
        async with admin.begin() as conn:
            await policy_version(conn, 3000)
    metadata = {
        "id": "run",
        "defaultDatasetId": "dataset",
        "defaultKeyValueStoreId": "store",
        "defaultRequestQueueId": "queue",
        "buildId": "build",
        "buildNumber": "1.2.3",
        "finishedAt": "2020-01-01T00:00:00Z",
    }

    async def apify(request):
        nonlocal pending
        calls.append(("apify", request.method))
        if request.method == "POST":
            async with admin.connect() as conn:
                assert (
                    await conn.scalar(
                        text("SELECT count(*) FROM reference_feed_effects WHERE window_id=:w"),
                        {"w": UUID(event.operation_id)},
                    )
                    == 1
                )
            assert json.loads(request.content)["resultsLimit"] == 20
            return httpx.Response(201, json={"data": metadata})
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_resources")) == 1
        if "/actor-runs/" in str(request.url):
            if pending:
                pending = False
                return httpx.Response(200, json={"data": {**metadata, "status": "RUNNING"}})
            return httpx.Response(200, json={"data": {**metadata, "status": "SUCCEEDED", "usageTotalUsd": 0.000007}})
        return httpx.Response(
            200,
            json=[
                {
                    "id": "private-post",
                    "ownerUsername": "fixture_profile",
                    "ownerFullName": "Perfil de ensaio",
                    "type": "Sidecar",
                    "caption": "private synthetic caption",
                    "images": [
                        "https://cdninstagram.com/first.jpg"
                        if pause_for_budget
                        else "https://cdninstagram.com/missing.jpg",
                        "https://cdninstagram.com/image.jpg",
                    ],
                }
            ],
        )

    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), "red").save(buffer, format="PNG")

    async def image(request):
        calls.append(("image", request.method))
        return (
            httpx.Response(404)
            if request.url.path.endswith("missing.jpg")
            else httpx.Response(200, content=buffer.getvalue(), headers={"content-type": "image/png"})
        )

    async def jev(request):
        calls.append(("jev", request.method))
        payload = json.loads(request.content)
        assert (
            payload["state"]["caption"] == ("private synthetic caption" if calls.count(("jev", "POST")) == 1 else None)
            and len(payload["assets"]) == 1
        )
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == calls.count(
                ("jev", "POST")
            )
        answers = {}
        for name, question in payload["questions"].items():
            choice = next(iter(question["criteria"]))
            answers[name] = {
                "type": "choice",
                "choice": choice,
                "confidence": 1,
                "probabilities": {key: int(key == choice) for key in question["criteria"]},
            }
        return httpx.Response(
            200, json={"model": "jev-test-model", "answers": answers, "usage": {"input_tokens": 10, "output_tokens": 5}}
        )

    worker = Database(settings, correlator=True)
    executor = ReferenceLearningExecution(
        worker,
        settings,
        apify_transport=httpx.MockTransport(apify),
        image_transport=httpx.MockTransport(image),
        jev_transport=httpx.MockTransport(jev),
    )
    try:
        if pending_first:
            assert await executor.run(event) == "pending"
        if pause_for_budget:
            assert await executor.run(event) == "budget_unavailable"
            async with admin.begin() as conn:
                assert await conn.scalar(text("SELECT count(*) FROM reference_learning_results")) == 0
                assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects")) == 1
                await policy_version(conn, 6000)
        assert await executor.run(event) == expected_status
        assert calls.count(("apify", "POST")) == 1 and calls.count(("jev", "POST")) == (2 if pause_for_budget else 1)
        count = len(calls)
        assert await executor.run(event) == expected_status and len(calls) == count
        async with database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
            captured = await session.scalar(
                text("SELECT public.reference_capture_generation_context(:b)"), {"b": UUID(event.business_id)}
            )
        assert captured["selected"][0]["analysis_status"] == expected_status and captured["learnings"]
        assert "private synthetic caption" not in json.dumps(captured) and "cdninstagram" not in json.dumps(captured)
        async with admin.connect() as conn:
            stored = await conn.scalar(text("SELECT row_to_json(r)::text FROM reference_learning_results r"))
            assert (
                "private-post" not in stored
                and "private synthetic caption" not in stored
                and "cdninstagram" not in stored
            )
            row = (
                await conn.execute(
                    text("""SELECT posts,images,status,coverage,profile_name FROM reference_learning_results""")
                )
            ).one()
            assert tuple(row) == (
                1,
                2 if pause_for_budget else 1,
                expected_status,
                "unconfirmed" if pause_for_budget else "partial",
                "Perfil de ensaio",
            )
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_windows")) == 2
            assert (
                await conn.scalar(
                    text("""SELECT count(*) FROM reference_feed_windows WHERE
                scheduled_at=accepted_at+interval '6 months' """)
                )
                == 1
            )
            assert (
                await conn.scalar(
                    text("""SELECT actual_usd_micros FROM reference_cost_reservations WHERE provider='apify' """)
                )
                == 7
            )
            assert (
                await conn.scalar(
                    text("""SELECT actual_usd_micros FROM reference_cost_reservations WHERE provider='jev' """)
                )
                is None
            )
    finally:
        await worker.close()


async def test_direct_video_and_reel_covers_reach_patterns_without_collecting_video_or_coauthors(
    admin, api, seeded, settings, database
):
    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    settings = await learning_settings(admin, settings)
    metadata = {
        "id": "video-run",
        "defaultDatasetId": "video-dataset",
        "defaultKeyValueStoreId": "video-store",
        "defaultRequestQueueId": "video-queue",
        "buildId": "video-build",
        "buildNumber": "1.2.3",
        "finishedAt": "2020-01-01T00:00:00Z",
    }
    rows = [
        {
            "id": "private-" + kind,
            "ownerUsername": "fixture_profile",
            "type": "Video",
            "productType": kind,
            "caption": "private synthetic " + kind + " caption",
            "displayUrl": "https://cdninstagram.com/" + kind + "-cover.jpg",
            "videoUrl": "https://cdninstagram.com/" + kind + "-video.mp4",
        }
        for kind in ("feed", "clips")
    ] + [
        {
            "id": "private-coauthored-post",
            "ownerUsername": "another_author",
            "coauthorProducers": [{"username": "fixture_profile"}],
            "taggedUsers": [{"username": "fixture_profile"}],
            "type": "Video",
            "productType": "clips",
            "caption": "private excluded coauthor caption",
            "displayUrl": "https://cdninstagram.com/excluded-cover.jpg",
            "videoUrl": "https://cdninstagram.com/excluded-video.mp4",
        }
    ]
    apify_calls, image_urls, analyzed_captions = [], [], []

    async def apify(request):
        apify_calls.append((request.method, request.url.path))
        if request.method == "POST":
            assert json.loads(request.content)["resultsLimit"] == 20
            return httpx.Response(201, json={"data": metadata})
        if request.url.path == "/v2/actor-runs/video-run":
            return httpx.Response(200, json={"data": {**metadata, "status": "SUCCEEDED", "usageTotalUsd": 0.000007}})
        assert request.url.path == "/v2/datasets/video-dataset/items"
        return httpx.Response(200, json=rows)

    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), "blue").save(buffer, format="PNG")

    async def image(request):
        image_urls.append(str(request.url))
        assert request.method == "GET" and str(request.url) in {
            "https://cdninstagram.com/feed-cover.jpg",
            "https://cdninstagram.com/clips-cover.jpg",
        }
        return httpx.Response(200, content=buffer.getvalue(), headers={"content-type": "image/png"})

    async def jev(request):
        payload = json.loads(request.content)
        analyzed_captions.append(payload["state"]["caption"])
        assert len(payload["assets"]) == 1
        assert next(iter(payload["assets"].values()))["type"] == "image"
        assert "videoUrl" not in json.dumps(payload) and "cdninstagram.com" not in json.dumps(payload)
        answers = {}
        for name, question in payload["questions"].items():
            choice = next(iter(question["criteria"]))
            answers[name] = {
                "type": "choice",
                "choice": choice,
                "confidence": 1,
                "probabilities": {key: int(key == choice) for key in question["criteria"]},
            }
        return httpx.Response(
            200, json={"model": "jev-test-model", "answers": answers, "usage": {"input_tokens": 10, "output_tokens": 5}}
        )

    worker = Database(settings, correlator=True)
    executor = ReferenceLearningExecution(
        worker,
        settings,
        apify_transport=httpx.MockTransport(apify),
        image_transport=httpx.MockTransport(image),
        jev_transport=httpx.MockTransport(jev),
    )
    try:
        assert await executor.run(event) == "partial"
        assert image_urls == ["https://cdninstagram.com/feed-cover.jpg", "https://cdninstagram.com/clips-cover.jpg"]
        assert analyzed_captions == ["private synthetic feed caption", "private synthetic clips caption"]
        call_counts = len(apify_calls), len(image_urls), len(analyzed_captions)
        assert await executor.run(event) == "partial"
        assert (len(apify_calls), len(image_urls), len(analyzed_captions)) == call_counts
        assert sum(method == "POST" for method, _ in apify_calls) == 1
        async with database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
            snapshot = await session.scalar(
                text("SELECT public.reference_capture_generation_context(:b)"), {"b": UUID(event.business_id)}
            )
        assert snapshot["selected"][0]["analysis_status"] == "partial"
        assert snapshot["learnings"][0]["reference_id"] == str(reference)
        assert snapshot["learnings"][0]["patterns"]
        response = await api.get(base + "/reference-learnings", headers=headers)
        assert response.status_code == 200
        assert response.json()["references"][0]["analysis_status"] == "partial"
        assert response.json()["references"][0]["patterns"]
        async with admin.connect() as conn:
            assert tuple(
                (await conn.execute(text("SELECT posts,images,status,coverage FROM reference_learning_results"))).one()
            ) == (2, 2, "partial", "partial")
            assert await conn.scalar(text("SELECT count(*) FROM reference_post_effects WHERE state='completed'")) == 2
            stored = await conn.scalar(text("SELECT row_to_json(r)::text FROM reference_learning_results r"))
            durable = stored + json.dumps(snapshot) + response.text
            for raw in ("private-feed", "private-clips", "private-coauthored", "private synthetic", "cdninstagram.com"):
                assert raw not in durable
    finally:
        await worker.close()


async def test_learning_event_stays_pending_until_relay_feature_is_enabled(
    admin, api, seeded, settings, relay_database
):
    from app.services.outbox import claim_events

    event, _, _, _ = await canonical_learning_fixture(admin, api, seeded, settings)
    disabled = await claim_events(relay_database, uuid4())
    assert all(item.event.event_id != event.event_id for item in disabled)
    async with admin.connect() as conn:
        assert (
            await conn.scalar(text("SELECT state FROM outbox_events WHERE id=:id"), {"id": UUID(event.event_id)})
            == "pending"
        )
    enabled = await claim_events(relay_database, uuid4(), include_learning=True)
    assert any(item.event == event for item in enabled)
