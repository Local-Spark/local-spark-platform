"""In-memory filtering and provisional score projection; no I/O or persistence.

The caller must prove the two provider effects and their exact inputs before
committing this projection. This helper cannot establish provider provenance.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.adapters.google_places import PlaceCandidate
from app.adapters.jev_reference_similarity import SimilarityJudgment
from app.services.reference_reputation import EXPERIMENTAL_PENALIZED_VERSION, experimental_penalized_reputation_score


class ObservationSanitizationError(ValueError):
    """Stable failure without provider data in the error message."""


@dataclass(frozen=True, repr=False)
class CandidateObservation:
    candidate_id: UUID
    place: PlaceCandidate


@dataclass(frozen=True, repr=False)
class SanitizedObservation:
    candidate_id: UUID
    place_id: str
    reputation_score: Decimal
    reputation_formula_version: str = EXPERIMENTAL_PENALIZED_VERSION


def sanitize_similar_observations(
    observations: tuple[CandidateObservation, ...], judgments: tuple[SimilarityJudgment, ...]
) -> tuple[SanitizedObservation, ...]:
    """Keep only definite Jev matches before calculating the experimental score.

    One judgment must correspond to every observation. Missing ratings or zero
    reviews cannot be scored and are omitted. Provider input and judgments are
    not retained; the ephemeral candidate UUID links subsequent effects.
    """
    if not isinstance(observations, tuple) or len(observations) > 20:
        raise ObservationSanitizationError("REFERENCE_OBSERVATIONS_INVALID")
    if not isinstance(judgments, tuple):
        raise ObservationSanitizationError("REFERENCE_JUDGMENTS_INVALID")
    ids: set[UUID] = set()
    places: set[str] = set()
    for item in observations:
        if (
            not isinstance(item, CandidateObservation)
            or not isinstance(item.candidate_id, UUID)
            or not isinstance(item.place, PlaceCandidate)
            or not isinstance(item.place.place_id, str)
            or not item.place.place_id.strip()
            or item.place.place_id != item.place.place_id.strip()
            or len(item.place.place_id) > 2048
            or item.candidate_id in ids
            or item.place.place_id in places
        ):
            raise ObservationSanitizationError("REFERENCE_OBSERVATIONS_INVALID")
        ids.add(item.candidate_id)
        places.add(item.place.place_id)
    decisions: dict[UUID, str] = {}
    for judgment in judgments:
        if (
            not isinstance(judgment, SimilarityJudgment)
            or not isinstance(judgment.candidate_id, UUID)
            or judgment.candidate_id not in ids
            or judgment.candidate_id in decisions
            or judgment.choice not in ("match", "no_match", "uncertain")
        ):
            raise ObservationSanitizationError("REFERENCE_JUDGMENTS_INVALID")
        decisions[judgment.candidate_id] = judgment.choice
    if set(decisions) != ids:
        raise ObservationSanitizationError("REFERENCE_JUDGMENTS_INVALID")
    result: list[SanitizedObservation] = []
    for item in observations:
        if decisions[item.candidate_id] != "match":
            continue
        try:
            score = experimental_penalized_reputation_score(item.place.rating, item.place.rating_count)
        except (ValueError, ArithmeticError):
            raise ObservationSanitizationError("REFERENCE_OBSERVATIONS_INVALID") from None
        if score is not None:
            result.append(SanitizedObservation(item.candidate_id, item.place.place_id, score))
    return tuple(result)
