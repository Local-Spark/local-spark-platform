"""Durable trace expiry; only identifiers and delays enter Temporal history."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class CreationLabRetentionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        while True:
            seconds = cast(
                int,
                await workflow.execute_activity(
                    "expire_creation_lab_trace",
                    event.operation_id,
                    result_type=int,
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=10), maximum_interval=timedelta(minutes=10)
                    ),
                ),
            )
            if seconds <= 0:
                return "expired_or_ineligible"
            await workflow.sleep(timedelta(seconds=seconds + 1))
