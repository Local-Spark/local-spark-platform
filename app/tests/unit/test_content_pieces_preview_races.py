"""Preview import rechecks its authoritative row after reading private bytes."""

import hashlib
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.content_pieces import PieceFromPreview
from app.services import content_pieces
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.tests.unit.test_business_collection_contract import picture


@pytest.mark.parametrize("changed", ["missing", "key", "hash", "format"])
async def test_changed_preview_after_download_never_creates_a_piece(settings, monkeypatch, changed):
    data = picture()
    key = "private/original.png"
    row = {"object_key": key, "sha256": hashlib.sha256(data).hexdigest(), "format": "photo"}
    if changed == "missing":
        row = None
    else:
        row[{"key": "object_key", "hash": "sha256", "format": "format"}[changed]] = "changed"
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = row
    session = Mock(execute=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(*_):
        yield session

    database = Mock(transaction=transaction)
    store = Mock(get_image=AsyncMock(return_value=data))
    monkeypatch.setattr(MediaPreviewService, "file_key", AsyncMock(return_value=key))
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    write = AsyncMock(side_effect=AssertionError("changed preview must not write a version"))
    monkeypatch.setattr(content_pieces, "write_version", write)
    service = content_pieces.ContentPieceService(settings, database, store)
    with pytest.raises(AuthError, match="PIECE_PREVIEW_UNAVAILABLE"):
        await service.from_preview(
            uuid4(), uuid4(), uuid4(), PieceFromPreview(operation_id=uuid4(), preview_id=uuid4())
        )
    store.get_image.assert_awaited_once_with(key)
    write.assert_not_awaited()
    assert session.execute.await_count == 1
