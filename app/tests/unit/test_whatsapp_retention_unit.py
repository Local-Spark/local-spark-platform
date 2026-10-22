"""Purge skips object storage for text and tolerates stale ownership."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.services import whatsapp_retention as module
from app.services.whatsapp_retention import PurgeClaim, UploadClaim


async def test_purge_text_with_stale_claim(monkeypatch):
    claim = PurgeClaim(uuid4(), uuid4(), uuid4(), None, 3)
    monkeypatch.setattr(module, "purge_expired_raw", AsyncMock())
    monkeypatch.setattr(module, "reconcile_uploads", AsyncMock(return_value=0))
    monkeypatch.setattr(module, "claim_expired_assets", AsyncMock(return_value=[claim]))
    finish = AsyncMock(return_value=False)
    monkeypatch.setattr(module, "finish_purge", finish)
    store = AsyncMock()
    assert await module.purge_once(Mock(), store, uuid4()) == 0
    store.delete.assert_not_awaited()
    finish.assert_awaited_once()


async def test_reconciler_keeps_intent_when_claim_was_replaced(monkeypatch):
    claim = UploadClaim(uuid4(), "private/attempt", 2)
    monkeypatch.setattr(module, "claim_upload_intents", AsyncMock(return_value=[claim]))
    monkeypatch.setattr(module, "finish_upload_reconcile", AsyncMock(return_value=False))
    store = AsyncMock()
    assert await module.reconcile_uploads(Mock(), store, uuid4()) == 0
    store.delete.assert_awaited_once_with("private/attempt")
