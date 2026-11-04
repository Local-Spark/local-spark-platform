"""Conservative in-memory matching of an owner's address to geocode results.

This helper neither authenticates provider output nor records a location. A
trusted activity must bind the matched candidate to its fenced provider effect
and current owner-supplied address before any persistent use.
"""

import math
import re
from unicodedata import normalize

from app.adapters.google_geocoding import GeocodingAddressComponent, GeocodingCandidate
from app.schemas.editorial_context import ReferenceAddress


def _normalized(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    result = " ".join(normalize("NFC", value).casefold().split())
    return result or None


def _postal(value: str | None) -> str | None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{5}-?[0-9]{3}", value) is None:
        return None
    return value.replace("-", "")


def _component(
    components: tuple[GeocodingAddressComponent, ...], kinds: frozenset[str], *, short: bool = False
) -> str | None:
    matches = [component for component in components if kinds.intersection(component.types)]
    if len(matches) != 1:
        return None
    return matches[0].short_text if short else matches[0].long_text


def _valid_candidate(value: object) -> bool:
    if not isinstance(value, GeocodingCandidate):
        return False
    if (
        not isinstance(value.place_id, str)
        or not 1 <= len(value.place_id) <= 2048
        or value.place_id != value.place_id.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value.place_id)
        or not isinstance(value.address_components, tuple)
        or len(value.address_components) > 100
        or value.confirmed is not False
    ):
        return False
    try:
        value.place_id.encode("utf-8")
        if any(
            type(coordinate) not in (int, float) or not math.isfinite(coordinate) or not lower <= coordinate <= upper
            for coordinate, lower, upper in ((value.latitude, -90, 90), (value.longitude, -180, 180))
        ):
            return False
    except (OverflowError, UnicodeEncodeError):
        return False
    for part in value.address_components:
        if (
            not isinstance(part, GeocodingAddressComponent)
            or not isinstance(part.long_text, str)
            or not 1 <= len(part.long_text.strip()) <= 300
            or (
                part.short_text is not None
                and (not isinstance(part.short_text, str) or not 1 <= len(part.short_text) <= 300)
            )
            or not isinstance(part.types, tuple)
            or not 1 <= len(part.types) <= 100
            or any(not isinstance(kind, str) or not 1 <= len(kind) <= 100 for kind in part.types)
        ):
            return False
    return True


def automatic_location_candidate(
    address: ReferenceAddress, results: tuple[GeocodingCandidate, ...]
) -> GeocodingCandidate | None:
    """Return the unique precise match, or None when owner review is needed.

    Components and the returned candidate remain in the caller's memory. The
    address must already be established as the business's own owner-supplied
    address; an arbitrary search origin is not enough to establish this.
    """
    if not isinstance(address, ReferenceAddress) or not isinstance(results, tuple) or len(results) != 1:
        return None
    candidate = results[0]
    if (
        not _valid_candidate(candidate)
        or candidate.country != "BR"
        or candidate.granularity != "ROOFTOP"
        or not address.street
        or not address.number
    ):
        return None
    components = candidate.address_components
    for expected, actual in (
        (address.street, _component(components, frozenset({"route"}))),
        (address.number, _component(components, frozenset({"street_number"}))),
        (address.city, _component(components, frozenset({"locality"}))),
        (address.state_code, _component(components, frozenset({"administrative_area_level_1"}), short=True)),
        (address.neighborhood, _component(components, frozenset({"neighborhood", "sublocality_level_1"}))),
    ):
        if expected is not None and (_normalized(actual) is None or _normalized(expected) != _normalized(actual)):
            return None
    if address.postal_code is not None:
        postal = _component(components, frozenset({"postal_code"}))
        if _postal(postal) is None or _postal(address.postal_code) != _postal(postal):
            return None
    return candidate
