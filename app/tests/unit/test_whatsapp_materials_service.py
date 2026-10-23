"""Consent audit and unreadable receipt safeguards."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


def database_with(session):
    @asynccontextmanager
    async def transaction(*_args):
        yield session

    return Mock(transaction=transaction)


async def test_owner_required_and_changes_are_audited(settings):
    ids = [uuid4() for _ in range(3)]
    session = Mock()
    session.scalar = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.consent_status(*ids)

    session.scalar.side_effect = [1, ids[1], 1, ids[1]]
    assert await service.accept_consent(*ids) == {"accepted": True}
    assert await service.revoke_consent(*ids) == {"accepted": False}
    assert session.execute.await_count == 3


async def test_repeated_consent_actions_do_not_duplicate_audit(settings):
    ids = [uuid4() for _ in range(3)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, None, 1, None])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    assert await service.accept_consent(*ids) == {"accepted": True}
    assert await service.revoke_consent(*ids) == {"accepted": False}
    session.execute.assert_not_awaited()


async def test_delete_material_replay_and_missing_record(settings):
    tenant, business, actor, event = [uuid4() for _ in range(4)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, None, 1, 1, None, None])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    assert await service.delete_material(tenant, business, actor, event) == {"status": "scheduled"}
    with pytest.raises(AuthError, match="MATERIAL_NOT_FOUND"):
        await service.delete_material(tenant, business, actor, event)
    session.execute.assert_not_awaited()


async def test_delete_material_first_request_records_audit(settings):
    tenant, business, actor, event = [uuid4() for _ in range(4)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, event])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    assert await service.delete_material(tenant, business, actor, event) == {"status": "scheduled"}
    session.execute.assert_awaited_once()


def test_receipt_hides_corrupt_or_unavailable_content():
    row = {
        "id": uuid4(),
        "group_id": uuid4(),
        "kind": "text",
        "state": "processed",
        "created_at": "now",
        "error_code": None,
        "ciphertext": "bad-token",
        "object_key": None,
        "mime_type": None,
        "size_bytes": None,
    }
    cipher = Fernet(Fernet.generate_key())
    assert WhatsAppMaterialsService._present(row, cipher)["text"] is None
    assert WhatsAppMaterialsService._present(row, None)["text"] is None
    assert WhatsAppMaterialsService._present({**row, "ciphertext": None}, cipher)["text"] is None
