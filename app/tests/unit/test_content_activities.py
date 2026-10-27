"""Candidate activities reject stale inputs and report each durable job state."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.services.auth import AuthError
from app.workflows import content_activities


class Result:
    def __init__(self, value):
        self.value = value

    def mappings(self):
        return self

    def one_or_none(self):
        return self.value


class Session:
    def __init__(self):
        self.row = None
        self.value = None

    @asynccontextmanager
    async def begin(self):
        yield self

    async def execute(self, *_args, **_kwargs):
        return Result(self.row)

    async def scalar(self, *_args, **_kwargs):
        return self.value


class DatabaseStub:
    def __init__(self):
        self.session = Session()

    @asynccontextmanager
    async def sessions(self):
        yield self.session

    @asynccontextmanager
    async def transaction(self, *_args):
        yield self.session


def activities(settings):
    key = Fernet.generate_key()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    worker = DatabaseStub()
    return content_activities.ContentCandidateActivities(cfg, worker, worker), worker, Fernet(key)


async def test_candidate_proposal_skips_absent_commands_and_rejected_inputs(settings, monkeypatch):
    adapter, worker, cipher = activities(settings)
    event, tenant, business, actor = (uuid4() for _ in range(4))
    assert await adapter.request_candidate_proposal(str(event)) == "skipped"
    worker.session.row = {
        "kind": "text",
        "ciphertext": cipher.encrypt(b"Aprovar").decode(),
        "tenant_id": tenant,
        "business_id": business,
        "actor_id": actor,
    }
    assert await adapter.request_candidate_proposal(str(event)) == "skipped"
    worker.session.row["ciphertext"] = cipher.encrypt(b"Pedir ajustes: usar outra foto").decode()
    assert await adapter.request_candidate_proposal(str(event)) == "skipped"
    worker.session.row["ciphertext"] = cipher.encrypt(b"Quero mostrar o cafe").decode()
    proposal_id = uuid4()
    request = AsyncMock(return_value=SimpleNamespace(id=proposal_id))
    monkeypatch.setattr(content_activities.EditorialProposalService, "request", request)
    assert await adapter.request_candidate_proposal(str(event)) == str(proposal_id)
    assert request.await_args.args[:3] == (tenant, business, actor)
    worker.session.row["kind"] = "image"
    assert await adapter.request_candidate_proposal(str(event)) == str(proposal_id)
    request.side_effect = AuthError("EDITORIAL_BLOCKED", 409)
    assert await adapter.request_candidate_proposal(str(event)) == "skipped"


@pytest.mark.parametrize(
    "state,expected", [("budget_blocked", "briefing_budget_blocked"), ("uncertain", "briefing_unavailable")]
)
async def test_disabled_interpreter_never_falls_back_for_an_existing_briefing(settings, monkeypatch, state, expected):
    adapter, worker, cipher = activities(settings)
    event = uuid4()
    worker.session.row = {
        "kind": "text",
        "ciphertext": cipher.encrypt(b"Mensagem").decode(),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "actor_id": uuid4(),
    }
    worker.session.value = state
    request = AsyncMock()
    monkeypatch.setattr(content_activities.EditorialProposalService, "request", request)
    assert await adapter.request_candidate_proposal(str(event)) == expected
    request.assert_not_awaited()


@pytest.mark.parametrize(
    "row,expected",
    [
        (None, "failed"),
        ({"state": "completed", "error_code": None}, "completed"),
        ({"state": "rejected", "error_code": "EDITORIAL_FACTS_REQUIRED"}, "needs_fact"),
        ({"state": "rejected", "error_code": "OTHER"}, "failed"),
        ({"state": "pending", "error_code": None}, "waiting"),
    ],
)
async def test_candidate_proposal_states(settings, row, expected):
    adapter, worker, _ = activities(settings)
    worker.session.row = row
    assert await adapter.candidate_proposal_state(str(uuid4())) == expected


async def test_candidate_preview_guards_and_states(settings, monkeypatch):
    adapter, worker, _ = activities(settings)
    event, proposal, preview = (uuid4() for _ in range(3))
    ids = [str(event), str(proposal)]
    assert await adapter.request_candidate_preview(ids) == "blocked"
    worker.session.row = {"tenant_id": uuid4(), "business_id": uuid4(), "actor_id": uuid4()}
    request = AsyncMock(return_value=SimpleNamespace(id=preview))
    monkeypatch.setattr(content_activities.MediaPreviewService, "request_candidate", request)
    assert await adapter.request_candidate_preview(ids) == str(preview)
    request.side_effect = AuthError("PREVIEW_BLOCKED", 409)
    assert await adapter.request_candidate_preview(ids) == "blocked"
    worker.session.value = None
    assert await adapter.candidate_preview_state(str(preview)) == "failed"
    worker.session.value = "completed"
    assert await adapter.candidate_preview_state(str(preview)) == "completed"


async def test_delivery_and_publication_activity_results(settings, monkeypatch):
    adapter, _, _ = activities(settings)
    record = AsyncMock(return_value=None)
    monkeypatch.setattr(content_activities.ContentDeliveryService, "record", record)
    event, preview = uuid4(), uuid4()
    assert await adapter.deliver_candidate_clarification(str(event)) == "delivery_blocked"
    assert await adapter.deliver_briefing_clarification(str(event)) == "delivery_blocked"
    assert await adapter.deliver_candidate_preview([str(event), str(preview)]) == "delivery_blocked"
    record.return_value = uuid4()
    assert await adapter.deliver_candidate_clarification(str(event)) == "clarification_delivered"
    assert await adapter.deliver_briefing_clarification(str(event)) == "clarification_delivered"
    assert record.await_args.kwargs == {"clarification": "briefing"}
    assert await adapter.deliver_candidate_preview([str(event), str(preview)]) == "candidate_delivered"
    publish = AsyncMock(return_value="published")
    monkeypatch.setattr(content_activities, "publish_fake", publish)
    assert await adapter.publish_fake_content([str(event), 3]) == "published"
    assert publish.await_args.args[-2:] == (event, 3)


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_experimental_interpreter_cannot_be_enabled_outside_development(settings, environment):
    cfg = settings.model_copy(update={"environment": environment})
    database = DatabaseStub()
    interpreter = SimpleNamespace(interpret=AsyncMock())
    with pytest.raises(ValueError, match="restricted to development and testing"):
        content_activities.ContentCandidateActivities(cfg, database, database, interpreter=interpreter)
    # The existing activity remains constructible when the experimental path is off.
    assert content_activities.ContentCandidateActivities(cfg, database, database).interpreter is None
