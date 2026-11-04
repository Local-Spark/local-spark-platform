"""Record delivery of a simulated fixture selection event."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class ReferenceSelectionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "record_reference_fixture_selection",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=0),
            ),
        )
