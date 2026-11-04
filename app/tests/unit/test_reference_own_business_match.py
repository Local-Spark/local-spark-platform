from dataclasses import replace

import pytest

from app.adapters.google_places import PlaceCandidate, PlacesAddressComponent, _candidate
from app.schemas.editorial_context import ReferenceAddress
from app.services.reference_own_business_match import OwnBusinessMatch, identify_own_business


@pytest.fixture
def address() -> ReferenceAddress:
    return ReferenceAddress(
        street="Rua das Flores",
        number="123",
        neighborhood="Centro",
        city="São Paulo",
        state_code="SP",
        postal_code="01001-000",
    )


def component(kind: str, value: str, *, short: str | None = None) -> PlacesAddressComponent:
    return PlacesAddressComponent(value, short, (kind,))


@pytest.fixture
def place() -> PlaceCandidate:
    return PlaceCandidate(
        "owner-id",
        "Café Solar",
        None,
        None,
        5.0,
        10,
        None,
        formatted_address="Rua das Flores, 123 - Centro, São Paulo - SP, 01001-000, Brasil",
        address_components=(
            component("route", "Rua das Flores"),
            component("street_number", "123"),
            component("neighborhood", "Centro"),
            component("locality", "São Paulo"),
            component("administrative_area_level_1", "São Paulo", short="SP"),
            component("postal_code", "01001000"),
            component("country", "Brasil", short="BR"),
        ),
    )


def changed(place: PlaceCandidate, kind: str, value: str | None, *, short: str | None = None) -> PlaceCandidate:
    remaining = tuple(c for c in place.address_components if kind not in c.types)
    return replace(place, address_components=remaining + ((component(kind, value, short=short),) if value else ()))


def other(place: PlaceCandidate) -> PlaceCandidate:
    return changed(changed(changed(place, "route", "Avenida Brasil"), "street_number", "4"), "locality", "Santos")


def test_identifies_one_clear_match(address: ReferenceAddress, place: PlaceCandidate) -> None:
    unrelated = replace(other(place), place_id="other", name="Padaria Estrela")
    assert identify_own_business("  CAFÉ Solar ", address, (place, unrelated)) == OwnBusinessMatch(
        "identified", ("owner-id",)
    )
    assert "Café" not in repr(place)


@pytest.mark.parametrize("complete", [True, False])
def test_optional_provider_components_do_not_invent_address_evidence(address, place, complete):
    components = [
        {"longText": part.long_text, "shortText": part.short_text or "", "types": list(part.types)}
        for part in place.address_components
    ]
    if not complete:
        components[0]["longText"] = ""
    parsed = _candidate(
        {
            "id": place.place_id,
            "displayName": {"text": place.name},
            "addressComponents": [{}, {"longText": "Unused", "types": []}, *components],
        }
    )
    result = identify_own_business("Café Solar", address, (parsed,))
    assert result.status == ("identified" if complete else "review")
    assert result.place_ids == (place.place_id,)


def test_no_results_is_absent(address: ReferenceAddress) -> None:
    assert identify_own_business(None, address, ()) == OwnBusinessMatch("absent", ())


@pytest.mark.parametrize("owner_name", [None, "", "   "])
def test_missing_owner_name_needs_review(
    address: ReferenceAddress, place: PlaceCandidate, owner_name: str | None
) -> None:
    assert identify_own_business(owner_name, address, (place,)).status == "review"


def test_incomplete_own_address_needs_review(place: PlaceCandidate) -> None:
    address = ReferenceAddress(city="São Paulo", state_code="SP")
    assert identify_own_business("Café Solar", address, (place,)).status == "review"


def test_unrelated_complete_candidate_is_absent(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert identify_own_business(
        "Café Solar", address, (replace(other(place), name="Padaria Estrela"),)
    ) == OwnBusinessMatch("absent", ())


@pytest.mark.parametrize("field,value", [("name", None), ("name", "")])
def test_missing_candidate_name_needs_review(
    address: ReferenceAddress, place: PlaceCandidate, field: str, value: str | None
) -> None:
    assert identify_own_business("Café Solar", address, (replace(place, **{field: value}),)).status == "review"


@pytest.mark.parametrize(
    "kind,value",
    [
        ("route", None),
        ("street_number", None),
        ("locality", None),
        ("administrative_area_level_1", None),
        ("route", "R. das Flores"),
        ("street_number", "124"),
        ("locality", "Santos"),
        ("neighborhood", "Outro bairro"),
        ("postal_code", "01001001"),
    ],
)
def test_missing_or_different_component_needs_review(
    address: ReferenceAddress, place: PlaceCandidate, kind: str, value: str | None
) -> None:
    assert identify_own_business("Café Solar", address, (changed(place, kind, value),)).status == "review"


def test_duplicate_component_needs_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    suspect = replace(place, address_components=place.address_components + (component("route", "Rua das Flores"),))
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


def test_other_business_same_address_needs_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert identify_own_business("Café Solar", address, (replace(place, name="Outro comércio"),)).status == "review"


def test_similar_name_needs_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert identify_own_business("Bar Zé", address, (replace(other(place), name="Bar Ze"),)).status == "review"


def test_two_potential_matches_need_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert identify_own_business("Café Solar", address, (place, replace(place, place_id="second"))) == OwnBusinessMatch(
        "review", ("owner-id", "second")
    )


def test_postal_code_hyphenation_is_ignored(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert (
        identify_own_business("Café Solar", address, (changed(place, "postal_code", "01001-000"),)).status
        == "identified"
    )


def test_complement_requires_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    assert (
        identify_own_business("Café Solar", address.model_copy(update={"complement": "Sala 10"}), (place,)).status
        == "review"
    )


def test_no_optional_address_fields(place: PlaceCandidate) -> None:
    address = ReferenceAddress(street="Rua das Flores", number="123", city="São Paulo", state_code="SP")
    assert identify_own_business("Café Solar", address, (place,)).status == "identified"


def test_sublocality_as_neighborhood(address: ReferenceAddress, place: PlaceCandidate) -> None:
    without_neighborhood = changed(place, "neighborhood", None)
    suspect = replace(
        without_neighborhood,
        address_components=without_neighborhood.address_components + (component("sublocality_level_1", "Centro"),),
    )
    assert identify_own_business("Café Solar", address, (suspect,)).status == "identified"


def test_missing_or_incomplete_components_cannot_be_inferred_from_formatted_address(
    address: ReferenceAddress, place: PlaceCandidate
) -> None:
    suspect = replace(
        other(place), name="Padaria", address_components=(), formatted_address="Avenida Central, 123 - SP"
    )
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


def test_same_locality_and_number_with_different_name_and_street_needs_review(
    address: ReferenceAddress, place: PlaceCandidate
) -> None:
    suspect = changed(replace(place, name="Cafeteria"), "route", "R. das Flores")
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


def test_invalid_components_never_identify(address: ReferenceAddress, place: PlaceCandidate) -> None:
    suspect = replace(place, name="Padaria", address_components=("invalid",))
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


@pytest.mark.parametrize("kind", ["subpremise", "floor", "room"])
def test_provider_unit_requires_review_if_owner_has_no_complement(
    address: ReferenceAddress, place: PlaceCandidate, kind: str
) -> None:
    suspect = replace(place, address_components=place.address_components + (component(kind, "Loja 2"),))
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


def test_malformed_component_types_require_review(address: ReferenceAddress, place: PlaceCandidate) -> None:
    malformed = PlacesAddressComponent("Rua", "Rua", None)
    suspect = replace(place, address_components=(malformed,))
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"


@pytest.mark.parametrize("country,short", [(None, None), ("Estados Unidos", "US"), ("Brasil", None)])
def test_missing_or_different_country_requires_review(
    address: ReferenceAddress, place: PlaceCandidate, country: str | None, short: str | None
) -> None:
    suspect = changed(place, "country", country, short=short)
    assert identify_own_business("Café Solar", address, (suspect,)).status == "review"
