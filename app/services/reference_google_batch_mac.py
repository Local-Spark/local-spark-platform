"""Commitment to an ephemeral Places batch, without retaining its contents.

This MAC is not proof of a provider response on its own. A trusted, fenced
activity must compute it immediately after decoding the response and must link
it to the Jev intent under the same search before any sanitized commit.
"""

import hashlib
import hmac
import json
import math
import re
from uuid import UUID

from pydantic import SecretStr

from app.adapters.google_places import PlaceCandidate, PlacesAddressComponent
from app.services.reference_observation_sanitizer import CandidateObservation

_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,64}")


class GoogleBatchBindingError(ValueError):
    """A stable error that never includes customer or provider data."""


def _optional_string(value: object, maximum: int) -> bool:
    return value is None or isinstance(value, str) and 0 < len(value) <= maximum and bool(value.strip())


def _optional_number(value: object, minimum: float, maximum: float) -> bool:
    if value is None:
        return True
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    return minimum <= value <= maximum and math.isfinite(value)


def google_batch_mac(
    key: SecretStr,
    *,
    key_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    search: UUID,
    google_effect: UUID,
    pilot: UUID,
    context_version: int,
    observations: tuple[CandidateObservation, ...],
) -> str:
    """Authenticate source-order candidates and all ephemeral fields.

    The candidate UUID and its array position must be used when constructing
    the Jev input. Only the MAC and version may be durably stored, never the
    serialized payload. This helper does not perform I/O or authorize writes.
    """
    if not isinstance(key, SecretStr):
        raise GoogleBatchBindingError("REFERENCE_BATCH_KEY_INVALID")
    try:
        signing_key = key.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise GoogleBatchBindingError("REFERENCE_BATCH_KEY_INVALID") from None
    if len(signing_key) < 32:
        raise GoogleBatchBindingError("REFERENCE_BATCH_KEY_INVALID")
    if (
        not isinstance(key_version, str)
        or not _VERSION.fullmatch(key_version)
        or any(not isinstance(value, UUID) for value in (tenant, business, actor, search, google_effect, pilot))
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or not isinstance(observations, tuple)
        or len(observations) > 20
    ):
        raise GoogleBatchBindingError("REFERENCE_BATCH_INVALID")
    ids: set[UUID] = set()
    places: set[str] = set()
    rows: list[list[object]] = []
    for item in observations:
        if not isinstance(item, CandidateObservation) or not isinstance(item.candidate_id, UUID):
            raise GoogleBatchBindingError("REFERENCE_BATCH_INVALID")
        place = item.place
        if (
            not isinstance(place, PlaceCandidate)
            or not isinstance(place.place_id, str)
            or not 0 < len(place.place_id) <= 2048
            or place.place_id != place.place_id.strip()
            or not _optional_string(place.name, 300)
            or not _optional_string(place.website, 2048)
            or not _optional_string(place.formatted_address, 1000)
            or not isinstance(place.address_components, tuple)
            or len(place.address_components) > 100
            or any(
                not isinstance(part, PlacesAddressComponent)
                or not isinstance(part.long_text, str)
                or not _optional_string(part.long_text, 300)
                or not _optional_string(part.short_text, 300)
                or not isinstance(part.types, tuple)
                or not 1 <= len(part.types) <= 100
                or any(not isinstance(kind, str) or not 1 <= len(kind) <= 100 for kind in part.types)
                for part in place.address_components
            )
            or not _optional_number(place.latitude, -90, 90)
            or not _optional_number(place.longitude, -180, 180)
            or not _optional_number(place.rating, 0, 5)
            or (place.rating_count is not None and (type(place.rating_count) is not int or place.rating_count < 0))
            or not isinstance(place.types, tuple)
            or len(place.types) > 50
            or any(
                not isinstance(value, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) is None
                for value in place.types
            )
            or len(set(place.types)) != len(place.types)
            or item.candidate_id in ids
            or place.place_id in places
        ):
            raise GoogleBatchBindingError("REFERENCE_BATCH_INVALID")
        ids.add(item.candidate_id)
        places.add(place.place_id)
        rows.append(
            [
                str(item.candidate_id),
                place.place_id,
                place.name,
                place.latitude,
                place.longitude,
                place.rating,
                place.rating_count,
                place.website,
                place.types,
                place.formatted_address,
                [[part.long_text, part.short_text, part.types] for part in place.address_components],
            ]
        )
    payload = json.dumps(
        [
            "reference-google-batch-v3",
            key_version,
            str(tenant),
            str(business),
            str(actor),
            str(search),
            str(google_effect),
            str(pilot),
            context_version,
            rows,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    return hmac.new(signing_key, payload, hashlib.sha256).hexdigest()
