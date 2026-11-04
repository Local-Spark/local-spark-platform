"""Use the canonical selection and persisted feed run before every external read."""

from uuid import UUID, uuid5

from app.adapters.apify_instagram_feed import FeedChargeableRequest, FeedInspectionIntent, SubmittedInstagramFeed
from app.adapters.reference_feed_image import FeedImageIntent
from app.db.session import Database
from app.services.reference_feed_budget_guard import DatabaseFeedBudgetGuard, FeedGuardContext
from app.services.reference_learning_store import LearningWindow, ReferenceLearningStore


class LearningFeedGuard(DatabaseFeedBudgetGuard):
    def __init__(
        self,
        database: Database,
        context: FeedGuardContext,
        store: ReferenceLearningStore,
        window: LearningWindow,
        *,
        token: UUID | None = None,
        run: SubmittedInstagramFeed | None = None,
    ) -> None:
        super().__init__(database, context)
        self.store, self.window, self.run = store, window, run
        self._token = token

    async def claim_submission(self, operation_id: UUID, request: FeedChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        result = await self.store.claim_feed(self._context, request)
        if result["created"] is not True:
            return False
        self._token = UUID(str(result["executor_token"]))
        self._mac = self._request_mac(request)
        return True

    def execution_token(self) -> UUID:
        if self._token is None:
            raise ValueError("REFERENCE_LEARNING_EXECUTOR_REQUIRED")
        return self._token

    async def claim_inspection(self, operation_id: UUID, intent: FeedInspectionIntent) -> bool:
        if (
            self.run is None
            or intent.submission != self.run
            or operation_id != uuid5(self._context.effect, "reference-feed-inspection-v1")
            or intent.run_request.method != "GET"
            or intent.dataset_request.method != "GET"
            or intent.run_request.url != f"https://api.apify.com/v2/actor-runs/{self.run.run_id}"
            or intent.dataset_request.url
            != (f"https://api.apify.com/v2/datasets/{self.run.dataset_id}/items?clean=true&limit=21")
        ):
            return False
        return await self.store.authorize(self.window, self._context.effect, self.execution_token(), self.run)

    async def inspection_uncertain(self, operation_id: UUID, intent: FeedInspectionIntent) -> None:
        # GET may be repeated against this exact persisted run; no second actor run is admitted.
        if not await self.claim_inspection(operation_id, intent):
            raise ValueError("REFERENCE_LEARNING_INSPECTION_INVALID")


class LearningImageGuard:
    def __init__(
        self,
        store: ReferenceLearningStore,
        window: LearningWindow,
        run: SubmittedInstagramFeed,
        token: UUID,
        operation: UUID,
        post_id: str,
        url: str,
    ) -> None:
        self.store, self.window, self.run, self.token = store, window, run, token
        self.operation, self.post_id, self.url = operation, post_id, url

    async def authorize(self, operation_id: UUID, intent: FeedImageIntent) -> bool:
        if (
            operation_id != self.operation
            or intent.method != "GET"
            or intent.run != self.run
            or intent.post_id != self.post_id
            or intent.url != self.url
        ):
            return False
        return await self.store.authorize(self.window, self.run.submission_id, self.token, self.run)
