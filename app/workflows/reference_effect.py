"""Workflows for simulated reference effects and their cost projection."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class ReferenceEffectWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "simulate_reference_effect",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=0),
            ),
        )


@workflow.defn
class ReferenceCostProjectionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "project_reference_cost",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=0),
            ),
        )


@workflow.defn
class ReferenceEffectProjectionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "project_reference_effect",
                event,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=0),
            ),
        )
