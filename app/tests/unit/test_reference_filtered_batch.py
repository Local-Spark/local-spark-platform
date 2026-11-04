"""Filtered batches admit only IDs and the derived score, never raw input."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.reference_filtered_batch import FilteredBatch


def candidate():
    return {
        "candidate_id": uuid4(),
        "place_id": "test-place",
        "reputation_score": "8.25",
        "reputation_formula_version": "penalized-3.4-v1",
    }


def test_valid_empty_and_scoreable_batch():
    assert FilteredBatch(candidates=()).candidates == ()
    batch = FilteredBatch(candidates=(candidate(),))
    assert batch.candidates[0].reputation_score == 8.25
    assert set(batch.model_dump()["candidates"][0]) == {
        "candidate_id",
        "place_id",
        "reputation_score",
        "reputation_formula_version",
    }


@pytest.mark.parametrize("field", ["name", "rating", "rating_count", "latitude", "longitude", "website", "types"])
def test_google_fields_cannot_be_smuggled_into_candidate(field):
    with pytest.raises(ValidationError):
        FilteredBatch(candidates=({**candidate(), field: "synthetic"},))


@pytest.mark.parametrize(
    "field,value",
    [
        ("place_id", ""),
        ("place_id", " padded "),
        ("reputation_score", -1),
        ("reputation_score", 11),
        ("reputation_score", "NaN"),
        ("reputation_formula_version", "free-form"),
    ],
)
def test_rejects_invalid_fields(field, value):
    with pytest.raises(ValidationError):
        FilteredBatch(candidates=({**candidate(), field: value},))


def test_duplicate_place_and_candidate_ids_and_more_than_twenty_are_rejected():
    first, second = candidate(), candidate()
    with pytest.raises(ValidationError):
        FilteredBatch(candidates=(first, second))
    with pytest.raises(ValidationError):
        FilteredBatch(candidates=(first, {**second, "candidate_id": first["candidate_id"], "place_id": "other"}))
    with pytest.raises(ValidationError):
        FilteredBatch(candidates=tuple({**candidate(), "place_id": str(i)} for i in range(21)))
