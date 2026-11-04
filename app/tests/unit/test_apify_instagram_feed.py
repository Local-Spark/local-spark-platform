"""Mock-only feed collection; all usernames, content and IDs are fictional."""

import json
from dataclasses import replace
from decimal import ROUND_UP, localcontext
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_instagram_feed import (
    ApifyInstagramFeed,
    FeedChargeableRequest,
    InstagramFeedError,
    SubmittedInstagramFeed,
    _image_url,
    _post,
    _posts,
)


class Guard:
    def __init__(self, submission=True, inspection=True, uncertain_failure=False):
        self.submission = submission
        self.inspection = inspection
        self.uncertain_failure = uncertain_failure
        self.seen = set()
        self.calls = []

    async def claim_submission(self, operation, request):
        self.calls.append(("submit", operation, request))
        if isinstance(self.submission, Exception):
            raise self.submission
        if operation in self.seen:
            return False
        self.seen.add(operation)
        return self.submission

    async def claim_inspection(self, operation, intent):
        self.calls.append(("inspect", operation, intent))
        if isinstance(self.inspection, Exception):
            raise self.inspection
        if operation in self.seen:
            return False
        self.seen.add(operation)
        return self.inspection

    async def submission_uncertain(self, operation, binding):
        self.calls.append(("submit_uncertain", operation, binding))
        if self.uncertain_failure:
            raise RuntimeError("synthetic guard secret")

    async def inspection_uncertain(self, operation, intent):
        self.calls.append(("inspect_uncertain", operation, intent))
        if self.uncertain_failure:
            raise RuntimeError("synthetic guard secret")


_MISSING = object()


def adapter(handler, guard=_MISSING, **changes):
    options = {
        "token": SecretStr("synthetic-token"),
        "guard": Guard() if guard is _MISSING else guard,
        "enabled": True,
        "transport": httpx.MockTransport(handler),
        "actor_build": "1.2.3",
        "max_actor_usd_micros": 50_000,
    }
    return ApifyInstagramFeed(**{**options, **changes})


def metadata(status="SUCCEEDED", **changes):
    return {
        "data": {
            "id": "test-run",
            "defaultDatasetId": "test-dataset",
            "defaultKeyValueStoreId": "test-kv",
            "defaultRequestQueueId": "test-queue",
            "buildNumber": "1.2.3",
            "buildId": "test-build",
            "status": status,
            "finishedAt": "2020-01-01T00:00:00Z",
            **changes,
        }
    }


def submitted(**changes):
    value = SubmittedInstagramFeed(
        uuid4(), "test_profile", "test-run", "test-dataset", "test-kv", "test-queue", "1.2.3", "test-build", 20
    )
    return replace(value, **changes)


def image_post(**changes):
    return {
        "id": "fake-post-1",
        "type": "Image",
        "ownerUsername": "test_profile",
        "caption": "synthetic caption",
        "displayUrl": "https://scontent.cdninstagram.com/fake.jpg?signature=synthetic",
        **changes,
    }


def price_metadata():
    return {
        "data": {
            "id": "shu8hvrXbJbY3Eb9W",
            "taggedBuilds": {"latest": {"buildNumber": "1.2.3"}},
            "pricingInfos": [
                {
                    "startedAt": "2026-01-01T00:00:00+00:00",
                    "pricingModel": "PAY_PER_EVENT",
                    "minimalMaxTotalChargeUsd": 0.0027,
                }
            ],
        }
    }


async def test_live_feed_checks_price_before_claim_and_reports_terminal_cost():
    guard, methods = Guard(), []

    def respond(request):
        methods.append(request.method)
        if request.url.path == "/v2/acts/shu8hvrXbJbY3Eb9W":
            assert not guard.calls
            return httpx.Response(200, json=price_metadata())
        if request.method == "POST":
            assert guard.calls[0][0] == "submit"
            assert "skipPinnedPosts" not in json.loads(request.content)
            return httpx.Response(201, json=metadata(actId="shu8hvrXbJbY3Eb9W"))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=metadata(actId="shu8hvrXbJbY3Eb9W", usageTotalUsd=0.0027001))
        return httpx.Response(200, json=[image_post()])

    client = adapter(respond, guard, network_enabled=True)
    run = await client.submit("test_profile", uuid4())
    result = await client.inspect(run, uuid4())
    assert result.state == "available" and result.reported_cost_usd_micros == 2701
    assert methods == ["GET", "POST", "GET", "GET"]


async def test_live_feed_rejects_changed_pricing_before_paid_claim():
    payload, guard = price_metadata(), Guard()
    payload["data"]["pricingInfos"][0]["isPPEPlatformUsagePaidByUser"] = True
    with pytest.raises(InstagramFeedError, match="FEED_PRICING_UNAVAILABLE"):
        await adapter(lambda _: httpx.Response(200, json=payload), guard, network_enabled=True).submit(
            "test_profile", uuid4()
        )
    assert not guard.calls


@pytest.mark.parametrize("stage", ["submit", "inspect"])
async def test_live_feed_wrong_actor_never_becomes_a_valid_run(stage):
    guard = Guard()

    def respond(request):
        if request.url.path == "/v2/acts/shu8hvrXbJbY3Eb9W":
            return httpx.Response(200, json=price_metadata())
        return httpx.Response(200, json=metadata(actId="another-actor"))

    client = adapter(respond, guard, network_enabled=True)
    with pytest.raises(InstagramFeedError, match="FEED_(SUBMISSION|RESULT)_UNCERTAIN"):
        if stage == "submit":
            await client.submit("test_profile", uuid4())
        else:
            await client.inspect(submitted(), uuid4())
    assert guard.calls[-1][0] == stage + "_uncertain"


@pytest.mark.parametrize("status", ["FAILED", "TIMED-OUT", "ABORTED", "SUCCEEDED", "RUNNING"])
async def test_feed_cost_is_exposed_only_when_run_is_terminal(status):
    def respond(request):
        body = metadata(status, usageTotalUsd=0.0054) if "/actor-runs/" in request.url.path else [image_post()]
        return httpx.Response(200, json=body)

    result = await adapter(respond).inspect(submitted(), uuid4())
    assert result.reported_cost_usd_micros == (None if status == "RUNNING" else 5400)


async def test_feed_malformed_receipt_preserves_uncertain_state():
    guard = Guard()

    def respond(request):
        body = metadata(usageTotalUsd=-1) if "/actor-runs/" in request.url.path else [image_post()]
        return httpx.Response(200, json=body)

    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN"):
        await adapter(respond, guard).inspect(submitted(), uuid4())
    assert guard.calls[-1][0] == "inspect_uncertain"


async def test_live_feed_transport_has_no_proxy_retry_or_cross_host_credentials(monkeypatch):
    created = []

    def factory(**kwargs):
        created.append(kwargs)
        return httpx.MockTransport(lambda _: httpx.Response(200, json=price_metadata()))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    client = adapter(lambda _: pytest.fail("unexpected"), network_enabled=True)
    request = client._request("GET", "https://api.apify.com/v2/acts/shu8hvrXbJbY3Eb9W", SecretStr("synthetic"))
    assert await client._json(request, None) == price_metadata()
    assert created == [{"retries": 0, "trust_env": False}]
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        await client._json(httpx.Request("GET", "https://unrelated.example"), None)


async def test_submit_binds_complete_actor_request_before_post_and_hides_secrets(caplog):
    operation = uuid4()
    guard = Guard()

    def handler(request):
        assert len(guard.calls) == 1
        kind, ident, binding = guard.calls[0]
        assert (kind, ident) == ("submit", operation)
        assert binding == FeedChargeableRequest(
            request.method,
            str(request.url),
            request.content,
            SecretStr("synthetic-token"),
            (("content-length", request.headers["content-length"]), ("content-type", "application/json")),
        )
        assert request.url.path == "/v2/acts/apify~instagram-scraper/runs"
        assert dict(request.url.params) == {
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.05",
            "maxItems": "20",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        }
        assert request.headers["Authorization"] == "Bearer synthetic-token"
        assert json.loads(request.content) == {
            "directUrls": ["https://www.instagram.com/test_profile/"],
            "resultsType": "posts",
            "resultsLimit": 20,
        }
        assert "test_profile" not in repr(binding)
        assert "synthetic-token" not in binding.url
        return httpx.Response(201, json=metadata())

    run = await adapter(handler, guard).submit("@Test_Profile", operation)
    assert run.submission_id == operation and run.username == "test_profile"
    assert (run.run_id, run.dataset_id, run.key_value_store_id, run.request_queue_id) == (
        "test-run",
        "test-dataset",
        "test-kv",
        "test-queue",
    )
    assert "test_profile" not in repr(run) and "synthetic-token" not in caplog.text


async def test_submission_budget_is_exact_even_with_hostile_decimal_context():
    def handler(request):
        assert request.url.params["maxTotalChargeUsd"] == "0.050001"
        return httpx.Response(201, json=metadata())

    with localcontext() as context:
        context.prec = 1
        context.rounding = ROUND_UP
        await adapter(handler, max_actor_usd_micros=50_001).submit("test_profile", uuid4())


def test_binding_rejects_credential_that_differs_from_sent_authorization():
    request = httpx.Request("POST", "https://api.apify.com/example", headers={"Authorization": "Bearer wrong"})
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        ApifyInstagramFeed._bind(request, SecretStr("synthetic-token"))


async def test_inspection_binds_run_and_exact_reads_before_transient_result(caplog):
    run, operation, guard = submitted(), uuid4(), Guard()

    def handler(request):
        assert len(guard.calls) == 1
        kind, ident, intent = guard.calls[0]
        assert (kind, ident, intent.submission) == ("inspect", operation, run)
        assert request.headers["Authorization"] == "Bearer synthetic-token"
        expected = FeedChargeableRequest("GET", str(request.url), b"", SecretStr("synthetic-token"), ())
        if request.url.path.endswith("/actor-runs/test-run"):
            assert intent.run_request == expected
            return httpx.Response(200, json=metadata())
        assert intent.dataset_request == expected
        assert request.url.params["limit"] == "21"
        return httpx.Response(200, json=[image_post(extra="ignored synthetic data")])

    result = await adapter(handler, guard).inspect(run, operation)
    assert result.state == "available" and result.coverage == "unconfirmed"
    assert result.posts[0].caption == "synthetic caption"
    assert len(result.posts[0].image_urls) == 1
    assert "synthetic caption" not in repr(result) and "synthetic caption" not in repr(result.posts[0])
    assert "test_profile" not in caplog.text and "synthetic-token" not in caplog.text


@pytest.mark.parametrize("profile", [None, "", "x" * 201, "a..b", "https://instagram.com/p/post/"])
async def test_invalid_profile_never_claims(profile):
    guard = Guard()
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no HTTP"), guard).submit(profile, uuid4())
    assert guard.calls == []


@pytest.mark.parametrize("limit", [0, 21, True, "20"])
async def test_invalid_limit_and_operation_are_rejected(limit):
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no HTTP")).submit("test_profile", uuid4(), results_limit=limit)
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no HTTP")).submit("test_profile", "not-a-uuid")


@pytest.mark.parametrize(
    "changes",
    [
        {"enabled": False},
        {"token": None},
        {"token": SecretStr("")},
        {"guard": None},
        {"transport": None},
        {"transport": httpx.AsyncHTTPTransport()},
        {"actor_build": "latest"},
        {"actor_build": None},
        {"max_actor_usd_micros": 0},
        {"max_actor_usd_micros": True},
        {"max_actor_usd_micros": 5_000_001},
    ],
)
async def test_real_transport_and_unconfigured_operation_are_always_disabled(changes):
    with pytest.raises(InstagramFeedError, match="FEED_DISABLED"):
        await adapter(lambda _: pytest.fail("no HTTP"), **changes).submit("test_profile", uuid4())


@pytest.mark.parametrize("outcome", [False, RuntimeError("synthetic guard secret")])
async def test_guard_failure_prevents_submission_and_hides_details(outcome):
    with pytest.raises(InstagramFeedError, match="FEED_BUDGET_UNAVAILABLE") as error:
        await adapter(lambda _: pytest.fail("no HTTP"), Guard(submission=outcome)).submit("test_profile", uuid4())
    assert "synthetic guard secret" not in str(error.value)


async def test_uncertain_submission_does_not_repeat_same_operation():
    guard, operation, attempts = Guard(), uuid4(), []

    def handler(request):
        attempts.append(1)
        raise httpx.ReadTimeout("synthetic private error", request=request)

    client = adapter(handler, guard)
    with pytest.raises(InstagramFeedError, match="FEED_SUBMISSION_UNCERTAIN") as error:
        await client.submit("test_profile", operation)
    assert "synthetic private error" not in str(error.value)
    assert [call[0] for call in guard.calls] == ["submit", "submit_uncertain"]
    with pytest.raises(InstagramFeedError, match="FEED_BUDGET_UNAVAILABLE"):
        await client.submit("test_profile", operation)
    assert attempts == [1]


async def test_lost_uncertainty_acknowledgement_does_not_reveal_or_resubmit():
    guard, operation = Guard(uncertain_failure=True), uuid4()
    client = adapter(lambda _: httpx.Response(500), guard)
    with pytest.raises(InstagramFeedError, match="FEED_SUBMISSION_UNCERTAIN") as error:
        await client.submit("test_profile", operation)
    assert "synthetic guard secret" not in str(error.value)
    with pytest.raises(InstagramFeedError, match="FEED_BUDGET_UNAVAILABLE"):
        await client.submit("test_profile", operation)


async def test_unexpected_transport_failure_does_not_expose_private_details():
    def handler(_):
        raise RuntimeError("synthetic provider secret")

    with pytest.raises(InstagramFeedError, match="FEED_SUBMISSION_UNCERTAIN") as error:
        await adapter(handler).submit("test_profile", uuid4())
    assert "synthetic provider secret" not in str(error.value)


@pytest.mark.parametrize(
    "response", [None, [], {}, {"data": []}, {"data": {}}, metadata(buildNumber="latest"), metadata(id="../bad")]
)
async def test_unusable_submission_reply_is_uncertain(response):
    with pytest.raises(InstagramFeedError, match="FEED_SUBMISSION_UNCERTAIN"):
        await adapter(lambda _: httpx.Response(201, json=response)).submit("test_profile", uuid4())


@pytest.mark.parametrize("outcome", [False, RuntimeError("synthetic guard secret")])
async def test_inspection_guard_failure_prevents_reads(outcome):
    with pytest.raises(InstagramFeedError, match="FEED_BUDGET_UNAVAILABLE"):
        await adapter(lambda _: pytest.fail("no HTTP"), Guard(inspection=outcome)).inspect(submitted(), uuid4())


@pytest.mark.parametrize(
    "run,operation",
    [
        (None, uuid4()),
        (submitted(submission_id="invalid"), uuid4()),
        (submitted(username=None), uuid4()),
        (submitted(username="@test_profile"), uuid4()),
        (submitted(run_id="../bad"), uuid4()),
        (submitted(dataset_id="bad/value"), uuid4()),
        (submitted(build_number="latest"), uuid4()),
        (submitted(results_limit=True), uuid4()),
        (submitted(results_limit=21), uuid4()),
        (submitted(), "invalid"),
    ],
)
async def test_invalid_or_forged_run_never_claims(run, operation):
    guard = Guard()
    with pytest.raises(InstagramFeedError, match="FEED_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no HTTP"), guard).inspect(run, operation)
    assert guard.calls == []


@pytest.mark.parametrize("status", ["READY", "RUNNING", "TIMING-OUT", "ABORTING"])
async def test_running_actor_returns_pending_without_reading_dataset(status):
    paths = []

    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json=metadata(status))

    result = await adapter(handler).inspect(submitted(), uuid4())
    assert result.state == "pending" and not result.posts
    assert paths == ["/v2/actor-runs/test-run"]


@pytest.mark.parametrize("status", ["FAILED", "TIMED-OUT", "ABORTED"])
async def test_failed_actor_can_expose_accessible_partial_posts_without_claiming_completeness(status):
    def handler(request):
        return httpx.Response(200, json=metadata(status) if "/actor-runs/" in request.url.path else [image_post()])

    result = await adapter(handler).inspect(submitted(), uuid4())
    assert result.state == "partial" and result.coverage == "partial" and len(result.posts) == 1


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {},
        {"data": []},
        metadata(id="wrong"),
        metadata(defaultDatasetId="other"),
        metadata(defaultKeyValueStoreId="other"),
        metadata(defaultRequestQueueId="other"),
        metadata(buildId="other"),
        metadata(buildNumber="1.2.4"),
        metadata(None),
        metadata("UNKNOWN"),
    ],
)
async def test_mismatched_or_unknown_run_metadata_is_uncertain(response):
    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN"):
        await adapter(lambda _: httpx.Response(200, json=response)).inspect(submitted(), uuid4())


@pytest.mark.parametrize(
    "response",
    [httpx.Response(429), httpx.Response(200, text="invalid json"), httpx.Response(200, content=b"x" * 1_000_001)],
)
async def test_failed_inspection_is_uncertain_and_does_not_retry(response):
    guard, operation, attempts = Guard(), uuid4(), []

    def handler(_):
        attempts.append(1)
        return response

    client = adapter(handler, guard)
    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN"):
        await client.inspect(submitted(), operation)
    assert [call[0] for call in guard.calls] == ["inspect", "inspect_uncertain"]
    with pytest.raises(InstagramFeedError, match="FEED_BUDGET_UNAVAILABLE"):
        await client.inspect(submitted(), operation)
    assert attempts == [1]


async def test_failed_inspection_uncertainty_acknowledgement_is_not_revealed():
    guard = Guard(uncertain_failure=True)
    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN") as error:
        await adapter(lambda _: httpx.Response(500), guard).inspect(submitted(), uuid4())
    assert "synthetic guard secret" not in str(error.value)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "x" * 2049,
        "https://evilcdninstagram.com/a.jpg",
        "http://cdninstagram.com/a.jpg",
        "https://user:pass@cdninstagram.com/a.jpg",
        "https://cdninstagram.com:8080/a.jpg",
        "https://cdninstagram.com/a.jpg#fragment",
        "https://cdninstagram.com:invalid/a.jpg",
    ],
)
def test_image_urls_cannot_target_arbitrary_or_malformed_hosts(url):
    assert _image_url(url) is None


def test_image_urls_accept_only_https_meta_cdn_and_do_not_fetch():
    assert _image_url("https://scontent.cdninstagram.com/a.jpg?sig=fake")
    assert _image_url("https://scontent.fbcdn.net/a.jpg")


@pytest.mark.parametrize(
    "row",
    [
        None,
        {},
        image_post(type="Unknown"),
        image_post(productType="clips"),
        image_post(ownerUsername="other"),
        image_post(ownerUsername="other", coauthorProducers=[{"username": "test_profile"}]),
        image_post(ownerUsername="other", taggedUsers=[{"username": "test_profile"}]),
        image_post(ownerUsername=None),
        image_post(id="../bad"),
        image_post(id=None),
        image_post(caption=None, displayUrl=None),
    ],
)
def test_unusable_wrong_owner_and_coauthored_rows_are_excluded(row):
    post, partial = _post(row, "test_profile")
    assert post is None and partial is True


def test_mixed_carousel_retains_images_and_video_covers_without_video_urls():
    post, partial = _post(
        image_post(
            type="Sidecar",
            images=["https://cdninstagram.com/flat.jpg"],
            childPosts=[
                {"type": "Image", "displayUrl": "https://cdninstagram.com/child.jpg"},
                {
                    "type": "Video",
                    "displayUrl": "https://cdninstagram.com/video.jpg",
                    "videoUrl": "https://cdninstagram.com/video.mp4",
                },
            ],
        ),
        "test_profile",
    )
    assert partial is True and post.caption == "synthetic caption"
    assert post.image_urls == ("https://cdninstagram.com/child.jpg", "https://cdninstagram.com/video.jpg")


@pytest.mark.parametrize(
    "changes",
    [
        {"caption": 42},
        {"caption": "x" * 10001},
        {"images": "bad"},
        {"images": ["bad"] * 21},
        {"carouselImages": ["http://invalid/"]},
        {"childPosts": None},
        {"childPosts": [{}] * 21},
        {"childPosts": [None]},
        {"childPosts": [{"type": "Image", "displayUrl": "https://fbcdn.net/image"}]},
    ],
)
def test_partial_or_malformed_fields_are_handled_without_losing_other_accessible_content(changes):
    post, _ = _post(image_post(**changes), "test_profile")
    assert post is not None


def test_duplicate_posts_empty_and_oversized_responses_are_not_misrepresented():
    result = _posts([image_post(), image_post()], "test_profile", 20, provider_partial=False)
    assert result.state == "partial" and len(result.posts) == 1
    assert _posts([], "test_profile", 20, provider_partial=False).state == "unavailable"
    assert _posts([], "test_profile", 20, provider_partial=True).coverage == "partial"
    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN"):
        _posts([image_post()] * 21, "test_profile", 20, provider_partial=False)
    with pytest.raises(InstagramFeedError, match="FEED_RESULT_UNCERTAIN"):
        _posts({}, "test_profile", 20, provider_partial=False)


@pytest.mark.parametrize("product_type", ["feed", "clips", "igtv", None])
def test_direct_video_or_reel_uses_only_cover_and_caption(product_type):
    row = image_post(
        type="Video",
        productType=product_type,
        videoUrl="https://cdninstagram.com/private-video.mp4",
        images=["https://cdninstagram.com/other-frame.jpg"],
        carouselImages=["https://cdninstagram.com/unrelated.jpg"],
        childPosts=[{"type": "Image", "displayUrl": "https://cdninstagram.com/child.jpg"}],
    )
    result = _posts([row, image_post(id="photo")], "test_profile", 20, provider_partial=False)
    assert result.state == "partial" and result.coverage == "partial"
    assert len(result.posts) == 2
    assert result.posts[0].caption == "synthetic caption"
    assert result.posts[0].image_urls == (row["displayUrl"],)


@pytest.mark.parametrize("cover", [None, "https://untrusted.example/cover.jpg"])
def test_video_without_accessible_cover_keeps_caption_only(cover):
    post, partial = _post(image_post(type="Video", displayUrl=cover), "test_profile")
    assert partial and post.caption == "synthetic caption" and post.image_urls == ()


def test_video_without_caption_or_cover_is_unavailable_without_using_video_url():
    post, partial = _post(
        image_post(type="Video", displayUrl=None, caption=None, videoUrl="https://cdninstagram.com/video.mp4"),
        "test_profile",
    )
    assert partial and post is None


def test_coauthor_or_tag_does_not_replace_direct_owner_in_mixed_batch():
    result = _posts(
        [
            image_post(
                type="Video",
                ownerUsername="other",
                coauthorProducers=[{"username": "test_profile"}],
                taggedUsers=[{"username": "test_profile"}],
            ),
            image_post(id="direct", coauthorProducers=[{"username": "other"}]),
        ],
        "test_profile",
        20,
        provider_partial=False,
    )
    assert result.state == "partial" and [post.post_id for post in result.posts] == ["direct"]


def test_duplicate_image_urls_are_deduplicated_and_missing_child_marks_partial():
    post, partial = _post(
        image_post(
            images=["https://scontent.cdninstagram.com/fake.jpg?signature=synthetic"], childPosts=[{"type": "Image"}]
        ),
        "test_profile",
    )
    assert partial is True and len(post.image_urls) == 1


def test_carousel_keeps_more_than_twenty_accessible_images_without_truncation():
    post, partial = _post(
        image_post(images=[f"https://cdninstagram.com/{index}.jpg" for index in range(21)]),
        "test_profile",
    )
    assert partial is False and len(post.image_urls) == 22
