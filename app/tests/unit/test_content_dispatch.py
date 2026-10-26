"""Local publication dispatcher never sends without an exact durable claim."""

from unittest.mock import AsyncMock
from uuid import uuid4

from temporalio.exceptions import WorkflowAlreadyStartedError

from app.services import content_dispatch


async def test_publication_dispatch_is_disabled_in_production(settings, monkeypatch):
    claim = AsyncMock()
    monkeypatch.setattr(content_dispatch, "claim_publications", claim)
    configured = settings.model_copy(update={"environment": "production"})
    assert await content_dispatch.dispatch_publications(AsyncMock(), AsyncMock(), configured, uuid4()) == 0
    claim.assert_not_awaited()


async def test_publication_dispatch_reuses_workflow_identity_and_handles_failure(settings, monkeypatch):
    delivery = uuid4()
    claim = AsyncMock(return_value=[(delivery, 3)])
    finish = AsyncMock()
    monkeypatch.setattr(content_dispatch, "claim_publications", claim)
    monkeypatch.setattr(content_dispatch, "finish_publication_dispatch", finish)
    client = AsyncMock()
    assert await content_dispatch.dispatch_publications(AsyncMock(), client, settings, uuid4()) == 1
    assert client.start_workflow.await_args.kwargs["id"] == f"fake-content-publish/{delivery}/3"
    assert finish.await_args.args[3] is True

    client.start_workflow.side_effect = WorkflowAlreadyStartedError(str(delivery), "FakeContentPublicationWorkflow")
    await content_dispatch.dispatch_publications(AsyncMock(), client, settings, uuid4())
    assert finish.await_args.args[3] is True

    client.start_workflow.side_effect = RuntimeError("Temporal unavailable")
    await content_dispatch.dispatch_publications(AsyncMock(), client, settings, uuid4())
    assert finish.await_args.args[3] is False
