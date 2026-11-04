"""Only durable identifiers cross the Temporal workflow boundary."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class BusinessGeocodingWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "resolve_business_address",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=5),
            ),
        )
