"""Only definite, scoreable matches survive this in-memory projection."""

from dataclasses import replace
from uuid import uuid4

import pytest

from app.adapters.google_places import PlaceCandidate, PlacesAddressComponent
from app.adapters.jev_reference_similarity import SimilarityJudgment
from app.services.reference_observation_sanitizer import (
    CandidateObservation,
    ObservationSanitizationError,
    sanitize_similar_observations,
)


def observation(place_id="test-place", rating=4.8, count=200):
    return CandidateObservation(uuid4(), PlaceCandidate(place_id, "secret name", 12.0, 13.0, rating, count, "secret"))


def judgment(item, choice="match"):
    return SimilarityJudgment(item.candidate_id, choice, None, None)


def test_filters_before_scoring_and_returns_only_allowlisted_fields():
    match = observation()
    excluded = observation("excluded", rating=-100)
    uncertain = observation("uncertain", rating=-100)
    missing = observation("no-score", count=0)
    result = sanitize_similar_observations(
        (match, excluded, uncertain, missing),
        (judgment(uncertain, "uncertain"), judgment(missing), judgment(match), judgment(excluded, "no_match")),
    )
    assert len(result) == 1 and result[0].place_id == "test-place"
    assert result[0].candidate_id == match.candidate_id
    assert result[0].reputation_formula_version == "penalized-3.4-v1"
    assert set(result[0].__dict__) == {"candidate_id", "place_id", "reputation_score", "reputation_formula_version"}
    assert "test-place" not in repr(result[0])


def test_empty_observations_are_valid():
    assert sanitize_similar_observations((), ()) == ()


@pytest.mark.parametrize("items", [None, [], (None,), tuple(observation(str(i)) for i in range(21))])
def test_invalid_observations_are_rejected(items):
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_OBSERVATIONS_INVALID"):
        sanitize_similar_observations(items, ())


def test_invalid_and_duplicate_identifiers_fail_closed():
    item = observation()
    for items in (
        (item, item),
        (item, replace(item, candidate_id=uuid4())),
        (replace(item, candidate_id="not-a-uuid"),),
        (replace(item, place=None),),
        (observation(" "),),
        (observation(" padded "),),
        (observation("x" * 2049),),
    ):
        with pytest.raises(ObservationSanitizationError, match="REFERENCE_OBSERVATIONS_INVALID"):
            sanitize_similar_observations(items, ())


def test_judgments_are_exactly_one_per_candidate_and_from_expected_domain():
    item = observation()
    valid = judgment(item)
    for values in (
        None,
        [],
        (None,),
        (),
        (valid, valid),
        (judgment(observation()),),
        (judgment(item, "maybe"),),
        (replace(valid, candidate_id=[]),),
    ):
        with pytest.raises(ObservationSanitizationError, match="REFERENCE_JUDGMENTS_INVALID"):
            sanitize_similar_observations((item,), values)


def test_matching_candidate_with_invalid_rating_is_rejected_without_echoing_data():
    item = observation(rating=-100)
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_OBSERVATIONS_INVALID") as error:
        sanitize_similar_observations((item,), (judgment(item),))
    assert "secret" not in str(error.value)


def test_formatted_google_address_does_not_survive_sanitization():
    original = observation()
    original = replace(
        original,
        place=replace(
            original.place,
            formatted_address="endereço privado do Google",
            address_components=(PlacesAddressComponent("Rua privada", None, ("route",)),),
        ),
    )
    result = sanitize_similar_observations((original,), (judgment(original),))
    assert len(result) == 1
    assert "formatted_address" not in result[0].__dict__
    assert "address_components" not in result[0].__dict__
    assert "endereço privado" not in repr(result[0])
