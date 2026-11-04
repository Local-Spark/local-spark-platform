"""Authenticate the exact Places request without retaining its private input.

This binding is groundwork only: it does not reserve money, invoke a provider,
or authorize dispatch. The eventual guard must compare it to a durable intent
and commit the reservation before returning permission to the adapter.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr

from app.adapters.google_places import PlacesChargeableRequest

_ENDPOINT = "https://places.googleapis.com/v1/places:searchNearby"
_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")


class PlacesBindingError(Exception):
    """A stable error which never includes credentials or request data."""


def places_request_mac(
    key: SecretStr,
    *,
    key_version: str,
    tariff_version: str,
    credential_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    search: UUID,
    effect: UUID,
    pilot: UUID,
    context_version: int,
    reserved_usd_micros: int,
    request: PlacesChargeableRequest,
) -> str:
    """Bind all execution and pricing inputs to an HMAC, without saving them."""
    if not isinstance(key, SecretStr):
        raise PlacesBindingError("PLACES_BINDING_KEY_INVALID")
    try:
        signing_key = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise PlacesBindingError("PLACES_BINDING_KEY_INVALID") from None
    if len(signing_key) < 32:
        raise PlacesBindingError("PLACES_BINDING_KEY_INVALID")
    if (
        not isinstance(key_version, str)
        or not _VERSION.fullmatch(key_version)
        or not isinstance(tariff_version, str)
        or not _VERSION.fullmatch(tariff_version)
        or not isinstance(credential_version, str)
        or not _VERSION.fullmatch(credential_version)
        or any(not isinstance(value, UUID) for value in (tenant, business, actor, search, effect, pilot))
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(request, PlacesChargeableRequest)
        or request.method != "POST"
        or request.url != _ENDPOINT
        or not isinstance(request.field_mask, str)
        or not request.field_mask
        or len(request.field_mask) > 4096
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 65536
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
    ):
        raise PlacesBindingError("PLACES_BINDING_INVALID")
    # Length-delimited JSON avoids ambiguous concatenation. Hex preserves the
    # exact bytes submitted over HTTP; field values never enter logs or storage.
    payload = json.dumps(
        [
            "places-request-v2",
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(search),
            str(effect),
            str(pilot),
            context_version,
            reserved_usd_micros,
            request.method,
            request.url,
            request.field_mask,
            request.body.hex(),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    try:
        credential_bytes = request.credential.get_secret_value().encode("ascii")
        if any(byte < 33 or byte > 126 for byte in credential_bytes):
            raise ValueError
    except (UnicodeEncodeError, ValueError):
        raise PlacesBindingError("PLACES_BINDING_INVALID") from None
    # Bind the actual billing credential without persisting a raw or unkeyed
    # hash of it. Domain separation prevents reuse as another commitment.
    credential_mac = hmac.new(signing_key, b"places-credential-v1\0" + credential_bytes, hashlib.sha256).digest()
    return hmac.new(signing_key, payload + b"\0" + credential_mac, hashlib.sha256).hexdigest()
