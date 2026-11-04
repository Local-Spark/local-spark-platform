"""Builder binds the same ordered observations to the Jev input and batch MAC."""

from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.google_places import PlaceCandidate
from app.adapters.jev_reference_similarity import SimilarityJudgment
from app.services.reference_observation_sanitizer import (
    CandidateObservation,
    ObservationSanitizationError,
    sanitize_similar_observations,
)
from app.services.reference_similarity_builder import build_bound_similarity_input


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
            CandidateObservation(uuid4(), PlaceCandidate("place-a", "name-a", 1.0, 2.0, 4.2, 100, None)),
            CandidateObservation(uuid4(), PlaceCandidate("place-b", "name-b", None, None, None, None, None)),
        ),
        "business_terms": ("coffee",),
        "business_description": "private description",
    }


def test_builder_never_separates_ids_names_and_committed_input():
    args = arguments()
    first, second = args["observations"]
    bound = build_bound_similarity_input(**args)
    assert [(candidate.candidate_id, candidate.name) for candidate in bound.request.candidates] == [
        (first.candidate_id, "name-a"),
        (second.candidate_id, "name-b"),
    ]
    assert bound.request.business_terms == ("coffee",) and bound.request.business_description == "private description"
    assert "name-a" not in repr(bound) and "private description" not in repr(bound)
    assert bound == build_bound_similarity_input(**args)
    reordered = build_bound_similarity_input(**{**args, "observations": (second, first)})
    assert reordered.source_batch_mac != bound.source_batch_mac
    assert reordered.request.candidates[0].candidate_id == second.candidate_id
    changed_name = replace(first, place=replace(first.place, name="other-name"))
    changed = build_bound_similarity_input(**{**args, "observations": (changed_name, second)})
    assert changed.source_batch_mac != bound.source_batch_mac and changed.request.candidates[0].name == "other-name"
    changed_rating = replace(first, place=replace(first.place, rating=3.0))
    changed = build_bound_similarity_input(**{**args, "observations": (changed_rating, second)})
    assert changed.source_batch_mac != bound.source_batch_mac
    assert changed.request == bound.request
    changed_type = replace(first, place=replace(first.place, types=("cafe",)))
    changed = build_bound_similarity_input(**{**args, "observations": (changed_type, second)})
    assert changed.source_batch_mac != bound.source_batch_mac and changed.request.candidates[0].types == ("cafe",)


def test_judgment_from_other_candidate_cannot_be_mixed_with_committed_batch():
    args = arguments()
    first, second = args["observations"]
    decisions = (
        SimilarityJudgment(first.candidate_id, "match", None, None),
        SimilarityJudgment(uuid4(), "match", None, None),
    )
    with pytest.raises(ObservationSanitizationError, match="REFERENCE_JUDGMENTS_INVALID"):
        sanitize_similar_observations((first, second), decisions)
