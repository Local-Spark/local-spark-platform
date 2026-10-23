"""Temporal dispatch IDs and retry behavior do not duplicate proposal execution."""

from unittest.mock import AsyncMock
from uuid import uuid4

from temporalio.exceptions import WorkflowAlreadyStartedError

from app.services import editorial_dispatch as module
from app.services.editorial_dispatch import ProposalClaim
from app.workflows import editorial_proposal as workflow_module
from app.workflows.editorial_activities import EditorialActivities


async def test_dispatch_accepts_existing_and_retries_transport_failure(settings, monkeypatch):
    claims = [ProposalClaim(uuid4(), uuid4(), 1) for _ in range(3)]
    monkeypatch.setattr(module, "claim_proposals", AsyncMock(return_value=claims))
    finish = AsyncMock()
    monkeypatch.setattr(module, "finish_proposal_dispatch", finish)
    client = AsyncMock()
    client.start_workflow.side_effect = [None, WorkflowAlreadyStartedError("id", "workflow"), RuntimeError()]
    assert await module.dispatch_proposals(AsyncMock(), client, settings, uuid4()) == 3
    assert [call.args[2] for call in finish.await_args_list] == [True, True, False]
    assert client.start_workflow.call_args.kwargs["id"].startswith("editorial-proposal/")


async def test_workflow_and_activity_execute_once(monkeypatch):
    execute = AsyncMock(return_value="completed")
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    assert await workflow_module.EditorialProposalWorkflow().run("proposal") == "completed"
    assert execute.await_count == 1
    service = AsyncMock()
    service.run.return_value = "completed"
    proposal = uuid4()
    assert await EditorialActivities(service).generate_editorial_proposal(str(proposal)) == "completed"
    service.run.assert_awaited_once_with(proposal)
