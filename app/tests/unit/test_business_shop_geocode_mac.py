from dataclasses import replace
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.google_geocoding import GEOCODING_FIELD_MASK, GeocodingChargeableRequest
from app.services.business_shop_geocode_mac import (
    ShopGeocodeBindingError,
    shop_geocode_address_text,
    shop_geocode_binding_mac,
    shop_geocode_candidate_mac,
)
from app.tests.unit.test_business_location_resolution import address, candidate


def scope():
    return {
        "key": SecretStr("synthetic-shop-geocode-key-0123456789"),
        "key_version": "v1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "address_version": 1,
        "origin": uuid4(),
        "effect": uuid4(),
        "context_version": 1,
    }


def binding_data():
    owner = address()
    request = httpx.Request(
        "GET",
        "https://geocode.googleapis.com/v4/geocode/address",
        params={
            "address.addressLines": shop_geocode_address_text(owner),
            "address.regionCode": "BR",
            "languageCode": "pt-BR",
        },
    )
    return {
        **scope(),
        "pilot": uuid4(),
        "tariff_version": "price-v1",
        "credential_version": "project-v1",
        "reserved_usd_micros": 50,
        "address": owner,
        "request": GeocodingChargeableRequest("GET", str(request.url), GEOCODING_FIELD_MASK, SecretStr("synthetic")),
    }


def test_request_binding_covers_owner_version_effect_and_provider_request():
    data = binding_data()
    first = shop_geocode_binding_mac(**data)
    assert len(first.shop_mac) == 64 and len(first.request_mac) == 64 and first == shop_geocode_binding_mac(**data)
    assert "Rua do Titular" not in repr(first) and "synthetic" not in repr(first)
    for field in ("tenant", "business", "actor", "origin", "effect", "pilot"):
        assert shop_geocode_binding_mac(**{**data, field: uuid4()}) != first
    for field, value in (
        ("key_version", "v2"),
        ("address_version", 2),
        ("context_version", 2),
        ("tariff_version", "price-v2"),
        ("credential_version", "project-v2"),
        ("reserved_usd_micros", 51),
    ):
        assert shop_geocode_binding_mac(**{**data, field: value}) != first
    for request in (
        replace(data["request"], credential=SecretStr("another")),
        replace(data["request"], field_mask="results.placeId"),
    ):
        assert shop_geocode_binding_mac(**{**data, "request": request}) != first


@pytest.mark.parametrize(
    "change,code",
    [
        ({"key": None}, "BUSINESS_SHOP_GEOCODE_KEY_INVALID"),
        ({"key": SecretStr("short")}, "BUSINESS_SHOP_GEOCODE_KEY_INVALID"),
        ({"key": SecretStr("private\ud800")}, "BUSINESS_SHOP_GEOCODE_KEY_INVALID"),
        ({"key_version": "!"}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"tenant": "bad"}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"business": UUID(int=0)}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"address_version": True}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"address_version": 0}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"address_version": 2**63}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"context_version": True}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"context_version": 0}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"context_version": 2**63}, "BUSINESS_SHOP_GEOCODE_INVALID"),
        ({"tariff_version": "!"}, "BUSINESS_SHOP_GEOCODE_INVALID"),
    ],
)
def test_invalid_request_binding_fails_without_disclosure(change, code):
    with pytest.raises(ShopGeocodeBindingError, match=code) as error:
        shop_geocode_binding_mac(**{**binding_data(), **change})
    assert "private" not in str(error.value)


def candidate_data():
    return {
        **scope(),
        "binding_mac": "a" * 64,
        "candidate_id": uuid4(),
        "address": address(),
        "results": (candidate(),),
    }


def test_candidate_mac_binds_complete_matching_transient_result_and_owner_input():
    data = candidate_data()
    first = shop_geocode_candidate_mac(**data)
    assert first == shop_geocode_candidate_mac(**data) and len(first) == 64
    assert "Rua do Titular" not in first
    for field in ("tenant", "business", "actor", "origin", "effect", "candidate_id"):
        assert shop_geocode_candidate_mac(**{**data, field: uuid4()}) != first
    item = data["results"][0]
    for changed in (
        replace(item, place_id="another"),
        replace(item, formatted_address="Outro formato"),
        replace(item, latitude=-23.6),
        replace(item, longitude=-46.7),
    ):
        assert shop_geocode_candidate_mac(**{**data, "results": (changed,)}) != first
    assert shop_geocode_candidate_mac(**{**data, "binding_mac": "b" * 64}) != first


@pytest.mark.parametrize(
    "change",
    [
        {"binding_mac": "bad"},
        {"candidate_id": None},
        {"candidate_id": UUID(int=0)},
    ],
)
def test_invalid_candidate_identity_fails_closed(change):
    with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID"):
        shop_geocode_candidate_mac(**{**candidate_data(), **change})


def test_ambiguous_or_incompatible_results_require_review():
    data = candidate_data()
    item = data["results"][0]
    for results in ((), (item, item), (replace(item, granularity="APPROXIMATE"),)):
        with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_REVIEW_REQUIRED"):
            shop_geocode_candidate_mac(**{**data, "results": results})


def test_unserializable_transient_field_fails_without_disclosure():
    data = candidate_data()
    item = replace(data["results"][0], formatted_address=object())
    with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID"):
        shop_geocode_candidate_mac(**{**data, "results": (item,)})


def test_invalid_owner_address_unicode_fails_without_disclosure():
    data = candidate_data()
    invalid = data["address"].model_copy(update={"complement": "private\ud800"})
    with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID") as error:
        shop_geocode_candidate_mac(**{**data, "address": invalid})
    assert "private" not in str(error.value)


def test_request_address_is_built_only_from_exact_owner_input():
    import httpx

    from app.adapters.google_geocoding import GeocodingChargeableRequest
    from app.services.business_shop_geocode_mac import shop_geocode_address_text, verify_shop_geocode_request_address

    owner = address()
    text = shop_geocode_address_text(owner)
    request = httpx.Request(
        "GET",
        "https://geocode.googleapis.com/v4/geocode/address",
        params={
            "address.addressLines": text,
            "address.regionCode": "BR",
            "languageCode": "pt-BR",
        },
    )
    binding = GeocodingChargeableRequest("GET", str(request.url), "results.location", SecretStr("synthetic"))
    verify_shop_geocode_request_address(owner, binding)
    assert text == "Rua do Titular, 10, São Paulo, SP, 01234567"
    for altered in (
        replace(binding, method="POST"),
        replace(binding, url=binding.url.replace("geocode.googleapis.com", "evil.invalid")),
        replace(binding, url=binding.url.replace("address.regionCode=BR", "address.regionCode=US")),
        replace(binding, url=binding.url + "&languageCode=pt-BR"),
        replace(binding, url=binding.url + "#fragment"),
        replace(binding, url=binding.url.replace("Titular", "Outro")),
    ):
        with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID"):
            verify_shop_geocode_request_address(owner, altered)
    with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID"):
        verify_shop_geocode_request_address(owner, None)


def test_invalid_or_oversized_owner_address_never_leaks():
    from app.schemas.editorial_context import ReferenceAddress
    from app.services.business_shop_geocode_mac import shop_geocode_address_text

    big = ReferenceAddress(
        street="a" * 120, number="1" * 30, complement="b" * 120, neighborhood="c" * 120, city="X", state_code="SP"
    )
    for bad in (
        None,
        big,
        address().model_copy(update={"street": 1}),
        address().model_copy(update={"street": "private\ud800"}),
    ):
        with pytest.raises(ShopGeocodeBindingError, match="BUSINESS_SHOP_GEOCODE_INVALID") as error:
            shop_geocode_address_text(bad)
        assert "private" not in str(error.value)
