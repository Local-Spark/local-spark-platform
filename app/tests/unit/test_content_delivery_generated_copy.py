"""Do not send a real-mode candidate when generated editorial copy is incomplete."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.content_deliveries import ContentDeliveryService
from app.services.media_previews import MediaPreviewService


@asynccontextmanager
async def scoped(value):
    yield value


@pytest.mark.parametrize("missing", ["art_text", "caption", "cta", "all"])
async def test_visual_ai_delivery_refuses_missing_generated_copy(settings, monkeypatch, missing):
    tenant, business, actor, event_id, preview_id = [uuid4() for _ in range(5)]
    document = {
        "title": "Croissant",
        "format": "photo",
        "angle": "Conheça o croissant",
        "fact_ids": [],
        "hypotheses": [],
        "questions": [],
        "art_text": "Croissant",
        "caption": "Conheça o croissant",
        "cta": "Envie mensagem",
    }
    for field in ("art_text", "caption", "cta"):
        if missing in {field, "all"}:
            document[field] = None
    event = {"tenant_id": tenant, "business_id": business, "actor_id": actor}
    preview = {
        "id": preview_id,
        "sha256": "a" * 64,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "generation_mode": "visual_ai",
        "document": document,
    }

    def result(value):
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: value))

    session = SimpleNamespace(
        begin=lambda: scoped(None),
        execute=AsyncMock(side_effect=[result(event), result(preview)]),
        scalar=AsyncMock(return_value=None),
    )
    worker = SimpleNamespace(sessions=lambda: scoped(session))
    file_key = AsyncMock(return_value="private/preview.jpg")
    monkeypatch.setattr(MediaPreviewService, "file_key", file_key)
    service = ContentDeliveryService(settings, SimpleNamespace(), worker)
    assert await service.record(event_id, preview_id) is None
    file_key.assert_awaited_once_with(tenant, business, actor, preview_id, review=True)
    assert session.execute.await_count == 2


async def test_historical_simulated_caption_does_not_bypass_current_processing_authority(settings, monkeypatch):
    from cryptography.fernet import Fernet
    from pydantic import SecretStr

    tenant, business, actor, event_id, preview_id, fact_id = [uuid4() for _ in range(6)]
    event = {"tenant_id": tenant, "business_id": business, "actor_id": actor}
    preview = {
        "sha256": "a" * 64,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "generation_mode": "local",
        "document": {
            "title": "Arquivo histórico",
            "hypotheses": [],
            "questions": [],
            "format": "photo",
            "angle": "Registro anterior",
            "fact_ids": [str(fact_id)],
            "script": [
                {
                    "role": "fact",
                    "visual": "brand_card",
                    "on_screen_text": "Croissant.",
                    "voiceover": "Croissant.",
                    "fact_ids": [str(fact_id)],
                }
            ],
        },
    }

    def result(value):
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: value))

    worker_session = SimpleNamespace(
        begin=lambda: scoped(None),
        execute=AsyncMock(side_effect=[result(event), result(preview)]),
        scalar=AsyncMock(return_value=None),
    )
    owner_session = SimpleNamespace(scalar=AsyncMock(return_value=False), execute=AsyncMock())
    worker = SimpleNamespace(sessions=lambda: scoped(worker_session))
    owner = SimpleNamespace(transaction=lambda *_: scoped(owner_session))
    monkeypatch.setattr(MediaPreviewService, "file_key", AsyncMock(return_value="private/history.jpg"))
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    assert await ContentDeliveryService(cfg, owner, worker).record(event_id, preview_id) is None
    owner_session.execute.assert_not_awaited()


@pytest.mark.parametrize("count", [0, 2])
@pytest.mark.parametrize("quoted", [False, True])
async def test_ambiguous_candidate_command_never_decides_or_publishes(settings, monkeypatch, count, quoted):
    from app.services.content_deliveries import apply_candidate_command

    candidates = [{"id": uuid4(), "actor_id": uuid4()} for _ in range(count)]
    session = SimpleNamespace(
        begin=lambda: scoped(None),
        execute=AsyncMock(return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(all=lambda: candidates))),
    )
    worker = SimpleNamespace(sessions=lambda: scoped(session))
    decide = AsyncMock()
    monkeypatch.setattr(ContentDeliveryService, "decide", decide)
    event = {"id": uuid4(), "tenant_id": uuid4(), "business_id": uuid4(), "sender_hash": "a" * 64}
    message = {"text": {"body": "Aprovar"}}
    if quoted:
        message["context"] = {"id": "unknown-provider-message"}
    assert await apply_candidate_command(settings, SimpleNamespace(), worker, event, message)
    decide.assert_not_awaited()


@pytest.mark.parametrize(
    "mode,code", [("local", "PREVIEW_LEGACY_CREATION_DISABLED"), ("visual_fake", "CANDIDATE_INVALID")]
)
async def test_candidate_decision_preserves_legacy_block_and_requires_sha(settings, monkeypatch, mode, code):
    from app.schemas.content_deliveries import ContentDecision
    from app.services.auth import AuthError
    from app.tests.unit.test_media_preview_races import _database

    tenant, business, actor, delivery, preview, proposal = [uuid4() for _ in range(6)]
    row = {
        "kind": "candidate",
        "actor_id": actor,
        "decision_operation_id": None,
        "decision_state": "pending",
        "delivery_state": "delivered",
        "preview_id": preview,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
    }
    artifact = {
        "state": "completed",
        "candidate": True,
        "proposal_id": proposal,
        "generation_mode": mode,
        "emphasis": "balanced",
        "parent_preview_id": None,
        "sha256": None,
    }
    source = {"id": proposal}
    database, session = _database([row, artifact, source])
    monkeypatch.setattr("app.services.content_deliveries.WhatsAppMaterialsService._require_owner", AsyncMock())
    inputs = AsyncMock(side_effect=AuthError("PREVIEW_LEGACY_CREATION_DISABLED", 409))
    monkeypatch.setattr(MediaPreviewService, "_inputs", inputs)
    monkeypatch.setattr(MediaPreviewService, "_validate_visual", AsyncMock())
    with pytest.raises(AuthError, match=code):
        await ContentDeliveryService(settings, database, database).decide(
            tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="request_changes")
        )
    if mode == "local":
        inputs.assert_awaited_once_with(session, source, emphasis="balanced", parent_preview_id=None, candidate=True)
    else:
        inputs.assert_not_awaited()
    assert all(not str(call.args[0]).startswith("UPDATE") for call in session.execute.await_args_list)


@pytest.mark.parametrize("recipe", ["legacy_overlay", "full_piece_v1"])
async def test_invalid_publication_approval_is_blocked(settings, monkeypatch, recipe):
    from app.services.content_deliveries import publish_fake
    from app.tests.unit.test_media_preview_races import _database

    tenant, business, actor, delivery, preview = [uuid4() for _ in range(5)]
    row = {
        "decision_state": "approved",
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "tenant_id": tenant,
        "business_id": business,
        "actor_id": actor,
        "preview_id": preview,
        "caption": "Legenda histórica",
        "scheduled_at": datetime.now(UTC),
        "approved_sha256": "a" * 64,
        "approval_digest": "changed",
        "visual_review_confirmation": {"preview_sha256": "incomplete"},
    }
    artifact = {"sha256": "a" * 64, "generation_mode": "local", "visual_recipe": recipe}
    database, session = _database([row, artifact, row])
    monkeypatch.setattr(MediaPreviewService, "file_key", AsyncMock(return_value="private/historical.jpg"))
    audit = AsyncMock()
    monkeypatch.setattr("app.services.content_deliveries._audit", audit)
    assert await publish_fake(settings, SimpleNamespace(), database, delivery, 3) == "failed"
    update = session.execute.await_args.args[1]
    assert update["state"] == "failed" and update["valid"] is False
    assert audit.await_args.args[2] == "content.publication_blocked"
