"""Historical static previews are readable but cannot become new content."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService
from app.tests.unit.test_media_preview_races import _database


def test_new_preview_defaults_to_the_full_visual_pipeline():
    request = PreviewRequest(operation_id=uuid4(), proposal_id=uuid4())
    assert request.generation_mode == "visual_ai"


@pytest.mark.parametrize("format", ["photo", "story"])
async def test_new_legacy_image_request_is_rejected(settings, monkeypatch, format):
    monkeypatch.setattr("app.services.media_previews.WhatsAppMaterialsService._require_owner", AsyncMock())
    database, _ = _database([None, {"document": {"format": format}}])
    service = MediaPreviewService(settings, database)
    request = PreviewRequest(operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local")
    with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
        await service.request(uuid4(), uuid4(), uuid4(), request)


async def test_already_claimed_legacy_image_never_renders(settings):
    preview_id = uuid4()
    database, _ = _database([{"proposal_id": uuid4(), "mime_type": "image/jpeg"}, None])
    service = MediaPreviewService(settings, database)
    service._fail = AsyncMock(return_value="failed")
    assert await service._render_local(preview_id, 1) == "failed"
    service._fail.assert_awaited_once_with(preview_id, 1, "PREVIEW_LEGACY_CREATION_DISABLED", False)
