import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.google_places import PLACES_FIELD_MASK, GooglePlacesNearby, PlacesError


class Guard:
    def __init__(self, outcome=True):
        self.outcome = outcome
        self.claims = []
        self.requests = []
        self.uncertain_calls = 0
        self.empty_commits = 0

    async def claim(self, operation_id, request):
        self.claims.append(operation_id)
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    async def uncertain(self):
        self.uncertain_calls += 1

    async def complete_empty(self):
        self.empty_commits += 1


def candidate(**changes):
    return {
        "id": "synthetic-id",
        "displayName": {"text": "Negócio Fictício"},
        "location": {"latitude": -23.5, "longitude": -46.6},
        "rating": 4.8,
        "userRatingCount": 173,
        "websiteUri": "https://example.com/",
        "types": ["restaurant", "food"],
        "formattedAddress": "Rua da Amostra, 10, São Paulo - SP",
        "addressComponents": [
            {"longText": "Rua da Amostra", "shortText": "R. Amostra", "types": ["route"]},
            {"longText": "10", "types": ["street_number"]},
        ],
        **changes,
    }


def provider(handler, guard=None):
    return GooglePlacesNearby(
        SecretStr("private-key"), guard or Guard(), enabled=True, transport=httpx.MockTransport(handler)
    )


@pytest.mark.parametrize("radius", [5, 20, 50])
async def test_uses_strict_circle_and_preserves_provider_order_and_values(radius, caplog):
    operation = uuid4()
    guard = Guard()

    def handler(request):
        assert guard.claims == [operation]
        assert request.method == "POST" and request.url.host == "places.googleapis.com"
        assert request.url.path == "/v1/places:searchNearby"
        assert request.headers["X-Goog-Api-Key"] == "private-key"
        binding = guard.requests[0]
        assert binding.method == request.method and binding.url == str(request.url)
        assert binding.body == request.content
        assert binding.field_mask == request.headers["X-Goog-FieldMask"]
        assert "private-key" not in repr(binding)
        assert "private-key" not in str(request.url)
        body = json.loads(request.content)
        assert body["includedTypes"] == ["restaurant"] and body["maxResultCount"] == 10
        assert body["locationRestriction"]["circle"] == {
            "center": {"latitude": -23.5, "longitude": -46.6},
            "radius": radius * 1000,
        }
        assert "rankPreference" not in body and "textQuery" not in body
        assert request.headers["X-Goog-FieldMask"] == PLACES_FIELD_MASK
        assert "places.formattedAddress" in request.headers["X-Goog-FieldMask"]
        assert "places.addressComponents" in request.headers["X-Goog-FieldMask"]
        return httpx.Response(200, json={"places": [candidate(rating=3), candidate(id="second", rating=5)]})

    result = await provider(handler, guard).search("restaurant", -23.5, -46.6, radius, operation)
    assert [item.place_id for item in result] == ["synthetic-id", "second"]
    assert [item.rating for item in result] == [3, 5]
    assert result[0].rating_count == 173 and result[0].website == "https://example.com/"
    assert result[0].types == ("restaurant", "food")
    assert result[0].formatted_address == "Rua da Amostra, 10, São Paulo - SP"
    assert result[0].address_components[0].long_text == "Rua da Amostra"
    assert result[0].address_components[0].short_text == "R. Amostra"
    assert result[0].address_components[1].types == ("street_number",)
    assert "Rua da Amostra" not in repr(result) and "Rua da Amostra" not in caplog.text
    assert "Negócio Fictício" not in repr(result) and "private-key" not in caplog.text


@pytest.mark.parametrize("data", [{}, {"places": []}])
async def test_no_candidates_is_empty(data):
    assert await provider(lambda _: httpx.Response(200, json=data)).search("restaurant", 1, 1, 5, uuid4()) == ()


async def test_place_id_technical_limit_accepts_2048_characters():
    result = await provider(lambda _: httpx.Response(200, json={"places": [candidate(id="x" * 2048)]})).search(
        "restaurant", 1, 1, 5, uuid4()
    )
    assert len(result[0].place_id) == 2048


async def test_empty_response_is_committed_once_and_replay_never_calls_provider():
    guard = Guard()
    assert (
        await provider(lambda _: httpx.Response(200, json={"places": []}), guard).search("restaurant", 1, 1, 5, uuid4())
        == ()
    )
    assert guard.empty_commits == 1 and guard.uncertain_calls == 0
    replay = Guard("completed_empty")
    assert await provider(lambda _: pytest.fail("network called"), replay).search("restaurant", 1, 1, 5, uuid4()) == ()
    assert replay.empty_commits == 0


async def test_empty_commit_failure_marks_reservation_uncertain_without_exposing_error():
    guard = Guard()

    async def failed_commit():
        raise RuntimeError("private database detail")

    guard.complete_empty = failed_commit
    with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN") as error:
        await provider(lambda _: httpx.Response(200, json={"places": []}), guard).search("restaurant", 1, 1, 5, uuid4())
    assert guard.uncertain_calls == 1 and "private database detail" not in str(error.value)


async def test_optional_fields_are_not_invented():
    found = await provider(lambda _: httpx.Response(200, json={"places": [{"id": "test-id"}]})).search(
        "restaurant", 1, 1, 5, uuid4()
    )
    assert (found[0].name, found[0].latitude, found[0].longitude, found[0].rating, found[0].rating_count) == (
        None,
        None,
        None,
        None,
        None,
    )
    assert found[0].website is None and found[0].formatted_address is None
    assert found[0].address_components == ()


async def test_protobuf_can_omit_zero_coordinate_fields():
    found = await provider(lambda _: httpx.Response(200, json={"places": [candidate(location={})]})).search(
        "restaurant", 1, 1, 5, uuid4()
    )
    assert found[0].latitude == 0 and found[0].longitude == 0


@pytest.mark.parametrize(
    "place_type,latitude,longitude,radius,operation",
    [
        ("", 1, 1, 5, uuid4()),
        ("café", 1, 1, 5, uuid4()),
        ("x" * 81, 1, 1, 5, uuid4()),
        ("restaurant", True, 1, 5, uuid4()),
        ("restaurant", "not a coordinate", 1, 5, uuid4()),
        ("restaurant", float("nan"), 1, 5, uuid4()),
        ("restaurant", 91, 1, 5, uuid4()),
        ("restaurant", 1, 181, 5, uuid4()),
        ("restaurant", 1, 1, 0, uuid4()),
        ("restaurant", 1, 1, 10, uuid4()),
        ("restaurant", 1, 1, 5.0, uuid4()),
        ("restaurant", 1, 1, 5, "bad-operation"),
    ],
)
async def test_invalid_request_never_claims_or_calls(place_type, latitude, longitude, radius, operation):
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network called"), guard).search(
            place_type, latitude, longitude, radius, operation
        )
    assert guard.claims == []


@pytest.mark.parametrize(
    "enabled,key,guard",
    [
        (False, SecretStr("key"), Guard()),
        (True, None, Guard()),
        (True, SecretStr(""), Guard()),
        (True, SecretStr("key"), None),
    ],
)
async def test_opt_in_credential_and_budget_guard_are_required(enabled, key, guard):
    with pytest.raises(PlacesError, match="PLACES_DISABLED"):
        await GooglePlacesNearby(key, guard, enabled=enabled).search("restaurant", 1, 1, 5, uuid4())
    if guard is not None:
        assert guard.claims == []


@pytest.mark.parametrize("outcome", [False, RuntimeError("private detail")])
async def test_budget_claim_must_complete_before_provider_call(outcome):
    guard = Guard(outcome)
    with pytest.raises(PlacesError, match="PLACES_BUDGET_UNAVAILABLE") as error:
        await provider(lambda _: pytest.fail("network called"), guard).search("restaurant", 1, 1, 5, uuid4())
    assert len(guard.claims) == 1 and "private detail" not in str(error.value)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        candidate(id=" "),
        candidate(id="x" * 2049),
        candidate(displayName="bad"),
        candidate(displayName={"text": " "}),
        candidate(location="bad"),
        candidate(location={"latitude": True, "longitude": 1}),
        candidate(location={"latitude": float("nan"), "longitude": 1}),
        candidate(location={"latitude": 91, "longitude": 1}),
        candidate(location={"latitude": 1, "longitude": 181}),
        candidate(rating=True),
        candidate(rating=5.1),
        candidate(rating=10**400),
        candidate(userRatingCount=-1),
        candidate(userRatingCount=True),
        candidate(websiteUri=" "),
        candidate(types="not-a-list"),
        candidate(types=["restaurant", "restaurant"]),
        candidate(types=["invalid type"]),
        candidate(types=[f"type_{number}" for number in range(51)]),
    ],
)
async def test_invalid_result_is_never_silently_accepted(bad):
    with pytest.raises(PlacesError, match="PLACES_RESPONSE_INVALID"):
        await provider(lambda _: httpx.Response(200, content=json.dumps({"places": [bad]}))).search(
            "restaurant", 1, 1, 5, uuid4()
        )


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(429),
        httpx.Response(201, json={}),
        httpx.Response(202, json={}),
        httpx.Response(200, text="bad json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, json={"unexpected": "unverified-empty"}),
        httpx.Response(200, json={"error": "provider failed"}),
        httpx.Response(200, json={"places": {}}),
        httpx.Response(200, json={"places": [candidate()] * 11}),
        httpx.Response(200, content=b"a" * 1_000_001),
    ],
)
async def test_provider_error_is_uncertain_not_retried_or_exposed(response):
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN") as error:
        await provider(lambda _: response, guard).search("restaurant", 1, 1, 5, uuid4())
    assert len(guard.claims) == 1 and "private-key" not in str(error.value)


async def test_network_error_stays_uncertain():
    def fail(request):
        raise httpx.ConnectError("private detail", request=request)

    with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN") as error:
        await provider(fail).search("restaurant", 1, 1, 5, uuid4())
    assert "private detail" not in str(error.value)


@pytest.mark.parametrize("bad_result", [False, True])
async def test_uncertain_dispatch_retains_guard_even_if_reconciliation_fails(bad_result):
    guard = Guard()

    async def unavailable():
        guard.uncertain_calls += 1
        raise RuntimeError("sensitive detail")

    guard.uncertain = unavailable

    def handler(request):
        if bad_result:
            return httpx.Response(200, json={"places": [{"id": ""}]})
        raise RuntimeError("sensitive detail")

    with pytest.raises(PlacesError) as error:
        await provider(handler, guard).search("restaurant", 1, 1, 5, uuid4())
    assert guard.uncertain_calls == 1
    assert "sensitive detail" not in str(error.value)


async def test_default_transport_has_no_retries_or_proxy_environment(monkeypatch):
    def factory(*, retries, trust_env):
        assert retries == 0 and trust_env is False
        return httpx.MockTransport(lambda _: httpx.Response(200, json={"places": []}))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    assert (
        await GooglePlacesNearby(SecretStr("key"), Guard(), enabled=True).search("restaurant", 1, 1, 5, uuid4()) == ()
    )


async def test_primary_types_are_explicit_and_do_not_intersect_with_general_type():
    operation = uuid4()
    guard = Guard()

    def handler(request):
        body = json.loads(request.content)
        assert body["includedPrimaryTypes"] == ["cafe", "bakery", "dessert_shop"]
        assert "includedTypes" not in body
        assert body["maxResultCount"] == 20
        return httpx.Response(200, json={"places": [candidate(id=f"fake-{i}") for i in range(20)]})

    results = await provider(handler, guard).search(
        None,
        -23.5,
        -46.6,
        5,
        operation,
        primary_types=["cafe", "bakery", "dessert_shop"],
        max_results=20,
    )
    assert len(results) == 20
    assert guard.claims == [operation]


async def test_up_to_fifty_explicit_primary_types_are_supported():
    primary = tuple(f"type_{number}" for number in range(50))

    def handler(request):
        assert json.loads(request.content)["includedPrimaryTypes"] == list(primary)
        return httpx.Response(200, json={"places": []})

    assert await provider(handler).search(None, 1, 1, 5, uuid4(), primary_types=primary) == ()


@pytest.mark.parametrize(
    "place_type,primary,max_results",
    [
        (None, None, 10),
        (None, [], 10),
        (None, ["cafe"] * 2, 10),
        (None, ["cafe", "café"], 10),
        (None, ["cafe", None], 10),
        (None, [f"type_{number}" for number in range(51)], 10),
        (None, "cafe", 10),
        ("cafe", ["bakery"], 10),
        ("cafe", None, 0),
        ("cafe", None, 21),
        ("cafe", None, True),
        ("cafe", None, 1.0),
    ],
)
async def test_invalid_extended_input_never_claims_or_calls(place_type, primary, max_results):
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_INPUT_INVALID"):
        await provider(lambda _: pytest.fail("network called"), guard).search(
            place_type, 1, 1, 5, uuid4(), primary_types=primary, max_results=max_results
        )
    assert guard.claims == []


async def test_rejects_response_exceeding_requested_limit():
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_RESULT_UNCERTAIN"):
        await provider(lambda _: httpx.Response(200, json={"places": [candidate()] * 2}), guard).search(
            None, 1, 1, 5, uuid4(), primary_types=["cafe"], max_results=1
        )
    assert len(guard.claims) == 1


@pytest.mark.parametrize("value", ["", "  ", "x" * 1001, 123, []])
async def test_malformed_formatted_address_is_uncertain_without_disclosure(value):
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_RESPONSE_INVALID") as error:
        await provider(
            lambda _: httpx.Response(200, json={"places": [candidate(formattedAddress=value)]}), guard
        ).search("restaurant", 1, 1, 5, uuid4())
    assert guard.uncertain_calls == 1 and "Rua da Amostra" not in str(error.value)


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
async def test_invalid_api_key_is_rejected_before_claim_without_disclosure(secret):
    guard = Guard()
    adapter = GooglePlacesNearby(
        SecretStr(secret), guard, enabled=True, transport=httpx.MockTransport(lambda _: pytest.fail("no call"))
    )
    with pytest.raises(PlacesError, match="PLACES_DISABLED") as error:
        await adapter.search("restaurant", 1, 1, 5, uuid4())
    assert "private" not in str(error.value) and not guard.claims


@pytest.mark.parametrize(
    "components",
    [
        None,
        {},
        [None],
        [{"longText": "x" * 301, "types": ["route"]}],
        [{"longText": "x", "shortText": "x" * 301, "types": ["route"]}],
        [{"longText": "x", "types": None}],
        [{"longText": "x", "types": [None]}],
        [{"longText": "x", "types": ["x" * 101]}],
        [{"types": "route"}],
        [{"types": [None]}],
        [{"longText": "", "types": [""]}],
        [{"longText": "", "shortText": 1, "types": []}],
        [{"longText": 1, "types": []}],
        [{"longText": "x", "types": ["route"]}] * 101,
        [{"longText": "x", "types": ["route"] * 101}],
    ],
)
async def test_malformed_address_components_are_uncertain_without_disclosure(components):
    guard = Guard()
    with pytest.raises(PlacesError, match="PLACES_RESPONSE_INVALID") as error:
        await provider(
            lambda _: httpx.Response(200, json={"places": [candidate(addressComponents=components)]}), guard
        ).search("restaurant", 1, 1, 5, uuid4())
    assert guard.uncertain_calls == 1 and "Rua da Amostra" not in str(error.value)


@pytest.mark.parametrize(
    "component",
    [
        {},
        {"longText": "Fixture"},
        {"longText": "Fixture", "types": []},
        {"types": ["route"]},
        {"longText": "", "types": ["route"]},
        {"longText": "", "shortText": "", "types": []},
    ],
)
async def test_default_address_component_fields_do_not_discard_a_valid_candidate(component):
    guard = Guard()
    usable = {"longText": "Rua da Amostra", "shortText": "", "types": ["route"]}
    found = await provider(
        lambda _: httpx.Response(200, json={"places": [candidate(addressComponents=[component, usable])]}), guard
    ).search("restaurant", 1, 1, 5, uuid4())
    assert len(found) == 1 and found[0].place_id == "synthetic-id"
    assert found[0].rating == 4.8 and found[0].rating_count == 173
    assert len(found[0].address_components) == 1
    assert found[0].address_components[0].long_text == "Rua da Amostra"
    assert found[0].address_components[0].short_text is None
    assert found[0].address_components[0].types == ("route",)
    assert guard.uncertain_calls == 0 and guard.empty_commits == 0
