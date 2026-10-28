"""Small contract checks independent of the database."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.visual_consent_gate import VisualConsentGate


@pytest.mark.parametrize(
    ("gate", "accepted", "expected"),
    [
        (None, None, "revoked"),
        (None, True, "active"),
        ("active", True, "active"),
        ("revocation_pending", True, "revocation_pending"),
        ("revoked", True, "revoked"),
        ("revocation_pending", False, "revoked"),
    ],
)
async def test_state_never_reactivates_a_withdrawn_authorization(gate, accepted, expected):
    session = AsyncMock()
    session.scalar.side_effect = [gate, accepted]
    service = VisualConsentGate(AsyncMock())
    assert await service._state(session, uuid4(), uuid4()) == expected


async def test_invalid_fence_is_rejected_before_database_access():
    database = AsyncMock()
    service = VisualConsentGate(database)
    with pytest.raises(AuthError, match="VISUAL_ADMISSION_INVALID"):
        await service.admit(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 0)
    database.transaction.assert_not_called()


async def test_admission_refuses_if_grant_disappears_before_it_is_captured():
    result = MagicMock()
    result.mappings.return_value.all.return_value = []
    session = SimpleNamespace(execute=AsyncMock(return_value=result), scalar=AsyncMock(return_value=None))

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    service = VisualConsentGate(SimpleNamespace(transaction=transaction))
    service._lock = AsyncMock()
    service._state = AsyncMock(return_value="active")
    with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
        await service.admit(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 1)


@pytest.mark.parametrize("method", ["enable", "request_withdrawal"])
async def test_contract_manages_visual_processing_without_changing_legacy_grants(monkeypatch, method):
    session = SimpleNamespace(execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    service = VisualConsentGate(SimpleNamespace(transaction=transaction))
    service._lock = AsyncMock()
    monkeypatch.setattr("app.services.visual_consent_gate.service_agreement_accepted", AsyncMock(return_value=True))
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
        await getattr(service, method)(uuid4(), uuid4(), uuid4())
    session.execute.assert_not_awaited()
