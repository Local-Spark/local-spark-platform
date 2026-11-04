from dataclasses import replace
from uuid import uuid4

import pytest

from app.adapters.google_places import PlaceCandidate
from app.adapters.jev_reference_similarity import SimilarityJudgment
from app.adapters.jev_reference_similarity_levels import LeveledSimilarityJudgment
from app.services.reference_leveled_observation_sanitizer import sanitize_leveled_observations
from app.services.reference_observation_sanitizer import CandidateObservation, ObservationSanitizationError


def observation(rating=4.5):
    return CandidateObservation(
        uuid4(), PlaceCandidate("synthetic-place", "fake", None, None, rating, 20, None, ("cafe",))
    )


def judgment(item, choice="match", level="high"):
    return LeveledSimilarityJudgment(item.candidate_id, choice, 0.99, (0.99, 0.005, 0.005), level)


@pytest.mark.parametrize("level", ["high", "medium", "low"])
def test_definite_match_with_known_level_is_scored(level):
    item = observation()
    result = sanitize_leveled_observations((item,), (judgment(item, level=level),))
    assert len(result) == 1 and result[0].candidate_id == item.candidate_id and result[0].reputation_score > 0


def test_unknown_is_excluded_before_rating_even_with_high_confidence():
    item = observation(rating="not-a-number")
    assert sanitize_leveled_observations((item,), (judgment(item, level="unknown"),)) == ()


@pytest.mark.parametrize("choice", ["no_match", "uncertain"])
def test_nonmatches_excluded_before_rating(choice):
    item = observation(rating="not-a-number")
    assert sanitize_leveled_observations((item,), (judgment(item, choice=choice),)) == ()


@pytest.mark.parametrize(
    "values",
    [
        None,
        [],
        (object(),),
        (SimilarityJudgment(uuid4(), "match", None, None),),
        (LeveledSimilarityJudgment(uuid4(), "match", None, None, "invented"),),
    ],
)
def test_requires_explicit_valid_levels(values):
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_LEVELS_INVALID"):
        sanitize_leveled_observations((), values)


def test_original_identity_and_completeness_checks_still_apply():
    item = observation()
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_JUDGMENTS_INVALID"):
        sanitize_leveled_observations((item,), (replace(judgment(item), candidate_id=uuid4()),))
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_JUDGMENTS_INVALID"):
        sanitize_leveled_observations((item,), ())
