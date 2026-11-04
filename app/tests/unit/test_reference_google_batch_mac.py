"""The private Google batch commitment is context-bound and order-sensitive."""

from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.google_places import PlaceCandidate, PlacesAddressComponent, _candidate
from app.services.reference_google_batch_mac import GoogleBatchBindingError, google_batch_mac
from app.services.reference_observation_sanitizer import CandidateObservation


def arguments():
    return {
        "key": SecretStr("synthetic-test-hmac-key-not-for-use-12345"),
        "key_version": "test-v1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "search": uuid4(),
        "google_effect": uuid4(),
        "pilot": uuid4(),
        "context_version": 1,
        "observations": (
            CandidateObservation(uuid4(), PlaceCandidate("place-a", "private-name", 1.0, 2.0, 4.2, 100, "website")),
            CandidateObservation(uuid4(), PlaceCandidate("place-b", None, None, None, None, None, None)),
        ),
    }


def test_mac_binds_every_identity_order_and_input_without_revealing_data():
    args = arguments()
    mac = google_batch_mac(**args)
    assert mac == google_batch_mac(**args) and len(mac) == 64
    assert "private-name" not in mac and "place-a" not in mac
    for name in ("tenant", "business", "actor", "search", "google_effect", "pilot"):
        assert google_batch_mac(**{**args, name: uuid4()}) != mac
    for name, value in (
        ("key", SecretStr("different-synthetic-key-not-for-use-12345")),
        ("key_version", "test-v2"),
        ("context_version", 2),
        ("observations", tuple(reversed(args["observations"]))),
    ):
        assert google_batch_mac(**{**args, name: value}) != mac
    first, second = args["observations"]
    assert google_batch_mac(**{**args, "observations": (replace(first, candidate_id=uuid4()), second)}) != mac
    for field, value in (
        ("place_id", "changed"),
        ("name", "changed"),
        ("latitude", 3.0),
        ("longitude", 4.0),
        ("rating", 3.2),
        ("rating_count", 99),
        ("website", "changed"),
        ("types", ("cafe",)),
        ("formatted_address", "Rua privada"),
        ("address_components", (PlacesAddressComponent("Rua privada", None, ("route",)),)),
    ):
        changed = replace(first, place=replace(first.place, **{field: value}))
        assert google_batch_mac(**{**args, "observations": (changed, second)}) != mac


def test_normalized_optional_address_components_keep_the_same_usable_batch_evidence():
    args = arguments()
    observation = args["observations"][0]
    usable = {"longText": "Synthetic street", "types": ["route"]}
    base = {"id": "synthetic-place", "addressComponents": [usable]}
    normalized = _candidate(
        {
            **base,
            "addressComponents": [
                {},
                {"longText": "No type"},
                {"types": ["route"]},
                {**usable, "shortText": ""},
            ],
        }
    )
    assert normalized == _candidate(base)
    assert google_batch_mac(**{**args, "observations": (replace(observation, place=normalized),)}) == google_batch_mac(
        **{**args, "observations": (replace(observation, place=_candidate(base)),)}
    )


@pytest.mark.parametrize("key", [None, SecretStr("short"), SecretStr("a" * 32 + "\ud800")])
def test_invalid_key_is_rejected_without_echoing(key):
    with pytest.raises(GoogleBatchBindingError, match="REFERENCE_BATCH_KEY_INVALID"):
        google_batch_mac(**{**arguments(), "key": key})


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_version", None),
        ("key_version", "!"),
        ("tenant", "invalid"),
        ("context_version", True),
        ("context_version", 0),
        ("context_version", 2**63),
        ("observations", []),
        ("observations", (None,)),
    ],
)
def test_invalid_metadata_is_rejected(field, value):
    with pytest.raises(GoogleBatchBindingError, match="REFERENCE_BATCH_INVALID"):
        google_batch_mac(**{**arguments(), field: value})


def test_invalid_candidates_and_duplicates_are_rejected():
    args = arguments()
    first, second = args["observations"]
    bad_places = (
        replace(first.place, place_id=None),
        replace(first.place, place_id=""),
        replace(first.place, place_id=" padded "),
        replace(first.place, place_id="a" * 2049),
        replace(first.place, name=" "),
        replace(first.place, website=" "),
        replace(first.place, formatted_address=" "),
        replace(first.place, formatted_address="x" * 1001),
        replace(first.place, address_components=[]),
        replace(first.place, address_components=(None,)),
        replace(
            first.place, address_components=tuple(PlacesAddressComponent("x", None, ("route",)) for _ in range(101))
        ),
        replace(first.place, address_components=(PlacesAddressComponent(None, None, ("route",)),)),
        replace(first.place, address_components=(PlacesAddressComponent(" ", None, ("route",)),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", " ", ("route",)),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", None, []),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", None, ()),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", None, (None,)),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", None, ("",)),)),
        replace(first.place, address_components=(PlacesAddressComponent("x", None, ("x" * 101,)),)),
        replace(first.place, latitude=float("nan")),
        replace(first.place, longitude=True),
        replace(first.place, rating=6.0),
        replace(first.place, rating_count=-1),
        replace(first.place, rating_count=True),
        replace(first.place, types=[]),
        replace(first.place, types=("bad-type",)),
        replace(first.place, types=("cafe", "cafe")),
        replace(first.place, types=tuple(str(i) for i in range(51))),
    )
    invalid = [(replace(first, place=value),) for value in bad_places]
    invalid += [
        (replace(first, place=None),),
        (replace(first, candidate_id="x"),),
        (first, first),
        (first, replace(second, place=replace(second.place, place_id=first.place.place_id))),
        tuple(CandidateObservation(uuid4(), replace(first.place, place_id=str(i))) for i in range(21)),
    ]
    for observations in invalid:
        with pytest.raises(GoogleBatchBindingError, match="REFERENCE_BATCH_INVALID") as error:
            google_batch_mac(**{**args, "observations": observations})
        assert "private-name" not in str(error.value)


def test_empty_batch_is_bound_to_the_search():
    args = {**arguments(), "observations": ()}
    assert google_batch_mac(**args) != google_batch_mac(**{**args, "search": uuid4()})
