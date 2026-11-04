"""Canonical selections and durable analysis use only synthetic local fixtures."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.reference_learning_store import ReferenceLearningStore
from app.tests.integration.test_reference_search_admission import _business
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


async def canonical_learning_fixture(admin, api, seeded, settings):
    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    response = await api.post(
        base + "/references",
        headers=headers,
        json={"operation_id": str(uuid4()), "instagram": "fixture_profile", "note": "Aprender tom e cores."},
    )
    assert response.status_code == 200, response.text
    reference = UUID(response.json()["id"])
    async with admin.connect() as conn:
        row = (
            await conn.execute(
                text("""SELECT id,event_id FROM reference_feed_windows
          WHERE tenant_id=:t AND business_id=:b AND reference_id=:r"""),
                {"t": tenant, "b": business, "r": reference},
            )
        ).one()
    event = BusinessEvent(str(row.event_id), str(tenant), str(business), str(actor), str(row.id))
    return event, base, headers, reference


async def test_manual_acceptance_creates_a_canonical_window_and_owner_snapshot(admin, api, seeded, settings, database):
    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    tenant, business, actor = UUID(event.tenant_id), UUID(event.business_id), UUID(event.actor_id)
    worker = Database(settings, correlator=True)
    try:
        window = await ReferenceLearningStore(worker).load(event)
        assert window.reference == reference and window.association_version == 1
        assert window.profile == "fixture_profile" and window.state == "pending" and window.feed is None
        async with database.transaction(tenant, actor) as session:
            value = await session.scalar(text("SELECT reference_capture_generation_context(:b)"), {"b": business})
        assert value["version"] == 1 and value["learnings"] == []
        assert value["selected"] == [
            {
                "reference_id": str(reference),
                "association_version": 1,
                "source": "owner",
                "instagram_handle": "fixture_profile",
                "note": "Aprender tom e cores.",
                "score": None,
                "similarity": None,
                "analysis_status": "not_requested",
            }
        ]
    finally:
        await worker.close()


async def test_suggested_selection_profile_change_and_owner_sharing_use_one_version_authority(
    admin, api, seeded, settings, database
):
    import json

    from sqlalchemy.exc import DBAPIError

    from app.tests.integration.test_reference_profile_overrides import _setup
    from app.tests.integration.test_reference_real_selection import _result
    from app.tests.unit.test_core import access_token

    tenant, business, actor, cycle, result, candidate, place, base, correction = await _setup(admin, seeded)
    second, candidates, places = await _result(admin, tenant, business, actor, cycle, 20, places=[uuid4(), uuid4()])
    # The test administrator seeds published discovery history; the selection itself
    # still enters through the restricted owner API and its real writer.
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_cycle_reviews
          (tenant_id,business_id,cycle_id,first_result_id,required_place_ids)
          VALUES(:t,:b,:c,:r,ARRAY[]::uuid[])"""),
            {"t": tenant, "b": business, "c": cycle, "r": result},
        )
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    selection = {
        "operation_id": str(uuid4()),
        "cycle_id": str(cycle),
        "selection": [
            {"result_id": str(result), "candidate_id": str(candidate)},
            {"result_id": str(second), "candidate_id": str(candidates[0])},
            {"result_id": str(second), "candidate_id": str(candidates[1])},
        ],
    }
    response = await api.post(base + "/selection", headers=headers, json=selection)
    assert response.status_code == 200, response.text
    async with database.transaction(tenant, actor) as session:
        initial = await session.scalar(text("SELECT reference_capture_generation_context(:b)"), {"b": business})
    selected = {item["reference_id"]: item for item in initial["selected"]}
    assert len(selected) == 3 and all(item["association_version"] == 1 for item in selected.values())
    assert selected[str(place)]["instagram_handle"] == "provider_suggestion"
    assert selected[str(places[0])]["analysis_status"] == "unavailable"
    assert initial["learnings"] == []
    versions = json.dumps([{"reference_id": str(place), "association_version": 1}])
    async with admin.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT id,event_id FROM reference_feed_windows WHERE reference_id=:r"), {"r": place}
            )
        ).one()
    original_event = BusinessEvent(str(row.event_id), str(tenant), str(business), str(actor), str(row.id))
    # Another active owner can read the same derived context; viewers and other tenants cannot.
    with pytest.raises(DBAPIError, match="OWNER_INACTIVE"):
        async with database.transaction(tenant, seeded["viewer"]) as session:
            await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": business})
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": tenant, "a": seeded["viewer"]},
        )
    async with database.transaction(tenant, seeded["viewer"]) as session:
        shared = await session.scalar(text("SELECT reference_capture_generation_context(:b)"), {"b": business})
    assert shared == initial
    with pytest.raises(DBAPIError, match="BUSINESS_NOT_FOUND"):
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": business})
    changed = await api.put(base + f"/profiles/{place}", headers=headers, json=correction)
    assert changed.status_code == 200, changed.text
    async with database.transaction(tenant, actor) as session:
        assert not await session.scalar(
            text("SELECT reference_generation_context_is_current(:b,CAST(:v AS jsonb))"), {"b": business, "v": versions}
        )
        for bad in (
            None,
            {},
            [None],
            [{"reference_id": "not-a-uuid", "association_version": 1}],
            [{"reference_id": str(place), "association_version": "999999999999999999999999"}],
        ):
            assert not await session.scalar(
                text("SELECT reference_generation_context_is_current(:b,CAST(:v AS jsonb))"),
                {"b": business, "v": json.dumps(bad)},
            )
        current = await session.scalar(text("SELECT reference_capture_generation_context(:b)"), {"b": business})
    revised = next(item for item in current["selected"] if item["reference_id"] == str(place))
    assert revised["association_version"] == 2 and revised["instagram_handle"] == "correct_profile"
    worker = Database(settings, correlator=True)
    try:
        assert (await ReferenceLearningStore(worker).load(original_event)).state == "cancelled"
    finally:
        await worker.close()
    async with admin.connect() as conn:
        rows = (
            await conn.execute(
                text("""SELECT association_version,instagram_handle,status
          FROM reference_feed_windows WHERE reference_id=:r ORDER BY association_version"""),
                {"r": place},
            )
        ).all()
    assert [tuple(row) for row in rows] == [(1, "provider_suggestion", "cancelled"), (2, "correct_profile", "pending")]


async def canonical_feed_fixture(admin, api, seeded, settings, *, persist_run=True):
    """Return a genuinely admitted window, claimed feed and persisted synthetic run."""
    from pydantic import SecretStr

    from app.adapters.apify_instagram_feed import ApifyInstagramFeed, SubmittedInstagramFeed
    from app.services.reference_feed_budget_guard import FeedGuardContext
    from app.tests.integration.test_reference_places_budget_guard import _pilot

    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    store = ReferenceLearningStore(worker)
    window = await store.load(event)
    pilot, _ = await _pilot(admin, cap=100)
    tariff = "feed-" + uuid4().hex
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs(version,provider,field_mask,
          minimum_reserved_usd_micros,active) VALUES(:v,'apify','apify-instagram-feed:1.2.3',1,true)"""),
            {"v": tariff},
        )
    context = FeedGuardContext(
        window.tenant,
        window.business,
        window.actor,
        reference,
        1,
        window.window,
        None,
        None,
        uuid4(),
        uuid4(),
        pilot,
        SecretStr("synthetic-feed-key-0123456789abcdef"),
        "test-key",
        tariff,
        "test-credential",
        40,
        window.profile,
        "1.2.3",
    )
    key = SecretStr("synthetic-apify-key")
    request = ApifyInstagramFeed._request(
        "POST",
        "https://api.apify.com/v2/acts/apify~instagram-scraper/runs",
        key,
        params={
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.00004",
            "maxItems": "20",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        },
        body={"directUrls": ["https://www.instagram.com/fixture_profile/"], "resultsType": "posts", "resultsLimit": 20},
    )
    claimed = await store.claim_feed(context, ApifyInstagramFeed._bind(request, key))
    assert claimed["created"] is True
    token = UUID(claimed["executor_token"])
    run = SubmittedInstagramFeed(
        context.effect, window.profile, "run", "dataset", "store", "queue", "1.2.3", "build", 20
    )
    if persist_run:
        await store.record_run(window, context.effect, token, run)
    return worker, window, context, token, run


@pytest.mark.parametrize("persist_run", [False, True])
async def test_uncertain_submission_status_is_shared_and_run_recovery_remains_distinct(
    admin, api, seeded, settings, database, persist_run
):
    worker, window, feed, token, run = await canonical_feed_fixture(
        admin, api, seeded, settings, persist_run=persist_run
    )
    try:
        async with worker.transaction(window.tenant, window.actor) as session:
            await session.scalar(
                text("SELECT reference_feed_uncertain(:effect,:token)"), {"effect": feed.effect, "token": token}
            )
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
                {"t": window.tenant, "a": seeded["viewer"]},
            )
        for actor in (window.actor, seeded["viewer"]):
            async with database.transaction(window.tenant, actor) as session:
                status = await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": window.business})
                snapshot = await session.scalar(
                    text("SELECT reference_capture_generation_context(:b)"), {"b": window.business}
                )
            assert status["references"][0]["analysis_status"] == ("pending" if persist_run else "unavailable")
            assert status["references"][0]["update_status"] == ("running" if persist_run else None)
            assert snapshot["selected"][0]["analysis_status"] == ("pending" if persist_run else "unavailable")
            if not persist_run:
                assert status["references"][0]["next_analysis_at"] is None
    finally:
        await worker.close()


@pytest.mark.parametrize("acknowledged", [False, True])
async def test_missing_run_closes_unavailable_without_releasing_hold_or_late_run(
    admin, api, seeded, settings, database, acknowledged
):
    from sqlalchemy.exc import DBAPIError

    worker, window, feed, token, run = await canonical_feed_fixture(admin, api, seeded, settings, persist_run=False)
    try:
        store = ReferenceLearningStore(worker)
        if acknowledged:
            async with worker.transaction(window.tenant, window.actor) as session:
                await session.scalar(
                    text("SELECT reference_feed_uncertain(:effect,:token)"), {"effect": feed.effect, "token": token}
                )
        for changes in ({"token": uuid4()}, {"posts": 1}, {"profile_name": "Unproved name"}):
            values = {"token": token, "posts": 0, "profile_name": None, **changes}
            with pytest.raises(DBAPIError, match="FENCE_INVALID"):
                await store.finish(
                    window,
                    feed.effect,
                    values["token"],
                    patterns=(),
                    status="unavailable",
                    posts=values["posts"],
                    images=0,
                    coverage="unconfirmed",
                    profile_name=values["profile_name"],
                )
        finished = await store.finish(
            window, feed.effect, token, patterns=(), status="unavailable", posts=0, images=0, coverage="unconfirmed"
        )
        assert finished["state"] == "unavailable" and finished["next_window_id"]
        assert (
            await store.finish(
                window, feed.effect, token, patterns=(), status="unavailable", posts=0, images=0, coverage="unconfirmed"
            )
        )["state"] == "unavailable"
        with pytest.raises(DBAPIError, match="FENCE_INVALID"):
            await store.record_run(window, feed.effect, token, run)
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE effect_id=:e"), {"e": feed.effect}
                )
                == "uncertain"
            )
            assert (
                await conn.scalar(
                    text("SELECT reserved_usd_micros FROM reference_provider_pilots WHERE id=:p"), {"p": feed.pilot}
                )
                == 40
            )
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_windows")) == 2
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_resources")) == 0
        async with database.transaction(window.tenant, window.actor) as session:
            status = await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": window.business})
        assert status["references"][0]["analysis_status"] == "unavailable"
        assert status["references"][0]["update_status"] == "scheduled"
    finally:
        await worker.close()


async def test_canonical_feed_claim_and_persisted_run_survive_retry(admin, api, seeded, settings):
    from dataclasses import replace

    from sqlalchemy.exc import DBAPIError

    worker, window, context, token, run = await canonical_feed_fixture(admin, api, seeded, settings)
    try:
        store = ReferenceLearningStore(worker)
        loaded = await store.load(
            BusinessEvent(
                str(window.event), str(window.tenant), str(window.business), str(window.actor), str(window.window)
            )
        )
        assert loaded.submitted_run() == run and loaded.feed.executor_token == token
        assert await store.authorize(window, context.effect, token, run)
        assert not await store.authorize(window, context.effect, uuid4(), run)
        assert not await store.authorize(window, context.effect, token, replace(run, username="other_profile"))
        with pytest.raises(ValueError, match="RUN_INVALID"):
            await store.record_run(window, context.effect, token, replace(run, submission_id=uuid4()))
        await store.record_run(window, context.effect, token, run)
        async with worker.transaction(window.tenant, window.actor) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.execute(text("SELECT executor_token FROM reference_feed_effects"))
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_resources")) == 1
            assert await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
    finally:
        await worker.close()


async def test_only_proven_patterns_are_persisted_and_next_window_follows_acceptance(
    admin, api, seeded, settings, database
):
    import httpx
    from pydantic import SecretStr
    from sqlalchemy.exc import DBAPIError

    from app.adapters.jev_reference_post_analysis import JevReferencePostAnalysis
    from app.services.reference_learning_projection import DerivedPattern
    from app.services.reference_pattern_vocabulary import aggregate_pattern_choices
    from app.services.reference_post_analysis_guard import DatabasePostAnalysisGuard, PostGuardContext
    from app.tests.unit.test_jev_reference_post_analysis import response_for

    worker, window, feed, token, run = await canonical_feed_fixture(admin, api, seeded, settings)
    try:
        tariff = "jev-" + uuid4().hex
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO reference_provider_tariffs(version,provider,field_mask,
              minimum_reserved_usd_micros,active) VALUES(:v,'jev','jev-model:jev-1.14.0',1,true)"""),
                {"v": tariff},
            )
        context = PostGuardContext(
            window.tenant,
            window.business,
            window.actor,
            window.window,
            window.reference,
            1,
            feed.effect,
            token,
            uuid4(),
            "b" * 64,
            feed.pilot,
            feed.key,
            "test-key",
            tariff,
            "test-credential",
            5,
            caption_mac="a" * 64,
        )
        guard = DatabasePostAnalysisGuard(worker, context)
        model = JevReferencePostAnalysis(
            SecretStr("synthetic"),
            "jev-1.14.0",
            guard,
            enabled=True,
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=response_for(r))),
        )
        result = await model.analyze(caption="Private synthetic caption", image=None, operation_id=context.effect)
        await guard.record(result)
        store = ReferenceLearningStore(worker)
        with pytest.raises(DBAPIError, match="PATTERN_UNPROVED"):
            await store.finish(
                window,
                feed.effect,
                token,
                patterns=(DerivedPattern(dimension="editorial", observation="Private synthetic caption"),),
                status="completed",
                posts=1,
                images=0,
                coverage="unconfirmed",
            )
        patterns = aggregate_pattern_choices((result.choices,))
        result = await store.finish(
            window,
            feed.effect,
            token,
            patterns=patterns,
            status="completed",
            posts=1,
            images=0,
            coverage="unconfirmed",
            profile_name="Perfil de demonstração",
        )
        assert result["state"] == "completed"
        assert (
            await store.finish(
                window,
                feed.effect,
                token,
                patterns=patterns,
                status="completed",
                posts=1,
                images=0,
                coverage="unconfirmed",
                profile_name="Perfil de demonstração",
            )
        )["state"] == "completed"
        async with database.transaction(window.tenant, window.actor) as session:
            snapshot = await session.scalar(
                text("SELECT reference_capture_generation_context(:b)"), {"b": window.business}
            )
            status = await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": window.business})
        assert snapshot["selected"][0]["analysis_status"] == "completed"
        assert snapshot["learnings"][0]["analysis_id"] == str(window.window)
        assert len(snapshot["learnings"][0]["patterns"]) == len(patterns)
        assert status["references"][0]["update_status"] == "scheduled"
        assert status["references"][0]["profile_name"] == "Perfil de demonstração"
        with pytest.raises(DBAPIError, match="FENCE_INVALID"):
            await store.finish(
                window,
                feed.effect,
                uuid4(),
                patterns=patterns,
                status="completed",
                posts=1,
                images=0,
                coverage="unconfirmed",
                profile_name="Perfil de demonstração",
            )
        with pytest.raises(DBAPIError, match="RESULT_CONFLICT"):
            await store.finish(
                window,
                feed.effect,
                token,
                patterns=patterns,
                status="completed",
                posts=1,
                images=0,
                coverage="unconfirmed",
                profile_name="Outro nome",
            )
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("""SELECT scheduled_at=((accepted_at AT TIME ZONE 'UTC')+interval '6 months') AT TIME\
 ZONE 'UTC'
              FROM reference_feed_windows WHERE id=:w"""),
                    {"w": UUID(result["next_window_id"])},
                )
                is True
            )
            persisted = await conn.scalar(text("SELECT patterns::text FROM reference_learning_results"))
            assert "Private synthetic caption" not in persisted
        async with worker.transaction(window.tenant, window.actor) as session:
            assert (
                await session.scalar(
                    text("SELECT reference_feed_window_active(:b,:w)"),
                    {"b": window.business, "w": UUID(result["next_window_id"])},
                )
                is False
            )
    finally:
        await worker.close()


async def test_budget_blocks_keep_one_window_and_removed_profiles_cancel_it(admin, api, seeded, settings, database):
    import json

    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        store = ReferenceLearningStore(worker)
        window = await store.load(event)
        await store.block(window, "budget")
        await store.block(window, "budget")
        await store.block(window, "configuration")
        async with database.transaction(window.tenant, window.actor) as session:
            snapshot = await session.scalar(
                text("SELECT reference_capture_generation_context(:b)"), {"b": window.business}
            )
            status = await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": window.business})
            versions = json.dumps([{"reference_id": str(reference), "association_version": 1}])
            assert await session.scalar(
                text("SELECT reference_generation_context_is_current(:b,CAST(:v AS jsonb))"),
                {"b": window.business, "v": versions},
            )
        assert snapshot["selected"][0]["analysis_status"] == "unavailable"
        assert status["references"][0]["update_status"] == "waiting"
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_windows")) == 1
            assert await conn.scalar(text("SELECT count(*) FROM reference_feed_effects")) == 0
            assert (
                await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.learning_blocked'"))
                == 2
            )
        response = await api.request(
            "DELETE", base + f"/references/{reference}", headers=headers, json={"operation_id": str(uuid4())}
        )
        assert response.status_code == 204, response.text
        assert (await store.load(event)).state == "cancelled"
        assert (await store.load(event)).state == "cancelled"
        async with database.transaction(window.tenant, window.actor) as session:
            assert not await session.scalar(
                text("SELECT reference_generation_context_is_current(:b,CAST(:v AS jsonb))"),
                {"b": window.business, "v": versions},
            )
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.learning_cancelled'"))
                == 1
            )
    finally:
        await worker.close()


async def test_unavailable_analysis_keeps_apify_name_and_calendar_anchor(admin, api, seeded, settings, database):
    import calendar

    from sqlalchemy.exc import DBAPIError

    worker, window, feed, token, run = await canonical_feed_fixture(admin, api, seeded, settings)
    try:
        # Model a delayed initial run: the reference was accepted on an August 31.
        # All later dates must derive from that acceptance, never February's clamped day.
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE reference_feed_windows SET accepted_at=
              make_timestamptz(extract(year FROM clock_timestamp())::integer-2,8,31,12,0,0,'UTC')
              WHERE id=:w"""),
                {"w": window.window},
            )
        store = ReferenceLearningStore(worker)
        for invalid in (" ", " name", "name\n", "x" * 201):
            with pytest.raises(DBAPIError, match="RESULT_INVALID"):
                await store.finish(
                    window,
                    feed.effect,
                    token,
                    patterns=(),
                    status="unavailable",
                    posts=0,
                    images=0,
                    coverage="unconfirmed",
                    profile_name=invalid,
                )
        completed = await store.finish(
            window,
            feed.effect,
            token,
            patterns=(),
            status="unavailable",
            posts=0,
            images=0,
            coverage="unconfirmed",
            profile_name="Nome Apify",
        )
        async with database.transaction(window.tenant, window.actor) as session:
            status = await session.scalar(text("SELECT reference_read_learning_status(:b)"), {"b": window.business})
            snapshot = await session.scalar(
                text("SELECT reference_capture_generation_context(:b)"), {"b": window.business}
            )
        assert status["references"][0]["profile_name"] == "Nome Apify"
        assert status["references"][0]["analysis_status"] == "unavailable"
        assert status["references"][0]["update_status"] == "scheduled"
        assert snapshot["selected"][0]["analysis_status"] == "unavailable" and snapshot["learnings"] == []
        async with admin.connect() as conn:
            value = (
                await conn.execute(
                    text("""SELECT scheduled_at,
              extract(month FROM scheduled_at AT TIME ZONE 'UTC')::int AS month,
              extract(day FROM scheduled_at AT TIME ZONE 'UTC')::int AS day,
              scheduled_at>clock_timestamp() AS future,
              date '2024-08-31'+interval '12 months' AS august,
              date '2024-08-31'+interval '6 months' AS february
              FROM reference_feed_windows WHERE id=:w"""),
                    {"w": UUID(completed["next_window_id"])},
                )
            ).one()
        assert value.future and value.month in (2, 8)
        assert value.day == calendar.monthrange(value.scheduled_at.year, value.month)[1]
        assert value.august.day == 31 and value.february.day == 28
    finally:
        await worker.close()
