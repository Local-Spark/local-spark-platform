"""Authenticate a private manual-origin geocoding request in memory only."""

import hashlib
import hmac
import json
import re
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.adapters.google_geocoding import GeocodingChargeableRequest

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_ENDPOINT = "https://geocode.googleapis.com/v4/geocode/address"


class GeocodingBindingError(Exception):
    """Stable code without address, credential or provider result."""


def geocoding_request_mac(
    key: SecretStr,
    *,
    key_version: str,
    tariff_version: str,
    credential_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    origin: UUID,
    effect: UUID,
    pilot: UUID,
    context_version: int,
    reserved_usd_micros: int,
    request: GeocodingChargeableRequest,
) -> str:
    """Bind financial identity, exact encoded address query, mask and actual key."""
    if not isinstance(key, SecretStr):
        raise GeocodingBindingError("GEOCODING_BINDING_KEY_INVALID")
    try:
        signing_key = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise GeocodingBindingError("GEOCODING_BINDING_KEY_INVALID") from None
    if len(signing_key) < 32:
        raise GeocodingBindingError("GEOCODING_BINDING_KEY_INVALID")
    if (
        any(
            not isinstance(v, str) or _VERSION.fullmatch(v) is None
            for v in (key_version, tariff_version, credential_version)
        )
        or any(not isinstance(v, UUID) for v in (tenant, business, actor, origin, effect, pilot))
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(request, GeocodingChargeableRequest)
        or request.method != "GET"
        or not isinstance(request.url, str)
        or len(request.url) > 4096
        or not isinstance(request.field_mask, str)
        or not 1 <= len(request.field_mask) <= 4096
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
    ):
        raise GeocodingBindingError("GEOCODING_BINDING_INVALID")
    try:
        url = httpx.URL(request.url)
        pairs = url.params.multi_items()
        params = dict(pairs)
        if (
            str(url.copy_with(query=None)) != _ENDPOINT
            or url.userinfo
            or url.fragment
            or len(pairs) != len(params)
            or set(params) != {"address.addressLines", "address.regionCode", "languageCode"}
            or params["address.regionCode"] != "BR"
            or params["languageCode"] != "pt-BR"
            or not 1 <= len(params["address.addressLines"]) <= 300
            or params["address.addressLines"] != params["address.addressLines"].strip()
        ):
            raise ValueError
    except (httpx.InvalidURL, ValueError, TypeError):
        raise GeocodingBindingError("GEOCODING_BINDING_INVALID") from None
    payload = json.dumps(
        [
            "geocoding-request-v1",
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(origin),
            str(effect),
            str(pilot),
            context_version,
            reserved_usd_micros,
            request.method,
            request.url,
            request.field_mask,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    try:
        credential_bytes = request.credential.get_secret_value().encode("ascii")
        if any(byte < 33 or byte > 126 for byte in credential_bytes):
            raise ValueError
    except (UnicodeEncodeError, ValueError):
        raise GeocodingBindingError("GEOCODING_BINDING_INVALID") from None
    credential_mac = hmac.new(signing_key, b"geocoding-credential-v1\0" + credential_bytes, hashlib.sha256).digest()
    return hmac.new(signing_key, payload + b"\0" + credential_mac, hashlib.sha256).hexdigest()
