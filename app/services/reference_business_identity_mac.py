"""Private commitment to owner-supplied business identity for one search.

Pure HMAC calculation does not prove where an address came from. The admission
service loads the current business name and declared address under locks, binds
this commitment to the search and revalidates that identity before publication.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr, ValidationError
from pydantic_core import PydanticSerializationError

from app.schemas.editorial_context import ReferenceAddress


class BusinessIdentityBindingError(Exception):
    """Stable error without the business name, address or signing key."""


def business_identity_mac(
    key: SecretStr,
    *,
    key_version: str,
    tenant: UUID,
    business: UUID,
    search: UUID,
    search_actor: UUID,
    context_version: int,
    business_row_version: int,
    address_version: int | None,
    location_version: int | None,
    name: str,
    address: ReferenceAddress | None,
) -> str:
    """Bind exact owner data; an unproven search address must be passed as None."""
    if not isinstance(key, SecretStr):
        raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_KEY_INVALID")
    try:
        signing_key = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_KEY_INVALID") from None
    if len(signing_key) < 32:
        raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_KEY_INVALID")
    if (
        not isinstance(key_version, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", key_version) is None
        or any(not isinstance(item, UUID) for item in (tenant, business, search, search_actor))
        or any(item.int == 0 for item in (tenant, business, search, search_actor))
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or type(business_row_version) is not int
        or not 0 < business_row_version <= 9_223_372_036_854_775_807
        or (
            address_version is not None
            and (type(address_version) is not int or not 0 < address_version <= 9_223_372_036_854_775_807)
        )
        or (
            location_version is not None
            and (type(location_version) is not int or not 0 < location_version <= 9_223_372_036_854_775_807)
        )
        or not isinstance(name, str)
        or not 1 <= len(name.strip()) <= 120
        or name != name.strip()
        or ((address is None) != (address_version is None))
        or (location_version is not None and address is None)
        or (address is not None and not isinstance(address, ReferenceAddress))
    ):
        raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID")
    try:
        name.encode("utf-8")
        if address is not None:
            validated = ReferenceAddress.model_validate(address.model_dump(warnings="error"))
            data = validated.model_dump(mode="json", exclude_none=True)
            for value in data.values():
                value.encode("utf-8")
        else:
            data = None
        payload = json.dumps(
            [
                "reference-business-identity-v1",
                key_version,
                str(tenant),
                str(business),
                str(search),
                str(search_actor),
                context_version,
                business_row_version,
                address_version,
                location_version,
                name,
                data,
            ],
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (ValidationError, PydanticSerializationError, TypeError, UnicodeError, ValueError):
        raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID") from None
    return hmac.new(signing_key, payload, hashlib.sha256).hexdigest()
