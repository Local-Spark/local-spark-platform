"""Authenticate a contacts lookup without storing provider input or credentials.

This pure binding does not create a durable intent, reserve money or send IO.
The source shortlist and six-month cycle must be verified by a future writer.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.schemas.reference_contacts_effect import ContactsChargeableRequest, valid_place_id

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_BUILD = re.compile(r"[0-9]+[.][0-9]+[.][0-9]+")
_USD = re.compile(r"(?:0|[1-9][0-9]*)(?:[.][0-9]{1,6})?")
_ENDPOINT = "https://api.apify.com/v2/acts/{actor_id}/runs"


class ContactsBindingError(Exception):
    """Stable code without Place ID, account key or provider content."""


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _actor_limit(value: str) -> int:
    if _USD.fullmatch(value) is None:
        raise ValueError
    whole, _, decimal = value.partition(".")
    return int(whole) * 1_000_000 + int((decimal + "000000")[:6])


def contacts_request_mac(
    key: SecretStr,
    *,
    key_version: str,
    tariff_version: str,
    credential_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    cycle: UUID,
    batch: UUID,
    candidate: UUID,
    place_id: str,
    effect: UUID,
    pilot: UUID,
    context_version: int,
    reserved_usd_micros: int,
    build: str,
    request: ContactsChargeableRequest,
) -> str:
    """Bind a source candidate, exact Actor request and actual billing account."""
    if not isinstance(key, SecretStr):
        raise ContactsBindingError("CONTACTS_BINDING_KEY_INVALID")
    try:
        signing_key = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise ContactsBindingError("CONTACTS_BINDING_KEY_INVALID") from None
    if len(signing_key) < 32:
        raise ContactsBindingError("CONTACTS_BINDING_KEY_INVALID")
    if (
        any(
            not isinstance(v, str) or _VERSION.fullmatch(v) is None
            for v in (key_version, tariff_version, credential_version)
        )
        or any(not isinstance(v, UUID) for v in (tenant, business, actor, cycle, batch, candidate, effect, pilot))
        or not valid_place_id(place_id)
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(build, str)
        or len(build) > 64
        or _BUILD.fullmatch(build) is None
        or not isinstance(request, ContactsChargeableRequest)
        or not isinstance(request.provider_actor_id, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request.provider_actor_id) is None
        or request.method != "POST"
        or not isinstance(request.url, str)
        or len(request.url) > 4096
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 65536
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
        or request.headers != (("content-length", str(len(request.body))), ("content-type", "application/json"))
    ):
        raise ContactsBindingError("CONTACTS_BINDING_INVALID")
    try:
        url = httpx.URL(request.url)
        pairs = url.params.multi_items()
        params = dict(pairs)
        if (
            str(url.copy_with(query=None)) != _ENDPOINT.format(actor_id=request.provider_actor_id)
            or url.userinfo
            or url.fragment
            or len(pairs) != len(params)
            or set(params)
            != {"build", "maxTotalChargeUsd", "timeout", "memory", "restartOnError", "forcePermissionLevel"}
            or params["build"] != build
            or params["timeout"] != "120"
            or params["memory"] != "1024"
            or params["restartOnError"] != "false"
            or params["forcePermissionLevel"] != "LIMITED_PERMISSIONS"
            or not 0 < _actor_limit(params["maxTotalChargeUsd"]) <= reserved_usd_micros
        ):
            raise ValueError
        body = json.loads(request.body, object_pairs_hook=_object)
        if (
            not isinstance(body, dict)
            or set(body) != {"placeIds", "scrapeContacts", "maxCrawledPlacesPerSearch", "language"}
            or body["placeIds"] != [place_id]
            or body["scrapeContacts"] is not True
            or type(body["maxCrawledPlacesPerSearch"]) is not int
            or body["maxCrawledPlacesPerSearch"] != 1
            or body["language"] != "pt-BR"
        ):
            raise ValueError
    except (httpx.InvalidURL, UnicodeDecodeError, ValueError, TypeError, KeyError):
        raise ContactsBindingError("CONTACTS_BINDING_INVALID") from None
    payload = json.dumps(
        [
            "apify-place-contacts-v3",
            request.provider_actor_id,
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(cycle),
            str(batch),
            str(candidate),
            place_id,
            str(effect),
            str(pilot),
            context_version,
            reserved_usd_micros,
            build,
            request.method,
            request.url,
            request.headers,
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
        raise ContactsBindingError("CONTACTS_BINDING_INVALID") from None
    credential_mac = hmac.new(signing_key, b"contacts-credential-v1\0" + credential_bytes, hashlib.sha256).digest()
    return hmac.new(signing_key, payload + b"\0" + credential_mac, hashlib.sha256).hexdigest()
