"""Bind an exact transient Jev request to its effect and financial intent."""

import hashlib
import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr

from app.adapters.jev_reference_similarity import JevChargeableRequest

_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_MODEL = re.compile(r"[A-Za-z0-9_.-]{1,120}")


class JevBindingError(Exception):
    """Stable error without request inputs, private context or credentials."""


def jev_request_mac(
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
    parent_google_effect: UUID,
    source_batch_mac: str,
    context_version: int,
    reserved_usd_micros: int,
    request: JevChargeableRequest,
) -> str:
    """Authenticate the exact request and its cost identity without retaining inputs."""
    if not isinstance(key, SecretStr) or len(key.get_secret_value().encode()) < 32:
        raise JevBindingError("JEV_BINDING_KEY_INVALID")
    if (
        not isinstance(key_version, str)
        or not _VERSION.fullmatch(key_version)
        or not isinstance(tariff_version, str)
        or not _VERSION.fullmatch(tariff_version)
        or not isinstance(credential_version, str)
        or not _VERSION.fullmatch(credential_version)
        or any(
            not isinstance(value, UUID)
            for value in (tenant, business, actor, search, effect, pilot, parent_google_effect)
        )
        or not isinstance(source_batch_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", source_batch_mac) is None
        or type(context_version) is not int
        or context_version < 1
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(request, JevChargeableRequest)
        or request.method != "POST"
        or request.url != _ENDPOINT
        or not isinstance(request.model, str)
        or not _MODEL.fullmatch(request.model)
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 262_144
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
    ):
        raise JevBindingError("JEV_BINDING_INVALID")
    try:
        payload_model = json.loads(request.body)
    except (ValueError, TypeError, UnicodeDecodeError):
        raise JevBindingError("JEV_BINDING_INVALID") from None
    if not isinstance(payload_model, dict) or payload_model.get("model") != request.model:
        raise JevBindingError("JEV_BINDING_INVALID")
    payload = json.dumps(
        [
            "jev-reference-request-v1",
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(search),
            str(effect),
            str(pilot),
            str(parent_google_effect),
            source_batch_mac,
            context_version,
            reserved_usd_micros,
            request.method,
            request.url,
            request.model,
            request.body.hex(),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    signing_key = key.get_secret_value().encode()
    credential_mac = hmac.new(
        signing_key, b"jev-credential-v1\0" + request.credential.get_secret_value().encode(), hashlib.sha256
    ).digest()
    return hmac.new(signing_key, payload + b"\0" + credential_mac, hashlib.sha256).hexdigest()
