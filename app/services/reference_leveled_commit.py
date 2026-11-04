"""Prepare an exact, private similarity snapshot for the fixture-only chain.

Matching source MACs and fences bind a trusted in-memory activity; this helper
cannot authenticate the provider response or authorize any real provider call.
"""

import hmac
import json
import re
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.jev_reference_similarity_levels import LeveledSimilarityJudgment
from app.db.session import Database
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_filtered_commit import FilteredCommitContext, FilteredCommitError
from app.services.reference_google_batch_mac import GoogleBatchBindingError, google_batch_mac
from app.services.reference_leveled_observation_sanitizer import sanitize_leveled_observations
from app.services.reference_observation_sanitizer import CandidateObservation, ObservationSanitizationError
from app.services.reference_own_business_match import OwnBusinessMatch


async def commit_leveled_batch(
    database: Database,
    context: FilteredCommitContext,
    batch: FilteredBatch,
    *,
    observations: tuple[CandidateObservation, ...],
    judgments: tuple[LeveledSimilarityJudgment, ...],
    source_key: SecretStr,
    source_key_version: str,
    pilot: UUID,
    own_match: OwnBusinessMatch | None = None,
) -> UUID:
    if (
        not isinstance(context, FilteredCommitContext)
        or not isinstance(batch, FilteredBatch)
        or any(
            not isinstance(value, UUID)
            for value in (
                context.tenant,
                context.business,
                context.actor,
                context.search,
                context.batch,
                context.google_effect,
                context.google_event,
                context.google_token,
                context.jev_effect,
                context.jev_event,
                context.jev_token,
                pilot,
            )
        )
        or context.google_effect == context.jev_effect
        or not isinstance(context.source_batch_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", context.source_batch_mac) is None
        or type(context.context_version) is not int
        or not 0 < context.context_version <= 9_223_372_036_854_775_807
        or not isinstance(observations, tuple)
        or not isinstance(judgments, tuple)
        or len(observations) != len(judgments)
        or any(not isinstance(item, CandidateObservation) for item in observations)
        or any(not isinstance(item, LeveledSimilarityJudgment) for item in judgments)
        or any(
            observation.candidate_id != judgment.candidate_id
            for observation, judgment in zip(observations, judgments, strict=True)
        )
    ):
        raise FilteredCommitError("REFERENCE_LEVELED_INPUT_INVALID")
    try:
        source_mac = google_batch_mac(
            source_key,
            key_version=source_key_version,
            tenant=context.tenant,
            business=context.business,
            actor=context.actor,
            search=context.search,
            google_effect=context.google_effect,
            pilot=pilot,
            context_version=context.context_version,
            observations=observations,
        )
        filtered = sanitize_leveled_observations(observations, judgments)
    except (GoogleBatchBindingError, ObservationSanitizationError):
        raise FilteredCommitError("REFERENCE_LEVELED_INPUT_INVALID") from None
    if not hmac.compare_digest(source_mac, context.source_batch_mac):
        raise FilteredCommitError("REFERENCE_LEVELED_INPUT_INVALID")
    if [item.model_dump(mode="json") for item in batch.candidates] != [
        {
            "candidate_id": str(item.candidate_id),
            "place_id": item.place_id,
            "reputation_score": str(item.reputation_score),
            "reputation_formula_version": item.reputation_formula_version,
        }
        for item in filtered
    ]:
        raise FilteredCommitError("REFERENCE_LEVELED_INPUT_INVALID")
    projection = [
        {"candidate_id": str(j.candidate_id), "judgment": j.choice, "similarity_level": j.similarity_level}
        for j in judgments
    ]
    statement = """SELECT public.reference_filtered_commit_with_similarity(
        :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
        :source,:context,CAST(:candidates AS jsonb),CAST(:judgments AS jsonb))"""
    if own_match is not None:
        statement = """SELECT public.reference_filtered_commit_with_identity(
            :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
            :source,:context,CAST(:candidates AS jsonb),CAST(:judgments AS jsonb),CAST(:own_match AS jsonb))"""
    async with database.transaction(context.tenant, context.actor) as session:
        result = await session.scalar(
            text(statement),
            {
                "business": context.business,
                "search": context.search,
                "batch": context.batch,
                "google": context.google_effect,
                "google_event": context.google_event,
                "google_token": context.google_token,
                "jev": context.jev_effect,
                "jev_event": context.jev_event,
                "jev_token": context.jev_token,
                "source": context.source_batch_mac,
                "context": context.context_version,
                "candidates": json.dumps(batch.model_dump(mode="json")["candidates"], separators=(",", ":")),
                "judgments": json.dumps(projection, separators=(",", ":")),
                "own_match": json.dumps({"status": own_match.status, "place_ids": list(own_match.place_ids)})
                if own_match is not None
                else None,
            },
        )
    if result != context.batch:
        raise FilteredCommitError("REFERENCE_LEVELED_RESULT_INVALID")
    return context.batch
