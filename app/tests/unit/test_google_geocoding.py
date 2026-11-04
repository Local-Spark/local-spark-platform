import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.google_geocoding import GEOCODING_FIELD_MASK, GeocodingError, GoogleGeocoding


class Guard:
    def __init__(self, outcome=True):
        self.outcome = outcome
        self.claims = []
        self.requests = []
        self.uncertain_count = 0

    async def claim(self, operation_id, request):
        self.claims.append(operation_id)
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    async def uncertain(self):
        self.uncertain_count += 1


def candidate(**changes):
    return {
        "placeId": "synthetic-id",
        "formattedAddress": "Rua Fictícia, 10, Exemplo - SP, Brasil",
        "location": {"latitude": -23.5, "longitude": -46.6},
        "granularity": "ROOFTOP",
        "postalAddress": {"regionCode": "BR"},
        **changes,
    }


def provider(handler, guard=None):
    return GoogleGeocoding(
        SecretStr("private-key"), guard or Guard(), enabled=True, transport=httpx.MockTransport(handler)
    )


async def test_v4_request_returns_all_unconfirmed_candidates_after_guard_claim(caplog):
    operation = uuid4()
    guard = Guard()

    def handler(request):
        assert guard.claims == [operation]
        assert guard.requests[0].url == str(request.url)
        assert guard.requests[0].field_mask == request.headers["X-Goog-FieldMask"]
        assert guard.requests[0].credential == SecretStr("private-key")
        assert "Fictícia" not in repr(guard.requests[0])
        assert request.url.host == "geocode.googleapis.com"
        assert request.url.path == "/v4/geocode/address"
        assert request.url.params["address.addressLines"] == "Rua Fictícia 10"
        assert request.url.params["address.regionCode"] == "BR"
        assert request.url.params["languageCode"] == "pt-BR"
        assert request.headers["X-Goog-Api-Key"] == "private-key"
        assert "private-key" not in str(request.url)
        assert request.headers["X-Goog-FieldMask"] == GEOCODING_FIELD_MASK
        assert "results.addressComponents" in request.headers["X-Goog-FieldMask"]
        return httpx.Response(
            200,
            json={"results": [candidate(), candidate(placeId="second", granularity="APPROXIMATE")]},
        )

    result = await provider(handler, guard).geocode("Rua Fictícia 10", operation)
    assert [item.place_id for item in result] == ["synthetic-id", "second"]
    assert all(item.confirmed is False for item in result)
    assert result[0].country == "BR" and result[1].granularity == "APPROXIMATE"
    assert "Rua Fictícia" not in repr(result) and "private-key" not in caplog.text
    assert "Rua Fictícia" not in caplog.text


@pytest.mark.parametrize("data", [{}, {"results": []}])
async def test_no_results_is_empty_not_a_confirmed_location(data):
    assert await provider(lambda _: httpx.Response(200, json=data)).geocode("Rua Fictícia", uuid4()) == ()


async def test_missing_optional_country_does_not_claim_location_is_in_brazil():
    item = candidate()
    del item["postalAddress"]
    found = await provider(lambda _: httpx.Response(200, json={"results": [item]})).geocode("Fictícia", uuid4())
    assert found[0].country is None and found[0].confirmed is False


async def test_place_id_technical_limit_accepts_2048_characters():
    found = await provider(lambda _: httpx.Response(200, json={"results": [candidate(placeId="x" * 2048)]})).geocode(
        "Fictícia", uuid4()
    )
    assert len(found[0].place_id) == 2048


@pytest.mark.parametrize("bad", ["", "  ", "x" * 301, None])
async def test_invalid_address_cannot_reserve_or_send(bad):
    guard = Guard()
    with pytest.raises(GeocodingError, match="GEOCODING_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("no call"), guard).geocode(bad, uuid4())
    assert not guard.claims


async def test_invalid_operation_is_rejected():
    with pytest.raises(GeocodingError, match="GEOCODING_INPUT_INVALID"):
        await GoogleGeocoding().geocode("Fictícia", "bad-id")


@pytest.mark.parametrize(
    "enabled,key,guard",
    [
        (False, SecretStr("key"), Guard()),
        (True, None, Guard()),
        (True, SecretStr(""), Guard()),
        (True, SecretStr("key"), None),
    ],
)
async def test_explicit_activation_credential_and_guard_required(enabled, key, guard):
    with pytest.raises(GeocodingError, match="GEOCODING_DISABLED"):
        await GoogleGeocoding(key, guard, enabled=enabled).geocode("Fictícia", uuid4())
    if guard is not None:
        assert not guard.claims


@pytest.mark.parametrize("outcome", [False, RuntimeError("private failure")])
async def test_budget_must_be_claimed_before_network(outcome):
    guard = Guard(outcome)
    with pytest.raises(GeocodingError, match="GEOCODING_BUDGET_UNAVAILABLE") as error:
        await provider(lambda _: pytest.fail("no call"), guard).geocode("Fictícia", uuid4())
    assert "private failure" not in str(error.value)
    assert len(guard.claims) == 1


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        candidate(placeId=""),
        candidate(placeId="x" * 2049),
        candidate(formattedAddress=" "),
        candidate(formattedAddress="x" * 501),
        candidate(location="bad"),
        candidate(granularity=""),
        candidate(location={"latitude": True, "longitude": 1}),
        candidate(location={"latitude": float("nan"), "longitude": 1}),
        candidate(location={"latitude": 10**400, "longitude": 1}),
        candidate(location={"latitude": 91, "longitude": 1}),
        candidate(location={"latitude": 1, "longitude": 181}),
        candidate(postalAddress="bad"),
        candidate(postalAddress={"regionCode": "BRA"}),
    ],
)
async def test_invalid_candidates_fail_closed(bad):
    with pytest.raises(GeocodingError, match="GEOCODING_RESPONSE_INVALID"):
        await provider(lambda _: httpx.Response(200, content=json.dumps({"results": [bad]}))).geocode(
            "Fictícia", uuid4()
        )


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(429),
        httpx.Response(201, json={}),
        httpx.Response(200, json={"unexpected": "value"}),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, json={"error": "provider failed"}),
        httpx.Response(200, json={"results": {}}),
        httpx.Response(200, json={"results": [candidate()] * 101}),
        httpx.Response(200, content=b"a" * 1_000_001),
    ],
)
async def test_provider_errors_are_uncertain_and_do_not_leak(response):
    guard = Guard()
    with pytest.raises(GeocodingError, match="GEOCODING_RESULT_UNCERTAIN") as error:
        await provider(lambda _: response, guard).geocode("Rua particular", uuid4())
    assert len(guard.claims) == 1 and "Rua particular" not in str(error.value)
    assert guard.uncertain_count == 1


async def test_network_failure_stays_uncertain():
    def fail(request):
        raise httpx.ConnectError("private network detail", request=request)

    with pytest.raises(GeocodingError, match="GEOCODING_RESULT_UNCERTAIN") as error:
        await provider(fail).geocode("Fictícia", uuid4())
    assert "private network detail" not in str(error.value)


@pytest.mark.parametrize(
    "response,code",
    [
        (httpx.Response(200, json={"results": [{}]}), "GEOCODING_RESPONSE_INVALID"),
        (httpx.Response(500), "GEOCODING_RESULT_UNCERTAIN"),
    ],
)
async def test_lost_uncertainty_ack_never_leaks_or_retries(response, code):
    class BrokenGuard(Guard):
        async def uncertain(self):
            raise ConnectionError("private acknowledgement")

    guard = BrokenGuard()
    with pytest.raises(GeocodingError, match=code) as error:
        await provider(lambda _: response, guard).geocode("Fictícia", uuid4())
    assert "private acknowledgement" not in str(error.value)
    assert len(guard.claims) == 1


async def test_default_transport_is_bounded_and_never_uses_proxy_environment(monkeypatch):
    def factory(*, retries, trust_env):
        assert retries == 0 and trust_env is False
        return httpx.MockTransport(lambda _: httpx.Response(200, json={"results": []}))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    assert await GoogleGeocoding(SecretStr("key"), Guard(), enabled=True).geocode("Fictícia", uuid4()) == ()


async def test_structured_components_are_transient_and_preserved_in_memory():
    item = candidate(
        addressComponents=[
            {"longText": "Rua Fictícia", "shortText": "R. Fictícia", "types": ["route"]},
            {"longText": "10", "types": ["street_number"]},
        ]
    )
    result = await provider(lambda _: httpx.Response(200, json={"results": [item]})).geocode("Fictícia", uuid4())
    assert result[0].address_components[0].long_text == "Rua Fictícia"
    assert result[0].address_components[0].short_text == "R. Fictícia"
    assert result[0].address_components[1].types == ("street_number",)
    assert "Rua Fictícia" not in repr(result[0].address_components)


@pytest.mark.parametrize(
    "components",
    [
        None,
        {},
        [None],
        [{}],
        [{"longText": "", "types": ["route"]}],
        [{"longText": "x" * 301, "types": ["route"]}],
        [{"longText": "x", "shortText": "", "types": ["route"]}],
        [{"longText": "x", "shortText": "x" * 301, "types": ["route"]}],
        [{"longText": "x", "types": []}],
        [{"longText": "x", "types": [None]}],
        [{"longText": "x", "types": ["x" * 101]}],
        [{"longText": "x", "types": ["route"]}] * 101,
        [{"longText": "x", "types": ["route"] * 101}],
    ],
)
async def test_malformed_structured_components_are_uncertain(components):
    guard = Guard()
    with pytest.raises(GeocodingError, match="GEOCODING_RESPONSE_INVALID"):
        await provider(
            lambda _: httpx.Response(200, json={"results": [candidate(addressComponents=components)]}), guard
        ).geocode("Fictícia", uuid4())
    assert guard.uncertain_count == 1


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
async def test_invalid_api_key_is_rejected_before_claim_without_disclosure(secret):
    guard = Guard()
    adapter = GoogleGeocoding(
        SecretStr(secret), guard, enabled=True, transport=httpx.MockTransport(lambda _: pytest.fail("no call"))
    )
    with pytest.raises(GeocodingError, match="GEOCODING_DISABLED") as error:
        await adapter.geocode("Rua Fictícia", uuid4())
    assert "private" not in str(error.value) and not guard.claims


async def test_invalid_address_unicode_does_not_leak_or_claim():
    guard = Guard()
    with pytest.raises(GeocodingError, match="GEOCODING_INPUT_INVALID") as error:
        await provider(lambda _: pytest.fail("no call"), guard).geocode("private\ud800", uuid4())
    assert "private" not in str(error.value) and not guard.claims
