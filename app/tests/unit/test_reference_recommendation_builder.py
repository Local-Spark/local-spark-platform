"""Recommendation input cannot reorder or substitute another place."""

from dataclasses import replace
from uuid import uuid4

import pytest

from app.adapters.google_places import PlaceCandidate
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_observation_sanitizer import CandidateObservation
from app.services.reference_recommendation_builder import RecommendationBuildError, build_recommendation_input


def values():
    observations = tuple(
        CandidateObservation(
            uuid4(), PlaceCandidate(f"place-{i}", f"private-name-{i}", 1.0, 2.0, 4.0, 10, None, ("cafe",))
        )
        for i in range(3)
    )
    shortlist = FilteredBatch(
        candidates=tuple(
            {
                "candidate_id": item.candidate_id,
                "place_id": item.place.place_id,
                "reputation_score": "8.2",
                "reputation_formula_version": "penalized-3.4-v1",
            }
            for item in (observations[2], observations[0])
        )
    )
    return observations, shortlist


def test_build_uses_same_id_place_and_authorized_order():
    observations, shortlist = values()
    result = build_recommendation_input(observations, shortlist, business_terms=("cafe",), business_description=None)
    assert [item.candidate_id for item in result.candidates] == [
        observations[2].candidate_id,
        observations[0].candidate_id,
    ]
    assert [item.name for item in result.candidates] == ["private-name-2", "private-name-0"]
    assert all(
        item.types == ("cafe",) and item.reputation_score == shortlist.candidates[0].reputation_score
        for item in result.candidates
    )
    assert "private-name" not in repr(result)


def test_invalid_or_mismatched_mapping_fails_closed_without_leak():
    observations, shortlist = values()
    wrong_id = shortlist.candidates[0].model_copy(update={"candidate_id": uuid4()})
    wrong_place = shortlist.candidates[0].model_copy(update={"place_id": "other"})
    too_many = FilteredBatch(
        candidates=tuple(
            {
                "candidate_id": uuid4(),
                "place_id": str(i),
                "reputation_score": "8",
                "reputation_formula_version": "penalized-3.4-v1",
            }
            for i in range(11)
        )
    )
    for obs, selected in (
        (None, shortlist),
        ([], shortlist),
        (observations * 8, shortlist),
        (observations, None),
        (observations, FilteredBatch(candidates=())),
        (observations, too_many),
        ((None,), shortlist),
        ((observations[0], observations[0]), shortlist),
        ((replace(observations[0], candidate_id=[]),), shortlist),
        ((replace(observations[0], place=None),), shortlist),
        ((replace(observations[0], place=replace(observations[0].place, place_id=None)),), shortlist),
        ((observations[0], replace(observations[1], place=observations[0].place)), shortlist),
        (observations, FilteredBatch(candidates=(wrong_id,))),
        (observations, FilteredBatch(candidates=(wrong_place,))),
    ):
        with pytest.raises(RecommendationBuildError, match="RECOMMENDATION_MAPPING_INVALID") as error:
            build_recommendation_input(obs, selected, business_terms=("cafe",), business_description=None)
        assert "private-name" not in str(error.value)
