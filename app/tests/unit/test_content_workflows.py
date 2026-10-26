"""Candidate and fake-publication workflows keep IO in activities."""

from unittest.mock import AsyncMock

import pytest

from app.workflows import content_candidate, content_publication


@pytest.mark.parametrize(
    "states,expected",
    [
        (["needs_fact"], "clarification_delivered"),
        (["failed"], "proposal_failed"),
        (["completed", "failed"], "preview_failed"),
        (["completed", "completed"], "candidate_delivered"),
    ],
)
async def test_candidate_workflow_outcomes(monkeypatch, states, expected):
    pending = iter(states)

    async def execute(name, *args, **kwargs):
        if name == "request_candidate_proposal":
            return "proposal-id"
        if name == "candidate_proposal_state":
            return next(pending)
        if name == "deliver_candidate_clarification":
            return "clarification_delivered"
        if name == "request_candidate_preview":
            return "preview-id"
        if name == "candidate_preview_state":
            return next(pending)
        if name == "deliver_candidate_preview":
            return "candidate_delivered"
        raise AssertionError(name)

    monkeypatch.setattr(content_candidate.workflow, "execute_activity", execute)
    monkeypatch.setattr(content_candidate.workflow, "sleep", AsyncMock())
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == expected


async def test_candidate_workflow_skips_and_blocks(monkeypatch):
    execute = AsyncMock(return_value="skipped")
    monkeypatch.setattr(content_candidate.workflow, "execute_activity", execute)
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == "skipped"

    execute.side_effect = ["proposal-id", "completed", "blocked"]
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == "preview_blocked"


async def test_fake_publication_workflow_delegates(monkeypatch):
    execute = AsyncMock(return_value="published")
    monkeypatch.setattr(content_publication.workflow, "execute_activity", execute)
    assert await content_publication.FakeContentPublicationWorkflow().run("delivery-id", 2) == "published"
    assert execute.await_args.args == ("publish_fake_content", ["delivery-id", 2])


@pytest.mark.parametrize("stall_at,expected", [("proposal", "proposal_timeout"), ("preview", "preview_timeout")])
async def test_candidate_workflow_has_bounded_waits(monkeypatch, stall_at, expected):
    async def execute(name, *args, **kwargs):
        if name == "request_candidate_proposal":
            return "proposal-id"
        if name == "candidate_proposal_state":
            return "waiting" if stall_at == "proposal" else "completed"
        if name == "request_candidate_preview":
            return "preview-id"
        if name == "candidate_preview_state":
            return "pending"
        raise AssertionError(name)

    sleep = AsyncMock()
    monkeypatch.setattr(content_candidate.workflow, "execute_activity", execute)
    monkeypatch.setattr(content_candidate.workflow, "sleep", sleep)
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == expected
    assert sleep.await_count == 60
