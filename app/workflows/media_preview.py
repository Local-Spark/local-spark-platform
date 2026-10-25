"""Deterministic Temporal owner for one static preview attempt."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class StaticPreviewWorkflow:
    @workflow.run
    async def run(self, preview_id: str, fence: int) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "render_static_preview",
                args=[preview_id, fence],
                result_type=str,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=1),
            ),
        )
