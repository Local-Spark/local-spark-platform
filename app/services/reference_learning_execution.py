"""Collect and analyze selected profiles without persisting publications.

The run and opaque sample identities survive activity retries. Captions, URLs and
image bytes stay in this process; only our pattern codes and coverage are stored.
"""

from collections.abc import Callable
from dataclasses import replace
from typing import Literal
from uuid import UUID, uuid5

import httpx

from app.adapters.apify_instagram_feed import ApifyInstagramFeed, InstagramFeedError, InstagramFeedPost
from app.adapters.jev_reference_post_analysis import JevReferencePostAnalysis, PostAnalysisError, PostAnalysisResult
from app.adapters.reference_feed_image import FeedImage, FeedImageDownloader, FeedImageError
from app.core.config import Settings
from app.db.session import Database
from app.services.reference_feed_analysis_input import build_feed_analysis_input
from app.services.reference_feed_budget_guard import FeedGuardContext
from app.services.reference_learning_guards import LearningFeedGuard, LearningImageGuard
from app.services.reference_learning_store import LearningWindow, ReferenceLearningStore
from app.services.reference_pattern_vocabulary import aggregate_pattern_choices
from app.services.reference_post_analysis_guard import (
    DatabasePostAnalysisGuard,
    PostGuardContext,
    caption_claimed,
    load_caption_sample,
    load_post_sample,
    post_sample_mac,
    record_feed_terminal_cost,
)
from app.workflows.contracts import BusinessEvent


class LearningBudgetUnavailable(Exception):
    """Preserve the current run and completed samples until budget becomes available."""


class ReferenceLearningExecution:
    def __init__(
        self,
        database: Database,
        settings: Settings,
        *,
        apify_transport: httpx.MockTransport | None = None,
        image_transport: httpx.MockTransport | None = None,
        jev_transport: httpx.MockTransport | None = None,
    ) -> None:
        self.database, self.settings = database, settings
        self.store = ReferenceLearningStore(database)
        self.apify_transport, self.image_transport, self.jev_transport = apify_transport, image_transport, jev_transport

    def _context(self, window: LearningWindow) -> FeedGuardContext:
        s, existing = self.settings, window.feed
        assert s.reference_provider_hmac_key is not None and s.reference_provider_pilot_id is not None
        effect = existing.effect if existing else uuid5(window.window, "reference-learning-feed-v1")
        return FeedGuardContext(
            tenant=window.tenant,
            business=window.business,
            actor=window.actor,
            reference=window.reference,
            association_version=window.association_version,
            analysis_window=window.window,
            search=None,
            selection=None,
            effect=effect,
            event=existing.event if existing else uuid5(effect, "reference-feed-requested-v1"),
            pilot=existing.pilot if existing else s.reference_provider_pilot_id,
            key=s.reference_provider_hmac_key,
            key_version=existing.key_version if existing else s.reference_provider_key_version,
            tariff_version=existing.tariff_version if existing else s.reference_feed_tariff_version,
            credential_version=existing.credential_version if existing else s.reference_feed_credential_version,
            reserved_usd_micros=existing.reserved_usd_micros if existing else s.reference_feed_reserved_usd_micros,
            profile=window.profile,
            build=existing.build if existing else s.reference_feed_actor_build,
        )

    async def run(self, event: BusinessEvent, *, heartbeat: Callable[[], None] = lambda: None) -> str:
        if not self.settings.reference_learning_ready():
            return "disabled"
        window = await self.store.load(event)
        if window.state not in ("pending", "blocked"):
            return window.state
        if window.feed is not None and window.feed.key_version != self.settings.reference_provider_key_version:
            return "configuration_unavailable"
        context, run = self._context(window), window.submitted_run()
        token = window.feed.executor_token if window.feed else None
        if window.feed is not None and run is None:
            # Close this unavailable attempt without releasing its hold or repeating the POST.
            return await self._missing_run(window)
        guard = LearningFeedGuard(self.database, context, self.store, window, token=token, run=run)
        provider = ApifyInstagramFeed(
            self.settings.reference_apify_api_token,
            guard,
            enabled=True,
            network_enabled=self.apify_transport is None,
            transport=self.apify_transport,
            actor_build=context.build,
            max_actor_usd_micros=context.reserved_usd_micros,
        )
        heartbeat()
        if run is None:
            try:
                run = await provider.submit(window.profile, context.effect, results_limit=20)
            except InstagramFeedError as exc:
                if str(exc) in ("FEED_BUDGET_UNAVAILABLE", "FEED_PRICING_UNAVAILABLE"):
                    await self.store.block(
                        window, "budget" if str(exc) == "FEED_BUDGET_UNAVAILABLE" else "configuration"
                    )
                    return "budget_unavailable"
                recovered = await self.store.load(event)
                if recovered.state not in ("pending", "blocked"):
                    return recovered.state
                if recovered.feed is None:
                    await self.store.block(recovered, "configuration")
                    return "configuration_unavailable"
                if recovered.submitted_run() is not None:
                    return "pending"
                return await self._missing_run(recovered)
            token = guard.execution_token()
            await self.store.record_run(window, context.effect, token, run)
            guard.run = run
        assert token is not None
        try:
            result = await provider.inspect(run, uuid5(context.effect, "reference-feed-inspection-v1"))
        except InstagramFeedError:
            # Recovery only repeats GETs for the durable run, never submission.
            return "pending"
        if result.state == "pending":
            return "pending"
        await record_feed_terminal_cost(
            self.database,
            window.tenant,
            window.actor,
            window.business,
            context.effect,
            token,
            result.reported_cost_usd_micros,
        )
        if result.state == "unavailable":
            await self.store.finish(
                window,
                context.effect,
                token,
                patterns=(),
                status="unavailable",
                posts=0,
                images=0,
                coverage=result.coverage,
                profile_name=result.profile_name,
            )
            return "unavailable"
        feed = build_feed_analysis_input(window.reference, window.association_version, window.profile, run, result)
        all_results: list[PostAnalysisResult] = []
        post_count = image_count = 0
        partial = feed.coverage == "partial"
        for post in feed.posts:
            heartbeat()
            try:
                samples, images, incomplete = await self._post(window, context, token, post, heartbeat)
            except LearningBudgetUnavailable:
                return "budget_unavailable"
            all_results.extend(samples)
            image_count += images
            post_count += bool(samples)
            partial = partial or incomplete
        patterns = aggregate_pattern_choices(tuple(sample.choices for sample in all_results))
        status: Literal["completed", "partial", "unavailable"] = (
            "unavailable" if not patterns else "partial" if partial else "completed"
        )
        await self.store.finish(
            window,
            context.effect,
            token,
            patterns=patterns,
            status=status,
            posts=post_count,
            images=image_count,
            coverage="partial" if partial else feed.coverage,
            profile_name=result.profile_name,
        )
        return status

    async def _missing_run(self, window: LearningWindow) -> str:
        assert window.feed is not None
        if window.feed.executor_token is None:
            return "budget_unavailable"
        await self.store.finish(
            window,
            window.feed.effect,
            window.feed.executor_token,
            patterns=(),
            status="unavailable",
            posts=0,
            images=0,
            coverage="unconfirmed",
            profile_name=None,
        )
        return "unavailable"

    async def _post(
        self,
        window: LearningWindow,
        context: FeedGuardContext,
        token: UUID,
        post: InstagramFeedPost,
        heartbeat: Callable[[], None],
    ) -> tuple[list[PostAnalysisResult], int, bool]:
        key = context.key
        caption_text = post.caption if post.caption and post.caption.strip() else None
        caption_mac = post_sample_mac(key, window.window, post.post_id, None)
        caption_used = await caption_claimed(
            self.database,
            window.tenant,
            window.actor,
            window.business,
            window.window,
            caption_mac,
        )
        results: list[PostAnalysisResult] = []
        images, partial = 0, False
        run = window.submitted_run()
        # A newly submitted run is reloaded before image reads; no token or raw feed enters Temporal.
        if run is None:
            window = await self.store.load(
                BusinessEvent(
                    str(window.event),
                    str(window.tenant),
                    str(window.business),
                    str(window.actor),
                    str(window.window),
                )
            )
            run = window.submitted_run()
        assert run is not None
        for index, url in enumerate(post.image_urls):
            heartbeat()
            sample_mac = post_sample_mac(key, window.window, post.post_id, index)
            saved = await load_post_sample(
                self.database,
                window.tenant,
                window.actor,
                window.business,
                window.window,
                sample_mac,
            )
            if saved is not None:
                if saved.result is not None:
                    results.append(saved.result)
                    images += 1
                else:
                    partial = True
                continue
            operation = uuid5(window.window, sample_mac)
            downloader = FeedImageDownloader(
                LearningImageGuard(self.store, window, run, token, operation, post.post_id, url),
                enabled=True,
                network_enabled=self.image_transport is None,
                transport=self.image_transport,
            )
            try:
                image = await downloader.fetch(run, post, url, operation)
            except FeedImageError:
                partial = True
                continue
            caption = caption_text if not caption_used else None
            caption_used = caption_used or caption is not None
            analyzed = await self._analyze(
                window, context, token, sample_mac, caption_mac if caption else None, caption, image
            )
            if analyzed is None:
                partial = True
                if caption is not None:
                    caption_used = await caption_claimed(
                        self.database,
                        window.tenant,
                        window.actor,
                        window.business,
                        window.window,
                        caption_mac,
                    )
            else:
                results.append(analyzed)
                images += 1
        # A successful prior caption-only sample remains usable even when images become accessible later.
        saved_caption = await load_caption_sample(
            self.database,
            window.tenant,
            window.actor,
            window.business,
            window.window,
            caption_mac,
        )
        if saved_caption is not None:
            if saved_caption.result is not None:
                if not any(code in ("tone", "theme") for result in results for code, _ in result.choices):
                    results.append(
                        replace(
                            saved_caption.result,
                            choices=tuple(
                                pair for pair in saved_caption.result.choices if pair[0] in ("tone", "theme")
                            ),
                        )
                    )
            else:
                partial = True
        elif not caption_used and caption_text:
            analyzed = await self._analyze(window, context, token, caption_mac, caption_mac, caption_text, None)
            if analyzed is None:
                partial = True
            else:
                results.append(analyzed)
        return results, images, partial

    async def _analyze(
        self,
        window: LearningWindow,
        feed: FeedGuardContext,
        token: UUID,
        sample_mac: str,
        caption_mac: str | None,
        caption: str | None,
        image: FeedImage | None,
    ) -> PostAnalysisResult | None:
        s = self.settings
        effect = uuid5(window.window, sample_mac)
        context = PostGuardContext(
            tenant=window.tenant,
            business=window.business,
            actor=window.actor,
            window=window.window,
            reference=window.reference,
            association_version=window.association_version,
            parent_feed_effect=feed.effect,
            parent_feed_token=token,
            effect=effect,
            sample_mac=sample_mac,
            pilot=feed.pilot,
            key=feed.key,
            key_version=feed.key_version,
            tariff_version=s.reference_jev_tariff_version,
            credential_version=s.reference_jev_credential_version,
            reserved_usd_micros=s.reference_post_reserved_usd_micros,
            caption_mac=caption_mac,
        )
        guard = DatabasePostAnalysisGuard(self.database, context)
        provider = JevReferencePostAnalysis(
            s.typesafe_api_key,
            s.intent_ai_model,
            guard,
            enabled=True,
            network_enabled=self.jev_transport is None,
            transport=self.jev_transport,
        )
        try:
            result = await provider.analyze(caption=caption, image=image, operation_id=effect)
        except PostAnalysisError as exc:
            if str(exc) == "REFERENCE_POST_ANALYSIS_BUDGET_UNAVAILABLE":
                raise LearningBudgetUnavailable from None
            return None
        await guard.record(result)
        return result
