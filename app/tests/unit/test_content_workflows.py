"""Candidate and fake-publication workflows keep IO in activities."""

from datetime import timedelta
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


@pytest.mark.parametrize(
    "outcomes,expected",
    [
        (["briefing_needs_clarification", "clarification_delivered"], "clarification_delivered"),
        (["briefing_pending", "briefing_unavailable"], "briefing_unavailable"),
        (["briefing_pending"] * 61, "briefing_timeout"),
    ],
)
async def test_briefing_workflow_handles_uncertainty_and_bounded_waits(monkeypatch, outcomes, expected):
    execute = AsyncMock(side_effect=outcomes)
    monkeypatch.setattr(content_candidate.workflow, "execute_activity", execute)
    monkeypatch.setattr(content_candidate.workflow, "sleep", AsyncMock())
    monkeypatch.setattr(content_candidate.workflow, "patched", lambda _: True)
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == expected
    if expected == "clarification_delivered":
        assert execute.await_args_list[-1].args == ("deliver_briefing_clarification", "event-id")


@pytest.mark.parametrize(
    "outcomes,patched,expected,sleeps",
    [
        (["briefing_budget_blocked", "briefing_budget_blocked", "briefing_pending", "skipped"], True, "skipped", 3),
        (["briefing_budget_blocked"] * 169, True, "briefing_budget_timeout", 168),
        (["briefing_budget_blocked"], False, "briefing_budget_blocked", 0),
        (["briefing_budget_blocked", "briefing_unavailable"], True, "briefing_unavailable", 1),
    ],
)
async def test_budget_wait_is_bounded_deterministic_and_never_retries_uncertain(
    monkeypatch, outcomes, patched, expected, sleeps
):
    execute, sleep = AsyncMock(side_effect=outcomes), AsyncMock()
    monkeypatch.setattr(content_candidate.workflow, "execute_activity", execute)
    monkeypatch.setattr(content_candidate.workflow, "sleep", sleep)
    monkeypatch.setattr(content_candidate.workflow, "patched", lambda _: patched)
    assert await content_candidate.ContentCandidateWorkflow().run("event-id") == expected
    assert sleep.await_count == sleeps
    assert all(call.args == (timedelta(hours=1),) for call in sleep.await_args_list)


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
