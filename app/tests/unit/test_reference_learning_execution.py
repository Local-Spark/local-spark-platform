from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, uuid5

import pytest
from pydantic import SecretStr

from app.adapters.apify_instagram_feed import InstagramFeedError, InstagramFeedPost, InstagramFeedResult
from app.adapters.jev_reference_post_analysis import PostAnalysisError, PostAnalysisResult
from app.adapters.reference_feed_image import FeedImageError
from app.services import reference_learning_execution as module
from app.services.reference_learning_store import LearningWindow, StoredFeedRun, StoredLearningFeed
from app.services.reference_post_analysis_guard import PostSample, post_sample_mac
from app.workflows.contracts import BusinessEvent


def window(*, feed=True, **changes):
    data = {name: uuid4() for name in ("tenant", "business", "actor", "window", "event", "reference")}
    stored = (
        StoredLearningFeed(
            effect=uuid4(),
            event=uuid4(),
            pilot=uuid4(),
            state="running",
            executor_token=uuid4(),
            key_version="v1",
            tariff_version="v1",
            credential_version="v1",
            build="1.2.3",
            reserved_usd_micros=100_000,
            request_mac="a" * 64,
            run=StoredFeedRun(
                run_id="run",
                dataset_id="dataset",
                store_id="store",
                queue_id="queue",
                build_id="build",
                actor_build="1.2.3",
            ),
        )
        if feed
        else None
    )
    return LearningWindow(
        **{
            **data,
            "association_version": 1,
            "profile": "synthetic",
            "accepted_at": datetime.now(UTC),
            "scheduled_at": datetime.now(UTC),
            "state": "pending",
            "feed": stored,
            **changes,
        }
    )


def event(w):
    return BusinessEvent(str(w.event), str(w.tenant), str(w.business), str(w.actor), str(w.window))


def setup(settings, monkeypatch, w=None):
    monkeypatch.setattr(type(settings), "reference_learning_ready", lambda _: True)
    settings.reference_provider_hmac_key = SecretStr("synthetic-key-more-than-32-bytes-long")
    settings.reference_provider_key_version = "v1"
    settings.reference_provider_pilot_id = uuid4()
    settings.reference_feed_actor_build = "1.2.3"
    settings.reference_feed_tariff_version = settings.reference_feed_credential_version = "v1"
    settings.reference_feed_reserved_usd_micros = 100_000
    settings.reference_post_reserved_usd_micros = 3_000
    w = w or window()
    r = module.ReferenceLearningExecution(SimpleNamespace(), settings)
    r.store = SimpleNamespace(
        load=AsyncMock(return_value=w),
        finish=AsyncMock(),
        block=AsyncMock(),
        record_run=AsyncMock(),
        authorize=AsyncMock(return_value=True),
    )
    provider = SimpleNamespace(
        submit=AsyncMock(return_value=w.submitted_run()), inspect=AsyncMock(return_value=InstagramFeedResult("pending"))
    )
    monkeypatch.setattr(module, "ApifyInstagramFeed", MagicMock(return_value=provider))
    monkeypatch.setattr(module, "record_feed_terminal_cost", AsyncMock())
    monkeypatch.setattr(module, "caption_claimed", AsyncMock(return_value=False))
    monkeypatch.setattr(module, "load_post_sample", AsyncMock(return_value=None))
    monkeypatch.setattr(module, "load_caption_sample", AsyncMock(return_value=None))
    return r, w, provider


def sample(editorial=True):
    return PostAnalysisResult(
        (("tone", "friendly"),) if editorial else (("format", "photo"),), "reference-patterns-v1", "jev", 1, 1
    )


async def test_off_and_terminal_never_contact_provider(settings, monkeypatch):
    r, w, p = setup(settings, monkeypatch)
    monkeypatch.setattr(type(settings), "reference_learning_ready", lambda _: False)
    assert await r.run(event(w)) == "disabled"
    r.store.load.assert_not_awaited()
    monkeypatch.setattr(type(settings), "reference_learning_ready", lambda _: True)
    r.store.load.return_value = w.model_copy(update={"state": "cancelled"})
    assert await r.run(event(w)) == "cancelled"
    p.submit.assert_not_awaited()


async def test_no_response_and_rotated_key_never_resubmit(settings, monkeypatch):
    r, w, p = setup(settings, monkeypatch)
    r.store.load.return_value = w.model_copy(update={"feed": w.feed.model_copy(update={"run": None})})
    assert await r.run(event(w)) == "unavailable"
    r.store.load.return_value = w.model_copy(update={"feed": w.feed.model_copy(update={"key_version": "old"})})
    assert await r.run(event(w)) == "configuration_unavailable"
    p.submit.assert_not_awaited()


@pytest.mark.parametrize(
    "failure", ["FEED_BUDGET_UNAVAILABLE", "FEED_PRICING_UNAVAILABLE", "FEED_SUBMISSION_UNCERTAIN"]
)
async def test_submission_errors_preserve_retry_classification(settings, monkeypatch, failure):
    r, w, p = setup(settings, monkeypatch, window(feed=False))
    p.submit.side_effect = InstagramFeedError(failure)
    if failure.endswith("UNCERTAIN"):
        feed = window().feed.model_copy(update={"run": None, "state": "uncertain"})
        r.store.load.side_effect = [w, w.model_copy(update={"feed": feed})]
    assert await r.run(event(w)) == ("unavailable" if failure.endswith("UNCERTAIN") else "budget_unavailable")
    assert r.store.finish.await_count == int(failure.endswith("UNCERTAIN"))


async def test_new_run_is_saved_before_inspection_and_unknown_get_reuses_it(settings, monkeypatch):
    r, w, p = setup(settings, monkeypatch, window(feed=False))
    run = window().submitted_run()
    p.submit.return_value = run
    token = uuid4()
    monkeypatch.setattr(module.LearningFeedGuard, "execution_token", lambda _: token)

    async def inspect(*_):
        r.store.record_run.assert_awaited_once()
        raise InstagramFeedError("FEED_RESULT_UNCERTAIN")

    p.inspect.side_effect = inspect
    assert await r.run(event(w)) == "pending"
    p.submit.assert_awaited_once()


async def test_pending_and_unavailable_settle_only_terminal_response(settings, monkeypatch):
    r, w, p = setup(settings, monkeypatch)
    assert await r.run(event(w)) == "pending"
    module.record_feed_terminal_cost.assert_not_awaited()
    p.inspect.return_value = InstagramFeedResult("unavailable", reported_cost_usd_micros=7)
    assert await r.run(event(w)) == "unavailable"
    assert module.record_feed_terminal_cost.await_args.args[-1] == 7
    assert r.store.finish.await_args.kwargs["patterns"] == ()


@pytest.mark.parametrize(
    "incomplete,patterns,expected", [(False, True, "completed"), (True, True, "partial"), (False, False, "unavailable")]
)
async def test_finish_stores_patterns_and_counts_only(settings, monkeypatch, incomplete, patterns, expected):
    r, w, p = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", "private caption", ())
    p.inspect.return_value = InstagramFeedResult("available", (post,))
    r._post = AsyncMock(return_value=([sample()] if patterns else [], 2, incomplete))
    assert await r.run(event(w)) == expected
    saved = r.store.finish.await_args.kwargs
    assert saved["posts"] == int(patterns) and saved["images"] == 2
    assert "private caption" not in repr(saved) and "post" not in repr(saved["patterns"])


async def test_every_carousel_image_is_visited_and_caption_sent_once(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", "caption", tuple(f"https://cdninstagram.com/{i}.jpg" for i in range(25)))
    fetch = AsyncMock(return_value=object())
    monkeypatch.setattr(module, "FeedImageDownloader", MagicMock(return_value=SimpleNamespace(fetch=fetch)))
    r._analyze = AsyncMock(side_effect=[sample()] + [sample(False)] * 24)
    results, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert len(results) == images == 25 and not partial
    assert fetch.await_count == 25
    assert [call.args[-2] for call in r._analyze.await_args_list] == ["caption"] + [None] * 24


@pytest.mark.parametrize("caption", ["caption", None, ""])
async def test_inaccessible_images_fall_back_to_caption_without_fake_visuals(settings, monkeypatch, caption):
    r, w, _ = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", caption, ("https://cdninstagram.com/a.jpg",))
    monkeypatch.setattr(
        module,
        "FeedImageDownloader",
        MagicMock(return_value=SimpleNamespace(fetch=AsyncMock(side_effect=FeedImageError()))),
    )
    r._analyze = AsyncMock(return_value=sample())
    results, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert images == 0 and partial and len(results) == bool(caption)
    if caption:
        assert r._analyze.await_args.args[-2:] == (caption, None)


async def test_first_accessible_image_receives_caption_and_budget_failure_is_partial(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", "caption", ("https://cdninstagram.com/a.jpg", "https://cdninstagram.com/b.jpg"))
    fetch = AsyncMock(side_effect=[FeedImageError(), object()])
    monkeypatch.setattr(module, "FeedImageDownloader", MagicMock(return_value=SimpleNamespace(fetch=fetch)))
    r._analyze = AsyncMock(return_value=None)
    results, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert not results and images == 0 and partial
    assert r._analyze.await_args.args[-2] == "caption"


@pytest.mark.parametrize("state", ["completed", "uncertain"])
async def test_recovery_reads_samples_and_never_resends_uncertain_caption(settings, monkeypatch, state):
    r, w, _ = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", "caption", ("https://cdninstagram.com/a.jpg",))
    module.caption_claimed.return_value = True
    result = sample() if state == "completed" else None
    module.load_post_sample.side_effect = [PostSample(state, True, result), None]
    r._analyze = AsyncMock()
    values, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert len(values) == images == (state == "completed") and partial == (state != "completed")
    r._analyze.assert_not_awaited()


@pytest.mark.parametrize("state", ["completed", "uncertain", "new"])
async def test_caption_only_recovery_and_failure(settings, monkeypatch, state):
    r, w, _ = setup(settings, monkeypatch)
    post = InstagramFeedPost("post", "caption", ())
    if state != "new":
        module.load_caption_sample.return_value = PostSample(state, True, sample() if state == "completed" else None)
    r._analyze = AsyncMock(return_value=None)
    values, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert not images and len(values) == (state == "completed") and partial == (state != "completed")


async def test_new_window_reloads_recorded_run_before_images(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    empty = w.model_copy(update={"feed": None})
    r._analyze = AsyncMock(return_value=sample())
    await r._post(
        empty, r._context(empty), w.feed.executor_token, InstagramFeedPost("post", "caption", ()), lambda: None
    )
    r.store.load.assert_awaited_once_with(event(w))


async def test_caption_anchor_preserves_editorial_when_its_image_disappears(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    module.caption_claimed.return_value = True
    mixed = PostAnalysisResult((("tone", "friendly"), ("format", "photo")), "reference-patterns-v1", "jev", 1, 1)
    module.load_caption_sample.return_value = PostSample("completed", True, mixed)
    r._analyze = AsyncMock()
    values, images, partial = await r._post(
        w, r._context(w), w.feed.executor_token, InstagramFeedPost("post", "caption", ()), lambda: None
    )
    assert not images and not partial and values[0].choices == (("tone", "friendly"),)
    r._analyze.assert_not_awaited()


async def test_caption_anchor_does_not_double_count_existing_image_result(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    module.caption_claimed.return_value = True
    mixed = PostAnalysisResult((("tone", "friendly"), ("format", "photo")), "reference-patterns-v1", "jev", 1, 1)
    saved = PostSample("completed", True, mixed)
    module.load_post_sample.return_value = module.load_caption_sample.return_value = saved
    post = InstagramFeedPost("post", "caption", ("https://cdninstagram.com/a.jpg",))
    values, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert images == 1 and not partial and values == [mixed]


async def test_visual_only_failure_reports_partial_without_caption_request(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    monkeypatch.setattr(
        module, "FeedImageDownloader", MagicMock(return_value=SimpleNamespace(fetch=AsyncMock(return_value=object())))
    )
    r._analyze = AsyncMock(return_value=None)
    post = InstagramFeedPost("post", None, ("https://cdninstagram.com/a.jpg",))
    values, images, partial = await r._post(w, r._context(w), w.feed.executor_token, post, lambda: None)
    assert not values and not images and partial
    assert r._analyze.await_args.args[-2] is None
    module.caption_claimed.assert_awaited_once()


@pytest.mark.parametrize("failure", [False, True])
async def test_analyzer_binds_sample_caption_and_preserves_uncertainty(settings, monkeypatch, failure):
    r, w, _ = setup(settings, monkeypatch)
    guard = SimpleNamespace(record=AsyncMock())
    monkeypatch.setattr(module, "DatabasePostAnalysisGuard", MagicMock(return_value=guard))
    analyzer = SimpleNamespace(
        analyze=AsyncMock(side_effect=PostAnalysisError() if failure else None, return_value=sample())
    )
    monkeypatch.setattr(module, "JevReferencePostAnalysis", MagicMock(return_value=analyzer))
    mac = post_sample_mac(r.settings.reference_provider_hmac_key, w.window, "post", None)
    result = await r._analyze(w, r._context(w), w.feed.executor_token, mac, mac, "caption", None)
    assert (result is None) == failure
    context = module.DatabasePostAnalysisGuard.call_args.args[1]
    assert context.caption_mac == mac and context.effect == uuid5(w.window, mac)
    assert guard.record.await_count == int(not failure)


async def test_budget_denial_keeps_current_window_and_run_for_later_analysis(settings, monkeypatch):
    r, w, p = setup(settings, monkeypatch)
    p.inspect.return_value = InstagramFeedResult("available", (InstagramFeedPost("post", "caption", ()),))
    r._post = AsyncMock(side_effect=module.LearningBudgetUnavailable())
    assert await r.run(event(w)) == "budget_unavailable"
    r.store.finish.assert_not_awaited()
    r.store.block.assert_not_awaited()
    p.submit.assert_not_awaited()


async def test_post_budget_denial_is_distinct_from_an_uncertain_sent_request(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    analyzer = SimpleNamespace(
        analyze=AsyncMock(side_effect=PostAnalysisError("REFERENCE_POST_ANALYSIS_BUDGET_UNAVAILABLE"))
    )
    monkeypatch.setattr(module, "JevReferencePostAnalysis", MagicMock(return_value=analyzer))
    with pytest.raises(module.LearningBudgetUnavailable):
        await r._analyze(w, r._context(w), w.feed.executor_token, "a" * 64, "b" * 64, "caption", None)


async def test_blank_caption_keeps_accessible_visual_analysis(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    monkeypatch.setattr(
        module, "FeedImageDownloader", MagicMock(return_value=SimpleNamespace(fetch=AsyncMock(return_value=object())))
    )
    r._analyze = AsyncMock(return_value=sample(False))
    values, images, partial = await r._post(
        w,
        r._context(w),
        w.feed.executor_token,
        InstagramFeedPost("post", "  ", ("https://cdninstagram.com/a.jpg",)),
        lambda: None,
    )
    assert images == 1 and not partial and values[0].choices == (("format", "photo"),)
    assert r._analyze.await_args.args[-2] is None


@pytest.mark.parametrize("recovery", ["none", "run", "cancelled", "token"])
async def test_unknown_submission_recovers_only_durable_state(settings, monkeypatch, recovery):
    r, w, p = setup(settings, monkeypatch, window(feed=False))
    feed = window().feed
    restored = w
    if recovery == "run":
        restored = w.model_copy(update={"feed": feed})
    if recovery == "cancelled":
        restored = w.model_copy(update={"state": "cancelled"})
    if recovery == "token":
        restored = w.model_copy(update={"feed": feed.model_copy(update={"run": None, "executor_token": None})})
    r.store.load.side_effect = [w, restored]
    p.submit.side_effect = InstagramFeedError("FEED_SUBMISSION_UNCERTAIN")
    expected = {
        "none": "configuration_unavailable",
        "run": "pending",
        "cancelled": "cancelled",
        "token": "budget_unavailable",
    }
    assert await r.run(event(w)) == expected[recovery]
    r.store.finish.assert_not_awaited()
