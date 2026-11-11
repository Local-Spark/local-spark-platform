"""Activity failures expose stable metadata, never source code or model responses."""

import asyncio

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.motion_orchestrator import MotionOrchestrator
from app.workflows.contracts import BusinessEvent


class MotionActivities:
    def __init__(self, runner: MotionOrchestrator):
        self.runner = runner

    @activity.defn(name="run_motion_production")
    async def run(self, event: BusinessEvent) -> str:
        try:
            # Cancel locally before Temporal's outer timeout, leaving time for
            # the runner to persist uncertainty instead of an orphaned activity.
            async with asyncio.timeout(55 * 60):
                return await self.runner.run(event)
        except Exception:
            raise ApplicationError(
                "Motion production unavailable", type="MotionProductionUnavailable", non_retryable=True
            ) from None
