"""Defensive request and render branches under concurrent database changes."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.media_previews import PreviewRequest
from app.services import media_retention
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService, RenderInputs
from app.services.media_retention import PreviewPurgeClaim
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _result(row):
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = row
    result.mappings.return_value.one.return_value = row
    return result


def _database(rows):
    session = Mock()
    session.execute = AsyncMock(side_effect=[_result(row) for row in rows])

    @asynccontextmanager
    async def opened(*_):
        yield session

    session.begin = opened
    return Mock(transaction=opened, sessions=opened), session


async def test_concurrent_operation_conflict_is_detected_after_insert_race(settings, monkeypatch):
    tenant, business, actor, proposal, operation = [uuid4() for _ in range(5)]
    row = {"operation_id": operation, "request_hash": "another-hash"}
    database, _ = _database(
        [None, {"context_version": 1, "expires_at": datetime.now(UTC) + timedelta(days=1)}, None, row]
    )
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(
        service,
        "_inputs",
        AsyncMock(return_value=RenderInputs("Test", "#6557ed", "photo", "Fato.", None, None, None, uuid4(), "a" * 64)),
    )
    with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
        await service.request(tenant, business, actor, PreviewRequest(operation_id=operation, proposal_id=proposal))


async def test_proposal_removed_after_claim_fails_without_render(settings, monkeypatch):
    preview, proposal = uuid4(), uuid4()
    database, _ = _database([{"proposal_id": proposal}, None])
    service = MediaPreviewService(settings, database)
    failed = AsyncMock(return_value="skipped")
    monkeypatch.setattr(service, "_fail", failed)
    assert await service.render(preview, 3) == "skipped"
    failed.assert_awaited_once_with(preview, 3, "PROPOSAL_NOT_FOUND", False)


async def test_purge_does_not_count_superseded_claim(monkeypatch):
    claim = PreviewPurgeClaim(uuid4(), uuid4(), 2, "previews/key.jpg")
    monkeypatch.setattr(media_retention, "claim_expired_previews", AsyncMock(return_value=[claim]))
    monkeypatch.setattr(media_retention, "finish_preview_purge", AsyncMock(return_value=False))
    store = AsyncMock()
    assert await media_retention.purge_expired_previews(Mock(), store, claim.owner) == 0
    store.delete.assert_awaited_once_with(claim.object_key)
