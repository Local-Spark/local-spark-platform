from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_contacts_terminal_failure import ApifyContactsTerminalFailure, ContactsTerminalError
from app.adapters.apify_place_contacts import SubmittedPlaceContacts


class Guard:
    def __init__(self, outcome=True, fail_ack=False):
        self.outcome, self.fail_ack, self.calls, self.uncertain_calls = outcome, fail_ack, [], []

    async def claim(self, operation, binding):
        self.calls.append((operation, binding))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    async def uncertain(self, operation, binding):
        self.uncertain_calls.append((operation, binding))
        if self.fail_ack:
            raise ConnectionError("private ack")


def submission():
    return SubmittedPlaceContacts(
        uuid4(), "place-test", "run-1", "data-1", "store-1", "queue-1", "build-1", "1.2.3", "actor-1"
    )


def response_data(run, status):
    return {
        "data": {
            "id": run.run_id,
            "actId": run.provider_actor_id,
            "defaultDatasetId": run.dataset_id,
            "defaultKeyValueStoreId": run.key_value_store_id,
            "defaultRequestQueueId": run.request_queue_id,
            "buildId": run.build_id,
            "buildNumber": run.build_number,
            "status": status,
        }
    }


def provider(handler, guard=None):
    return ApifyContactsTerminalFailure(
        SecretStr("private-key"), guard or Guard(), enabled=True, transport=httpx.MockTransport(handler)
    )


@pytest.mark.parametrize("status", ["FAILED", "TIMED-OUT", "ABORTED"])
async def test_mock_authenticated_exact_run_and_build_yields_only_terminal_failure(status, caplog):
    run, guard, operation = submission(), Guard(), uuid4()

    def handler(request):
        assert len(guard.calls) == 1 and guard.calls[0][0] == operation
        binding = guard.calls[0][1]
        assert binding.submission == run and binding.request.url == str(request.url)
        assert binding.request.credential == SecretStr("private-key") and "private-key" not in repr(binding)
        assert request.url.path == "/v2/actor-runs/run-1" and request.headers["Authorization"] == "Bearer private-key"
        return httpx.Response(200, json=response_data(run, status))

    failure = await provider(handler, guard).inspect(run, operation)
    assert failure.status == status and failure.run_id == "run-1" and failure.build_id == "build-1"
    assert not guard.uncertain_calls and "run-1" not in repr(failure) and "private-key" not in caplog.text


@pytest.mark.parametrize("status", ["READY", "RUNNING", "TIMING-OUT", "ABORTING", "SUCCEEDED"])
async def test_nonfailure_never_produces_retry_evidence(status):
    run = submission()
    assert await provider(lambda _: httpx.Response(200, json=response_data(run, status))).inspect(run, uuid4()) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("submission_id", "bad"),
        ("place_id", ""),
        ("run_id", "bad/id"),
        ("dataset_id", "bad/id"),
        ("key_value_store_id", "bad/id"),
        ("request_queue_id", "bad/id"),
        ("build_id", "bad/id"),
        ("provider_actor_id", "bad/id"),
        ("build_number", None),
        ("build_number", "latest"),
        ("build_number", "1" * 65),
    ],
)
async def test_invalid_source_never_claims_or_contacts_provider(field, value):
    guard = Guard()
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network"), guard).inspect(
            replace(submission(), **{field: value}), uuid4()
        )
    assert not guard.calls


async def test_invalid_object_and_operation_are_rejected():
    for run, operation in ((None, uuid4()), (submission(), "bad")):
        with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_INPUT_INVALID"):
            await ApifyContactsTerminalFailure().inspect(run, operation)


@pytest.mark.parametrize(
    "enabled,key,guard,transport",
    [
        (False, SecretStr("key"), Guard(), True),
        (True, None, Guard(), True),
        (True, SecretStr(""), Guard(), True),
        (True, SecretStr("key"), None, True),
        (True, SecretStr("key"), Guard(), False),
    ],
)
async def test_no_real_transport_or_unconfigured_effect(enabled, key, guard, transport):
    adapter = ApifyContactsTerminalFailure(
        key,
        guard,
        enabled=enabled,
        transport=httpx.MockTransport(lambda _: pytest.fail("network")) if transport else None,
    )
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_DISABLED"):
        await adapter.inspect(submission(), uuid4())
    if guard is not None:
        assert not guard.calls


@pytest.mark.parametrize("outcome", [False, None, 1, RuntimeError("private guard")])
async def test_durable_inspection_claim_is_required(outcome):
    guard = Guard(outcome)
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_GUARD_UNAVAILABLE") as error:
        await provider(lambda _: pytest.fail("network"), guard).inspect(submission(), uuid4())
    assert "private guard" not in str(error.value) and not guard.uncertain_calls


@pytest.mark.parametrize(
    "change",
    [
        {"id": "other"},
        {"actId": "other"},
        {"defaultDatasetId": "other"},
        {"defaultKeyValueStoreId": "other"},
        {"defaultRequestQueueId": "other"},
        {"buildId": "other"},
        {"buildNumber": "1.2.4"},
        {"status": "UNKNOWN"},
    ],
)
async def test_different_run_resources_build_or_unknown_status_are_uncertain(change):
    run, guard = submission(), Guard()
    body = response_data(run, "FAILED")
    body["data"].update(change)
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_RESULT_UNCERTAIN"):
        await provider(lambda _: httpx.Response(200, json=body), guard).inspect(run, uuid4())
    assert len(guard.uncertain_calls) == 1


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(201, json={}),
        httpx.Response(500),
        httpx.Response(200, text="not-json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, json={}),
        httpx.Response(200, content=b"x" * 1_000_001),
    ],
)
async def test_http_and_malformed_responses_are_uncertain(response):
    guard = Guard(fail_ack=True)
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_RESULT_UNCERTAIN") as error:
        await provider(lambda _: response, guard).inspect(submission(), uuid4())
    assert "private ack" not in str(error.value) and len(guard.uncertain_calls) == 1


async def test_transport_timeout_is_uncertain_without_provider_details():
    def timeout(request):
        raise httpx.ReadTimeout("private provider detail", request=request)

    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_RESULT_UNCERTAIN") as error:
        await provider(timeout).inspect(submission(), uuid4())
    assert "private provider detail" not in str(error.value)


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
async def test_invalid_credential_fails_before_inspection_without_disclosure(secret):
    adapter = ApifyContactsTerminalFailure(
        SecretStr(secret),
        Guard(),
        enabled=True,
        transport=httpx.MockTransport(lambda _: pytest.fail("network")),
    )
    with pytest.raises(ContactsTerminalError, match="CONTACTS_TERMINAL_DISABLED") as error:
        await adapter.inspect(submission(), uuid4())
    assert "private" not in str(error.value)
