"""Exclude unknown similarity before calculating any reputation score.

This is a pure projection; its caller must prove provider provenance and ensure
these judgments were produced by the same fenced request as the observations.
"""

from dataclasses import replace

from app.adapters.jev_reference_similarity_levels import LeveledSimilarityJudgment
from app.services.reference_observation_sanitizer import (
    CandidateObservation,
    ObservationSanitizationError,
    SanitizedObservation,
    sanitize_similar_observations,
)


def sanitize_leveled_observations(
    observations: tuple[CandidateObservation, ...], judgments: tuple[LeveledSimilarityJudgment, ...]
) -> tuple[SanitizedObservation, ...]:
    """Retain only definite matches with an explicit, known similarity level."""
    if not isinstance(judgments, tuple) or any(
        not isinstance(judgment, LeveledSimilarityJudgment)
        or judgment.similarity_level not in ("high", "medium", "low", "unknown")
        for judgment in judgments
    ):
        raise ObservationSanitizationError("REFERENCE_LEVELS_INVALID")
    eligible = tuple(
        replace(judgment, choice="uncertain") if judgment.similarity_level == "unknown" else judgment
        for judgment in judgments
    )
    return sanitize_similar_observations(observations, eligible)
