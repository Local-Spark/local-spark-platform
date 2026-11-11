"""Temporal executes a durable one-attempt production; no private content in history."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class MotionProductionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "run_motion_production",
                event,
                result_type=str,
                schedule_to_start_timeout=timedelta(minutes=5),
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=RetryPolicy(maximum_attempts=1),
            ),
        )
