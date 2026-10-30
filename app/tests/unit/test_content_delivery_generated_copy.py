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
