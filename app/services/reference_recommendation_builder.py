"""Build a Jev recommendation input from a proven shortlist in memory only.

The caller must hold the original observation batch and validate its provider
fences. This helper checks the ID/Place ID mapping but cannot prove provenance
or reconstruct names and types after the original response has been discarded.
"""

from uuid import UUID

from app.adapters.google_places import PlaceCandidate
from app.adapters.jev_reference_recommendations import RecommendationCandidate, RecommendationInput
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_observation_sanitizer import CandidateObservation


class RecommendationBuildError(ValueError):
    """Stable error without raw provider or customer inputs."""


def build_recommendation_input(
    observations: tuple[CandidateObservation, ...],
    shortlist: FilteredBatch,
    *,
    business_terms: tuple[str, ...],
    business_description: str | None,
) -> RecommendationInput:
    """Preserve shortlist order and copy only the names/types for those IDs."""
    if (
        not isinstance(observations, tuple)
        or len(observations) > 20
        or not isinstance(shortlist, FilteredBatch)
        or not 1 <= len(shortlist.candidates) <= 10
    ):
        raise RecommendationBuildError("RECOMMENDATION_MAPPING_INVALID")
    lookup = {}
    places: set[str] = set()
    for observation in observations:
        if (
            not isinstance(observation, CandidateObservation)
            or not isinstance(observation.candidate_id, UUID)
            or not isinstance(observation.place, PlaceCandidate)
            or not isinstance(observation.place.place_id, str)
            or observation.candidate_id in lookup
            or observation.place.place_id in places
        ):
            raise RecommendationBuildError("RECOMMENDATION_MAPPING_INVALID")
        lookup[observation.candidate_id] = observation
        places.add(observation.place.place_id)
    candidates = []
    for candidate in shortlist.candidates:
        matched = lookup.get(candidate.candidate_id)
        if matched is None or matched.place.place_id != candidate.place_id:
            raise RecommendationBuildError("RECOMMENDATION_MAPPING_INVALID")
        candidates.append(
            RecommendationCandidate(
                candidate.candidate_id, matched.place.name, matched.place.types, candidate.reputation_score
            )
        )
    return RecommendationInput(business_terms, business_description, tuple(candidates))
