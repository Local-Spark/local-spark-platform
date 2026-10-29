"""Reject malformed or conflicting durable changes without applying effects."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _result(*, one=None, rows=None):
    mapping = Mock()
    mapping.one_or_none.return_value = one
    mapping.all.return_value = rows or []
    return Mock(mappings=Mock(return_value=mapping))


@pytest.mark.asyncio
async def test_replayed_operation_must_match_identity_and_cannot_repeat_failure(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    old = {
        "actor_id": actor,
        "kind": "context_update",
        "resource_key": "context",
        "request_hash": "a" * 64,
        "state": "failed",
    }
    session = Mock(execute=AsyncMock(return_value=_result(one=old)))
    arguments = (session, tenant, business, actor, operation, "context_update", "context", "a" * 64, {})
    with pytest.raises(AuthError, match="VISUAL_CHANGE_FAILED"):
        await VisualPendingChanges.enqueue_in_session(*arguments)
    old["request_hash"] = "b" * 64
    with pytest.raises(AuthError, match="VISUAL_CHANGE_OPERATION_CONFLICT"):
        await VisualPendingChanges.enqueue_in_session(*arguments)


@pytest.mark.asyncio
async def test_unknown_pending_kind_is_marked_failed_and_audited(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    row = {"kind": "unknown", "actor_id": actor, "operation_id": operation}

    @asynccontextmanager
    async def nested():
        yield

    session = Mock(scalar=AsyncMock(return_value=0), execute=AsyncMock(), begin_nested=nested)
    session.execute.side_effect = [_result(rows=[row]), _result()]
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    audit = AsyncMock()
    monkeypatch.setattr(VisualConsentGate, "_audit", audit)
    await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
    assert session.execute.await_args.args[1]["error"] == "VISUAL_CHANGE_KIND_INVALID"
    audit.assert_awaited_once_with(session, tenant, business, actor, "visual.change_failed")


@pytest.mark.asyncio
@pytest.mark.parametrize("author", ["self", "missing", "other"])
async def test_unresolved_command_never_transfers_authorship(author):
    tenant, business, actor = [uuid4() for _ in range(3)]
    previous = {"self": actor, "missing": None, "other": uuid4()}[author]
    session = Mock(scalar=AsyncMock(return_value=previous))
    if author == "other":
        with pytest.raises(AuthError, match="VISUAL_CHANGE_STAFF_REQUIRED"):
            await VisualPendingChanges.require_change_author_in_session(session, tenant, business, actor, "context")
    else:
        await VisualPendingChanges.require_change_author_in_session(session, tenant, business, actor, "context")


@pytest.mark.asyncio
async def test_failed_command_by_another_author_cannot_be_superseded(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value={"status": "failed"}))
    audit = AsyncMock()
    monkeypatch.setattr(VisualConsentGate, "_audit", audit)
    session = Mock(execute=AsyncMock(return_value=_result()), scalar=AsyncMock(return_value=uuid4()))
    with pytest.raises(AuthError, match="VISUAL_CHANGE_STAFF_REQUIRED"):
        await VisualPendingChanges.enqueue_in_session(
            session, tenant, business, actor, operation, "context_update", "context", "a" * 64, {}
        )
    assert session.execute.await_count == 1
    audit.assert_not_awaited()
