"""Pure commitment to a future tied-position Jev effect, with no side effects.

The trusted caller must construct the ordered tied IDs and the provider body
from the same authorized batch. The MAC alone does not prove that relationship,
prove an actual tie, reserve a budget, or authorize a provider call.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr

from app.adapters.jev_reference_tiebreak import TieBreakRequest

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_MODEL = re.compile(r"[A-Za-z0-9_.-]{1,120}")


class TieBreakBindingError(ValueError):
    """Stable code without private request, identifiers or credentials."""


def tiebreak_request_mac(
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
    google_effect: UUID,
    similarity_effect: UUID,
    batch_id: UUID,
    context_version: int,
    source_batch_mac: str,
    reserved_usd_micros: int,
    tied_candidate_ids: tuple[UUID, ...],
    request: TieBreakRequest,
) -> str:
    if not isinstance(key, SecretStr):
        raise TieBreakBindingError("TIE_BREAK_BINDING_KEY_INVALID")
    try:
        key_bytes = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise TieBreakBindingError("TIE_BREAK_BINDING_KEY_INVALID") from None
    if len(key_bytes) < 32:
        raise TieBreakBindingError("TIE_BREAK_BINDING_KEY_INVALID")
    if (
        any(
            not isinstance(v, str) or not _VERSION.fullmatch(v)
            for v in (key_version, tariff_version, credential_version)
        )
        or any(
            not isinstance(v, UUID)
            for v in (tenant, business, actor, search, effect, pilot, google_effect, similarity_effect, batch_id)
        )
        or len({effect, google_effect, similarity_effect}) != 3
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or not isinstance(source_batch_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", source_batch_mac) is None
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(tied_candidate_ids, tuple)
        or not 2 <= len(tied_candidate_ids) <= 20
        or any(not isinstance(value, UUID) for value in tied_candidate_ids)
        or len(set(tied_candidate_ids)) != len(tied_candidate_ids)
        or not isinstance(request, TieBreakRequest)
        or request.method != "POST"
        or request.url != "https://api.typesafe.ai/v1/systemone"
        or not isinstance(request.model, str)
        or not _MODEL.fullmatch(request.model)
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 262_144
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
        or request.headers
        != (
            ("content-length", str(len(request.body))),
            ("content-type", "application/json"),
            ("host", "api.typesafe.ai"),
            ("x-client-request-id", str(effect)),
        )
    ):
        raise TieBreakBindingError("TIE_BREAK_BINDING_INVALID")
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError, UnicodeDecodeError):
        raise TieBreakBindingError("TIE_BREAK_BINDING_INVALID") from None
    if not isinstance(body, dict) or body.get("model") != request.model:
        raise TieBreakBindingError("TIE_BREAK_BINDING_INVALID")
    try:
        credential = request.credential.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise TieBreakBindingError("TIE_BREAK_BINDING_INVALID") from None
    credential_mac = hmac.new(key_bytes, b"reference-tiebreak-credential-v1\0" + credential, hashlib.sha256).hexdigest()
    payload = json.dumps(
        [
            "reference-tiebreak-v1",
            key_version,
            tariff_version,
            credential_version,
            str(tenant),
            str(business),
            str(actor),
            str(search),
            str(effect),
            str(pilot),
            str(google_effect),
            str(similarity_effect),
            str(batch_id),
            context_version,
            source_batch_mac,
            reserved_usd_micros,
            [str(candidate) for candidate in tied_candidate_ids],
            request.method,
            request.url,
            request.headers,
            request.model,
            request.body.hex(),
            credential_mac,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hmac.new(key_bytes, payload, hashlib.sha256).hexdigest()
