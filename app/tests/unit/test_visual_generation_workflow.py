"""The paid effect cannot inherit retries or the old static-preview timeout."""

from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.workflows import visual_generation
from app.workflows.visual_generation_activities import VisualGenerationActivities


async def test_workflow_requests_one_bounded_effect(monkeypatch):
    execute = AsyncMock(return_value="completed")
    monkeypatch.setattr(visual_generation.workflow, "execute_activity", execute)
    assert await visual_generation.VisualGenerationWorkflow().run("preview", 4) == "completed"
    assert execute.call_args.args == ("run_visual_generation",)
    options = execute.call_args.kwargs
    assert options["args"] == ["preview", 4]
    assert options["schedule_to_start_timeout"] == timedelta(minutes=1)
    assert options["start_to_close_timeout"] == timedelta(minutes=10)
    assert options["retry_policy"].maximum_attempts == 1


async def test_activity_passes_the_preview_identity_to_the_injected_runner():
    preview = uuid4()
    runner = AsyncMock()
    runner.run_preview.return_value = "uncertain"
    activity = VisualGenerationActivities(runner)
    assert await activity.run_visual_generation(str(preview), 7) == "uncertain"
    runner.run_preview.assert_awaited_once_with(preview, 7)


async def test_activity_rejects_invalid_identity_before_effect():
    runner = AsyncMock()
    with pytest.raises(ValueError):
        await VisualGenerationActivities(runner).run_visual_generation("not-a-uuid", 1)
    runner.run_preview.assert_not_awaited()
