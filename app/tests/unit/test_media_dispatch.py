"""Preview workflow IDs, activity wiring and retry decisions are deterministic."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
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


@pytest.mark.parametrize("accepted", [False, True])
async def test_real_dispatch_acknowledgement_never_resets_effect_for_retry(accepted):
    database = AsyncMock()
    await module.finish_preview_dispatch(database, PreviewClaim(uuid4(), uuid4(), 1, 1, "visual_ai"), accepted)
    database.sessions.assert_not_called()


async def test_real_dispatch_uses_explicit_readiness_and_stable_separate_workflow(settings, monkeypatch):
    from app.tests.unit.test_visual_generation_runner import _enabled

    claims = [PreviewClaim(uuid4(), uuid4(), 1, 1, "visual_ai")]
    claimed = AsyncMock(return_value=claims)
    monkeypatch.setattr(module, "claim_previews", claimed)
    monkeypatch.setattr(module, "finish_preview_dispatch", AsyncMock())
    client = AsyncMock()
    owner, database = uuid4(), AsyncMock()
    assert await module.dispatch_previews(database, client, _enabled(settings), owner) == 1
    claimed.assert_awaited_once_with(database, owner, visual_enabled=True)
    assert client.start_workflow.await_args.args == ("VisualGenerationWorkflow",)
    assert client.start_workflow.await_args.kwargs["id"] == f"visual-preview/{claims[0].id}"


async def test_claim_retains_persisted_mode_and_uses_no_expired_real_lease_for_retry():
    rows = [
        {"id": uuid4(), "dispatch_fence": 2, "attempts": 1, "generation_mode": "visual_ai"},
        {"id": uuid4(), "dispatch_fence": 3, "attempts": 2, "generation_mode": "visual_fake"},
    ]
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    session = AsyncMock()
    session.execute.return_value = result

    @asynccontextmanager
    async def sessions():
        yield session

    session.begin = MagicMock(side_effect=sessions)
    database = SimpleNamespace(sessions=sessions)
    owner = uuid4()
    claims = await module.claim_previews(database, owner, visual_enabled=True)
    assert [claim.generation_mode for claim in claims] == ["visual_ai", "visual_fake"]
    assert all(claim.owner == owner for claim in claims)
    assert claims[0].fence == 2 and claims[1].attempt == 2
    query, params = session.execute.await_args.args
    assert "AND generation_mode<>'visual_ai'" in str(query)
    assert "interval '12 minutes'" in str(query)
    assert params["visual_enabled"] is True
