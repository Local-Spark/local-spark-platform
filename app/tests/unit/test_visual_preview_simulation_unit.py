"""Failure and replay behavior of the explicitly simulated visual pipeline."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService, _digest, _visual_render_key
from app.tests.unit.test_media_preview_races import _database


def test_simulation_is_development_only_and_adjustment_is_not_supported(settings):
    cfg = settings.model_copy(update={"visual_ai_mode": "fake", "environment": "staging"})
    with pytest.raises(ValueError, match="Fake visual AI"):
        cfg.editorial_ai_safety()
    with pytest.raises(ValidationError, match="VISUAL_ADJUSTMENT_UNAVAILABLE"):
        PreviewRequest(
            operation_id=uuid4(), proposal_id=uuid4(), generation_mode="visual_fake", parent_preview_id=uuid4()
        )


@pytest.fixture
def visual_case(settings, monkeypatch):
    tenant, business, actor, proposal, operation, source = [uuid4() for _ in range(6)]
    context = SimpleNamespace(fingerprint="f" * 64, context_version=1, script_version=1, source_asset_id=source)
    prepared = SimpleNamespace(
        context=context, request_hash="a" * 64, request=SimpleNamespace(size="1024x1280", model="test")
    )
    cfg = settings.model_copy(update={"visual_ai_mode": "fake", "visual_ai_monthly_budget_usd_micros": 100})
    prepare = AsyncMock(return_value=prepared)
    monkeypatch.setattr("app.services.visual_requests.VisualRequestService.prepare", prepare)
    monkeypatch.setattr("app.services.visual_context.VisualContextService.capture", AsyncMock(return_value=context))
    monkeypatch.setattr("app.services.media_previews.WhatsAppMaterialsService._require_owner", AsyncMock())
    monkeypatch.setattr("app.services.media_previews._audit", AsyncMock())
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.status", AsyncMock(return_value="active"))
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate._lock", AsyncMock())
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate._state", AsyncMock(return_value="active"))
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.admit", AsyncMock(return_value=True))
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.finish", AsyncMock(return_value="active"))
    monkeypatch.setattr("app.services.media_previews.PreviewRead.model_validate", lambda row: row)
    row = {
        "tenant_id": tenant,
        "business_id": business,
        "actor_id": actor,
        "proposal_id": proposal,
        "operation_id": operation,
        "render_key": _visual_render_key(context.fingerprint, operation, True),
        "visual_fingerprint": context.fingerprint,
        "candidate": True,
        "generation_mode": "visual_fake",
    }
    body = PreviewRequest(operation_id=operation, proposal_id=proposal, generation_mode="visual_fake")
    return SimpleNamespace(
        tenant=tenant,
        business=business,
        actor=actor,
        proposal=proposal,
        operation=operation,
        prepared=prepared,
        prepare=prepare,
        cfg=cfg,
        row=row,
        body=body,
    )


async def test_withdrawal_blocks_queued_visual_before_any_photo_is_loaded(visual_case, monkeypatch):
    c = visual_case
    monkeypatch.setattr(
        "app.services.visual_consent_gate.VisualConsentGate.status", AsyncMock(return_value="revocation_pending")
    )
    db, _ = _database([])
    with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
        await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    c.prepare.assert_not_awaited()

    monkeypatch.setattr(
        "app.services.visual_consent_gate.VisualConsentGate.admit",
        AsyncMock(side_effect=AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)),
    )
    db, _ = _database([c.row])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_visual_fake(uuid4(), 1) == "failed"
    c.prepare.assert_not_awaited()
    service._fail.assert_awaited_once_with(service._fail.await_args.args[0], 1, "VISUAL_AI_CONSENT_REQUIRED", False)


async def test_existing_admission_never_starts_a_second_execution(visual_case, monkeypatch):
    c = visual_case
    admit = AsyncMock(return_value=False)
    finish = AsyncMock()
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.admit", admit)
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.finish", finish)
    db, _ = _database([c.row])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_visual_fake(uuid4(), 1) == "failed"
    c.prepare.assert_not_awaited()
    finish.assert_not_awaited()


async def test_queue_creation_rechecks_consent_under_business_lock(visual_case, monkeypatch):
    c = visual_case
    monkeypatch.setattr(
        "app.services.visual_consent_gate.VisualConsentGate._state", AsyncMock(return_value="revocation_pending")
    )
    db, _ = _database([])
    with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
        await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    c.prepare.assert_not_awaited()


async def test_read_only_validation_passes_preview_identity_to_context(visual_case, monkeypatch):
    c = visual_case
    row = {**c.row, "id": uuid4()}
    capture = AsyncMock(return_value=c.prepared.context)
    monkeypatch.setattr("app.services.visual_context.VisualContextService.capture", capture)
    db, _ = _database([])
    await MediaPreviewService(c.cfg, db)._validate_visual(row, c.actor, view_only=True)
    assert capture.await_args.kwargs["completed_preview_id"] == row["id"]


async def test_interrupted_admitted_execution_stays_unresolved(visual_case, monkeypatch):
    c = visual_case
    finish = AsyncMock()
    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate.finish", finish)
    c.prepare.side_effect = asyncio.CancelledError
    db, _ = _database([c.row])
    with pytest.raises(asyncio.CancelledError):
        await MediaPreviewService(c.cfg, db, AsyncMock())._render_visual_fake(uuid4(), 1)
    finish.assert_not_awaited()


async def test_visual_request_disabled_and_replay_conflicts(settings, visual_case):
    c = visual_case
    db, _ = _database([])
    disabled = MediaPreviewService(settings, db)
    with pytest.raises(AuthError, match="VISUAL_FAKE_DISABLED"):
        await disabled.request(c.tenant, c.business, c.actor, c.body)
    request_hash = _digest({"proposal": c.proposal, "mode": "visual_fake", "candidate": True})
    for changes in (
        {"request_hash": "other", "render_key": c.row["render_key"]},
        {"request_hash": request_hash, "render_key": "other"},
    ):
        db, _ = _database([changes])
        service = MediaPreviewService(c.cfg, db)
        with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
            await service.request_candidate(c.tenant, c.business, c.actor, c.body)
    db, _ = _database([None, None])
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    db, _ = _database([None, {"expires_at": datetime.now(UTC) + timedelta(hours=1)}, None, None])
    with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
        await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    for changed in (
        {"request_hash": "bad", "render_key": c.row["render_key"]},
        {"request_hash": request_hash, "render_key": "bad"},
    ):
        db, _ = _database([None, {"expires_at": datetime.now(UTC) + timedelta(hours=1)}, None, changed])
        with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
            await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    matching = {"request_hash": request_hash, "render_key": c.row["render_key"]}
    db, _ = _database([None, {"expires_at": datetime.now(UTC) + timedelta(hours=1)}, None, matching])
    assert await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body) == matching


async def test_new_visual_request_is_recorded_and_audited(visual_case):
    from app.services import media_previews

    c = visual_case
    created = {"id": uuid4(), "request_hash": "new", "render_key": c.row["render_key"]}
    db, session = _database([None, {"expires_at": datetime.now(UTC) + timedelta(hours=1)}, created])
    result = await MediaPreviewService(c.cfg, db).request_candidate(c.tenant, c.business, c.actor, c.body)
    assert result is created
    media_previews._audit.assert_awaited_once_with(session, created, "media.preview_requested")


async def test_visual_validation_fails_closed_on_mode_and_changed_context(settings, monkeypatch, visual_case):
    c = visual_case
    db, _ = _database([])
    service = MediaPreviewService(c.cfg, db)
    with pytest.raises(AuthError, match="VISUAL_FAKE_DISABLED"):
        await MediaPreviewService(settings, db)._validate_visual(c.row, c.actor)
    with pytest.raises(AuthError, match="VISUAL_FAKE_DISABLED"):
        await service._validate_visual({**c.row, "generation_mode": "local"}, c.actor)
    monkeypatch.setattr(
        "app.services.visual_context.VisualContextService.capture",
        AsyncMock(return_value=SimpleNamespace(fingerprint="different")),
    )
    with pytest.raises(AuthError, match="PREVIEW_INPUT_CHANGED"):
        await service._validate_visual(c.row, c.actor)


async def test_visual_render_guards_replays_changed_sources_and_fence(settings, monkeypatch, visual_case):
    c = visual_case
    preview = uuid4()
    db, _ = _database([])
    service = MediaPreviewService(settings, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_visual_fake(preview, 1) == "failed"
    service._fail.assert_awaited_once_with(preview, 1, "VISUAL_FAKE_DISABLED", False)
    db, _ = _database([None])
    assert await MediaPreviewService(c.cfg, db, AsyncMock())._render_visual_fake(preview, 1) == "skipped"
    db, _ = _database([c.row])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    original_context = c.prepared.context
    c.prepared.context = SimpleNamespace(fingerprint="changed")
    assert await service._render_visual_fake(preview, 1) == "failed"
    service._fail.assert_awaited_once_with(preview, 1, "PREVIEW_INPUT_CHANGED", False)
    c.prepared.context = original_context
    reserve = AsyncMock(return_value=SimpleNamespace(created=False))
    monkeypatch.setattr("app.services.visual_attempts.VisualAttemptService.reserve", reserve)
    db, _ = _database([c.row])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_visual_fake(preview, 1) == "failed"
    service._fail.assert_awaited_once_with(preview, 1, "VISUAL_OUTCOME_UNCERTAIN", False)
    reserve.return_value = SimpleNamespace(created=True, reservation=SimpleNamespace(id=uuid4()))
    finish = AsyncMock()
    monkeypatch.setattr("app.services.visual_cost_ledger.VisualCostLedger.finish", finish)
    changed = SimpleNamespace(request_hash="different")
    c.prepare.side_effect = [c.prepared, changed]
    db, _ = _database([c.row])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_visual_fake(preview, 1) == "failed"
    service._fail.assert_awaited_once_with(preview, 1, "PREVIEW_INPUT_CHANGED", False)
    finish.assert_awaited_once()
    c.prepare.side_effect = None
    db, _ = _database([c.row, None])
    service = MediaPreviewService(c.cfg, db, AsyncMock())
    assert await service._render_visual_fake(preview, 1) == "skipped"
    service.store.delete.assert_awaited_once()


async def test_cleanup_failure_does_not_override_preview_failure(visual_case, monkeypatch):
    c = visual_case
    db, _ = _database([c.row])
    store = AsyncMock()
    store.put.side_effect = AuthError("SIMULATED_STORAGE_FAILURE", 409)
    store.delete.side_effect = RuntimeError("cleanup unavailable")
    service = MediaPreviewService(c.cfg, db, store)
    service._fail = AsyncMock(return_value="failed")
    monkeypatch.setattr(
        "app.services.visual_attempts.VisualAttemptService.reserve",
        AsyncMock(return_value=SimpleNamespace(created=True, reservation=SimpleNamespace(id=uuid4()))),
    )
    monkeypatch.setattr("app.services.visual_cost_ledger.VisualCostLedger.finish", AsyncMock())
    assert await service._render_visual_fake(uuid4(), 1) == "failed"
    service._fail.assert_awaited_once()
    store.delete.assert_awaited_once()
