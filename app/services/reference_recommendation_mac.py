"""Bind a future recommendation effect to its exact private request and shortlist.

The caller must build request and shortlist from the same authorized batch in
one trusted activity. This pure MAC alone neither proves that mapping nor
reserves funds; no provider I/O or database writes happen here.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr

from app.adapters.jev_reference_recommendations import RecommendationRequest
from app.schemas.reference_filtered_batch import FilteredBatch

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_MODEL = re.compile(r"[A-Za-z0-9_.-]{1,120}")


class RecommendationBindingError(ValueError):
    """Stable error without private inputs or credentials."""


def recommendation_request_mac(
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
    shortlist: FilteredBatch,
    request: RecommendationRequest,
) -> str:
    if not isinstance(key, SecretStr):
        raise RecommendationBindingError("RECOMMENDATION_BINDING_KEY_INVALID")
    try:
        key_bytes = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise RecommendationBindingError("RECOMMENDATION_BINDING_KEY_INVALID") from None
    if len(key_bytes) < 32:
        raise RecommendationBindingError("RECOMMENDATION_BINDING_KEY_INVALID")
    if (
        any(
            not isinstance(value, str) or not _VERSION.fullmatch(value)
            for value in (key_version, tariff_version, credential_version)
        )
        or any(
            not isinstance(value, UUID)
            for value in (
                tenant,
                business,
                actor,
                search,
                effect,
                pilot,
                google_effect,
                similarity_effect,
                batch_id,
            )
        )
        or len({effect, google_effect, similarity_effect}) != 3
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or not isinstance(source_batch_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", source_batch_mac) is None
        or type(reserved_usd_micros) is not int
        or not 0 < reserved_usd_micros <= 5_000_000
        or not isinstance(shortlist, FilteredBatch)
        or not 1 <= len(shortlist.candidates) <= 10
        or not isinstance(request, RecommendationRequest)
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
            ("x-client-request-id", str(effect)),
        )
    ):
        raise RecommendationBindingError("RECOMMENDATION_BINDING_INVALID")
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError, UnicodeDecodeError):
        raise RecommendationBindingError("RECOMMENDATION_BINDING_INVALID") from None
    if not isinstance(body, dict) or body.get("model") != request.model:
        raise RecommendationBindingError("RECOMMENDATION_BINDING_INVALID")
    try:
        credential_bytes = request.credential.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise RecommendationBindingError("RECOMMENDATION_BINDING_INVALID") from None
    credential_mac = hmac.new(
        key_bytes, b"reference-recommendation-credential-v1\0" + credential_bytes, hashlib.sha256
    ).hexdigest()
    payload = json.dumps(
        [
            "reference-recommendation-v1",
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
            shortlist.model_dump(mode="json")["candidates"],
            request.method,
            request.url,
            request.model,
            request.body.hex(),
            request.headers,
            credential_mac,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hmac.new(key_bytes, payload, hashlib.sha256).hexdigest()
