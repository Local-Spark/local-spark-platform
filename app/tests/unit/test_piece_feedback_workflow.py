"""Feedback is optional learning data; lab approval cannot approve production."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.piece_feedback import LabPieceApproval, PieceFeedbackWrite
from app.services import lab_piece_approval, piece_feedback
from app.services.auth import AuthError


class Database:
    def __init__(self, session):
        self.session = session

    @asynccontextmanager
    async def transaction(self, *args):
        yield self.session


def test_feedback_accepts_free_text_without_encoding_a_fixed_preference():
    body = PieceFeedbackWrite(operation_id=uuid4(), version_id=uuid4(), note="Gostei da posição do logo")
    assert body.note == "Gostei da posição do logo"
    with pytest.raises(ValidationError):
        PieceFeedbackWrite(operation_id=uuid4(), version_id=uuid4(), note="   ")


@pytest.mark.parametrize("state,origin", [("running", "lab"), ("completed", "whatsapp")])
async def test_lab_approval_rejects_active_or_productive_run(settings, monkeypatch, state, origin):
    session = SimpleNamespace(execute=AsyncMock())
    svc = lab_piece_approval.LabPieceApprovalService(settings, Database(session))
    monkeypatch.setattr(lab_piece_approval, "require_lab_access", AsyncMock())
    svc.execution.guard = AsyncMock(return_value={"origin": origin, "state": state})
    with pytest.raises(AuthError) as error:
        await svc.approve(uuid4(), uuid4(), LabPieceApproval(operation_id=uuid4(), version_id=uuid4(), sha256="a" * 64))
    assert error.value.code == "LAB_COMPLETED_PIECE_REQUIRED"
    session.execute.assert_not_awaited()


async def test_feedback_requires_an_actual_approved_version(settings, monkeypatch):
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = None
    session = SimpleNamespace(execute=AsyncMock(return_value=result), scalar=AsyncMock(return_value=None))
    svc = piece_feedback.PieceFeedbackService(settings, Database(session))
    svc.cipher = SimpleNamespace(fingerprint=lambda value: "a" * 64)
    monkeypatch.setattr(piece_feedback.WhatsAppMaterialsService, "_require_owner", AsyncMock())
    event = AsyncMock()
    monkeypatch.setattr(piece_feedback, "_event", event)
    with pytest.raises(AuthError) as error:
        await svc.record(
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
            PieceFeedbackWrite(operation_id=uuid4(), version_id=uuid4(), note="Gostei muito"),
        )
    assert error.value.code == "FEEDBACK_APPROVED_VERSION_REQUIRED"
    event.assert_not_awaited()
