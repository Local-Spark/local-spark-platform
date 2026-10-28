"""Activity boundary; authorization and effect safety belong to the runner."""

from typing import Protocol
from uuid import UUID

from temporalio import activity


class VisualGenerationRunner(Protocol):
    async def run_preview(self, preview_id: UUID, fence: int) -> str: ...


class VisualGenerationActivities:
    def __init__(self, runner: VisualGenerationRunner) -> None:
        self.runner = runner

    @activity.defn
    async def run_visual_generation(self, preview_id: str, fence: int) -> str:
        return await self.runner.run_preview(UUID(preview_id), fence)
