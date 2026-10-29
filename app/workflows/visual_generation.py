"""Separate single-attempt workflow; the runner authorizes every visual effect."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class VisualGenerationWorkflow:
    @workflow.run
    async def run(self, preview_id: str, fence: int) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "run_visual_generation",
                args=[preview_id, fence],
                result_type=str,
                schedule_to_start_timeout=timedelta(minutes=1),
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            ),
        )
