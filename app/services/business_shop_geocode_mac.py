"""Private commitments for a shop-address geocode and one automatic result.

These pure functions perform no network, storage, authorization or verification
of provider provenance. A trusted activity must compute the request MAC from
the exact locked owner-entered address and bind it to the fenced effect.
"""

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from uuid import UUID

import httpx
from pydantic import SecretStr, ValidationError
from pydantic_core import PydanticSerializationError

from app.adapters.google_geocoding import GeocodingCandidate, GeocodingChargeableRequest
from app.schemas.editorial_context import ReferenceAddress
from app.services.business_location_resolution import automatic_location_candidate
from app.services.reference_geocoding_request_mac import GeocodingBindingError, geocoding_request_mac


class ShopGeocodeBindingError(Exception):
    """Stable code without address, coordinates, provider data or secrets."""


def _key(key: SecretStr, key_version: str) -> bytes:
    if not isinstance(key, SecretStr):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_KEY_INVALID")
    try:
        encoded = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_KEY_INVALID") from None
    if len(encoded) < 32:
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_KEY_INVALID")
    if not isinstance(key_version, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", key_version) is None:
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID")
    return encoded


def _scope(
    tenant: UUID, business: UUID, actor: UUID, address_version: int, origin: UUID, effect: UUID, context: int
) -> None:
    identifiers = (tenant, business, actor, origin, effect)
    if (
        any(not isinstance(value, UUID) for value in identifiers)
        or any(value.int == 0 for value in identifiers)
        or type(address_version) is not int
        or not 0 < address_version <= 9_223_372_036_854_775_807
        or type(context) is not int
        or not 0 < context <= 9_223_372_036_854_775_807
    ):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID")


def _mac(key: bytes, payload: list[object]) -> str:
    try:
        encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "ascii"
        )
    except (TypeError, ValueError, UnicodeError):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID") from None
    return hmac.new(key, encoded, hashlib.sha256).hexdigest()


def shop_geocode_address_text(address: ReferenceAddress) -> str:
    """Format only the explicitly owner-entered address for a single request."""
    if not isinstance(address, ReferenceAddress):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID")
    try:
        value = ReferenceAddress.model_validate(address.model_dump(warnings="error"))
        parts = (
            value.street,
            value.number,
            value.complement,
            value.neighborhood,
            value.city,
            value.state_code,
            value.postal_code,
        )
        result = ", ".join(part for part in parts if part is not None)
        result.encode("utf-8")
        if not 1 <= len(result) <= 300:
            raise ValueError
        return result
    except (ValidationError, PydanticSerializationError, TypeError, ValueError, UnicodeError):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID") from None


def verify_shop_geocode_request_address(address: ReferenceAddress, request: GeocodingChargeableRequest) -> None:
    """Require the actual request URL to use the owner's exact formatted address.

    The caller must still verify the full request MAC, credential, tariff,
    effect and source address under the corresponding transactional fences.
    """
    expected = shop_geocode_address_text(address)
    if not isinstance(request, GeocodingChargeableRequest) or request.method != "GET":
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID")
    try:
        url = httpx.URL(request.url)
        pairs = url.params.multi_items()
        params = dict(pairs)
        if (
            str(url.copy_with(query=None)) != "https://geocode.googleapis.com/v4/geocode/address"
            or url.userinfo
            or url.fragment
            or len(pairs) != len(params)
            or set(params) != {"address.addressLines", "address.regionCode", "languageCode"}
            or params["address.addressLines"] != expected
            or params["address.regionCode"] != "BR"
            or params["languageCode"] != "pt-BR"
        ):
            raise ValueError
    except (httpx.InvalidURL, TypeError, ValueError):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID") from None


@dataclass(frozen=True, repr=False)
class ShopGeocodeBinding:
    request_mac: str
    shop_mac: str


def shop_geocode_binding_mac(
    key: SecretStr,
    *,
    key_version: str,
    tariff_version: str,
    credential_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    address_version: int,
    origin: UUID,
    effect: UUID,
    pilot: UUID,
    context_version: int,
    reserved_usd_micros: int,
    address: ReferenceAddress,
    request: GeocodingChargeableRequest,
) -> ShopGeocodeBinding:
    """Bind the actual request and credential to the exact owner address version.

    The caller must load the address from trusted storage and reserve/claim the
    provider effect; the returned commitments alone cannot authorize a call.
    """
    signing_key = _key(key, key_version)
    _scope(tenant, business, actor, address_version, origin, effect, context_version)
    verify_shop_geocode_request_address(address, request)
    try:
        request_mac = geocoding_request_mac(
            key,
            key_version=key_version,
            tariff_version=tariff_version,
            credential_version=credential_version,
            tenant=tenant,
            business=business,
            actor=actor,
            origin=origin,
            effect=effect,
            pilot=pilot,
            context_version=context_version,
            reserved_usd_micros=reserved_usd_micros,
            request=request,
        )
    except GeocodingBindingError:
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID") from None
    return ShopGeocodeBinding(
        request_mac,
        _mac(
            signing_key,
            [
                "business-shop-geocode-binding-v2",
                key_version,
                str(tenant),
                str(business),
                str(actor),
                address_version,
                str(origin),
                str(effect),
                context_version,
                request_mac,
            ],
        ),
    )


def shop_geocode_candidate_mac(
    key: SecretStr,
    *,
    key_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    address_version: int,
    origin: UUID,
    effect: UUID,
    context_version: int,
    binding_mac: str,
    candidate_id: UUID,
    address: ReferenceAddress,
    results: tuple[GeocodingCandidate, ...],
) -> str:
    """Bind the entire single precise result only after the conservative match.

    Inputs remain in memory. The resulting MAC alone cannot authenticate the
    provider response or prove that the owner address came from trusted storage.
    """
    signing_key = _key(key, key_version)
    _scope(tenant, business, actor, address_version, origin, effect, context_version)
    if (
        not isinstance(binding_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", binding_mac) is None
        or not isinstance(candidate_id, UUID)
        or candidate_id.int == 0
    ):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID")
    candidate = automatic_location_candidate(address, results)
    if candidate is None:
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_REVIEW_REQUIRED")
    try:
        owner_address = address.model_dump(mode="json", exclude_none=True, warnings="error")
        for value in owner_address.values():
            value.encode("utf-8")
        fields = [
            candidate.place_id,
            candidate.formatted_address,
            candidate.latitude,
            candidate.longitude,
            candidate.granularity,
            candidate.country,
            [[part.long_text, part.short_text, part.types] for part in candidate.address_components],
        ]
        return _mac(
            signing_key,
            [
                "business-shop-geocode-candidate-v1",
                key_version,
                str(tenant),
                str(business),
                str(actor),
                address_version,
                str(origin),
                str(effect),
                context_version,
                binding_mac,
                str(candidate_id),
                owner_address,
                fields,
            ],
        )
    except (TypeError, UnicodeError, ValueError):
        raise ShopGeocodeBindingError("BUSINESS_SHOP_GEOCODE_INVALID") from None
