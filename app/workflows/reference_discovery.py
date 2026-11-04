"""Temporal workflow for a strictly local, explicitly marked simulation."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class ReferenceDiscoveryWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        try:
            return cast(
                str,
                await workflow.execute_activity(
                    "simulate_reference_discovery",
                    event,
                    result_type=str,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=5),
                ),
            )
        except ActivityError:
            return cast(
                str,
                await workflow.execute_activity(
                    "fail_reference_simulation",
                    event,
                    result_type=str,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=0),
                ),
            )
