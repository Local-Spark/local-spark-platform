"""Sanitized future results cannot carry provider fields outside the allowlist."""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.reference_real_results import ApifyInstagramOption, ReferenceRealCandidate, ReferenceRealResultInput


def candidate(**changes):
    return {
        "place_id": "synthetic-place-1",
        "reputation_score": Decimal("9.123456789"),
        "reputation_formula_version": "penalized-3.4-v1",
        **changes,
    }


def batch(candidates):
    return {"search_id": uuid4(), "operation_id": uuid4(), "candidates": candidates}


def test_result_preserves_order_precision_and_unverified_instagram_options():
    first = candidate(
        instagram_options=[{"handle": "https://www.instagram.com/Cafe.Exemplo/"}], jev_recommendation_rank=2
    )
    second = candidate(place_id="synthetic-place-2", reputation_score=Decimal("9.123456788"), jev_recommendation_rank=1)
    result = ReferenceRealResultInput.model_validate(batch([first, second]))
    assert [item.place_id for item in result.candidates] == ["synthetic-place-1", "synthetic-place-2"]
    assert result.candidates[0].reputation_score == Decimal("9.123456789")
    assert result.candidates[0].instagram_options == (
        ApifyInstagramOption(handle="cafe.exemplo", source="apify", association="unverified"),
    )


def test_empty_result_is_representable_without_deciding_search_retry_policy():
    assert ReferenceRealResultInput.model_validate(batch([])).candidates == ()


@pytest.mark.parametrize("forbidden", ["rating", "rating_count", "name", "latitude", "longitude", "website", "raw"])
def test_google_source_fields_cannot_enter_candidate(forbidden):
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ReferenceRealCandidate.model_validate(candidate(**{forbidden: "synthetic-data"}))


@pytest.mark.parametrize("bad_score", ["NaN", "Infinity", "-0.1", "10.01"])
def test_score_must_be_finite_and_between_zero_and_ten(bad_score):
    with pytest.raises(ValidationError):
        ReferenceRealCandidate.model_validate(candidate(reputation_score=bad_score))


@pytest.mark.parametrize("bad_id", ["", "  ", " synthetic-id", "synthetic-id ", "x" * 2049])
def test_place_id_must_be_nonempty_bounded_and_preserved(bad_id):
    with pytest.raises(ValidationError):
        ReferenceRealCandidate.model_validate(candidate(place_id=bad_id))


@pytest.mark.parametrize("bad_version", ["", "a" * 65, "formula with spaces"])
def test_formula_version_is_a_bounded_stable_identifier(bad_version):
    with pytest.raises(ValidationError):
        ReferenceRealCandidate.model_validate(candidate(reputation_formula_version=bad_version))


def test_profiles_are_instagram_only_unverified_and_distinct_after_normalization():
    with pytest.raises(ValidationError):
        ApifyInstagramOption(handle="valid", source="google")
    with pytest.raises(ValidationError):
        ApifyInstagramOption(handle="valid", association="confirmed")
    with pytest.raises(ValidationError):
        ApifyInstagramOption(handle="https://www.instagram.com/p/POST/")
    with pytest.raises(ValidationError, match="Instagram profile options must be distinct"):
        ReferenceRealCandidate.model_validate(candidate(instagram_options=[{"handle": "@Cafe"}, {"handle": "cafe"}]))


def test_batch_rejects_duplicates_more_than_ten_and_duplicate_recommendation_ranks():
    with pytest.raises(ValidationError, match="Candidates must have distinct Place IDs"):
        ReferenceRealResultInput.model_validate(batch([candidate(), candidate()]))
    with pytest.raises(ValidationError):
        ReferenceRealResultInput.model_validate(batch([candidate(place_id=f"fixture-{n}") for n in range(11)]))
    with pytest.raises(ValidationError, match="Jev recommendation ranks must be distinct"):
        ReferenceRealResultInput.model_validate(
            batch([candidate(jev_recommendation_rank=1), candidate(place_id="other", jev_recommendation_rank=1)])
        )
    with pytest.raises(ValidationError, match="Jev recommendation ranks must form a sequence"):
        ReferenceRealResultInput.model_validate(batch([candidate(jev_recommendation_rank=2)]))


@pytest.mark.parametrize("rank", [0, 4, True, "1"])
def test_recommendation_ranks_are_numbers_one_through_three(rank):
    with pytest.raises(ValidationError):
        ReferenceRealCandidate.model_validate(candidate(jev_recommendation_rank=rank))
