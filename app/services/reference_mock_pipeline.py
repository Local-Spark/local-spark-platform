"""Fenced reference pipeline for fixture transports only, not a Temporal activity.

The caller provides private inputs directly in memory. No route or workflow may
serialize this input; production admission, loading and pricing remain pending.
"""

from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID, uuid5

import httpx
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.google_places import GooglePlacesNearby
from app.adapters.jev_reference_similarity_levels import JevReferenceSimilarityLevels
from app.db.session import Database
from app.schemas.reference_filtered_batch import FilteredBatch, FilteredBatchCandidate
from app.services.reference_filtered_commit import FilteredCommitContext
from app.services.reference_jev_budget_guard import JevGuardContext
from app.services.reference_jev_intent import jev_effect_id
from app.services.reference_jev_intent_guard import IntentJevBudgetGuard
from app.services.reference_leveled_commit import commit_leveled_batch
from app.services.reference_leveled_observation_sanitizer import sanitize_leveled_observations
from app.services.reference_observation_sanitizer import CandidateObservation
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard, PlacesGuardContext
from app.services.reference_similarity_builder import build_bound_similarity_input


class ReferenceMockPipelineError(Exception):
    """A stable failure with no provider content or credentials."""


@dataclass(frozen=True, repr=False)
class MockPipelineInput:
    google: PlacesGuardContext
    context_version: int
    place_type: str
    latitude: float
    longitude: float
    radius_km: int
    business_terms: tuple[str, ...]
    business_description: str | None
    google_key: SecretStr
    jev_key: SecretStr
    jev_model: str
    jev_tariff_version: str
    jev_credential_version: str
    jev_reserved_usd_micros: int


@dataclass(frozen=True)
class MockPipelineResult:
    search_id: UUID
    batch_id: UUID | None
    state: Literal["empty", "filtered"]


async def _recover(database: Database, context: PlacesGuardContext) -> MockPipelineResult | None:
    async with database.transaction(context.tenant, context.actor) as session:
        value = await session.scalar(
            text("""SELECT public.reference_filtered_recovery(
          :business,:search,:google,:event)"""),
            {
                "business": context.business,
                "search": context.search,
                "google": context.effect,
                "event": context.event,
            },
        )
    if value is None:
        return None
    if value["state"] == "empty" and value["batch_id"] is None:
        return MockPipelineResult(context.search, None, "empty")
    if value["state"] == "filtered":
        async with database.transaction(context.tenant, context.actor) as session:
            snapshot = await session.scalar(
                text("""SELECT public.reference_similarity_snapshot_recovery(
              :business,:search,:google,:event)"""),
                {
                    "business": context.business,
                    "search": context.search,
                    "google": context.effect,
                    "event": context.event,
                },
            )
        if snapshot is None or snapshot["batch_id"] != value["batch_id"]:
            raise ReferenceMockPipelineError("REFERENCE_RECOVERY_INVALID")
        return MockPipelineResult(context.search, UUID(value["batch_id"]), "filtered")
    raise ReferenceMockPipelineError("REFERENCE_RECOVERY_INVALID")


async def run_mock_reference_pipeline(
    database: Database,
    inputs: MockPipelineInput,
    *,
    google_transport: httpx.MockTransport,
    jev_transport: httpx.MockTransport,
) -> MockPipelineResult:
    """Execute a single fenced chain. Replays never repeat either provider call."""
    if not isinstance(google_transport, httpx.MockTransport) or not isinstance(jev_transport, httpx.MockTransport):
        raise ReferenceMockPipelineError("REFERENCE_MOCK_TRANSPORT_REQUIRED")
    google = inputs.google
    if inputs.context_version != google.context_version:
        raise ReferenceMockPipelineError("REFERENCE_CONTEXT_INVALID")
    google_guard = DatabasePlacesBudgetGuard(database, google)
    jev_guard: IntentJevBudgetGuard | None = None
    try:
        places = await GooglePlacesNearby(
            inputs.google_key, google_guard, enabled=True, transport=google_transport
        ).search(inputs.place_type, inputs.latitude, inputs.longitude, inputs.radius_km, google.effect, max_results=20)
        if not places:
            return MockPipelineResult(google.search, None, "empty")
        observations = tuple(
            CandidateObservation(uuid5(google.effect, f"candidate:{index}"), place)
            for index, place in enumerate(places)
        )
        bound = build_bound_similarity_input(
            google.key,
            key_version=google.key_version,
            tenant=google.tenant,
            business=google.business,
            actor=google.actor,
            search=google.search,
            google_effect=google.effect,
            pilot=google.pilot,
            context_version=inputs.context_version,
            observations=observations,
            business_terms=inputs.business_terms,
            business_description=inputs.business_description,
        )
        jev_effect = jev_effect_id(google.effect)
        jev_context = JevGuardContext(
            tenant=google.tenant,
            business=google.business,
            actor=google.actor,
            search=google.search,
            effect=jev_effect,
            pilot=google.pilot,
            event=uuid5(jev_effect, "request-event"),
            key=google.key,
            key_version=google.key_version,
            tariff_version=inputs.jev_tariff_version,
            credential_version=inputs.jev_credential_version,
            reserved_usd_micros=inputs.jev_reserved_usd_micros,
            parent_google_effect=google.effect,
            parent_executor_token=google_guard.execution_token(),
            source_batch_mac=bound.source_batch_mac,
            context_version=inputs.context_version,
        )
        jev_guard = IntentJevBudgetGuard(database, jev_context, google.event)
        judgment = await JevReferenceSimilarityLevels(
            inputs.jev_key, inputs.jev_model, jev_guard, enabled=True, transport=jev_transport
        ).classify(bound.request, jev_effect)
        candidates = sanitize_leveled_observations(observations, judgment.judgments)
        batch = FilteredBatch(
            candidates=tuple(
                FilteredBatchCandidate(
                    candidate_id=item.candidate_id,
                    place_id=item.place_id,
                    reputation_score=item.reputation_score,
                    reputation_formula_version=cast(Literal["penalized-3.4-v1"], item.reputation_formula_version),
                )
                for item in candidates
            )
        )
        batch_id = uuid5(google.search, "filtered-batch-v1")
        await commit_leveled_batch(
            database,
            FilteredCommitContext(
                tenant=google.tenant,
                business=google.business,
                actor=google.actor,
                search=google.search,
                batch=batch_id,
                google_effect=google.effect,
                google_event=google.event,
                google_token=google_guard.execution_token(),
                jev_effect=jev_effect,
                jev_event=jev_guard.event_id(),
                jev_token=jev_guard.execution_token(),
                source_batch_mac=bound.source_batch_mac,
                context_version=inputs.context_version,
            ),
            batch,
            observations=observations,
            judgments=judgment.judgments,
            source_key=google.key,
            source_key_version=google.key_version,
            pilot=google.pilot,
        )
        return MockPipelineResult(google.search, batch_id, "filtered")
    except Exception:
        if jev_guard is not None:
            try:
                await jev_guard.uncertain()
            except Exception:
                pass
        try:
            await google_guard.uncertain()
        except Exception:
            pass
        if google_guard.intent_validated():
            try:
                previous = await _recover(database, google)
                if previous is not None:
                    return previous
            except Exception:
                pass
        raise ReferenceMockPipelineError("REFERENCE_MOCK_PIPELINE_INCOMPLETE") from None
