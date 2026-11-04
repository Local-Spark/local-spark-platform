import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_profile_check import ApifyProfileCheck, ProfileCheckError, SubmittedProfileCheck


class Guard:
    def __init__(self, submission=50_000, inspection=True):
        self.submission = submission
        self.inspection = inspection
        self.operations = set()
        self.calls = []

    async def claim_submission(self, operation_id, username):
        self.calls.append(("submit", operation_id, username))
        if isinstance(self.submission, Exception):
            raise self.submission
        if operation_id in self.operations:
            return None
        self.operations.add(operation_id)
        return self.submission

    async def claim_inspection(self, operation_id, submission_id, username, run_id, dataset_id):
        self.calls.append(("inspect", operation_id, submission_id, username, run_id, dataset_id))
        if isinstance(self.inspection, Exception):
            raise self.inspection
        if operation_id in self.operations:
            return False
        self.operations.add(operation_id)
        return self.inspection


def provider(handler, guard=None):
    return ApifyProfileCheck(
        SecretStr("private-token"), guard or Guard(), enabled=True, transport=httpx.MockTransport(handler)
    )


def run():
    return SubmittedProfileCheck(uuid4(), "perfil_teste", "run-id", "dataset-id")


def run_response(status="SUCCEEDED", **changes):
    return {"data": {"id": "run-id", "defaultDatasetId": "dataset-id", "status": status, **changes}}


def row(status="SUCCESS", **changes):
    return {"input": "perfil_teste", "username": "perfil_teste", "status": status, "isPrivate": False, **changes}


async def test_submit_claims_budget_and_returns_only_run_ids(caplog):
    operation = uuid4()
    guard = Guard()

    def handler(request):
        assert guard.calls == [("submit", operation, "perfil_teste")]
        assert request.method == "POST" and request.url.host == "api.apify.com"
        assert request.url.path == "/v2/acts/coregent~instagram-profile-scraper/runs"
        assert request.url.params["maxTotalChargeUsd"] == "0.05"
        assert request.url.params["forcePermissionLevel"] == "LIMITED_PERMISSIONS"
        assert request.headers["Authorization"] == "Bearer private-token"
        assert "private-token" not in str(request.url)
        assert json.loads(request.content) == {
            "profiles": ["perfil_teste"],
            "includeBusinessContact": False,
            "includeBioLinks": False,
            "includeRelatedProfiles": False,
            "includeRecentPosts": False,
            "maxConcurrency": 1,
            "maxRetries": 0,
            "debugMode": False,
        }
        return httpx.Response(201, json={"data": {"id": "run-id", "defaultDatasetId": "dataset-id"}})

    result = await provider(handler, guard).submit("@perfil_teste", operation)
    assert result.submission_id == operation and result.username == "perfil_teste"
    assert (result.run_id, result.dataset_id) == ("run-id", "dataset-id")
    assert "perfil_teste" not in repr(result) and "private-token" not in caplog.text


async def test_inspection_requires_ownership_claim_then_minimizes_public_result(caplog):
    handle = run()
    operation = uuid4()
    guard = Guard()

    def handler(request):
        assert guard.calls == [("inspect", operation, handle.submission_id, "perfil_teste", "run-id", "dataset-id")]
        assert request.headers["Authorization"] == "Bearer private-token"
        if request.url.path.endswith("/actor-runs/run-id"):
            return httpx.Response(200, json=run_response())
        assert request.url.path.endswith("/datasets/dataset-id/items")
        assert request.url.params["limit"] == "2" and request.url.params["clean"] == "true"
        return httpx.Response(200, json=[row(biography="private biography", recentPosts=[{"caption": "secret"}])])

    result = await provider(handler, guard).inspect(handle, operation)
    assert result.state == "public" and result.retryable is False
    assert result.association_confirmed is False and result.posts_analyzed is False
    assert "biography" not in repr(result) and "secret" not in repr(result)
    assert "perfil_teste" not in caplog.text and "private-token" not in caplog.text


async def test_inspection_cannot_change_username_bound_to_submission():
    submission = uuid4()

    class BoundGuard(Guard):
        async def claim_inspection(self, operation_id, submission_id, username, run_id, dataset_id):
            return submission_id == submission and username == "perfil_teste"

    forged_run = SubmittedProfileCheck(submission, "outro_perfil", "run-id", "dataset-id")
    with pytest.raises(ProfileCheckError, match="PROFILE_BUDGET_UNAVAILABLE"):
        await provider(lambda _: pytest.fail("no network"), BoundGuard()).inspect(forged_run, uuid4())


@pytest.mark.parametrize(
    "provider_status,privacy,expected,retryable",
    [
        ("SUCCESS", True, "private", False),
        ("SUCCESS", None, "partial", True),
        ("PARTIAL_RESULT", False, "partial", True),
        ("PROFILE_NOT_FOUND", None, "not_found_unconfirmed", True),
        ("INVALID_INPUT", None, "invalid", False),
        ("PROFILE_UNAVAILABLE", None, "unavailable", True),
        ("RATE_LIMITED", None, "unavailable", True),
        ("LOGIN_WALL", None, "unavailable", True),
        ("BLOCKED", None, "unavailable", True),
        ("TEMPORARY_INSTAGRAM_ERROR", None, "unavailable", True),
        ("PROVIDER_ERROR", None, "unavailable", True),
    ],
)
async def test_documented_actor_states_never_invent_identity(provider_status, privacy, expected, retryable):
    def handler(request):
        if request.url.path.endswith("/actor-runs/run-id"):
            return httpx.Response(200, json=run_response())
        return httpx.Response(200, json=[row(provider_status, isPrivate=privacy)])

    result = await provider(handler).inspect(run(), uuid4())
    assert result.state == expected and result.provider_status == provider_status and result.retryable is retryable
    assert result.association_confirmed is False and result.posts_analyzed is False


@pytest.mark.parametrize("status", ["READY", "RUNNING", "TIMING-OUT", "ABORTING"])
async def test_running_actor_never_reads_dataset(status):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json=run_response(status))

    result = await provider(handler).inspect(run(), uuid4())
    assert result.state == "pending" and result.retryable is True
    assert calls == ["/v2/actor-runs/run-id"]


@pytest.mark.parametrize("status", ["FAILED", "TIMED-OUT", "ABORTED"])
async def test_terminal_failed_actor_is_unavailable_not_nonexistent(status):
    result = await provider(lambda _: httpx.Response(200, json=run_response(status))).inspect(run(), uuid4())
    assert result.state == "unavailable" and result.retryable is True


@pytest.mark.parametrize("profile", ["", "x" * 201, "https://instagram.com/p/abc/", "a..b", None])
async def test_invalid_profile_is_rejected_before_any_claim(profile):
    guard = Guard()
    with pytest.raises(ProfileCheckError, match="PROFILE_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("no network"), guard).submit(profile, uuid4())
    assert guard.calls == []


async def test_invalid_submission_operation_is_rejected():
    with pytest.raises(ProfileCheckError, match="PROFILE_INPUT_INVALID"):
        await ApifyProfileCheck().submit("perfil_teste", "bad-id")


@pytest.mark.parametrize(
    "enabled,token,guard",
    [
        (False, SecretStr("key"), Guard()),
        (True, None, Guard()),
        (True, SecretStr(""), Guard()),
        (True, SecretStr("key"), None),
    ],
)
async def test_disabled_or_unconfigured_never_claims_or_calls(enabled, token, guard):
    with pytest.raises(ProfileCheckError, match="PROFILE_CHECK_DISABLED"):
        await ApifyProfileCheck(token, guard, enabled=enabled).submit("perfil_teste", uuid4())
    if guard:
        assert guard.calls == []


@pytest.mark.parametrize("amount", [None, 0, -1, True, 100_000_001, RuntimeError("private guard info")])
async def test_submission_guard_must_claim_positive_bounded_event_budget(amount):
    guard = Guard(submission=amount)
    with pytest.raises(ProfileCheckError, match="PROFILE_BUDGET_UNAVAILABLE") as error:
        await provider(lambda _: pytest.fail("no network"), guard).submit("perfil_teste", uuid4())
    assert "private guard info" not in str(error.value) and len(guard.calls) == 1


@pytest.mark.parametrize("outcome", [False, RuntimeError("private guard info")])
async def test_inspection_guard_blocks_unauthorized_or_unbudgeted_reads(outcome):
    guard = Guard(inspection=outcome)
    with pytest.raises(ProfileCheckError, match="PROFILE_BUDGET_UNAVAILABLE") as error:
        await provider(lambda _: pytest.fail("no network"), guard).inspect(run(), uuid4())
    assert "private guard info" not in str(error.value) and len(guard.calls) == 1


async def test_uncertain_submission_cannot_be_resent_with_same_operation():
    guard = Guard()
    operation = uuid4()
    count = []

    def handler(request):
        count.append(1)
        raise httpx.ReadTimeout("private request", request=request)

    adapter = provider(handler, guard)
    with pytest.raises(ProfileCheckError, match="PROFILE_SUBMISSION_UNCERTAIN") as error:
        await adapter.submit("perfil_teste", operation)
    assert "private request" not in str(error.value)
    with pytest.raises(ProfileCheckError, match="PROFILE_BUDGET_UNAVAILABLE"):
        await adapter.submit("perfil_teste", operation)
    assert count == [1]


@pytest.mark.parametrize("body", [None, [], {}, {"data": []}, {"data": {}}, {"data": {"id": "https://bad"}}])
async def test_malformed_submission_outcome_is_uncertain(body):
    with pytest.raises(ProfileCheckError, match="PROFILE_SUBMISSION_UNCERTAIN"):
        await provider(lambda _: httpx.Response(200, json=body)).submit("perfil_teste", uuid4())


@pytest.mark.parametrize(
    "handle,operation",
    [
        (None, uuid4()),
        (SubmittedProfileCheck("bad", "perfil_teste", "run-id", "dataset-id"), uuid4()),
        (SubmittedProfileCheck(uuid4(), "perfil_teste", "https://bad", "dataset-id"), uuid4()),
        (SubmittedProfileCheck(uuid4(), "perfil_teste", "run-id", "../bad"), uuid4()),
        (SubmittedProfileCheck(uuid4(), "@perfil_teste", "run-id", "dataset-id"), uuid4()),
        (run(), "bad"),
    ],
)
async def test_invalid_run_handles_cannot_claim_or_call(handle, operation):
    guard = Guard()
    with pytest.raises(ProfileCheckError, match="PROFILE_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("no network"), guard).inspect(handle, operation)
    assert guard.calls == []


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        [],
        {},
        {"data": []},
        run_response(id="wrong"),
        run_response(defaultDatasetId="wrong"),
        run_response(None),
        run_response("UNKNOWN"),
    ],
)
async def test_inconsistent_run_metadata_is_uncertain(metadata):
    with pytest.raises(ProfileCheckError, match="PROFILE_RESULT_UNCERTAIN"):
        await provider(lambda _: httpx.Response(200, json=metadata)).inspect(run(), uuid4())


@pytest.mark.parametrize(
    "rows",
    [
        None,
        [],
        [None],
        [row(), row()],
        [{}],
        [row(input="someone_else")],
        [row(username="someone_else")],
        [row(status=3)],
        [row(status="UNKNOWN")],
        [row(isPrivate="false")],
    ],
)
async def test_absent_ambiguous_or_mismatched_rows_are_not_marked_found(rows):
    def handler(request):
        return httpx.Response(200, json=run_response() if request.url.path.endswith("/actor-runs/run-id") else rows)

    with pytest.raises(ProfileCheckError, match="PROFILE_RESULT_UNCERTAIN"):
        await provider(handler).inspect(run(), uuid4())


@pytest.mark.parametrize(
    "response",
    [httpx.Response(429), httpx.Response(200, text="bad json"), httpx.Response(200, content=b"a" * 1_000_001)],
)
async def test_inspection_http_failures_are_uncertain_and_not_automatically_retried(response):
    guard = Guard()
    operation = uuid4()
    calls = []

    def handler(_):
        calls.append(1)
        return response

    adapter = provider(handler, guard)
    with pytest.raises(ProfileCheckError, match="PROFILE_RESULT_UNCERTAIN"):
        await adapter.inspect(run(), operation)
    with pytest.raises(ProfileCheckError, match="PROFILE_BUDGET_UNAVAILABLE"):
        await adapter.inspect(run(), operation)
    assert calls == [1]


async def test_default_transport_has_no_automatic_retries_or_proxy_environment(monkeypatch):
    def factory(*, retries, trust_env):
        assert retries == 0 and trust_env is False
        return httpx.MockTransport(lambda _: httpx.Response(200, json=run_response("RUNNING")))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    result = await ApifyProfileCheck(SecretStr("key"), Guard(), enabled=True).inspect(run(), uuid4())
    assert result.state == "pending"
