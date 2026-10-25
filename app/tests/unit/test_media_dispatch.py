"""Preview workflow IDs, activity wiring and retry decisions are deterministic."""

from unittest.mock import AsyncMock
from uuid import uuid4

from temporalio.exceptions import WorkflowAlreadyStartedError

from app.services import media_dispatch as module
from app.services.media_dispatch import PreviewClaim
from app.workflows import media_preview as workflow_module
from app.workflows.media_activities import MediaPreviewActivities


async def test_dispatch_accepts_existing_workflow_and_retries_transport_failure(settings, monkeypatch):
    claims = [PreviewClaim(uuid4(), uuid4(), 1, attempt) for attempt in range(1, 4)]
    monkeypatch.setattr(module, "claim_previews", AsyncMock(return_value=claims))
    finish = AsyncMock()
    monkeypatch.setattr(module, "finish_preview_dispatch", finish)
    client = AsyncMock()
    client.start_workflow.side_effect = [None, WorkflowAlreadyStartedError("id", "workflow"), RuntimeError()]
    assert await module.dispatch_previews(AsyncMock(), client, settings, uuid4()) == 3
    assert [call.args[2] for call in finish.await_args_list] == [True, True, False]
    assert client.start_workflow.call_args.kwargs["id"].startswith("media-preview/")


async def test_static_preview_workflow_and_activity_are_thin(monkeypatch):
    execute = AsyncMock(return_value="completed")
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    assert await workflow_module.StaticPreviewWorkflow().run("preview", 7) == "completed"
    assert execute.call_args.kwargs["args"] == ["preview", 7]
    service = AsyncMock()
    service.render.return_value = "completed"
    preview = uuid4()
    assert await MediaPreviewActivities(service).render_static_preview(str(preview), 7) == "completed"
    service.render.assert_awaited_once_with(preview, 7)
