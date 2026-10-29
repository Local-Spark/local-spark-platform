"""Queued script changes keep authorship and apply in proposal -> visual order."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.visual_pending_scripts import (
    apply_pending_script_changes,
    require_script_change_slot,
    script_change_status,
)


def _edit_payload(operation):
    return {
        "operation_id": str(operation),
        "expected_version": 1,
        "title": "Uma pausa especial",
        "angle": "Conheça os produtos do nosso negócio",
        "script": [
            {
                "role": "fact",
                "visual": "brand_card",
                "on_screen_text": "Croissant.",
                "voiceover": "Croissant.",
                "fact_ids": [str(uuid4())],
            },
            {
                "role": "cta",
                "visual": "brand_card",
                "on_screen_text": "Converse com a equipe",
                "voiceover": "Converse com a equipe",
                "fact_ids": [],
            },
        ],
    }


def _case(settings, monkeypatch, *, kind="script_edit", active=False):
    tenant, business, actor, proposal, operation = (uuid4() for _ in range(5))
    command = {
        "operation_id": operation,
        "actor_id": actor,
        "kind": kind,
        "payload": {
            "proposal_id": str(proposal),
            "expected_version": 1,
            "body": _edit_payload(operation)
            if kind == "script_edit"
            else {"operation_id": str(operation), "decision": "accepted"},
        },
    }
    commands = [command, command, None]
    events, updates = [], []

    async def execute(statement, params=None):
        sql = str(statement)
        value = None
        if "SELECT * FROM business_visual_pending_changes" in sql:
            value = commands.pop(0)
        elif "SELECT id FROM editorial_proposals" in sql:
            events.append("proposal")
        elif "UPDATE business_visual_pending_changes" in sql:
            updates.append(params)
        result = MagicMock()
        result.mappings.return_value.one_or_none.return_value = value
        return result

    @asynccontextmanager
    async def opened(*_):
        yield session

    session = SimpleNamespace(
        execute=AsyncMock(side_effect=execute), scalar=AsyncMock(side_effect=[active, 1]), begin_nested=opened
    )
    database = SimpleNamespace(transaction=opened)
    lock = AsyncMock(side_effect=lambda *_: events.append("visual"))
    edit, review, apply, audit = AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr("app.services.whatsapp_materials.WhatsAppMaterialsService._require_owner", AsyncMock())
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate._lock", lock)
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate._audit", audit)
    monkeypatch.setattr("app.services.editorial_proposals.EditorialProposalService._edit_script_in_session", edit)
    monkeypatch.setattr("app.services.editorial_proposals.EditorialProposalService._review_script_in_session", review)
    monkeypatch.setattr("app.services.visual_pending_changes.VisualPendingChanges.apply_pending_in_session", apply)
    return SimpleNamespace(
        settings=settings,
        database=database,
        tenant=tenant,
        business=business,
        actor=actor,
        proposal=proposal,
        operation=operation,
        command=command,
        commands=commands,
        session=session,
        events=events,
        updates=updates,
        edit=edit,
        review=review,
        apply=apply,
        audit=audit,
    )


async def _run(case):
    await apply_pending_script_changes(case.settings, case.database, case.tenant, case.business, case.actor)


@pytest.mark.parametrize("kind", ["script_edit", "script_review"])
async def test_pending_author_applies_only_after_proposal_and_visual_locks(settings, monkeypatch, kind):
    case = _case(settings, monkeypatch, kind=kind)
    await _run(case)
    assert case.events == ["proposal", "visual"]
    handler = case.edit if kind == "script_edit" else case.review
    handler.assert_awaited_once()
    assert handler.await_args.kwargs == {"enqueue": False}
    assert handler.await_args.args[3] == case.actor
    assert case.updates[0]["state"] == "completed" and case.updates[0]["error"] is None
    case.apply.assert_awaited_once_with(case.session, case.tenant, case.business)
    assert case.audit.await_args.args[-1] == "visual.change_applied"


@pytest.mark.parametrize("reason", ["none", "different_kind", "different_author"])
async def test_no_command_or_other_authorship_does_not_acquire_proposal_lock(settings, monkeypatch, reason):
    case = _case(settings, monkeypatch)
    if reason == "none":
        case.commands[:] = [None]
    elif reason == "different_kind":
        case.command["kind"] = "catalog_update"
    else:
        case.command["actor_id"] = uuid4()
    await _run(case)
    assert case.events == [] and case.updates == []
    case.edit.assert_not_awaited()
    case.audit.assert_not_awaited()


async def test_active_visual_work_preserves_the_pending_script(settings, monkeypatch):
    case = _case(settings, monkeypatch, active=True)
    await _run(case)
    assert case.events == ["proposal", "visual"] and case.updates == []
    case.edit.assert_not_awaited()
    case.apply.assert_not_awaited()


@pytest.mark.parametrize("replacement", [None, {"operation_id": uuid4()}])
async def test_a_command_changed_before_lock_is_read_again(settings, monkeypatch, replacement):
    case = _case(settings, monkeypatch)
    case.commands[1] = replacement
    await _run(case)
    assert case.updates == []
    case.edit.assert_not_awaited()
    case.apply.assert_not_awaited()


@pytest.mark.parametrize("failure", ["script_validation", "review_version"])
async def test_revalidation_failure_is_durable_without_applying_stale_command(settings, monkeypatch, failure):
    case = _case(settings, monkeypatch, kind="script_edit" if failure == "script_validation" else "script_review")
    if failure == "script_validation":
        case.edit.side_effect = AuthError("SCRIPT_CONTEXT_CHANGED", 409)
        expected = "SCRIPT_CONTEXT_CHANGED"
    else:
        case.session.scalar.side_effect = [False, 2]
        expected = "SCRIPT_VERSION_CONFLICT"
    await _run(case)
    assert case.updates[0]["state"] == "failed" and case.updates[0]["error"] == expected
    case.review.assert_not_awaited()
    assert case.audit.await_args.args[-1] == "visual.change_failed"


async def test_script_pending_status_uses_the_proposal_resource(settings, monkeypatch):
    status = AsyncMock(return_value={"operation_id": uuid4(), "status": "pending"})
    monkeypatch.setattr("app.services.visual_pending_changes.VisualPendingChanges.status_in_session", status)
    session = SimpleNamespace()
    tenant, business, proposal = uuid4(), uuid4(), uuid4()
    assert await script_change_status(session, tenant, business, proposal) == status.return_value
    status.assert_awaited_once_with(session, tenant, business, f"script:{proposal}")


@pytest.mark.parametrize("changed", [None, "actor_id", "kind", "resource_key", "request_hash"])
async def test_matching_pending_operation_replays_before_checking_other_resources(changed):
    tenant, business, actor, proposal, operation = (uuid4() for _ in range(5))
    previous = {
        "actor_id": actor,
        "kind": "script_edit",
        "resource_key": f"script:{proposal}",
        "request_hash": "a" * 64,
    }
    if changed:
        previous[changed] = uuid4() if changed == "actor_id" else "different"
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = previous
    session = SimpleNamespace(execute=AsyncMock(return_value=result), scalar=AsyncMock())
    args = (session, tenant, business, actor, proposal, operation, "script_edit", "a" * 64)
    if changed:
        with pytest.raises(AuthError, match="VISUAL_CHANGE_OPERATION_CONFLICT"):
            await require_script_change_slot(*args)
    else:
        await require_script_change_slot(*args)
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize("blocked", [False, True])
async def test_new_script_command_waits_for_other_resource_pending_or_failed(blocked):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = None
    session = SimpleNamespace(execute=AsyncMock(return_value=result), scalar=AsyncMock(return_value=blocked))
    args = (session, uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), "script_edit", "a" * 64)
    if blocked:
        with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
            await require_script_change_slot(*args)
    else:
        await require_script_change_slot(*args)
