"""Authenticate a transient Apify feed submission without storing its inputs.

This pure binding does not authorize, reserve, persist, or send an effect.
The trusted caller must load the association and budget from durable state.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.adapters.apify_instagram_feed import FeedChargeableRequest
from app.schemas.owner_references import instagram_handle

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_BUILD = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_USD = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?")
_ENDPOINT = "https://api.apify.com/v2/acts/apify~instagram-scraper/runs"


class FeedBindingError(Exception):
    """A stable error without request contents or credentials."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _actor_limit(value: str) -> int:
    if _USD.fullmatch(value) is None:
        raise FeedBindingError("FEED_BINDING_INVALID")
    whole, _, fractional = value.partition(".")
    return int(whole) * 1_000_000 + int((fractional + "000000")[:6])


def _validate_request(request: FeedChargeableRequest, *, profile: str, build: str, reserved_usd_micros: int) -> None:
    if (
        not isinstance(request, FeedChargeableRequest)
        or request.method != "POST"
        or not isinstance(request.url, str)
        or len(request.url) > 4096
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 65_536
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
        or request.headers != (("content-length", str(len(request.body))), ("content-type", "application/json"))
    ):
        raise FeedBindingError("FEED_BINDING_INVALID")
    try:
        url = httpx.URL(request.url)
        if str(url.copy_with(query=None)) != _ENDPOINT or url.fragment or url.userinfo:
            raise ValueError
        items = url.params.multi_items()
        params = dict(items)
        if len(items) != len(params) or set(params) != {
            "build",
            "maxTotalChargeUsd",
            "maxItems",
            "timeout",
            "memory",
            "restartOnError",
            "forcePermissionLevel",
        }:
            raise ValueError
        if (
            params["build"] != build
            or params["timeout"] != "120"
            or params["memory"] != "1024"
            or params["restartOnError"] != "false"
            or params["forcePermissionLevel"] != "LIMITED_PERMISSIONS"
            or re.fullmatch(r"(?:[1-9]|1[0-9]|20)", params["maxItems"]) is None
            or not 0 < _actor_limit(params["maxTotalChargeUsd"]) <= reserved_usd_micros
        ):
            raise ValueError
        payload = json.loads(request.body, object_pairs_hook=_unique_object)
        if (
            not isinstance(payload, dict)
            or set(payload) != {"directUrls", "resultsType", "resultsLimit"}
            or payload["directUrls"] != [f"https://www.instagram.com/{profile}/"]
            or payload["resultsType"] != "posts"
            or type(payload["resultsLimit"]) is not int
            or payload["resultsLimit"] != int(params["maxItems"])
        ):
            raise ValueError
    except (httpx.InvalidURL, UnicodeDecodeError, ValueError, TypeError, KeyError):
        raise FeedBindingError("FEED_BINDING_INVALID") from None


def feed_request_mac(
    key: SecretStr,
    *,
    key_version: str,
    tariff_version: str,
    credential_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    reference: UUID,
    association_version: int,
    analysis_window: UUID,
    search: UUID | None,
    selection: UUID | None,
    effect: UUID,
    pilot: UUID,
    reserved_usd_micros: int,
    profile: str,
    build: str,
    request: FeedChargeableRequest,
) -> str:
    """Bind authorized identity, all Actor input and the actual billing credential."""
    if not isinstance(key, SecretStr) or len(key.get_secret_value().encode()) < 32:
        raise FeedBindingError("FEED_BINDING_KEY_INVALID")
    if (
        any(
            not isinstance(value, str) or _VERSION.fullmatch(value) is None
            for value in (key_version, tariff_version, credential_version)
        )
        or any(
            not isinstance(value, UUID)
            for value in (tenant, business, actor, reference, analysis_window, effect, pilot)
        )
        or (search is not None and not isinstance(search, UUID))
        or (selection is not None and not isinstance(selection, UUID))
        or type(association_version) is not int
        or association_version < 1
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(profile, str)
        or not isinstance(build, str)
        or len(build) > 64
        or _BUILD.fullmatch(build) is None
    ):
        raise FeedBindingError("FEED_BINDING_INVALID")
    try:
        if instagram_handle(profile) != profile:
            raise ValueError
    except ValueError:
        raise FeedBindingError("FEED_BINDING_INVALID") from None
    _validate_request(request, profile=profile, build=build, reserved_usd_micros=reserved_usd_micros)
    payload = json.dumps(
        [
            "apify-feed-submission-v2",
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(reference),
            association_version,
            str(analysis_window),
            str(search) if search else None,
            str(selection) if selection else None,
            str(effect),
            str(pilot),
            reserved_usd_micros,
            profile,
            build,
            request.method,
            request.url,
            request.headers,
            request.body.hex(),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    signing_key = key.get_secret_value().encode()
    credential_mac = hmac.new(
        signing_key, b"apify-feed-credential-v1\0" + request.credential.get_secret_value().encode(), hashlib.sha256
    ).digest()
    return hmac.new(signing_key, payload + b"\0" + credential_mac, hashlib.sha256).hexdigest()
