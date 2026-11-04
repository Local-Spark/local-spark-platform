"""Bind the exact in-memory Jev request to its durable intent before claim."""

from uuid import UUID

from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.db.session import Database
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard, JevGuardContext, JevGuardStateError
from app.services.reference_jev_intent import create_jev_intent


class IntentJevBudgetGuard:
    """Single-use adapter guard; no network is performed while a transaction is open."""

    def __init__(self, database: Database, context: JevGuardContext, google_event: UUID) -> None:
        self._database = database
        self._context = context
        self._google_event = google_event
        self._attempted = False
        self._guard: DatabaseJevBudgetGuard | None = None

    async def claim(self, operation_id: UUID, request: JevChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        self._context = await create_jev_intent(self._database, self._context, self._google_event, request)
        self._guard = DatabaseJevBudgetGuard(self._database, self._context)
        return await self._guard.claim(operation_id, request)

    async def uncertain(self) -> None:
        if self._guard is None:
            raise JevGuardStateError("JEV_EXECUTOR_NOT_CLAIMED")
        await self._guard.uncertain()

    def execution_token(self) -> UUID:
        if self._guard is None:
            raise JevGuardStateError("JEV_EXECUTOR_NOT_CLAIMED")
        return self._guard.execution_token()

    def event_id(self) -> UUID:
        return self._context.event
