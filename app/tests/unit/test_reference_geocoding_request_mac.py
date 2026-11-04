from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.google_geocoding import GEOCODING_FIELD_MASK, GeocodingChargeableRequest
from app.services.reference_geocoding_request_mac import GeocodingBindingError, geocoding_request_mac


def values():
    request = httpx.Request(
        "GET",
        "https://geocode.googleapis.com/v4/geocode/address",
        params={"address.addressLines": "Rua Fictícia 10", "address.regionCode": "BR", "languageCode": "pt-BR"},
    )
    return {
        "key": SecretStr("synthetic-signing-key-0123456789abcdef"),
        "key_version": "key-1",
        "tariff_version": "price-1",
        "credential_version": "project-1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "origin": uuid4(),
        "effect": uuid4(),
        "pilot": uuid4(),
        "context_version": 1,
        "reserved_usd_micros": 100,
        "request": GeocodingChargeableRequest(
            "GET", str(request.url), "results.placeId,results.location", SecretStr("synthetic-api-key")
        ),
    }


def test_geocoding_mac_binds_private_request_credential_and_financial_identity():
    data = values()
    first = geocoding_request_mac(**data)
    assert first == geocoding_request_mac(**data) and len(first) == 64
    for field in ("tenant", "business", "actor", "origin", "effect", "pilot"):
        assert geocoding_request_mac(**{**data, field: uuid4()}) != first
    for field, value in (
        ("key_version", "key-2"),
        ("tariff_version", "price-2"),
        ("credential_version", "project-2"),
        ("context_version", 2),
        ("reserved_usd_micros", 101),
    ):
        assert geocoding_request_mac(**{**data, field: value}) != first
    request = data["request"]
    for changed in (
        replace(request, credential=SecretStr("another-key")),
        replace(request, field_mask="results.placeId"),
        replace(request, url=request.url.replace("Fict", "Outro")),
    ):
        assert geocoding_request_mac(**{**data, "request": changed}) != first
    assert "Fictícia" not in first and "synthetic-api-key" not in first and "Fictícia" not in repr(request)


@pytest.mark.parametrize(
    "field,value",
    [
        ("key", None),
        ("key", SecretStr("short")),
        ("key_version", ""),
        ("tariff_version", "!"),
        ("credential_version", None),
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
def test_geocoding_mac_rejects_invalid_metadata(field, value):
    with pytest.raises(GeocodingBindingError):
        geocoding_request_mac(**{**values(), field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("method", "POST"),
        ("url", "https://untrusted.invalid"),
        ("url", "x" * 4097),
        (
            "url",
            "https://geocode.googleapis.com/v4/geocode/address?address.addressLines=foo&address.regionCode=US&languageCode=pt-BR",
        ),
        (
            "url",
            "https://geocode.googleapis.com/v4/geocode/address?address.addressLines=foo&address.addressLines=bar&address.regionCode=BR&languageCode=pt-BR",
        ),
        (
            "url",
            "https://geocode.googleapis.com/v4/geocode/address?address.addressLines=foo&address.regionCode=BR&languageCode=pt-BR#fragment",
        ),
        ("field_mask", ""),
        ("field_mask", "x" * 4097),
        ("credential", None),
        ("credential", SecretStr("")),
    ],
)
def test_geocoding_mac_rejects_invalid_request(field, value):
    data = values()
    with pytest.raises(GeocodingBindingError, match="GEOCODING_BINDING_INVALID"):
        geocoding_request_mac(**{**data, "request": replace(data["request"], **{field: value})})


def test_structured_components_mask_is_covered_by_request_mac():
    data = values()
    request = data["request"]
    current = replace(request, field_mask=GEOCODING_FIELD_MASK)
    different = replace(current, field_mask=GEOCODING_FIELD_MASK.replace(",results.addressComponents", ""))
    assert geocoding_request_mac(**{**data, "request": current}) != geocoding_request_mac(
        **{**data, "request": different}
    )


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
def test_invalid_geocoding_credential_fails_without_disclosure(secret):
    data = values()
    with pytest.raises(GeocodingBindingError, match="GEOCODING_BINDING_INVALID") as error:
        geocoding_request_mac(**{**data, "request": replace(data["request"], credential=SecretStr(secret))})
    assert "private" not in str(error.value)


def test_invalid_geocoding_signing_key_fails_without_disclosure():
    with pytest.raises(GeocodingBindingError, match="GEOCODING_BINDING_KEY_INVALID") as error:
        geocoding_request_mac(**{**values(), "key": SecretStr("private\ud800")})
    assert "private" not in str(error.value)
