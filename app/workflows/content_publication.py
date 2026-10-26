"""Deterministic local publication orchestration."""

from datetime import timedelta
from typing import cast

from temporalio import workflow


@workflow.defn
class FakeContentPublicationWorkflow:
    @workflow.run
    async def run(self, delivery_id: str, fence: int) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "publish_fake_content",
                [delivery_id, fence],
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
            ),
        )
