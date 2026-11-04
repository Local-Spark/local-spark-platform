"""One durable discovery pipeline; provider responses remain inside this activity.

The database owns identities, eligibility, reservations and publication. This
service composes the existing adapters and scoring functions and saves only
allowed classifications, scores, IDs and independent Instagram associations.
"""

from dataclasses import asdict
from typing import Any, Literal, cast
from uuid import UUID, uuid5

import httpx
from sqlalchemy import text

from app.adapters.apify_place_contacts import ApifyPlaceContacts
from app.adapters.google_places import GooglePlacesNearby
from app.adapters.jev_primary_place_types import JevPrimaryPlaceTypeMapper
from app.adapters.jev_reference_recommendations import (
    JevReferenceRecommendations,
    RecommendationCandidate,
    RecommendationInput,
)
from app.adapters.jev_reference_similarity_levels import JevReferenceSimilarityLevels
from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ReferenceAddress
from app.schemas.owner_references import instagram_handle
from app.schemas.reference_filtered_batch import FilteredBatch, FilteredBatchCandidate
from app.services.reference_business_identity import load_business_identity
from app.services.reference_contacts_budget_guard import ContactsGuardContext
from app.services.reference_contacts_runs import load_contacts_run, record_contacts_cost, record_contacts_run
from app.services.reference_context_loader import LoadedSearchContext, load_search_context
from app.services.reference_execution_store import (
    ExecutionCandidate,
    ExecutionState,
    load_execution,
    ranked_candidates,
    record_output,
)
from app.services.reference_filtered_commit import FilteredCommitContext
from app.services.reference_google_intent import google_effect_id
from app.services.reference_jev_budget_guard import JevGuardContext
from app.services.reference_jev_intent import jev_effect_id
from app.services.reference_jev_intent_guard import IntentJevBudgetGuard
from app.services.reference_leveled_commit import commit_leveled_batch
from app.services.reference_leveled_observation_sanitizer import sanitize_leveled_observations
from app.services.reference_observation_sanitizer import CandidateObservation
from app.services.reference_own_business_match import identify_own_business
from app.services.reference_places_budget_guard import PlacesGuardContext
from app.services.reference_publication import (
    CompletedContacts,
    CompletedEffect,
    CompletedRecommendation,
    PublicationProjection,
    publish_reference_shortlist,
)
from app.services.reference_similarity_builder import build_bound_similarity_input
from app.services.reference_stage_guards import IntentContactsGuard, IntentPlacesGuard, JevStageGuard, StageContext
from app.workflows.contracts import BusinessEvent


class ReferenceExecutionError(Exception):
    """Stable failure without source content, location, tokens or credentials."""


class ReferenceProviderExecution:
    def __init__(
        self,
        database: Database,
        settings: Settings,
        *,
        google_transport: httpx.MockTransport | None = None,
        jev_transport: httpx.MockTransport | None = None,
        apify_transport: httpx.MockTransport | None = None,
    ) -> None:
        self.database, self.settings = database, settings
        self.google_transport, self.jev_transport, self.apify_transport = (
            google_transport,
            jev_transport,
            apify_transport,
        )

    def _stage(
        self,
        event: BusinessEvent,
        search: UUID,
        state: ExecutionState,
        kind: str,
        shortlist: FilteredBatch | None = None,
    ) -> StageContext:
        s = self.settings
        assert s.reference_provider_hmac_key is not None and s.reference_provider_pilot_id is not None
        effect = uuid5(search, "reference-jev-" + kind + "-v1")
        similarity = state.effect("jev", "discovery")
        return StageContext(
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            search,
            effect,
            uuid5(effect, "request-event"),
            s.reference_provider_pilot_id,
            state.context_version,
            s.reference_provider_hmac_key,
            s.reference_provider_key_version,
            s.reference_jev_tariff_version,
            s.reference_jev_credential_version,
            s.reference_jev_reserved_usd_micros,
            state.source_batch_mac or state.request_mac,
            state.batch_id,
            similarity.id if similarity else None,
            shortlist,
        )

    async def _state(self, event: BusinessEvent, search: UUID) -> ExecutionState:
        return await load_execution(
            self.database,
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            search,
            UUID(event.event_id),
        )

    async def run(self, event: BusinessEvent) -> str:
        if not self.settings.reference_discovery_ready():
            return "disabled"
        search = uuid5(UUID(event.operation_id), f"reference-provider-search-v1:{event.tenant_id}:{event.business_id}")
        try:
            status = await self._run(event, search)
            await self._progress(event, search, status)
            return status
        except Exception:
            try:
                await self._progress(event, search, "provider_uncertain")
            except Exception:
                pass
            # Provider adapters preserve a potentially charged request. Activity retry
            # reuses durable output/run identities; it never blindly dispatches again.
            raise ReferenceExecutionError("REFERENCE_EXECUTION_INCOMPLETE") from None

    async def _progress(self, event: BusinessEvent, search: UUID, status: str) -> None:
        async with self.database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
            await session.scalar(
                text("SELECT public.reference_execution_progress(:business,:search,:event,:status)"),
                {
                    "business": UUID(event.business_id),
                    "search": search,
                    "event": UUID(event.event_id),
                    "status": status,
                },
            )

    async def _run(self, event: BusinessEvent, search: UUID) -> str:
        state = await self._state(event, search)
        if state.state == "completed":
            return "completed"
        if state.state != "pending":
            return "type_mapping_unavailable" if state.execution_status == "type_mapping_unavailable" else "unavailable"
        if state.execution_status in ("pending", "contacts_failed"):
            await self._progress(event, search, "running")
        s = self.settings
        assert s.reference_provider_hmac_key is not None
        keys = {s.reference_provider_key_version: s.reference_provider_hmac_key}
        context = await load_search_context(
            self.database,
            keys,
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            search,
            UUID(event.event_id),
        )
        if state.batch_id is None:
            types = await self._map(event, search, state, context)
            if not types:
                async with self.database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
                    await session.scalar(
                        text("SELECT reference_release_unmapped_search(:business,:search,:event,:operation)"),
                        {
                            "business": UUID(event.business_id),
                            "search": search,
                            "event": UUID(event.event_id),
                            "operation": uuid5(search, "mapping-unavailable-v1"),
                        },
                    )
                return "type_mapping_unavailable"
            google = state.effect("google", "discovery")
            if google is not None:
                if google.state == "completed_empty":
                    return await self._empty(event, search, google)
                # A committed send without its in-memory response is uncertain. It
                # must be reconciled; issuing another paid search would duplicate it.
                if google.state != "pending":
                    return "provider_uncertain"
            await self._discover(event, search, state, context, types)
            state = await self._state(event, search)
            google = state.effect("google", "discovery")
            if state.batch_id is None and google is not None and google.state == "completed_empty":
                return await self._empty(event, search, google)
        # The review was committed atomically with the batch; recovery never needs
        # names/addresses from Google to decide which Place ID was the owner's shop.
        from app.services.reference_own_review import ReferenceOwnReviewService

        review = await ReferenceOwnReviewService(self.database).read(
            UUID(event.tenant_id), UUID(event.business_id), UUID(event.actor_id), search
        )
        if review.status == "awaiting_confirmation":
            return "awaiting_own_review"
        candidates = ranked_candidates(state.candidates, review.excluded_place_id)
        commit = state.commit_context(UUID(event.tenant_id), UUID(event.business_id), UUID(event.actor_id), search)
        async with self.database.transaction(commit.tenant, commit.actor) as session:
            await session.scalar(
                text("SELECT public.reference_prepare_shortlist(:business,:search,:batch,:operation,:candidates)"),
                {
                    "business": commit.business,
                    "search": search,
                    "batch": commit.batch,
                    "operation": uuid5(search, "shortlist-v1"),
                    "candidates": [c.candidate_id for c in candidates],
                },
            )
        recommendation = await self._recommend(event, search, state, context, candidates)
        contacts = []
        for candidate in candidates:
            contact = await self._contacts(event, search, state, candidate)
            if contact == "pending":
                return "contacts_pending"
            if contact == "failed":
                return "contacts_failed"
            if contact == "uncertain":
                return "provider_uncertain"
            if contact is not None:
                contacts.append(contact)
        await publish_reference_shortlist(
            self.database,
            commit,
            PublicationProjection(
                operation_id=uuid5(search, "publication-v1"), recommendation=recommendation, contacts=tuple(contacts)
            ),
        )
        return "completed"

    async def _map(
        self, event: BusinessEvent, search: UUID, state: ExecutionState, context: LoadedSearchContext
    ) -> tuple[str, ...]:
        previous = state.effect("jev", "mapping")
        if previous is not None and previous.output is not None:
            return tuple(previous.output["types"]) if previous.output["state"] == "mapped" else ()
        if previous is not None and previous.state != "pending":
            raise ReferenceExecutionError("REFERENCE_MAPPING_UNCERTAIN")
        c = self._stage(event, search, state, "mapping")
        guard = JevStageGuard(self.database, c, "mapping")
        result = await JevPrimaryPlaceTypeMapper(
            self.settings.typesafe_api_key,
            self.settings.intent_ai_model,
            guard,
            enabled=True,
            network_enabled=True,
            transport=self.jev_transport,
        ).map(context.business_terms, context.business_description, c.effect)
        await record_output(
            self.database,
            c.tenant,
            c.business,
            c.actor,
            c.effect,
            guard.execution_token(),
            "mapping",
            {"state": result.state, "types": list(result.types), "taxonomy_version": result.taxonomy_version},
        )
        return result.types if result.state == "mapped" else ()

    async def _discover(
        self,
        event: BusinessEvent,
        search: UUID,
        state: ExecutionState,
        context: LoadedSearchContext,
        types: tuple[str, ...],
    ) -> None:
        s = self.settings
        assert s.reference_provider_hmac_key is not None and s.reference_provider_pilot_id is not None
        ge = google_effect_id(search)
        g = PlacesGuardContext(
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            search,
            ge,
            s.reference_provider_pilot_id,
            uuid5(ge, "request-event"),
            context.context_version,
            s.reference_provider_hmac_key,
            s.reference_provider_key_version,
            s.reference_google_tariff_version,
            s.reference_google_credential_version,
            s.reference_google_reserved_usd_micros,
        )
        guard = IntentPlacesGuard(self.database, g)
        identity = await load_business_identity(
            self.database, {g.key_version: g.key}, g.tenant, g.business, g.actor, search
        )
        places = await GooglePlacesNearby(
            s.reference_google_api_key, guard, enabled=True, transport=self.google_transport
        ).search(None, context.latitude, context.longitude, context.radius_km, ge, primary_types=types, max_results=20)
        if not places:
            return
        match = identify_own_business(
            identity.name, ReferenceAddress.model_validate(identity.address.model_dump()), places
        )
        observations = tuple(
            CandidateObservation(uuid5(ge, f"candidate:{index}"), place) for index, place in enumerate(places)
        )
        bound = build_bound_similarity_input(
            g.key,
            key_version=g.key_version,
            tenant=g.tenant,
            business=g.business,
            actor=g.actor,
            search=search,
            google_effect=ge,
            pilot=g.pilot,
            context_version=context.context_version,
            observations=observations,
            business_terms=context.business_terms,
            business_description=context.business_description,
        )
        je = jev_effect_id(ge)
        jc = JevGuardContext(
            g.tenant,
            g.business,
            g.actor,
            search,
            je,
            g.pilot,
            uuid5(je, "request-event"),
            g.key,
            g.key_version,
            s.reference_jev_tariff_version,
            s.reference_jev_credential_version,
            s.reference_jev_reserved_usd_micros,
            ge,
            guard.execution_token(),
            bound.source_batch_mac,
            context.context_version,
        )
        jguard = IntentJevBudgetGuard(self.database, jc, guard.context.event)
        judgment = await JevReferenceSimilarityLevels(
            s.typesafe_api_key,
            s.intent_ai_model,
            jguard,
            enabled=True,
            network_enabled=True,
            transport=self.jev_transport,
        ).classify(bound.request, je)
        sanitized = sanitize_leveled_observations(observations, judgment.judgments)
        batch = FilteredBatch(candidates=tuple(FilteredBatchCandidate.model_validate(asdict(c)) for c in sanitized))
        commit = FilteredCommitContext(
            g.tenant,
            g.business,
            g.actor,
            search,
            uuid5(search, "filtered-batch-v1"),
            ge,
            guard.context.event,
            guard.execution_token(),
            je,
            jguard.event_id(),
            jguard.execution_token(),
            bound.source_batch_mac,
            context.context_version,
        )
        await commit_leveled_batch(
            self.database,
            commit,
            batch,
            observations=observations,
            judgments=judgment.judgments,
            source_key=g.key,
            source_key_version=g.key_version,
            pilot=g.pilot,
            own_match=match,
        )

    async def _recommend(
        self,
        event: BusinessEvent,
        search: UUID,
        state: ExecutionState,
        context: LoadedSearchContext,
        candidates: tuple[ExecutionCandidate, ...],
    ) -> CompletedRecommendation | None:
        if not candidates:
            return None
        previous = state.effect("jev", "recommendation")
        if previous is not None and previous.state != "pending":
            if previous.output is None:
                return None  # Report unavailable; no invented recommendations or repeated spend.
            if previous.token is None:
                raise ReferenceExecutionError("REFERENCE_RECOMMENDATION_INVALID")
            return CompletedRecommendation(
                effect=CompletedEffect(effect_id=previous.id, event_id=previous.event, executor_token=previous.token),
                candidate_ids=tuple(UUID(v) for v in previous.output["candidate_ids"]),
            )
        shortlist = FilteredBatch(
            candidates=tuple(
                FilteredBatchCandidate.model_validate(
                    c.model_dump(exclude={"similarity_level", "source_position", "contacts_cache"})
                )
                for c in candidates
            )
        )
        c = self._stage(event, search, state, "recommendation", shortlist)
        guard = JevStageGuard(self.database, c, "recommendation")
        value = RecommendationInput(
            context.business_terms,
            context.business_description,
            tuple(
                RecommendationCandidate(
                    item.candidate_id,
                    None,
                    (),
                    item.reputation_score,
                    cast(Literal["high", "medium", "low"], item.similarity_level),
                )
                for item in candidates
            ),
        )
        recommendations = await JevReferenceRecommendations(
            self.settings.typesafe_api_key,
            self.settings.intent_ai_model,
            guard,
            enabled=True,
            network_enabled=True,
            transport=self.jev_transport,
        ).recommend(value, c.effect)
        ids = tuple(r.candidate_id for r in recommendations)
        await record_output(
            self.database,
            c.tenant,
            c.business,
            c.actor,
            c.effect,
            guard.execution_token(),
            "recommendation",
            {"candidate_ids": [str(value) for value in ids]},
        )
        return CompletedRecommendation(
            effect=CompletedEffect(effect_id=c.effect, event_id=c.event, executor_token=guard.execution_token()),
            candidate_ids=ids,
        )

    async def _contacts(
        self, event: BusinessEvent, search: UUID, state: ExecutionState, candidate: ExecutionCandidate
    ) -> CompletedContacts | Literal["pending", "failed", "uncertain"] | None:
        if candidate.contacts_cache == "completed":
            return None
        if candidate.contacts_cache == "pending":
            return "pending"
        s = self.settings
        assert (
            s.reference_provider_hmac_key is not None
            and s.reference_provider_pilot_id is not None
            and state.batch_id is not None
            and state.source_batch_mac is not None
        )
        attempts = [e for e in state.effects if e.candidate_id == candidate.candidate_id]
        previous = max(attempts, key=lambda e: e.attempt_no or 0) if attempts else None
        if previous is not None and previous.state == "failed_definitive":
            effect = uuid5(previous.id, "contacts-retry-v1")
            previous = None
        else:
            effect = previous.id if previous is not None else uuid5(candidate.candidate_id, "contacts-v1")
        if previous is not None and previous.output is not None:
            assert previous.token is not None
            return CompletedContacts(
                candidate_id=candidate.candidate_id,
                effect=CompletedEffect(effect_id=effect, event_id=previous.event, executor_token=previous.token),
                handles=tuple(previous.output["handles"]),
                primary_handle=previous.output["primary_handle"],
            )
        c = ContactsGuardContext(
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            state.cycle_id,
            state.batch_id,
            candidate.candidate_id,
            candidate.place_id,
            uuid5(state.cycle_id, "contacts-place:" + candidate.place_id),
            effect,
            uuid5(effect, "request-event"),
            s.reference_provider_pilot_id,
            state.context_version,
            s.reference_provider_hmac_key,
            s.reference_provider_key_version,
            s.reference_apify_tariff_version,
            s.reference_apify_credential_version,
            s.reference_apify_reserved_usd_micros,
            s.reference_apify_actor_build,
            s.reference_apify_actor_id,
        )
        guard = IntentContactsGuard(self.database, c, search, state.source_batch_mac)
        adapter = ApifyPlaceContacts(
            s.reference_apify_api_token,
            guard,
            enabled=True,
            network_enabled=True,
            transport=self.apify_transport,
            actor_build=c.build,
            provider_actor_id=c.provider_actor_id,
            max_actor_usd_micros=c.reserved_usd_micros,
        )
        existing = await load_contacts_run(self.database, c) if previous else None
        if existing is not None:
            run, token = existing
        elif previous is not None and previous.state != "pending":
            return "uncertain"
        else:
            run = await adapter.submit(c.place_id, c.effect)
            token = guard.execution_token()
            await record_contacts_run(self.database, c, token, run)
        result = await adapter.inspect(run, uuid5(effect, "contacts-inspection-v1"))
        if result.state == "pending":
            return "pending"
        if result.reported_cost_usd_micros is not None:
            await record_contacts_cost(self.database, c, token, run, result.reported_cost_usd_micros)
        if result.state == "unavailable":
            async with self.database.transaction(c.tenant, c.actor) as session:
                await session.scalar(
                    text("SELECT public.reference_contacts_terminal_failure(:business,:lookup,:effect,:token,:status)"),
                    {
                        "business": c.business,
                        "lookup": c.lookup,
                        "effect": effect,
                        "token": token,
                        "status": result.terminal_failure,
                    },
                )
            return "failed"
        handles = tuple(
            dict.fromkeys(instagram_handle(link.url) for link in result.social_links if link.platform == "instagram")
        )
        primary = handles[0] if handles else None
        await record_output(
            self.database,
            c.tenant,
            c.business,
            c.actor,
            effect,
            token,
            "contacts",
            {"handles": list(handles), "primary_handle": primary},
        )
        return CompletedContacts(
            candidate_id=candidate.candidate_id,
            effect=CompletedEffect(effect_id=effect, event_id=c.event, executor_token=token),
            handles=handles,
            primary_handle=primary,
        )

    async def _empty(self, event: BusinessEvent, search: UUID, google: Any) -> str:
        from app.services.reference_empty_search import advance_empty_search

        key = self.settings.reference_provider_hmac_key
        assert key is not None
        result = await advance_empty_search(
            self.database,
            key,
            self.settings.reference_provider_key_version,
            UUID(event.tenant_id),
            UUID(event.business_id),
            UUID(event.actor_id),
            search,
        )
        return "completed" if result.state == "exhausted" else "radius_successor"
