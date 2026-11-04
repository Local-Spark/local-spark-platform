from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.google_places import PlacesChargeableRequest
from app.services.reference_places_request_mac import PlacesBindingError, places_request_mac


def _values():
    return {
        "key": SecretStr("synthetic-key-for-testing-only-0123456789"),
        "key_version": "test-key-v1",
        "tariff_version": "synthetic-price-v1",
        "credential_version": "synthetic-project-v1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "search": uuid4(),
        "effect": uuid4(),
        "pilot": uuid4(),
        "context_version": 1,
        "reserved_usd_micros": 20000,
        "request": PlacesChargeableRequest(
            "POST",
            "https://places.googleapis.com/v1/places:searchNearby",
            "places.id,places.rating,places.userRatingCount",
            b'{"locationRestriction":{"circle":{"center":{"latitude":0}}}}',
            SecretStr("synthetic-api-key"),
        ),
    }


def test_mac_binds_exact_request_and_financial_identity_without_revealing_inputs():
    values = _values()
    first = places_request_mac(**values)
    assert first == places_request_mac(**values)
    assert len(first) == 64
    for name in ("tenant", "business", "actor", "search", "effect", "pilot"):
        assert places_request_mac(**{**values, name: uuid4()}) != first
    for name, value in (
        ("key", SecretStr("different-synthetic-key-0123456789abcdef")),
        ("key_version", "test-key-v2"),
        ("tariff_version", "synthetic-price-v2"),
        ("credential_version", "synthetic-project-v2"),
        ("reserved_usd_micros", 20001),
        ("context_version", 2),
    ):
        assert places_request_mac(**{**values, name: value}) != first
    request = values["request"]
    assert places_request_mac(**{**values, "request": replace(request, body=request.body + b" ")}) != first
    assert (
        places_request_mac(**{**values, "request": replace(request, credential=SecretStr("different-api-key"))})
        != first
    )
    assert (
        places_request_mac(**{**values, "request": replace(request, field_mask=request.field_mask + ",places.id")})
        != first
    )
    assert "latitude" not in first and "synthetic-key" not in first
    assert "latitude" not in repr(request)


@pytest.mark.parametrize("key", [None, SecretStr("short")])
def test_key_must_be_explicit_and_long_enough(key):
    with pytest.raises(PlacesBindingError, match="PLACES_BINDING_KEY_INVALID"):
        places_request_mac(**{**_values(), "key": key})


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_version", None),
        ("key_version", ""),
        ("tariff_version", None),
        ("tariff_version", "!"),
        ("credential_version", None),
        ("credential_version", "!"),
        ("tenant", "bad"),
        ("context_version", True),
        ("context_version", 0),
        ("context_version", 9_223_372_036_854_775_808),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", 5_000_001),
        ("request", None),
    ],
)
def test_invalid_metadata_is_rejected_without_exposing_private_details(field, value):
    with pytest.raises(PlacesBindingError, match="PLACES_BINDING_INVALID"):
        places_request_mac(**{**_values(), field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("method", "GET"),
        ("url", "https://untrusted.invalid/"),
        ("field_mask", None),
        ("field_mask", ""),
        ("field_mask", "a" * 4097),
        ("body", "not bytes"),
        ("body", b""),
        ("body", b"a" * 65537),
        ("credential", None),
        ("credential", SecretStr("")),
    ],
)
def test_invalid_request_is_rejected_without_exposing_private_details(field, value):
    values = _values()
    with pytest.raises(PlacesBindingError, match="PLACES_BINDING_INVALID"):
        places_request_mac(**{**values, "request": replace(values["request"], **{field: value})})


def test_formatted_address_field_mask_changes_the_cost_binding():
    from app.adapters.google_places import PLACES_FIELD_MASK

    values = _values()
    current = replace(values["request"], field_mask=PLACES_FIELD_MASK)
    previous = replace(current, field_mask=PLACES_FIELD_MASK.replace(",places.formattedAddress", ""))
    assert places_request_mac(**{**values, "request": current}) != places_request_mac(**{**values, "request": previous})


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
def test_invalid_places_credential_fails_without_disclosure(secret):
    values = _values()
    with pytest.raises(PlacesBindingError, match="PLACES_BINDING_INVALID") as error:
        places_request_mac(**{**values, "request": replace(values["request"], credential=SecretStr(secret))})
    assert "private" not in str(error.value)


def test_invalid_places_signing_key_fails_without_disclosure():
    with pytest.raises(PlacesBindingError, match="PLACES_BINDING_KEY_INVALID") as error:
        places_request_mac(**{**_values(), "key": SecretStr("private\ud800")})
    assert "private" not in str(error.value)


def test_structured_address_component_mask_changes_cost_binding():
    from app.adapters.google_places import PLACES_FIELD_MASK

    values = _values()
    current = replace(values["request"], field_mask=PLACES_FIELD_MASK)
    previous = replace(current, field_mask=PLACES_FIELD_MASK.replace(",places.addressComponents", ""))
    assert places_request_mac(**{**values, "request": current}) != places_request_mac(**{**values, "request": previous})
