from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from app.schemas.editorial_context import ReferenceAddress
from app.services.reference_business_identity_mac import BusinessIdentityBindingError, business_identity_mac


def values():
    return {
        "key": SecretStr("synthetic-business-identity-key-0123456789"),
        "key_version": "key-1",
        "tenant": uuid4(),
        "business": uuid4(),
        "search": uuid4(),
        "search_actor": uuid4(),
        "context_version": 1,
        "business_row_version": 1,
        "address_version": 1,
        "location_version": 1,
        "name": "Empresa de teste",
        "address": ReferenceAddress(city="São Paulo", state_code="SP", street="Rua teste", number="10"),
    }


def test_exact_owner_identity_is_bound_without_exposing_name_or_address():
    data = values()
    original = business_identity_mac(**data)
    assert business_identity_mac(**data) == original and len(original) == 64
    for field in ("tenant", "business", "search", "search_actor"):
        assert business_identity_mac(**{**data, field: uuid4()}) != original
    for field, change in (
        ("key", SecretStr("another-synthetic-identity-key-0123456789")),
        ("key_version", "key-2"),
        ("context_version", 2),
        ("business_row_version", 2),
        ("address_version", 2),
        ("location_version", 2),
        ("name", "Outra empresa"),
        ("address", data["address"].model_copy(update={"number": "11"})),
    ):
        assert business_identity_mac(**{**data, field: change}) != original
    assert "Empresa" not in original and "Rua teste" not in original


def test_unavailable_shop_address_is_explicitly_bound_without_using_device_origin():
    data = values()
    without_address = {**data, "address_version": None, "location_version": None, "address": None}
    address_not_yet_geocoded = {**data, "location_version": None}
    assert business_identity_mac(**without_address) != business_identity_mac(**address_not_yet_geocoded)
    assert business_identity_mac(**address_not_yet_geocoded) != business_identity_mac(**data)


@pytest.mark.parametrize(
    "change",
    [
        {"key": None},
        {"key": SecretStr("short")},
        {"key": SecretStr("private\ud800")},
    ],
)
def test_invalid_key_fails_without_disclosure(change):
    with pytest.raises(BusinessIdentityBindingError, match="REFERENCE_BUSINESS_IDENTITY_KEY_INVALID") as error:
        business_identity_mac(**{**values(), **change})
    assert "private" not in str(error.value)


@pytest.mark.parametrize(
    "change",
    [
        {"key_version": None},
        {"key_version": "!"},
        {"tenant": "bad"},
        {"business": UUID(int=0)},
        {"context_version": True},
        {"context_version": 0},
        {"context_version": 2**63},
        {"business_row_version": True},
        {"business_row_version": 0},
        {"business_row_version": 2**63},
        {"address_version": True},
        {"address_version": 0},
        {"address_version": 2**63},
        {"location_version": True},
        {"location_version": 0},
        {"location_version": 2**63},
        {"name": None},
        {"name": ""},
        {"name": " padded "},
        {"name": "x" * 121},
        {"address": None},
        {"address": "bad"},
        {"name": "private\ud800"},
    ],
)
def test_invalid_identity_fails_closed_without_exposing_input(change):
    with pytest.raises(BusinessIdentityBindingError, match="REFERENCE_BUSINESS_IDENTITY_INVALID") as error:
        business_identity_mac(**{**values(), **change})
    assert "private" not in str(error.value)


def test_address_model_mutation_or_invalid_unicode_does_not_bypass_validation():
    data = values()
    for changed in (
        data["address"].model_copy(update={"street": 1}),
        data["address"].model_copy(update={"street": "private\ud800"}),
    ):
        with pytest.raises(BusinessIdentityBindingError, match="REFERENCE_BUSINESS_IDENTITY_INVALID") as error:
            business_identity_mac(**{**data, "address": changed})
        assert "private" not in str(error.value)
