"""Private selected-profile analysis state; provider content never enters storage."""

import json
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app.adapters.apify_instagram_feed import FeedChargeableRequest, SubmittedInstagramFeed
from app.db.session import Database
from app.services.reference_feed_budget_guard import FeedGuardContext
from app.services.reference_feed_request_mac import feed_request_mac
from app.services.reference_learning_projection import DerivedPattern
from app.workflows.contracts import BusinessEvent


class StoredFeedRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    dataset_id: str
    store_id: str
    queue_id: str
    build_id: str
    actor_build: str


class StoredLearningFeed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    effect: UUID
    event: UUID
    pilot: UUID
    state: Literal["pending", "running", "uncertain", "completed"]
    executor_token: UUID | None
    key_version: str
    tariff_version: str
    credential_version: str
    build: str
    reserved_usd_micros: int
    request_mac: str
    run: StoredFeedRun | None


class LearningWindow(BaseModel):
    """Use only inside activities; profile and executor token are not workflow data."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    tenant: UUID
    business: UUID
    actor: UUID
    window: UUID
    event: UUID
    reference: UUID
    association_version: int
    profile: str
    accepted_at: datetime
    scheduled_at: datetime
    state: Literal["pending", "blocked", "completed", "partial", "unavailable", "cancelled"]
    feed: StoredLearningFeed | None

    def submitted_run(self) -> SubmittedInstagramFeed | None:
        if self.feed is None or self.feed.run is None:
            return None
        run = self.feed.run
        return SubmittedInstagramFeed(
            self.feed.effect,
            self.profile,
            run.run_id,
            run.dataset_id,
            run.store_id,
            run.queue_id,
            run.actor_build,
            run.build_id,
            20,
        )


class ReferenceLearningStore:
    def __init__(self, database: Database):
        self.database = database

    async def load(self, event: BusinessEvent) -> LearningWindow:
        async with self.database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
            value = await session.scalar(
                text("SELECT public.reference_learning_load(:business,:window,:event)"),
                {
                    "business": UUID(event.business_id),
                    "window": UUID(event.operation_id),
                    "event": UUID(event.event_id),
                },
            )
        return LearningWindow.model_validate(value)

    async def claim_feed(self, context: FeedGuardContext, request: FeedChargeableRequest) -> dict[str, object]:
        c = context
        mac = feed_request_mac(
            c.key,
            key_version=c.key_version,
            tariff_version=c.tariff_version,
            credential_version=c.credential_version,
            tenant=c.tenant,
            business=c.business,
            actor=c.actor,
            reference=c.reference,
            association_version=c.association_version,
            analysis_window=c.analysis_window,
            search=c.search,
            selection=c.selection,
            effect=c.effect,
            pilot=c.pilot,
            reserved_usd_micros=c.reserved_usd_micros,
            profile=c.profile,
            build=c.build,
            request=request,
        )
        async with self.database.transaction(c.tenant, c.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_learning_feed_claim(
              :business,:window,:effect,:event,:pilot,:mac,:key,:tariff,:credential,:build,:amount,:reference,\
:version,:profile)"""),
                {
                    "business": c.business,
                    "window": c.analysis_window,
                    "effect": c.effect,
                    "event": c.event,
                    "pilot": c.pilot,
                    "mac": mac,
                    "key": c.key_version,
                    "tariff": c.tariff_version,
                    "credential": c.credential_version,
                    "build": c.build,
                    "amount": c.reserved_usd_micros,
                    "reference": c.reference,
                    "version": c.association_version,
                    "profile": c.profile,
                },
            )
        return dict(result)

    async def authorize(self, window: LearningWindow, effect: UUID, token: UUID, run: SubmittedInstagramFeed) -> bool:
        if run.username != window.profile or run.submission_id != effect or run.results_limit != 20:
            return False
        async with self.database.transaction(window.tenant, window.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_learning_feed_authorize(
              :business,:window,:effect,:token,:run)"""),
                {
                    "business": window.business,
                    "window": window.window,
                    "effect": effect,
                    "token": token,
                    "run": run.run_id,
                },
            )
        return result is True

    async def record_run(self, window: LearningWindow, effect: UUID, token: UUID, run: SubmittedInstagramFeed) -> None:
        if run.username != window.profile or run.submission_id != effect or run.results_limit != 20:
            raise ValueError("REFERENCE_LEARNING_RUN_INVALID")
        async with self.database.transaction(window.tenant, window.actor) as session:
            await session.scalar(
                text("""SELECT public.reference_record_feed_resources(
              :business,:effect,:token,:operation,:run,:dataset,:store,:queue,:build_id,:build)"""),
                {
                    "business": window.business,
                    "effect": effect,
                    "token": token,
                    "operation": uuid5(effect, "reference-feed-resources-v1"),
                    "run": run.run_id,
                    "dataset": run.dataset_id,
                    "store": run.key_value_store_id,
                    "queue": run.request_queue_id,
                    "build_id": run.build_id,
                    "build": run.build_number,
                },
            )

    async def finish(
        self,
        window: LearningWindow,
        effect: UUID,
        token: UUID,
        *,
        patterns: tuple[DerivedPattern, ...],
        status: Literal["completed", "partial", "unavailable"],
        posts: int,
        images: int,
        coverage: Literal["unconfirmed", "partial"],
        profile_name: str | None = None,
    ) -> dict[str, object]:
        async with self.database.transaction(window.tenant, window.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_learning_finish(
              :business,:window,:effect,:token,CAST(:patterns AS jsonb),:status,:posts,:images,:coverage,:prof\
ile_name)"""),
                {
                    "business": window.business,
                    "window": window.window,
                    "effect": effect,
                    "token": token,
                    "patterns": json.dumps([p.model_dump() for p in patterns]),
                    "status": status,
                    "posts": posts,
                    "images": images,
                    "coverage": coverage,
                    "profile_name": profile_name,
                },
            )
        return dict(result)

    async def block(self, window: LearningWindow, reason: Literal["configuration", "budget"]) -> None:
        async with self.database.transaction(window.tenant, window.actor) as session:
            await session.scalar(
                text("SELECT public.reference_learning_block(:business,:window,:reason)"),
                {"business": window.business, "window": window.window, "reason": reason},
            )
