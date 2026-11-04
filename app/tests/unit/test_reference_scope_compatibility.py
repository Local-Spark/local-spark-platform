"""New reference scope rules preserve old versions and durable queued edits."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.editorial_context import ContextContent, ContextRead, ContextRestore, ContextUpdate
from app.services.auth import AuthError
from app.services.editorial_context import (
    EditorialContextService,
    _digest,
    _preserve_omitted_legacy,
    _validate_reference_change,
)
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges

LEGACY = {"scope": "national"}
LOCAL = {
    "scope": "local",
    "radius_km": 5,
    "origin": {"method": "manual", "address": {"city": "Rio", "state_code": "RJ"}},
}


def content(preference):
    return ContextContent.model_validate({"preferences": {"reference_search": preference}})


def current(preference):
    return ContextRead.model_validate({"version": 1, "preferences": {"reference_search": preference}})


@pytest.mark.parametrize("radius", [5, 20, 50])
def test_new_local_choices_and_unchanged_legacy_are_valid(radius):
    _validate_reference_change(current(None), content({**LOCAL, "radius_km": radius}))
    _validate_reference_change(current(LEGACY), content(LEGACY))
    _validate_reference_change(current(LEGACY), content(None))


@pytest.mark.parametrize("preference", [{"scope": "national"}, {**LOCAL, "radius_km": 10}])
def test_new_legacy_choice_is_rejected(preference):
    with pytest.raises(AuthError, match="REFERENCE_SEARCH_NOT_SUPPORTED"):
        _validate_reference_change(current(None), content(preference))


def test_omitted_legacy_preserved_but_explicit_removal_or_supported_unchanged():
    omitted = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"tone": "friendly"}}
    )
    proposed = ContextContent.model_validate(omitted.model_dump(exclude={"expected_version", "operation_id"}))
    preserved, changed = _preserve_omitted_legacy(omitted, proposed, current(LEGACY))
    assert changed and preserved.preferences.reference_search.scope == "national"
    preserved, changed = _preserve_omitted_legacy(omitted, proposed, current(LOCAL))
    assert not changed and preserved.preferences.reference_search is None
    explicit = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"reference_search": None}}
    )
    proposed = ContextContent.model_validate(explicit.model_dump(exclude={"expected_version", "operation_id"}))
    _, changed = _preserve_omitted_legacy(explicit, proposed, current(LEGACY))
    assert not changed
    restore = ContextRestore(expected_version=1, target_version=1, operation_id=uuid4())
    _, changed = _preserve_omitted_legacy(restore, proposed, current(LEGACY))
    assert not changed
    _, changed = _preserve_omitted_legacy(omitted, proposed, current(None))
    assert not changed


async def test_pending_omission_preserves_legacy_without_changing_operation_digest(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"tone": "friendly"}}
    )
    proposed = ContextContent.model_validate(payload.model_dump(exclude={"expected_version", "operation_id"}))
    original = current(LEGACY)
    row = {
        "version": 1,
        "document": original.model_dump(mode="json", exclude={"version", "updated_at", "hypotheses", "pending_change"}),
        "created_at": None,
    }
    monkeypatch.setattr(EditorialContextService, "_version", AsyncMock(return_value=row))
    monkeypatch.setattr(EditorialContextService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    queue = AsyncMock(return_value=True)
    monkeypatch.setattr(VisualPendingChanges, "enqueue_in_session", queue)
    session = MagicMock()
    service = EditorialContextService(MagicMock())
    result = await service._queue_or_save(session, tenant, business, actor, payload, proposed, "context_update")
    assert result.pending_change is not None
    stored = queue.await_args.args[8]
    assert "reference_search" not in stored["preferences"]
    assert _digest(ContextUpdate.model_validate(stored)) == _digest(payload)
    save = AsyncMock()
    monkeypatch.setattr(EditorialContextService, "_save", save)
    pending = {
        "kind": "context_update",
        "payload": stored,
        "operation_id": payload.operation_id,
        "request_hash": _digest(payload),
        "actor_id": actor,
    }
    await EditorialContextService.apply_pending_in_session(session, tenant, business, pending)
    assert save.await_args.args[7].preferences.reference_search.scope == "national"
    assert save.await_args.args[7].preferences.tone == "friendly"


async def test_existing_complete_pending_payload_checks_current_context(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextUpdate.model_validate(
        {
            "expected_version": 1,
            "operation_id": uuid4(),
            "preferences": {"reference_search": LOCAL, "business_terms": []},
        }
    )
    # This historical complete payload predates business_characteristics.
    historical_payload = payload.model_dump(mode="json")
    historical_payload["preferences"].pop("business_characteristics")
    row = {
        "kind": "context_update",
        "payload": historical_payload,
        "operation_id": payload.operation_id,
        "request_hash": _digest(payload),
        "actor_id": actor,
    }
    lookup = AsyncMock(return_value=None)
    save = AsyncMock()
    monkeypatch.setattr(EditorialContextService, "_version", lookup)
    monkeypatch.setattr(EditorialContextService, "_save", save)
    await EditorialContextService.apply_pending_in_session(MagicMock(), tenant, business, row)
    lookup.assert_awaited_once()
    assert save.await_args.args[7].preferences.reference_search.radius_km == 5


async def test_queue_replays_first_and_saves_non_deferred_changes(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextUpdate(expected_version=0, operation_id=uuid4())
    proposed = ContextContent()
    replay = AsyncMock(return_value=ContextRead(version=1))
    monkeypatch.setattr(EditorialContextService, "_replay", replay)
    service = EditorialContextService(MagicMock())
    assert (
        await service._queue_or_save(MagicMock(), tenant, business, actor, payload, proposed, "context_update")
    ).version == 1
    replay.return_value = None
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(EditorialContextService, "_version", AsyncMock(return_value=None))
    monkeypatch.setattr(VisualPendingChanges, "enqueue_in_session", AsyncMock(return_value=False))
    save = AsyncMock(return_value=ContextRead(version=1))
    monkeypatch.setattr(EditorialContextService, "_save", save)
    assert (
        await service._queue_or_save(MagicMock(), tenant, business, actor, payload, proposed, "context_update")
    ).version == 1
    save.assert_awaited_once()


async def test_read_keeps_pending_status_for_owner(monkeypatch):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def transaction(*args):
        yield MagicMock()

    tenant, business, actor, operation = uuid4(), uuid4(), uuid4(), uuid4()
    service = EditorialContextService(MagicMock(transaction=transaction))
    monkeypatch.setattr(service, "_owner", AsyncMock())
    monkeypatch.setattr(service, "_version", AsyncMock(return_value=None))
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value={"operation_id": operation}))
    result = await service.read(tenant, business, actor)
    assert result.pending_change.operation_id == operation
