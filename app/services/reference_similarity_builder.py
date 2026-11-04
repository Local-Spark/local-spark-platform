"""Build the Jev input and source commitment from one immutable batch.

This preparation does not authorize provider calls or verify their provenance.
The activity must link both outputs to the fenced, durable Jev intent; raw
observations and this request must never be emitted to Temporal or logs.
"""

from dataclasses import dataclass
from uuid import UUID

from pydantic import SecretStr

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.services.reference_google_batch_mac import google_batch_mac
from app.services.reference_observation_sanitizer import CandidateObservation


@dataclass(frozen=True, repr=False)
class BoundSimilarityInput:
    source_batch_mac: str
    request: SimilarityInput


def build_bound_similarity_input(
    key: SecretStr,
    *,
    key_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    search: UUID,
    google_effect: UUID,
    pilot: UUID,
    context_version: int,
    observations: tuple[CandidateObservation, ...],
    business_terms: tuple[str, ...],
    business_description: str | None,
) -> BoundSimilarityInput:
    """Create both structures without ever accepting a separate mapping.

    Names and types are copied from the same transient source. The Jev adapter
    remains responsible for validating the input.
    """
    mac = google_batch_mac(
        key,
        key_version=key_version,
        tenant=tenant,
        business=business,
        actor=actor,
        search=search,
        google_effect=google_effect,
        pilot=pilot,
        context_version=context_version,
        observations=observations,
    )
    request = SimilarityInput(
        business_terms=business_terms,
        business_description=business_description,
        candidates=tuple(
            SimilarityCandidate(item.candidate_id, item.place.name, item.place.types) for item in observations
        ),
    )
    return BoundSimilarityInput(mac, request)
