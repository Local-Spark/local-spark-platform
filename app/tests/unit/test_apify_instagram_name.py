"""Name retrieval uses only the expected mock Instagram profile Actor."""

import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_instagram_name import (
    ApifyInstagramName,
    InstagramNameError,
    NameRun,
    _bind,
    _name,
)


class Guard:
    def __init__(self, submit=True, inspect=True, uncertain_failure=False):
        self.submit, self.inspect, self.uncertain_failure, self.calls = submit, inspect, uncertain_failure, []

    async def claim_submission(self, operation, request):
        self.calls.append(("submit", operation, request))
        if isinstance(self.submit, Exception):
            raise self.submit
        return self.submit

    async def claim_inspection(self, operation, intent):
        self.calls.append(("inspect", operation, intent))
        if isinstance(self.inspect, Exception):
            raise self.inspect
        return self.inspect

    async def submission_uncertain(self, operation, request):
        self.calls.append(("submit_uncertain", operation, request))
        if self.uncertain_failure:
            raise RuntimeError("secret")

    async def inspection_uncertain(self, operation, intent):
        self.calls.append(("inspect_uncertain", operation, intent))
        if self.uncertain_failure:
            raise RuntimeError("secret")


_MISSING = object()


def adapter(handler, guard=_MISSING, **changes):
    options = {
        "token": SecretStr("synthetic-token"),
        "guard": Guard() if guard is _MISSING else guard,
        "enabled": True,
        "transport": httpx.MockTransport(handler),
        "actor_id": "actor-id",
        "actor_build": "1.2.3",
        "max_actor_usd_micros": 50_001,
    }
    return ApifyInstagramName(**{**options, **changes})


def metadata(status="SUCCEEDED", **changes):
    return {
        "data": {
            "id": "run-id",
            "actId": "actor-id",
            "defaultDatasetId": "dataset-id",
            "defaultKeyValueStoreId": "kv-id",
            "defaultRequestQueueId": "queue-id",
            "buildId": "build-id",
            "buildNumber": "1.2.3",
            "status": status,
            **changes,
        }
    }


def run(**changes):
    return replace(
        NameRun(uuid4(), "profile", "actor-id", "run-id", "dataset-id", "kv-id", "queue-id", "1.2.3", "build-id"),
        **changes,
    )


async def test_submit_exact_fixed_actor_request_and_fenced_ids():
    guard, operation = Guard(), uuid4()

    def handler(request):
        kind, op, binding = guard.calls[0]
        assert (kind, op) == ("submit", operation) and binding.body == request.content
        assert request.url.path == "/v2/acts/apify~instagram-profile-scraper/runs"
        assert request.url.params["build"] == "1.2.3" and request.url.params["maxTotalChargeUsd"] == "0.050001"
        assert request.url.params["maxItems"] == "1"
        assert request.url.params["forcePermissionLevel"] == "LIMITED_PERMISSIONS"
        assert json.loads(request.content) == {"usernames": ["profile"], "includeAboutSection": False}
        assert binding.credential.get_secret_value() == "synthetic-token" and "profile" not in repr(binding)
        return httpx.Response(201, json=metadata())

    result = await adapter(handler, guard).submit("@Profile", operation)
    assert result.handle == "profile" and result.actor_id == "actor-id" and result.dataset_id == "dataset-id"
    assert result.key_value_store_id == "kv-id" and result.request_queue_id == "queue-id"
    assert "profile" not in repr(result)


async def test_inspection_verifies_run_and_profile_and_discards_other_fields():
    item, operation, guard = run(), uuid4(), Guard()

    def handler(request):
        assert guard.calls[0][1] == operation and guard.calls[0][2].run == item
        if request.url.path.endswith("/actor-runs/run-id"):
            return httpx.Response(200, json=metadata())
        assert request.url.params["limit"] == "2"
        return httpx.Response(
            200, json=[{"username": "PROFILE", "fullName": " Café Teste ", "otherGoogleField": "must not survive"}]
        )

    result = await adapter(handler, guard).inspect(item, operation)
    assert result.state == "found" and result.full_name == "Café Teste" and result.association_confirmed is False
    assert set(result.__dict__) == {"state", "full_name", "association_confirmed"}
    assert "Café" not in repr(result)


def test_binding_checks_sent_credential():
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_INPUT_INVALID"):
        _bind(
            httpx.Request("GET", "https://api.apify.com", headers={"Authorization": "Bearer wrong"}),
            SecretStr("synthetic-token"),
        )


@pytest.mark.parametrize("profile", [None, "", "x" * 201, "a..b"])
async def test_invalid_input_never_claims(profile):
    guard = Guard()
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call"), guard).submit(profile, uuid4())
    assert not guard.calls


async def test_invalid_operation_rejected():
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call")).submit("profile", "not-uuid")


@pytest.mark.parametrize(
    "change",
    [
        {"enabled": False},
        {"token": None},
        {"token": SecretStr("")},
        {"guard": None},
        {"transport": None},
        {"transport": httpx.AsyncHTTPTransport()},
        {"actor_id": "!"},
        {"actor_build": "latest"},
        {"max_actor_usd_micros": 0},
        {"max_actor_usd_micros": True},
        {"max_actor_usd_micros": 5_000_001},
    ],
)
async def test_disabled_or_unpinned_configuration_never_calls(change):
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_DISABLED"):
        await adapter(lambda _: pytest.fail("no call"), **change).submit("profile", uuid4())


@pytest.mark.parametrize("decision", [False, RuntimeError("secret")])
async def test_submission_guard_failure_never_dispatches(decision):
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_BUDGET_UNAVAILABLE"):
        await adapter(lambda _: pytest.fail("no call"), Guard(submit=decision)).submit("profile", uuid4())


@pytest.mark.parametrize(
    "body", [None, {}, {"data": []}, metadata(actId="maps-actor"), metadata(buildNumber="9.9.9"), metadata(id="bad/id")]
)
@pytest.mark.parametrize("uncertain_failure", [False, True])
async def test_bad_submission_is_uncertain_and_retains_fence(body, uncertain_failure):
    guard = Guard(uncertain_failure=uncertain_failure)
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_SUBMISSION_UNCERTAIN"):
        await adapter(lambda _: httpx.Response(201, json=body), guard).submit("profile", uuid4())
    assert guard.calls[-1][0] == "submit_uncertain"


@pytest.mark.parametrize(
    "change",
    [
        {"submission_id": "bad"},
        {"actor_id": "bad/id"},
        {"run_id": "bad/id"},
        {"dataset_id": "bad/id"},
        {"build_number": "latest"},
        {"handle": "Profile"},
        {"actor_id": "other"},
        {"build_number": "9.9.9"},
    ],
)
async def test_invalid_run_or_other_actor_is_not_inspected(change):
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call")).inspect(run(**change), uuid4())


async def test_wrong_run_type_or_operation_is_rejected():
    for value, operation in ((None, uuid4()), (run(), "bad")):
        with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_INPUT_INVALID"):
            await adapter(lambda _: pytest.fail("no call")).inspect(value, operation)


@pytest.mark.parametrize("decision", [False, RuntimeError("secret")])
async def test_inspection_guard_failure_never_dispatches(decision):
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_BUDGET_UNAVAILABLE"):
        await adapter(lambda _: pytest.fail("no call"), Guard(inspect=decision)).inspect(run(), uuid4())


@pytest.mark.parametrize(
    "status,state",
    [
        ("READY", "pending"),
        ("RUNNING", "pending"),
        ("TIMING-OUT", "pending"),
        ("ABORTING", "pending"),
        ("FAILED", "unavailable"),
        ("TIMED-OUT", "unavailable"),
        ("ABORTED", "unavailable"),
    ],
)
async def test_run_states_do_not_assume_name(status, state):
    result = await adapter(lambda _: httpx.Response(200, json=metadata(status))).inspect(run(), uuid4())
    assert result.state == state and result.full_name is None


@pytest.mark.parametrize(
    "body",
    [
        None,
        {},
        {"data": []},
        metadata(actId="maps-actor"),
        metadata(defaultDatasetId="other"),
        metadata(status="UNKNOWN"),
    ],
)
@pytest.mark.parametrize("uncertain_failure", [False, True])
async def test_invalid_metadata_is_uncertain(body, uncertain_failure):
    guard = Guard(uncertain_failure=uncertain_failure)
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_RESULT_UNCERTAIN"):
        await adapter(lambda _: httpx.Response(200, json=body), guard).inspect(run(), uuid4())
    assert guard.calls[-1][0] == "inspect_uncertain"


@pytest.mark.parametrize(
    "rows",
    [
        None,
        {},
        [None],
        [{"username": "different", "fullName": "Other"}],
        [{"username": "profile", "fullName": "x", "error": "failed"}],
        [{"username": "@profile", "fullName": "Other"}],
        [{"username": "profile", "fullName": " "}],
        [{"username": "profile", "fullName": "\ud800"}],
        [{"username": "profile", "fullName": "x" * 201}],
        [{"username": "profile", "fullName": "x\x00"}],
        [{"username": 22, "fullName": "x"}],
        [{"username": "a..b", "fullName": "x"}],
        [{"username": "profile", "fullName": []}],
        [{"username": "profile", "fullName": "x"}, {"username": "profile", "fullName": "x"}],
    ],
)
def test_untrusted_dataset_never_accepts_different_profile_or_bad_name(rows):
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_RESULT_UNCERTAIN"):
        _name(rows, "profile")


@pytest.mark.parametrize("rows", [[], [{"username": "profile"}], [{"username": "profile", "fullName": ""}]])
def test_missing_profile_name_is_unavailable(rows):
    assert _name(rows, "profile").state == "unavailable"


@pytest.mark.parametrize(
    "response",
    [httpx.Response(500), httpx.Response(200, content=b"bad json"), httpx.Response(200, content=b"x" * 1_000_001)],
)
async def test_bad_http_is_uncertain(response):
    guard = Guard()
    with pytest.raises(InstagramNameError, match="INSTAGRAM_NAME_RESULT_UNCERTAIN"):
        await adapter(lambda _: response, guard).inspect(run(), uuid4())
    assert guard.calls[-1][0] == "inspect_uncertain"
