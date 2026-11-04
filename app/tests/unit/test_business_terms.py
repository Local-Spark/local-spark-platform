"""Business terms keep legacy request hashes and explicit field presence."""

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.editorial_context import (
    ContextContent,
    ContextRead,
    ContextRestore,
    ContextUpdate,
    EditorialPreferences,
)
from app.services.editorial_context import EditorialContextService, _digest, _preserve_omitted_business_terms


def test_terms_preserve_unicode_order_and_trim_borders():
    preferences = EditorialPreferences.model_validate({"business_terms": ["  cafe\u0301  ", " Padaria ", "Doces"]})
    assert preferences.business_terms == ["café", "Padaria", "Doces"]
    assert "business_terms" in preferences.model_fields_set
    assert "business_terms" not in EditorialPreferences.model_validate({}).model_fields_set


@pytest.mark.parametrize("terms", [["  "], ["x" * 101], ["x"] * 51, ["cafe\u0301", "CAFÉ"], [" Padaria ", "padaria"]])
def test_invalid_or_duplicate_terms_rejected(terms):
    with pytest.raises(ValidationError):
        EditorialPreferences.model_validate({"business_terms": terms})


def test_fifty_hundred_character_terms_are_permitted():
    terms = [f"{i:02d}" + "x" * 98 for i in range(50)]
    assert EditorialPreferences.model_validate({"business_terms": terms}).business_terms == terms


def test_legacy_hash_is_stable_but_omission_and_explicit_clear_are_distinct():
    op = uuid4()
    omitted = ContextUpdate.model_validate({"expected_version": 0, "operation_id": op})
    cleared = ContextUpdate.model_validate(
        {"expected_version": 0, "operation_id": op, "preferences": {"business_terms": []}}
    )
    legacy = omitted.model_dump(mode="json")
    legacy["preferences"].pop("business_terms")
    legacy["preferences"].pop("business_characteristics")
    legacy["preferences"].pop("cta_destination")
    legacy["preferences"].pop("reference_search")
    encoded = json.dumps(legacy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert _digest(omitted) == hashlib.sha256(encoded.encode()).hexdigest()
    assert _digest(omitted) != _digest(cleared)


def test_omitted_terms_are_preserved_and_explicit_clear_is_respected():
    previous = ContextRead.model_validate({"version": 1, "preferences": {"business_terms": ["Café"]}})
    omitted = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"tone": "friendly"}}
    )
    content = ContextContent.model_validate(omitted.model_dump(exclude={"operation_id", "expected_version"}))
    assert _preserve_omitted_business_terms(omitted, content, previous).preferences.business_terms == ["Café"]
    explicit = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"business_terms": []}}
    )
    cleared = ContextContent.model_validate(explicit.model_dump(exclude={"operation_id", "expected_version"}))
    assert _preserve_omitted_business_terms(explicit, cleared, previous).preferences.business_terms == []
    restore = ContextRestore(expected_version=1, target_version=1, operation_id=uuid4())
    old_version = ContextContent.model_validate({"preferences": {"tone": "friendly"}})
    assert _preserve_omitted_business_terms(restore, old_version, previous).preferences.business_terms == ["Café"]
    known_empty = ContextContent.model_validate({"preferences": {"business_terms": []}})
    assert _preserve_omitted_business_terms(restore, known_empty, previous).preferences.business_terms == []


async def test_pending_old_payload_keeps_terms_and_legacy_digest(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"tone": "friendly"}}
    )
    original = payload.model_dump(mode="json")
    original["preferences"].pop("business_terms")
    original["preferences"].pop("business_characteristics")
    current = {"version": 1, "document": {"preferences": {"business_terms": ["Café"]}}, "created_at": None}
    monkeypatch.setattr(EditorialContextService, "_version", AsyncMock(return_value=current))
    save = AsyncMock()
    monkeypatch.setattr(EditorialContextService, "_save", save)
    pending = {
        "kind": "context_update",
        "payload": original,
        "operation_id": payload.operation_id,
        "request_hash": _digest(payload),
        "actor_id": actor,
    }
    await EditorialContextService.apply_pending_in_session(MagicMock(), tenant, business, pending)
    assert save.await_args.args[7].preferences.business_terms == ["Café"]


async def test_pending_restore_preserves_terms_when_history_precedes_field(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextRestore(expected_version=2, target_version=1, operation_id=uuid4())
    historical = {"document": {"preferences": {"tone": "friendly"}}}
    current = {"version": 2, "document": {"preferences": {"business_terms": ["Café"]}}, "created_at": None}
    monkeypatch.setattr(EditorialContextService, "_version", AsyncMock(side_effect=[historical, current]))
    save = AsyncMock()
    monkeypatch.setattr(EditorialContextService, "_save", save)
    pending = {
        "kind": "context_restore",
        "payload": payload.model_dump(mode="json"),
        "operation_id": payload.operation_id,
        "request_hash": _digest(payload),
        "actor_id": actor,
    }
    await EditorialContextService.apply_pending_in_session(MagicMock(), tenant, business, pending)
    assert save.await_args.args[7].preferences.business_terms == ["Café"]
    assert save.await_args.args[7].preferences.tone == "friendly"


async def test_changed_terms_require_no_search_while_unchanged_terms_do_not_lock(monkeypatch):
    from app.services.auth import AuthError
    from app.services.editorial_context import _guard_business_terms_change

    tenant, business = uuid4(), uuid4()
    old = ContextRead.model_validate({"version": 1, "preferences": {"business_terms": ["Café"]}})
    same = ContextContent.model_validate({"preferences": {"business_terms": ["Café"], "tone": "direct"}})
    changed = ContextContent.model_validate({"preferences": {"business_terms": ["Padaria"]}})
    lock = AsyncMock()
    monkeypatch.setattr("app.services.reference_cycles.lock_reference_head", lock)
    session = MagicMock(scalar=AsyncMock(return_value=1))
    await _guard_business_terms_change(session, tenant, business, old, same)
    lock.assert_not_awaited()
    with pytest.raises(AuthError, match="REFERENCE_SEARCH_IN_PROGRESS"):
        await _guard_business_terms_change(session, tenant, business, old, changed)
    session.scalar.return_value = None
    await _guard_business_terms_change(session, tenant, business, old, changed)
    assert lock.await_count == 2


async def test_queued_old_client_update_preserves_terms_and_digest(monkeypatch):
    from app.services.visual_consent_gate import VisualConsentGate
    from app.services.visual_pending_changes import VisualPendingChanges

    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ContextUpdate.model_validate(
        {"expected_version": 1, "operation_id": uuid4(), "preferences": {"tone": "direct"}}
    )
    proposed = ContextContent.model_validate(payload.model_dump(exclude={"operation_id", "expected_version"}))
    row = {"version": 1, "document": {"preferences": {"business_terms": ["Café"]}}, "created_at": None}
    monkeypatch.setattr(EditorialContextService, "_version", AsyncMock(return_value=row))
    monkeypatch.setattr(EditorialContextService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    queue = AsyncMock(return_value=True)
    monkeypatch.setattr(VisualPendingChanges, "enqueue_in_session", queue)
    service = EditorialContextService(MagicMock())
    result = await service._queue_or_save(MagicMock(), tenant, business, actor, payload, proposed, "context_update")
    assert result.pending_change is not None
    stored = queue.await_args.args[8]
    assert "business_terms" not in stored["preferences"]
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
    await EditorialContextService.apply_pending_in_session(MagicMock(), tenant, business, pending)
    assert save.await_args.args[7].preferences.business_terms == ["Café"]
