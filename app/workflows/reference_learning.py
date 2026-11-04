"""The timer and workflow history carry identities, dates and stable statuses only."""

from datetime import datetime, timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from app.workflows.contracts import BusinessEvent


@workflow.defn
class ReferenceLearningWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        scheduled: str = await workflow.execute_activity(
            "reference_learning_schedule",
            event,
            result_type=str,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        if scheduled == "cancelled":
            return scheduled
        wait = datetime.fromisoformat(scheduled) - workflow.now()
        if wait > timedelta(0):
            await workflow.sleep(wait)
        polls = 0
        while True:
            state: str = await workflow.execute_activity(
                "execute_reference_learning",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(hours=2),
                heartbeat_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
            polls += 1
            if polls >= 180 and state in ("pending", "budget_unavailable", "disabled", "configuration_unavailable"):
                workflow.continue_as_new(event)
            if state == "pending":
                await workflow.sleep(timedelta(seconds=10))
            elif state in ("budget_unavailable", "disabled", "configuration_unavailable"):
                await workflow.sleep(timedelta(hours=1))
            else:
                return state
