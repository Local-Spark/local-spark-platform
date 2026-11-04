"""Load private selection and feed data only inside activities."""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.reference_learning_execution import ReferenceLearningExecution
from app.workflows.contracts import BusinessEvent


class ReferenceLearningActivities:
    def __init__(self, executor: ReferenceLearningExecution) -> None:
        self.executor = executor

    @activity.defn
    async def reference_learning_schedule(self, event: BusinessEvent) -> str:
        try:
            window = await self.executor.store.load(event)
            return "cancelled" if window.state not in ("pending", "blocked") else window.scheduled_at.isoformat()
        except Exception:
            raise ApplicationError("Reference learning unavailable", type="ReferenceLearningUnavailable") from None

    @activity.defn
    async def execute_reference_learning(self, event: BusinessEvent) -> str:
        try:
            return await self.executor.run(event, heartbeat=activity.heartbeat)
        except Exception:
            raise ApplicationError("Reference learning unavailable", type="ReferenceLearningUnavailable") from None
