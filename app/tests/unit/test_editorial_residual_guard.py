"""The retained experimental guard must fail closed for an existing pending marker."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.editorial_consent_scope import VisualRunScope, admitted_visual_run, current_visual_run
from app.services.media_previews import MediaPreviewService


def test_visual_run_scope_is_restored_even_if_processing_fails():
    scope = VisualRunScope(uuid4(), uuid4(), uuid4(), uuid4(), 2)
    assert current_visual_run() is None
    with pytest.raises(RuntimeError, match="failure"):
        with admitted_visual_run(scope):
            assert current_visual_run() == scope
            raise RuntimeError("failure")
    assert current_visual_run() is None


async def test_stored_withdrawal_marker_blocks_preview_before_reading_content(settings):
    session = AsyncMock()
    session.scalar.return_value = 1
    proposal = {
        "state": "completed",
        "document": {},
        "review_state": "accepted",
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
    }
    with pytest.raises(AuthError, match="EDITORIAL_WITHDRAWAL_PENDING") as exc:
        await MediaPreviewService(settings, AsyncMock())._inputs(session, proposal)
    assert exc.value.status == 409
    session.scalar.assert_awaited_once()
    session.execute.assert_not_awaited()
