"""No plaintext escapes and the correlator only runs with explicit credentials."""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.entrypoints import whatsapp_correlator
from app.services.whatsapp_routing import material_kind, route_once


def encrypt(cipher, message):
    return cipher.encrypt(json.dumps(message).encode()).decode()


def test_material_classification_rejects_commands_and_malformed_payloads():
    cipher = Fernet(Fernet.generate_key())
    assert material_kind(cipher, "not-ciphertext") is None
    assert material_kind(cipher, cipher.encrypt(b"not-json").decode()) is None
    assert material_kind(cipher, encrypt(cipher, ["text"])) is None
    assert material_kind(cipher, encrypt(cipher, {"type": []})) is None
    assert material_kind(cipher, encrypt(cipher, {"type": "location"})) is None
    assert material_kind(cipher, encrypt(cipher, {"type": "text", "text": "bad"})) is None
    assert material_kind(cipher, encrypt(cipher, {"type": "text", "text": {"body": 1}})) is None
    assert material_kind(cipher, encrypt(cipher, {"type": "text", "text": {"body": " vincular ABC "}})) is None
    assert material_kind(cipher, encrypt(cipher, {"type": "text", "text": {"body": "ideia"}})) == "text"
    for kind in ("audio", "image", "video"):
        assert material_kind(cipher, encrypt(cipher, {"type": kind})) == kind


@pytest.mark.asyncio
async def test_empty_route_still_runs_retention(settings):
    session = Mock()
    query = Mock()
    query.mappings.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=query)

    @asynccontextmanager
    async def begin():
        yield

    session.begin = begin

    class FakeDatabase:
        @asynccontextmanager
        async def sessions(self):
            yield session

    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    assert await route_once(FakeDatabase(), cfg) == 0
    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_route_once_writes_only_supported_messages(settings):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    rows = [
        {
            "id": uuid4(),
            "ciphertext": encrypt(cipher, {"type": "text", "text": {"body": "ideia"}}),
            "expires_at": "expiry",
            "received_at": datetime(2026, 10, 23, 12, tzinfo=UTC),
            "tenant_id": tenant,
            "business_id": business,
            "actor_id": actor,
            "sender_hash": "0" * 64,
        },
        {
            "id": uuid4(),
            "ciphertext": encrypt(cipher, {"type": "text", "text": {"body": "VINCULAR code"}}),
            "expires_at": "expiry",
            "received_at": datetime(2026, 10, 23, 12, tzinfo=UTC),
            "tenant_id": tenant,
            "business_id": business,
            "actor_id": actor,
            "sender_hash": "0" * 64,
        },
    ]
    session = Mock()
    result = Mock()
    result.mappings.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)

    @asynccontextmanager
    async def begin():
        yield

    session.begin = begin

    class FakeDatabase:
        @asynccontextmanager
        async def sessions(self):
            yield session

    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    assert await route_once(FakeDatabase(), cfg) == 1
    assert session.execute.await_count == 7


@pytest.mark.asyncio
async def test_entrypoint_disabled_without_explicit_provider(settings, monkeypatch):
    monkeypatch.setattr(whatsapp_correlator, "get_settings", lambda: settings)
    await whatsapp_correlator.run_correlator()
    cfg = settings.model_copy(update={"meta_webhook_mode": "cloud", "correlator_database_url": None})
    monkeypatch.setattr(whatsapp_correlator, "get_settings", lambda: cfg)
    await whatsapp_correlator.run_correlator()
    cfg = settings.model_copy(update={"meta_webhook_mode": "cloud", "meta_encryption_key": None})
    monkeypatch.setattr(whatsapp_correlator, "get_settings", lambda: cfg)
    await whatsapp_correlator.run_correlator()


@pytest.mark.asyncio
async def test_entrypoint_closes_database_after_loop(settings, monkeypatch):
    cfg = settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "correlator_database_url": SecretStr("postgresql+asyncpg://test"),
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )
    monkeypatch.setattr(whatsapp_correlator, "get_settings", lambda: cfg)
    database = Mock()
    database.close = AsyncMock()
    monkeypatch.setattr(whatsapp_correlator, "Database", lambda *_args, **_kwargs: database)
    monkeypatch.setattr(whatsapp_correlator, "route_once", AsyncMock(side_effect=[0, 2]))
    receipts = AsyncMock(side_effect=[0, 1])
    monkeypatch.setattr(whatsapp_correlator, "process_receipts", receipts)
    calls = 0

    async def stop_after_second(_seconds):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(whatsapp_correlator.asyncio, "sleep", stop_after_second)
    with pytest.raises(asyncio.CancelledError):
        await whatsapp_correlator.run_correlator()
    database.close.assert_awaited_once()
    assert receipts.await_count == 2
