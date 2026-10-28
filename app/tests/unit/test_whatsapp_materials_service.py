"""Consent audit and unreadable receipt safeguards."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


@pytest.fixture(autouse=True)
def legacy_agreement(monkeypatch):
    monkeypatch.setattr("app.services.whatsapp_materials.service_agreement_accepted", AsyncMock(return_value=False))


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
    audits = [call for call in session.execute.await_args_list if "INSERT INTO audit_events" in str(call.args[0])]
    assert len(audits) == 2


async def test_repeated_consent_actions_do_not_duplicate_audit(settings):
    ids = [uuid4() for _ in range(3)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, None, 1, None])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    assert await service.accept_consent(*ids) == {"accepted": True}
    assert await service.revoke_consent(*ids) == {"accepted": False}
    assert not any("INSERT INTO audit_events" in str(call.args[0]) for call in session.execute.await_args_list)


async def test_audio_consent_is_owner_only_audited_and_requires_material_consent(settings):
    ids = [uuid4() for _ in range(3)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[None, 1, True, 1, ids[1], 1, ids[1], 1, None, False, 1, None, None])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.audio_consent_status(*ids)
    assert await service.audio_consent_status(*ids) == {"accepted": True}
    assert await service.set_audio_consent(*ids, True) == {"accepted": True}
    assert await service.set_audio_consent(*ids, False) == {"accepted": False}
    assert await service.set_audio_consent(*ids, False) == {"accepted": False}
    with pytest.raises(AuthError, match="WHATSAPP_CONSENT_REQUIRED"):
        await service.set_audio_consent(*ids, True)


async def test_material_deletion_is_rejected_without_side_effects(settings):
    tenant, business, actor, event = [uuid4() for _ in range(4)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, 1])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    with pytest.raises(AuthError, match="WHATSAPP_MATERIAL_DELETE_UNAVAILABLE") as error:
        await service.delete_material(tenant, business, actor, event)
    assert error.value.status == 409
    session.execute.assert_not_awaited()


async def test_deleting_missing_material_does_not_disclose_other_businesses(settings):
    tenant, business, actor, event = [uuid4() for _ in range(4)]
    session = Mock()
    session.scalar = AsyncMock(side_effect=[1, None])
    session.execute = AsyncMock()
    service = WhatsAppMaterialsService(settings, database_with(session))
    with pytest.raises(AuthError, match="MATERIAL_NOT_FOUND"):
        await service.delete_material(tenant, business, actor, event)
    session.execute.assert_not_awaited()


def test_receipt_hides_corrupt_or_unavailable_content():
    row = {
        "id": uuid4(),
        "group_id": uuid4(),
        "kind": "text",
        "state": "processed",
        "created_at": "now",
        "error_code": None,
        "ciphertext": "bad-token",
        "transcript_ciphertext": "bad-token",
        "transcription_state": "uncertain",
        "object_key": None,
        "mime_type": None,
        "size_bytes": None,
    }
    cipher = Fernet(Fernet.generate_key())
    assert WhatsAppMaterialsService._present(row, cipher)["text"] is None
    assert WhatsAppMaterialsService._present(row, None)["text"] is None
    assert WhatsAppMaterialsService._present({**row, "ciphertext": None}, cipher)["text"] is None
    assert WhatsAppMaterialsService._present(row, cipher)["transcript"] is None
    assert WhatsAppMaterialsService._present({**row, "transcript_ciphertext": None}, cipher)["transcript"] is None
    good = cipher.encrypt(b"Promocao amanha").decode()
    shown = WhatsAppMaterialsService._present({**row, "transcript_ciphertext": good}, cipher)
    assert shown["transcript"] == "Promocao amanha"


@pytest.mark.parametrize("action", ["audio", "accept", "revoke"])
async def test_individual_mutations_cannot_change_processing_after_agreement(settings, monkeypatch, action):
    ids = [uuid4() for _ in range(3)]
    session = Mock(scalar=AsyncMock(return_value=1), execute=AsyncMock())
    service = WhatsAppMaterialsService(settings, database_with(session))
    monkeypatch.setattr("app.services.whatsapp_materials.service_agreement_accepted", AsyncMock(return_value=True))
    mutation = {
        "audio": lambda: service.set_audio_consent(*ids, False),
        "accept": lambda: service.accept_consent(*ids),
        "revoke": lambda: service.revoke_consent(*ids),
    }[action]
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
        await mutation()
    assert all("UPDATE" not in str(call.args[0]) for call in session.execute.await_args_list)
