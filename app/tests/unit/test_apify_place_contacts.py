import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_place_contacts import ApifyPlaceContacts, PlaceContactsError, SubmittedPlaceContacts


class Guard:
    def __init__(self, submission=True, inspection=True):
        self.submission, self.inspection = submission, inspection
        self.operations = set()
        self.calls = []

    async def claim_submission(self, operation_id, request):
        self.calls.append(("submit", operation_id, json.loads(request.body)["placeIds"][0]))
        self.request = request
        if isinstance(self.submission, Exception):
            raise self.submission
        if operation_id in self.operations:
            return False
        self.operations.add(operation_id)
        return self.submission

    async def claim_inspection(self, operation_id, intent):
        submitted = intent.submission
        self.calls.append(
            (
                "inspect",
                operation_id,
                submitted.submission_id,
                submitted.place_id,
                submitted.run_id,
                submitted.dataset_id,
            )
        )
        self.intent = intent
        if isinstance(self.inspection, Exception):
            raise self.inspection
        if operation_id in self.operations:
            return False
        self.operations.add(operation_id)
        return self.inspection

    async def submission_uncertain(self, operation_id, request):
        self.submission_failed = True

    async def inspection_uncertain(self, operation_id, intent):
        self.inspection_failed = True


def provider(handler, guard=None):
    return ApifyPlaceContacts(
        SecretStr("secret"),
        guard or Guard(),
        enabled=True,
        transport=httpx.MockTransport(handler),
        actor_build="1.2.3",
        provider_actor_id="actor-id",
        max_actor_usd_micros=50_000,
    )


def run():
    return SubmittedPlaceContacts(
        uuid4(), "ChIJtest", "run-id", "dataset-id", "store-id", "queue-id", "build-id", "1.2.3", "actor-id"
    )


def metadata(status="SUCCEEDED", **changes):
    return {
        "data": {
            "id": "run-id",
            "actId": "actor-id",
            "defaultDatasetId": "dataset-id",
            "defaultKeyValueStoreId": "store-id",
            "defaultRequestQueueId": "queue-id",
            "buildId": "build-id",
            "buildNumber": "1.2.3",
            "status": status,
            "finishedAt": "2020-01-01T00:00:00Z",
            **changes,
        }
    }


def row(**changes):
    return {"placeId": "ChIJtest", **changes}


async def test_submit_one_place_with_durable_claim_and_no_sensitive_logging(caplog):
    operation, guard = uuid4(), Guard()

    def handler(request):
        assert guard.calls == [("submit", operation, "ChIJtest")]
        assert request.method == "POST" and request.url.host == "api.apify.com"
        assert request.url.path == "/v2/acts/actor-id/runs"
        assert request.url.params["maxTotalChargeUsd"] == "0.05"
        assert request.url.params["build"] == "1.2.3"
        assert guard.request.url == str(request.url) and guard.request.credential == SecretStr("secret")
        assert request.url.params["restartOnError"] == "false"
        assert request.url.params["forcePermissionLevel"] == "LIMITED_PERMISSIONS"
        assert request.headers["Authorization"] == "Bearer secret" and "secret" not in str(request.url)
        assert json.loads(request.content) == {
            "placeIds": ["ChIJtest"],
            "scrapeContacts": True,
            "maxCrawledPlacesPerSearch": 1,
            "language": "pt-BR",
        }
        return httpx.Response(201, json=metadata())

    result = await provider(handler, guard).submit("ChIJtest", operation)
    assert (result.submission_id, result.run_id, result.dataset_id) == (operation, "run-id", "dataset-id")
    assert "ChIJtest" not in repr(result) and "secret" not in caplog.text


async def test_inspect_provenance_minimization_and_unconfirmed_ownership(caplog):
    submission, operation, guard = run(), uuid4(), Guard()

    def handler(request):
        assert guard.calls == [("inspect", operation, submission.submission_id, "ChIJtest", "run-id", "dataset-id")]
        assert guard.intent.submission == submission
        if request.url.path.endswith("/actor-runs/run-id"):
            return httpx.Response(200, json=metadata())
        assert request.url.params["clean"] == "true" and request.url.params["limit"] == "2"
        return httpx.Response(
            200,
            json=[
                row(
                    website="https://example.org",
                    email="ignore@x.test",
                    instagrams=["https://instagram.com/exemplo"],
                )
            ],
        )

    result = await provider(handler, guard).inspect(submission, operation)
    assert result.state == "found" and result.website_source == "google_maps"
    assert result.website == "https://example.org" and result.social_links[0].source == "business_website"
    assert not result.association_confirmed and not result.identity_verified
    assert "instagram.com" not in repr(result) and "ChIJtest" not in caplog.text and "secret" not in caplog.text


@pytest.mark.parametrize("returned_id", ["ChIJother", "0x123:0x456"])
async def test_other_or_unproven_identifier_never_returns_links(returned_id):
    def handler(request):
        payload = (
            metadata()
            if "/actor-runs/" in request.url.path
            else [
                row(
                    placeId=returned_id,
                    website="https://other.example",
                    instagrams=["https://instagram.com/other"],
                )
            ]
        )
        return httpx.Response(200, json=payload)

    result = await provider(handler).inspect(run(), uuid4())
    assert result.state == "association_unverified"
    assert result.website is None and result.social_links == ()
    assert not result.association_confirmed and not result.identity_verified


@pytest.mark.parametrize(
    "status,expected",
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
async def test_run_states_never_access_dataset(status, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=metadata(status))

    result = await provider(handler).inspect(run(), uuid4())
    assert result.state == expected and len(requests) == 1


async def test_empty_result_does_not_prove_not_found():
    def handler(request):
        return httpx.Response(200, json=metadata() if "/actor-runs/" in request.url.path else [])

    assert (await provider(handler).inspect(run(), uuid4())).state == "not_found_unconfirmed"


@pytest.mark.parametrize("invalid", [None, "", "bad\x00name", "a" * 2049, 123])
async def test_invalid_place_id_never_contacts_provider(invalid):
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network")).submit(invalid, uuid4())


async def test_invalid_submission_operation():
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network")).submit("ChIJtest", "bad")


async def test_opaque_place_id_technical_limit_accepts_2048_characters():
    place_id = "x" * 2047 + "/"
    result = await provider(lambda _: httpx.Response(201, json=metadata())).submit(place_id, uuid4())
    assert result.place_id == place_id


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"enabled": True}, {"enabled": True, "token": SecretStr("")}, {"enabled": True, "token": SecretStr("key")}],
)
async def test_disabled_without_all_configuration(kwargs):
    with pytest.raises(PlaceContactsError, match="CONTACTS_DISABLED"):
        await ApifyPlaceContacts(**kwargs).submit("ChIJtest", uuid4())


@pytest.mark.parametrize("budget", [None, 0, -1, 100_000_001, 1, ValueError("secret")])
async def test_budget_claim_is_required_and_fails_closed(budget):
    with pytest.raises(PlaceContactsError, match="CONTACTS_BUDGET_UNAVAILABLE"):
        await provider(lambda _: pytest.fail("network"), Guard(submission=budget)).submit("ChIJtest", uuid4())


async def test_submit_cannot_be_replayed_after_uncertain_timeout():
    guard, operation, calls = Guard(), uuid4(), []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("token secret")

    adapter = provider(handler, guard)
    with pytest.raises(PlaceContactsError, match="CONTACTS_SUBMISSION_UNCERTAIN"):
        await adapter.submit("ChIJtest", operation)
    with pytest.raises(PlaceContactsError, match="CONTACTS_BUDGET_UNAVAILABLE"):
        await adapter.submit("ChIJtest", operation)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"data": {}},
        {"data": {"id": "bad/id", "defaultDatasetId": "d"}},
        {"data": {"id": "r", "defaultDatasetId": None}},
        metadata(actId="other"),
    ],
)
async def test_malformed_submit_is_uncertain(payload):
    with pytest.raises(PlaceContactsError, match="CONTACTS_SUBMISSION_UNCERTAIN"):
        await provider(lambda _: httpx.Response(201, json=payload)).submit("ChIJtest", uuid4())


@pytest.mark.parametrize("status", [200, 202, 400, 500])
async def test_http_failure_cannot_retry_submission(status):
    with pytest.raises(PlaceContactsError, match="CONTACTS_SUBMISSION_UNCERTAIN"):
        await provider(lambda _: httpx.Response(status)).submit("ChIJtest", uuid4())


async def test_invalid_json_and_oversize_response_are_uncertain():
    for content in (b"not-json", b"x" * 1_000_001):
        with pytest.raises(PlaceContactsError, match="CONTACTS_SUBMISSION_UNCERTAIN"):
            await provider(lambda _, content=content: httpx.Response(201, content=content)).submit("ChIJtest", uuid4())


@pytest.mark.parametrize(
    "run_data",
    [
        None,
        replace(run(), submission_id="bad"),
        replace(run(), place_id="bad\x00id"),
        replace(run(), run_id="bad/id"),
        replace(run(), dataset_id="bad/id"),
        replace(run(), key_value_store_id="bad/id"),
        replace(run(), request_queue_id="bad/id"),
        replace(run(), build_id="bad/id"),
        replace(run(), provider_actor_id="bad/id"),
        replace(run(), provider_actor_id="different"),
        replace(run(), build_number="latest"),
    ],
)
async def test_invalid_inspection_input(run_data):
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network")).inspect(run_data, uuid4())


async def test_invalid_inspection_operation():
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network")).inspect(run(), "bad")


@pytest.mark.parametrize("claimed", [False, None, 1, RuntimeError("secret")])
async def test_inspection_claim_is_mandatory(claimed):
    with pytest.raises(PlaceContactsError, match="CONTACTS_BUDGET_UNAVAILABLE"):
        await provider(lambda _: pytest.fail("network"), Guard(inspection=claimed)).inspect(run(), uuid4())


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"data": {}},
        metadata("BOGUS"),
        metadata(None),
        metadata(id="other"),
        metadata(actId="other"),
        metadata(defaultDatasetId="other"),
    ],
)
async def test_unrecognized_run_metadata_is_uncertain(payload):
    with pytest.raises(PlaceContactsError, match="CONTACTS_RESULT_UNCERTAIN"):
        await provider(lambda _: httpx.Response(200, json=payload)).inspect(run(), uuid4())


@pytest.mark.parametrize(
    "rows",
    [
        None,
        {},
        [1],
        [row(), row()],
        [{}],
        [row(error="unavailable")],
        [row(placeId=None)],
        [row(placeId="")],
        [row(website="javascript:bad")],
        [row(website=5)],
        [row(website="http://a:b@example.org")],
        [row(instagrams={})],
        [row(instagrams=[{}])],
        [row(instagrams=["bad"])],
        [row(instagrams=["http://user:pass@instagram.com/fixture"])],
        [row(instagrams=["javascript:bad"])],
        [row(instagrams=[{}] * 101)],
    ],
)
async def test_malformed_dataset_is_uncertain(rows):
    def handler(request):
        return httpx.Response(200, json=metadata() if "/actor-runs/" in request.url.path else rows)

    with pytest.raises(PlaceContactsError, match="CONTACTS_RESULT_UNCERTAIN"):
        await provider(handler).inspect(run(), uuid4())


async def test_website_and_socials_may_be_absent():
    def handler(request):
        return httpx.Response(200, json=metadata() if "/actor-runs/" in request.url.path else [row()])

    result = await provider(handler).inspect(run(), uuid4())
    assert result.state == "found" and result.website is None and result.social_links == ()


async def test_only_instagram_is_retained_from_social_links():
    def handler(request):
        payload = (
            metadata()
            if "/actor-runs/" in request.url.path
            else [
                row(
                    facebooks=["https://facebook.com/fixture"],
                    instagrams=["https://instagram.com/fixture"],
                    title="Google name must not be returned",
                )
            ]
        )
        return httpx.Response(200, json=payload)

    result = await provider(handler).inspect(run(), uuid4())
    assert [link.platform for link in result.social_links] == ["instagram"]


@pytest.mark.parametrize(
    "build,amount,transport",
    [
        (None, 50_000, True),
        ("x" * 65, 50_000, True),
        ("latest", 50_000, True),
        ("1.2.3", True, True),
        ("1.2.3", 0, True),
        ("1.2.3", 5_000_001, True),
        ("1.2.3", 50_000, False),
    ],
)
async def test_real_transport_and_incomplete_actor_budget_are_disabled(build, amount, transport):
    adapter = ApifyPlaceContacts(
        SecretStr("secret"),
        Guard(),
        enabled=True,
        transport=httpx.MockTransport(lambda _: pytest.fail("network")) if transport else None,
        actor_build=build,
        provider_actor_id="actor-id",
        max_actor_usd_micros=amount,
    )
    with pytest.raises(PlaceContactsError, match="CONTACTS_DISABLED"):
        await adapter.submit("ChIJtest", uuid4())


async def test_internal_helpers_refuse_wrong_credential_and_real_transport():
    request = httpx.Request("POST", "https://example.invalid", headers={"Authorization": "Bearer different"})
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        ApifyPlaceContacts._bind(request, SecretStr("secret"), "actor-id")
    with pytest.raises(PlaceContactsError, match="CONTACTS_DISABLED"):
        await ApifyPlaceContacts()._request_json(request)


async def test_lost_submission_and_inspection_failure_ack_stays_uncertain():
    class BrokenGuard(Guard):
        async def submission_uncertain(self, operation_id, request):
            raise ConnectionError("private")

        async def inspection_uncertain(self, operation_id, intent):
            raise ConnectionError("private")

    with pytest.raises(PlaceContactsError, match="CONTACTS_SUBMISSION_UNCERTAIN") as error:
        await provider(lambda _: httpx.Response(500), BrokenGuard()).submit("ChIJtest", uuid4())
    assert "private" not in str(error.value)
    with pytest.raises(PlaceContactsError, match="CONTACTS_RESULT_UNCERTAIN") as error:
        await provider(lambda _: httpx.Response(500), BrokenGuard()).inspect(run(), uuid4())
    assert "private" not in str(error.value)


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
async def test_invalid_credential_fails_before_request_without_disclosure(secret):
    adapter = ApifyPlaceContacts(
        SecretStr(secret),
        Guard(),
        enabled=True,
        transport=httpx.MockTransport(lambda _: pytest.fail("network")),
        actor_build="1.2.3",
        provider_actor_id="actor-id",
        max_actor_usd_micros=40,
    )
    with pytest.raises(PlaceContactsError, match="CONTACTS_DISABLED") as error:
        await adapter.submit("ChIJtest", uuid4())
    assert "private" not in str(error.value)


def pricing_payload(**changes):
    return {
        "data": {
            "id": "nwua9Gu5YrADL7ZDj",
            "taggedBuilds": {"latest": {"buildNumber": "1.2.3"}},
            "pricingInfos": [
                {
                    "startedAt": "2026-01-01T00:00:00+00:00",
                    "pricingModel": "PAY_PER_EVENT",
                    "minimalMaxTotalChargeUsd": 0.5,
                    **changes,
                }
            ],
        }
    }


def live_fixture(handler, guard=None, **changes):
    return ApifyPlaceContacts(
        SecretStr("synthetic-key"),
        guard or Guard(),
        enabled=True,
        transport=httpx.MockTransport(handler),
        actor_build="1.2.3",
        provider_actor_id="nwua9Gu5YrADL7ZDj",
        max_actor_usd_micros=500_000,
        network_enabled=True,
        **changes,
    )


async def test_compass_live_path_checks_pricing_before_single_admitted_post():
    calls = []
    guard = Guard()

    def respond(request):
        calls.append(request.method)
        if request.method == "GET":
            assert not guard.calls
            return httpx.Response(200, json=pricing_payload())
        assert guard.calls[0][0] == "submit"
        assert json.loads(request.content) == {
            "placeIds": ["ChIJtest"],
            "scrapeContacts": True,
            "maxCrawledPlacesPerSearch": 1,
            "language": "pt-BR",
        }
        return httpx.Response(201, json=metadata(actId="nwua9Gu5YrADL7ZDj"))

    result = await live_fixture(respond, guard).submit("ChIJtest", uuid4())
    assert result.provider_actor_id == "nwua9Gu5YrADL7ZDj" and calls == ["GET", "POST"]


@pytest.mark.parametrize(
    "changes",
    [
        {"pricingModel": "PRICE_PER_DATASET_ITEM"},
        {"isPPEPlatformUsagePaidByUser": True},
        {"minimalMaxTotalChargeUsd": 1},
        {"minimalMaxTotalChargeUsd": -1},
        {"minimalMaxTotalChargeUsd": "NaN"},
        {"startedAt": "2099-01-01T00:00:00+00:00"},
        {"startedAt": "2026-01-01T00:00:00"},
    ],
)
async def test_live_contacts_refuses_unbounded_or_unavailable_pricing(changes):
    guard = Guard()
    adapter = live_fixture(lambda request: httpx.Response(200, json=pricing_payload(**changes)), guard)
    with pytest.raises(PlaceContactsError, match="CONTACTS_PRICING_UNAVAILABLE"):
        await adapter.submit("ChIJtest", uuid4())
    assert not guard.calls


@pytest.mark.parametrize("field", ["id", "taggedBuilds", "pricingInfos"])
async def test_live_contacts_metadata_must_identify_reviewed_actor_and_build(field):
    payload = pricing_payload()
    payload["data"].pop(field)
    guard = Guard()
    with pytest.raises(PlaceContactsError, match="CONTACTS_PRICING_UNAVAILABLE"):
        await live_fixture(lambda _: httpx.Response(200, json=payload), guard).submit("ChIJtest", uuid4())
    assert not guard.calls


@pytest.mark.parametrize("status", ["SUCCEEDED", "FAILED"])
@pytest.mark.parametrize("value,expected", [(None, None), (0, 0), (0.0040001, 4001)])
async def test_terminal_run_reports_provider_cost_separately_from_profiles(status, value, expected):
    def respond(request):
        return httpx.Response(
            200, json=metadata(status=status, usageTotalUsd=value) if "/actor-runs/" in request.url.path else [row()]
        )

    result = await provider(respond).inspect(run(), uuid4())
    assert result.reported_cost_usd_micros == expected


@pytest.mark.parametrize("value", [True, -1, "0.01", float("inf"), 1_000_001])
async def test_malformed_cost_is_not_used_to_release_a_reservation(value):
    from app.adapters.apify_place_contacts import _reported_cost

    with pytest.raises(PlaceContactsError, match="CONTACTS_RESULT_UNCERTAIN"):
        _reported_cost({"usageTotalUsd": value})


@pytest.mark.parametrize("mismatch", ["actor", "build", "price_change"])
async def test_changed_actor_build_or_imminent_price_change_blocks_submission(mismatch):
    from datetime import UTC, datetime, timedelta

    payload = pricing_payload()
    if mismatch == "actor":
        payload["data"]["id"] = "another-actor"
    elif mismatch == "build":
        payload["data"]["taggedBuilds"]["latest"]["buildNumber"] = "2.0.0"
    else:
        payload["data"]["pricingInfos"].append(
            {
                "startedAt": (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
                "pricingModel": "PAY_PER_EVENT",
            }
        )
    guard = Guard()
    with pytest.raises(PlaceContactsError, match="CONTACTS_PRICING_UNAVAILABLE"):
        await live_fixture(lambda _: httpx.Response(200, json=payload), guard).submit("ChIJtest", uuid4())
    assert not guard.calls


async def test_live_transport_is_explicit_and_never_forwards_credentials_to_another_host(monkeypatch):
    created = []

    def factory(**kwargs):
        created.append(kwargs)
        return httpx.MockTransport(lambda _: httpx.Response(200, json=pricing_payload()))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    adapter = live_fixture(lambda _: pytest.fail("unexpected"))
    adapter._transport = None
    await adapter._check_current_pricing(SecretStr("synthetic-key"))
    assert created == [{"retries": 0, "trust_env": False}]
    with pytest.raises(PlaceContactsError, match="CONTACTS_INPUT_INVALID"):
        await adapter._request_json(httpx.Request("GET", "https://unrelated.example/"))
