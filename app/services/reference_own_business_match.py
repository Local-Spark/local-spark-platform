"""Conservative, in-memory identification of the owner's own business.

The caller must bind the versioned owner details and provider response to the
same authorized effect before using the decision. A geocoded address ID does
not identify a business listing. Google data handled here is never persisted.
"""

import re
from dataclasses import dataclass
from typing import Literal
from unicodedata import combining, normalize

from app.adapters.google_places import PlaceCandidate, PlacesAddressComponent
from app.schemas.editorial_context import ReferenceAddress


@dataclass(frozen=True)
class OwnBusinessMatch:
    status: Literal["identified", "review", "absent"]
    place_ids: tuple[str, ...]


def _tokens(value: str | None) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    return tuple(re.findall(r"[^\W_]+", normalize("NFKC", value).casefold(), flags=re.UNICODE))


def _approximate_tokens(value: str | None) -> tuple[str, ...]:
    return tuple(
        "".join(character for character in normalize("NFD", token) if not combining(character))
        for token in _tokens(value)
    )


def _component(
    components: tuple[PlacesAddressComponent, ...], kinds: frozenset[str], *, short: bool = False
) -> tuple[str, ...]:
    matches = [component for component in components if kinds.intersection(component.types)]
    if len(matches) != 1:
        return ()
    return _tokens(matches[0].short_text if short else matches[0].long_text)


def _address_evidence(owner: ReferenceAddress, candidate: PlaceCandidate) -> tuple[bool, bool, bool]:
    components = candidate.address_components
    if not isinstance(components, tuple) or any(
        not isinstance(item, PlacesAddressComponent)
        or not isinstance(item.types, tuple)
        or not all(isinstance(kind, str) for kind in item.types)
        for item in components
    ):
        return False, False, False
    street = _component(components, frozenset({"route"}))
    number = _component(components, frozenset({"street_number"}))
    city = _component(components, frozenset({"locality"}))
    state = _component(components, frozenset({"administrative_area_level_1"}), short=True)
    country = _component(components, frozenset({"country"}), short=True)
    complete = bool(street and number and city and state and country)
    same_locality = bool(
        number
        and city
        and state
        and number == _tokens(owner.number)
        and city == _tokens(owner.city)
        and state == _tokens(owner.state_code)
    )
    clear = bool(
        complete
        and country == ("br",)
        and same_locality
        and street == _tokens(owner.street)
        # Google does not necessarily identify an individual unit at an address.
        and owner.complement is None
        and not any({"subpremise", "floor", "room"}.intersection(component.types) for component in components)
    )
    if owner.neighborhood is not None:
        neighborhood = _component(components, frozenset({"neighborhood", "sublocality_level_1"}))
        clear = clear and neighborhood == _tokens(owner.neighborhood)
    if owner.postal_code is not None:
        postal = _component(components, frozenset({"postal_code"}))
        clear = clear and bool(postal) and "".join(postal) == "".join(_tokens(owner.postal_code))
    return clear, complete, same_locality


def identify_own_business(
    owner_name: str | None, owner_address: ReferenceAddress, candidates: tuple[PlaceCandidate, ...]
) -> OwnBusinessMatch:
    """Return one clear match, possible matches requiring review, or absence.

    Publication must wait for review. Absence concerns only the supplied
    results, never listings omitted by the provider. Neither formatted Google
    addresses nor Place IDs from geocoding prove business identity.
    """
    name = _tokens(owner_name)
    if not candidates:
        return OwnBusinessMatch("absent", ())
    if (
        not name
        or not isinstance(owner_address, ReferenceAddress)
        or not all(
            _tokens(value)
            for value in (owner_address.street, owner_address.number, owner_address.city, owner_address.state_code)
        )
    ):
        return OwnBusinessMatch("review", tuple(candidate.place_id for candidate in candidates))
    plausible: list[str] = []
    exact: list[str] = []
    name_words = set(_approximate_tokens(owner_name))
    for candidate in candidates:
        candidate_name = _tokens(candidate.name)
        address, address_complete, same_locality = _address_evidence(owner_address, candidate)
        same_name = candidate_name == name
        similar_name = bool(name_words.intersection(_approximate_tokens(candidate.name)))
        if same_name and address:
            exact.append(candidate.place_id)
        if same_name or similar_name or address or not candidate_name or not address_complete or same_locality:
            plausible.append(candidate.place_id)
    if len(exact) == 1 and len(plausible) == 1:
        return OwnBusinessMatch("identified", tuple(exact))
    if plausible:
        return OwnBusinessMatch("review", tuple(plausible))
    return OwnBusinessMatch("absent", ())
