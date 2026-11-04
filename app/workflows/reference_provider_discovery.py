"""Temporal transports identifiers and stable statuses, never source content."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from app.workflows.contracts import BusinessEvent


@workflow.defn
class ReferenceProviderDiscoveryWorkflow:
    def __init__(self) -> None:
        self._resumed = False

    @workflow.signal
    async def resume(self) -> None:
        self._resumed = True

    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        pending_polls = 0
        while True:
            status: str = await workflow.execute_activity(
                "execute_reference_provider_discovery",
                event,
                start_to_close_timeout=timedelta(minutes=15),
                schedule_to_close_timeout=timedelta(minutes=20),
                retry_policy=RetryPolicy(maximum_attempts=2),
                result_type=str,
            )
            if status in ("awaiting_own_review", "contacts_failed"):
                await workflow.wait_condition(lambda: self._resumed)
                self._resumed = False
                pending_polls = 0
            elif status in ("contacts_pending", "disabled"):
                if pending_polls >= 180:
                    workflow.continue_as_new(event)
                pending_polls += 1
                await workflow.sleep(timedelta(seconds=10) if status == "contacts_pending" else timedelta(hours=1))
            else:
                return status
