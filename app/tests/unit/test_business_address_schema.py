from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.business_address import BusinessAddressWrite


def address():
    return {"street": "Rua das Flores", "number": "123", "city": "São Paulo", "state_code": "SP"}


def test_owner_address_requires_a_street_and_number():
    with pytest.raises(ValidationError):
        BusinessAddressWrite(
            operation_id=uuid4(), expected_version=0, address={"city": "São Paulo", "state_code": "SP"}
        )


def test_address_does_not_accept_raw_geocoding_or_search_location():
    with pytest.raises(ValidationError):
        BusinessAddressWrite(operation_id=uuid4(), expected_version=0, address={**address(), "latitude": -23.0})


@pytest.mark.parametrize("version", [True, -1, 9_223_372_036_854_775_807])
def test_version_must_be_a_bounded_integer(version):
    with pytest.raises(ValidationError):
        BusinessAddressWrite(operation_id=uuid4(), expected_version=version, address=address())
