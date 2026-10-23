"""Outbound attempts never retry ambiguous Meta results or accept unbound commands."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.services.auth import AuthError
from app.services.whatsapp_replies import ClaimedReply, apply_inbound_command, dispatch_reply


async def test_reply_dispatch_states(settings, monkeypatch):
    import app.services.whatsapp_replies as module

    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_reply_enabled": True,
            "meta_encryption_key": SecretStr(key),
            "meta_access_token": SecretStr("test-token"),
            "meta_graph_version": "v23.0",
            "meta_phone_number_id": "123",
        }
    )
    reply = ClaimedReply(uuid4(), Fernet(key).encrypt(b"5511999999999").decode(), "Confirma?")
    claim = AsyncMock(return_value=reply)
    finish = AsyncMock()
    monkeypatch.setattr(module, "claim_reply", claim)
    monkeypatch.setattr(module, "finish_reply", finish)

    async def case(status, payload):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(status, json=payload))
        ) as http:
            assert await dispatch_reply(Mock(), cfg, http) is True

    await case(400, {"error": {"code": 1}})
    assert finish.await_args.args[2] == "failed"
    await case(503, {"error": {"code": 1}})
    assert finish.await_args.args[2] == "uncertain"
    await case(200, {"messages": [{}]})
    assert finish.await_args.args[2] == "uncertain"
    claim.return_value = None
    async with httpx.AsyncClient() as http:
        assert await dispatch_reply(Mock(), cfg, http) is False
        assert await dispatch_reply(Mock(), cfg.model_copy(update={"meta_reply_enabled": False}), http) is False


async def test_commands_require_unambiguous_prompt(settings, monkeypatch):
    import app.services.whatsapp_replies as module

    row = {"id": uuid4(), "tenant_id": uuid4(), "business_id": uuid4(), "sender_hash": "hash"}
    assert await apply_inbound_command(settings, Mock(), row, {"text": {"body": "Oi"}}) is False

    result = Mock()
    result.mappings.return_value.one_or_none.return_value = None
    result.mappings.return_value.all.return_value = []
    session = AsyncMock()
    session.execute.return_value = result

    @asynccontextmanager
    async def transaction():
        yield session

    database = Mock()

    @asynccontextmanager
    async def sessions():
        yield session

    database.sessions = sessions
    session.begin = transaction
    assert await apply_inbound_command(settings, database, row, {"text": {"body": "Confirmar"}}) is True
    assert (
        await apply_inbound_command(
            settings, database, row, {"text": {"body": "Descartar"}, "context": {"id": "wrong"}}
        )
        is True
    )
    result.mappings.return_value.one_or_none.return_value = {"id": uuid4(), "actor_id": uuid4()}
    owner_db = Mock()
    owner_db.close = AsyncMock()
    monkeypatch.setattr(module, "Database", lambda _: owner_db)
    decide = AsyncMock(side_effect=AuthError("CONTEXT_FACT_LIMIT", 409))
    monkeypatch.setattr(module, "EditorialConversationService", lambda *_: Mock(decide=decide))
    assert (
        await apply_inbound_command(
            settings, database, row, {"text": {"body": "Confirmar"}, "context": {"id": "wamid.test"}}
        )
        is True
    )
    decide.assert_awaited_once()
    owner_db.close.assert_awaited_once()
    decide.reset_mock()
    result.mappings.return_value.all.return_value = [{"id": uuid4(), "actor_id": uuid4()}]
    assert await apply_inbound_command(settings, database, row, {"text": {"body": "Descartar"}}) is True
    assert decide.await_args.args[-1] is False
    decide.reset_mock()
    result.mappings.return_value.all.return_value = [
        {"id": uuid4(), "actor_id": uuid4()},
        {"id": uuid4(), "actor_id": uuid4()},
    ]
    assert await apply_inbound_command(settings, database, row, {"text": {"body": "Confirmar"}}) is True
    decide.assert_not_awaited()
