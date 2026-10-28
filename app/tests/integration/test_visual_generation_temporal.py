"""Exercise the paid workflow's retry contract without an external provider."""

import os
from uuid import uuid4

import pytest
from temporalio.client import Client, WorkflowFailureError
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

from app.workflows.visual_generation import VisualGenerationWorkflow
from app.workflows.visual_generation_activities import VisualGenerationActivities

pytestmark = [pytest.mark.integration, pytest.mark.temporal]


async def test_visual_workflow_does_not_repeat_an_uncertain_effect():
    calls = []

    class Runner:
        async def run_preview(self, preview_id, fence):
            calls.append((preview_id, fence))
            raise ApplicationError("outcome unknown")

    queue = f"test-visual-once-{uuid4()}"
    preview = uuid4()
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    activities = VisualGenerationActivities(Runner())
    async with Worker(
        client,
        task_queue=queue,
        workflows=[VisualGenerationWorkflow],
        activities=[activities.run_visual_generation],
    ):
        with pytest.raises(WorkflowFailureError):
            await client.execute_workflow(
                VisualGenerationWorkflow.run,
                args=[str(preview), 9],
                id=f"test-visual-once/{preview}",
                task_queue=queue,
            )
    assert calls == [(preview, 9)]
