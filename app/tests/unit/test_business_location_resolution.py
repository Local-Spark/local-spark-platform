from dataclasses import replace

import pytest

from app.adapters.google_geocoding import GeocodingAddressComponent, GeocodingCandidate
from app.schemas.editorial_context import ReferenceAddress
from app.services.business_location_resolution import automatic_location_candidate


def component(kind, value, short=None):
    return GeocodingAddressComponent(value, short, (kind,))


def candidate():
    return GeocodingCandidate(
        "synthetic-place",
        "Rua fictícia",
        -23.5,
        -46.6,
        "ROOFTOP",
        "BR",
        (
            component("route", "Rua do Titular"),
            component("street_number", "10"),
            component("locality", "São Paulo"),
            component("administrative_area_level_1", "São Paulo", "SP"),
            component("postal_code", "01234-567"),
        ),
    )


def address():
    return ReferenceAddress(
        street="Rua do Titular", number="10", city="São Paulo", state_code="SP", postal_code="01234567"
    )


def test_automatic_match_uses_only_one_precise_exact_candidate_in_memory():
    item = candidate()
    assert automatic_location_candidate(address(), (item,)) is item
    assert "Rua do Titular" not in repr(item)


@pytest.mark.parametrize(
    "change",
    [
        {"country": None},
        {"country": "US"},
        {"granularity": "APPROXIMATE"},
        {"granularity": "RANGE_INTERPOLATED"},
        {"address_components": ()},
    ],
)
def test_imprecise_missing_and_wrong_country_require_owner_review(change):
    assert automatic_location_candidate(address(), (replace(candidate(), **change),)) is None


@pytest.mark.parametrize(
    "kind,value",
    [
        ("route", "Rua diversa"),
        ("street_number", "11"),
        ("locality", "Campinas"),
        ("postal_code", "01234568"),
        ("postal_code", "bad"),
    ],
)
def test_different_components_require_owner_review(kind, value):
    item = candidate()
    components = tuple(
        replace(part, long_text=value) if kind in part.types else part for part in item.address_components
    )
    assert automatic_location_candidate(address(), (replace(item, address_components=components),)) is None


def test_state_must_match_the_short_code_and_duplicates_are_ambiguous():
    item = candidate()
    parts = tuple(
        replace(part, short_text="RJ") if "administrative_area_level_1" in part.types else part
        for part in item.address_components
    )
    assert automatic_location_candidate(address(), (replace(item, address_components=parts),)) is None
    assert (
        automatic_location_candidate(
            address(), (replace(item, address_components=item.address_components + (item.address_components[0],)),)
        )
        is None
    )


def test_no_unique_result_or_insufficient_owner_address_requires_review():
    item = candidate()
    assert automatic_location_candidate(address(), ()) is None
    assert automatic_location_candidate(address(), (item, item)) is None
    assert automatic_location_candidate(address(), (None,)) is None
    assert automatic_location_candidate(ReferenceAddress(city="São Paulo", state_code="SP"), (item,)) is None
    assert (
        automatic_location_candidate(ReferenceAddress(street="Rua", city="São Paulo", state_code="SP"), (item,)) is None
    )
    assert automatic_location_candidate(None, (item,)) is None
    assert automatic_location_candidate(address(), [item]) is None


def test_supplied_neighborhood_must_also_match():
    item = candidate()
    addr = address().model_copy(update={"neighborhood": "Centro"})
    assert automatic_location_candidate(addr, (item,)) is None
    parts = item.address_components + (component("sublocality_level_1", "centro"),)
    assert automatic_location_candidate(addr, (replace(item, address_components=parts),)) is not None


def test_case_and_whitespace_can_be_normalized_without_weakening_component_match():
    item = candidate()
    parts = tuple(
        replace(part, long_text="  RUA   DO TITULAR  ") if "route" in part.types else part
        for part in item.address_components
    )
    assert automatic_location_candidate(address(), (replace(item, address_components=parts),)) is not None


def test_missing_optional_fields_do_not_invalidate_exact_proof():
    item = candidate()
    addr = ReferenceAddress(street="Rua do Titular", number="10", postal_code="01234567")
    assert automatic_location_candidate(addr, (item,)) is item


def test_precise_match_without_optional_postal_code_uses_city_and_state():
    item = candidate()
    addr = ReferenceAddress(street="Rua do Titular", number="10", city="São Paulo", state_code="SP")
    assert automatic_location_candidate(addr, (item,)) is item


async def test_parsed_mock_response_is_compared_without_persisting_or_rewriting_owner_address():
    import httpx
    from pydantic import SecretStr

    from app.adapters.google_geocoding import GoogleGeocoding

    class Guard:
        async def claim(self, operation_id, request):
            return True

        async def uncertain(self):
            raise AssertionError("unexpected uncertainty")

    from uuid import uuid4

    owner_address = address()
    body = {
        "results": [
            {
                "placeId": "synthetic-place",
                "formattedAddress": "Rua diferente escrita pelo Google",
                "location": {"latitude": -23.5, "longitude": -46.6},
                "granularity": "ROOFTOP",
                "postalAddress": {"regionCode": "BR"},
                "addressComponents": [
                    {"longText": "Rua do Titular", "types": ["route"]},
                    {"longText": "10", "types": ["street_number"]},
                    {"longText": "São Paulo", "types": ["locality"]},
                    {"longText": "São Paulo", "shortText": "SP", "types": ["administrative_area_level_1"]},
                    {"longText": "01234-567", "types": ["postal_code"]},
                ],
            }
        ],
    }
    adapter = GoogleGeocoding(
        SecretStr("synthetic-key"),
        Guard(),
        enabled=True,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
    )
    results = await adapter.geocode("Rua do Titular, 10", uuid4())
    assert automatic_location_candidate(owner_address, results) is results[0]
    assert owner_address.street == "Rua do Titular" and owner_address.number == "10"


@pytest.mark.parametrize(
    "change",
    [
        {"place_id": None},
        {"place_id": ""},
        {"place_id": " x "},
        {"place_id": "x" * 2049},
        {"place_id": "bad\x00id"},
        {"place_id": "bad\ud800"},
        {"address_components": []},
        {"address_components": (None,)},
        {"address_components": tuple(component("route", "x") for _ in range(101))},
        {"confirmed": True},
        {"latitude": None},
        {"latitude": True},
        {"latitude": float("nan")},
        {"latitude": 91.0},
        {"latitude": 10**400},
        {"longitude": -181.0},
    ],
)
def test_forged_candidate_is_rejected_without_using_its_data(change):
    assert automatic_location_candidate(address(), (replace(candidate(), **change),)) is None


@pytest.mark.parametrize(
    "change",
    [
        {"long_text": None},
        {"long_text": " "},
        {"long_text": "x" * 301},
        {"short_text": 1},
        {"short_text": ""},
        {"short_text": "x" * 301},
        {"types": []},
        {"types": ()},
        {"types": (None,)},
        {"types": ("",)},
        {"types": ("x" * 101,)},
        {"types": tuple("x" for _ in range(101))},
    ],
)
def test_forged_components_fail_closed(change):
    item = candidate()
    parts = (replace(item.address_components[0], **change), *item.address_components[1:])
    assert automatic_location_candidate(address(), (replace(item, address_components=parts),)) is None
