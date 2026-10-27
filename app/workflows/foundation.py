"""The first durable vertical slice; business workflows will build on this boundary."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class BusinessCreatedWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        result = await workflow.execute_activity(
            "record_business_created",
            event,
            result_type=str,
            start_to_close_timeout=timedelta(seconds=30),
            schedule_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=5,
                non_retryable_error_types=["InvalidEvent"],
            ),
        )
        if not isinstance(result, str):
            raise TypeError("Foundation activity returned an invalid result")
        return result


@workflow.defn
class BrandKitChangedWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        result = await workflow.execute_activity(
            "record_brand_kit_changed",
            event,
            result_type=str,
            start_to_close_timeout=timedelta(seconds=30),
            schedule_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=5,
                non_retryable_error_types=["InvalidEvent"],
            ),
        )
        if not isinstance(result, str):
            raise TypeError("Brand kit activity returned an invalid result")
        return result
