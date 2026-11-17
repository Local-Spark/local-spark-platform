"""New lab snapshots build automatically, including legacy video drafts."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.schemas.creation_lab import LabStart
from app.services.creation_lab_motion_requests import LabMotionRequests


@pytest.mark.parametrize("flow_version", [1, 2])
async def test_video_draft_has_no_construction_approval(settings, fake_database, monkeypatch, flow_version):
    settings.meta_encryption_key = SecretStr(Fernet.generate_key().decode())
    run, source = uuid4(), uuid4()
    requests = LabMotionRequests(settings, fake_database, run)
    monkeypatch.setattr("app.services.message_creation.message_text", lambda *args: "Reel automático")
    requests.context.capture = AsyncMock(return_value={"snapshot": True})
    assert await requests.build_snapshot(
        Mock(),
        {"tenant_id": uuid4(), "business_id": uuid4(), "flow_version": flow_version},
        LabStart(operation_id=uuid4(), source_attachment_id=source),
    ) == {"snapshot": True}
    request = requests.context.capture.await_args.args[3]
    assert request.source_asset_id == source
    assert not request.review_checkpoints
    assert not request.storyboard
