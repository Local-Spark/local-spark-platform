"""Failure, replay and race guards for owner-proven channel binding."""

import hashlib
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError

from app.services.auth import AuthError
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_link import WhatsAppLinkService


def fake_database(session):
    class Database:
        @asynccontextmanager
        async def transaction(self, *_args):
            yield session

        @asynccontextmanager
        async def sessions(self):
            yield session

    return Database()


def result(row):
    query = Mock()
    query.mappings.return_value.one_or_none.return_value = row
    query.mappings.return_value.all.return_value = row
    return query


def config(settings):
    return settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_public_phone": "+5511988887777",
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )


@pytest.mark.asyncio
async def test_owner_phone_guards(settings, monkeypatch):
    session = Mock()
    session.execute = AsyncMock(return_value=result(None))
    service = WhatsAppLinkService(settings, fake_database(session), None)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service._owner_phone(session, tenant, business, actor)
    session.execute.return_value = result({"phone": "+5511999999999", "phone_verified": False})
    with pytest.raises(AuthError, match="PHONE_VERIFICATION_REQUIRED"):
        await service._owner_phone(session, tenant, business, actor)

    async def paid(*_args):
        return {"access_active": True}

    monkeypatch.setattr("app.services.whatsapp_link.billing_status", paid)
    session.execute.return_value = result({"phone": "+5511999999999", "phone_verified": True})
    assert await service._owner_phone(session, tenant, business, actor) == "+5511999999999"


@pytest.mark.asyncio
async def test_status_owner_and_disabled_link(settings):
    session = Mock()
    session.scalar = AsyncMock(side_effect=[None])
    service = WhatsAppLinkService(settings, fake_database(session), None)
    ids = [uuid4() for _ in range(3)]
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.status(*ids)
    session.scalar = AsyncMock(side_effect=[1, False, False])
    assert await service.status(*ids) == {"enabled": False, "linked": False, "pending": False, "destination": None}


@pytest.mark.asyncio
async def test_start_guards(settings, monkeypatch):
    ids = [uuid4() for _ in range(3)]
    service = WhatsAppLinkService(settings, fake_database(Mock()), None)
    with pytest.raises(AuthError, match="WHATSAPP_UNAVAILABLE"):
        await service.start(*ids)
    service.settings = config(settings)
    with pytest.raises(AuthError, match="WHATSAPP_UNAVAILABLE"):
        await service.start(*ids)
    session = Mock()
    session.scalar = AsyncMock(side_effect=[True])
    service.database = fake_database(session)
    service.meta_database = fake_database(session)
    service.settings = service.settings.model_copy(update={"meta_public_phone": None})
    with pytest.raises(AuthError, match="WHATSAPP_DESTINATION_NOT_CONFIGURED"):
        await service.start(*ids)
    service.settings = config(settings)

    async def phone(*_args):
        return "+5511999999999"

    monkeypatch.setattr(service, "_owner_phone", phone)
    session.scalar = AsyncMock(side_effect=[None])
    with pytest.raises(AuthError, match="WHATSAPP_CONSENT_REQUIRED"):
        await service.start(*ids)
    session.scalar = AsyncMock(side_effect=[1, True])
    assert await service.start(*ids) == {"status": "linked"}
    session.scalar = AsyncMock(side_effect=[1, False, uuid4()])
    assert (await service.start(*ids))["status"] == "pending"
    session.scalar = AsyncMock(side_effect=[1, False, None])
    with pytest.raises(AuthError, match="WHATSAPP_LINK_WAIT"):
        await service.start(*ids)


@pytest.mark.asyncio
async def test_find_proof_ignores_untrusted_messages(settings):
    cfg = config(settings)
    cipher = Fernet(cfg.meta_encryption_key.get_secret_value().encode())
    samples = [
        "invalid-ciphertext",
        cipher.encrypt(b"invalid-json").decode(),
        cipher.encrypt(b'{"type":"image"}').decode(),
        cipher.encrypt(b'{"type":"text","text":null}').decode(),
        cipher.encrypt(b'{"type":"text","text":{"body":123}}').decode(),
        cipher.encrypt(b'{"type":"text","text":{"body":"hello"}}').decode(),
        cipher.encrypt(b'{"type":"text","text":{"body":"VINCULAR wrong"}}').decode(),
    ]
    session = Mock()
    session.execute = AsyncMock(return_value=result([{"id": uuid4(), "ciphertext": item} for item in samples]))
    service = WhatsAppLinkService(cfg, fake_database(session), fake_database(session))
    assert await service._find_proof("sender", datetime.now(UTC), hashlib.sha256(b"right").hexdigest()) is None
    assert sender_hash(cfg, "invalid") is None


@pytest.mark.asyncio
async def test_confirm_guards_and_races(settings, monkeypatch):
    cfg = config(settings)
    ids = [uuid4() for _ in range(3)]
    service = WhatsAppLinkService(settings, fake_database(Mock()), None)
    with pytest.raises(AuthError, match="WHATSAPP_UNAVAILABLE"):
        await service.confirm(*ids)
    service.settings = cfg
    with pytest.raises(AuthError, match="WHATSAPP_UNAVAILABLE"):
        await service.confirm(*ids)
    session = Mock()
    service.database = fake_database(session)
    service.meta_database = fake_database(session)

    async def phone(*_args):
        return "+5511999999999"

    monkeypatch.setattr(service, "_owner_phone", phone)
    session.execute = AsyncMock(return_value=result(None))
    session.scalar = AsyncMock(return_value=True)
    assert await service.confirm(*ids) == {"status": "linked"}
    session.scalar = AsyncMock(return_value=False)
    with pytest.raises(AuthError, match="WHATSAPP_LINK_NOT_PENDING"):
        await service.confirm(*ids)

    challenge = {
        "request_id": uuid4(),
        "token_hash": "a" * 64,
        "sender_hash": "b" * 64,
        "created_at": datetime.now(UTC),
    }
    session.execute = AsyncMock(return_value=result(challenge))
    with pytest.raises(AuthError, match="WHATSAPP_LINK_RETRY"):
        await service.confirm(*ids)
    challenge["sender_hash"] = sender_hash(cfg, "+5511999999999")

    async def no_proof(*_args):
        return None

    monkeypatch.setattr(service, "_find_proof", no_proof)
    with pytest.raises(AuthError, match="WHATSAPP_PROOF_NOT_RECEIVED"):
        await service.confirm(*ids)

    async def proof(*_args):
        return uuid4()

    monkeypatch.setattr(service, "_find_proof", proof)
    calls = 0

    async def changed_phone(*_args):
        nonlocal calls
        calls += 1
        return "+5511999999999" if calls == 1 else "+5511888888888"

    monkeypatch.setattr(service, "_owner_phone", changed_phone)
    with pytest.raises(AuthError, match="WHATSAPP_LINK_RETRY"):
        await service.confirm(*ids)
    monkeypatch.setattr(service, "_owner_phone", phone)
    session.scalar = AsyncMock(return_value=None)
    with pytest.raises(AuthError, match="WHATSAPP_LINK_RETRY"):
        await service.confirm(*ids)
    session.scalar = AsyncMock(return_value=uuid4())
    session.execute = AsyncMock(side_effect=[result(challenge), IntegrityError("insert", {}, Exception())])
    with pytest.raises(AuthError, match="WHATSAPP_SENDER_IN_USE"):
        await service.confirm(*ids)
