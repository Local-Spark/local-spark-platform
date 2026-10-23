"""Cover context decisions without SQLAlchemy's async greenlet boundary."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.editorial_context import ContextContent, ContextRead, ContextRestore, ContextUpdate
from app.services.auth import AuthError
from app.services.editorial_context import EditorialContextService


def service_with(session):
    @asynccontextmanager
    async def transaction(*_args):
        yield session

    return EditorialContextService(Mock(transaction=transaction))


def result(row=None, rows=None):
    mappings = Mock()
    mappings.one_or_none.return_value = row
    mappings.one.return_value = row
    mappings.all.return_value = rows if rows is not None else []
    return Mock(mappings=Mock(return_value=mappings))


@pytest.mark.asyncio
async def test_read_history_and_replay_paths(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    session = Mock(execute=AsyncMock())
    service = service_with(session)
    monkeypatch.setattr(service, "_owner", AsyncMock())
    row = {
        "version": 1,
        "document": {"facts": [], "preferences": {}},
        "created_at": datetime.now(UTC),
        "request_hash": "hash",
    }
    session.execute.side_effect = [
        result(),
        result(row),
        result(rows=[{"version": 1, "created_at": row["created_at"], "actor_id": actor}]),
        result(),
        result(row),
        result(row),
    ]
    with pytest.raises(AuthError, match="CONTEXT_VERSION_NOT_FOUND"):
        await service.read(tenant, business, actor, 99)
    assert (await service.read(tenant, business, actor)).version == 1
    assert (await service.history(tenant, business, actor))[0].version == 1
    assert await service._replay(session, tenant, business, operation, "hash") is None
    with pytest.raises(AuthError, match="CONTEXT_OPERATION_CONFLICT"):
        await service._replay(session, tenant, business, operation, "different")
    assert (await service._replay(session, tenant, business, operation, "hash")).version == 1


@pytest.mark.asyncio
async def test_save_replay_stale_and_success(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    session = Mock(execute=AsyncMock(), scalar=AsyncMock())
    service = service_with(session)
    content = ContextContent()
    existing = ContextRead(version=1)
    monkeypatch.setattr(service, "_replay", AsyncMock(return_value=existing))
    assert await service._save(session, tenant, business, actor, 0, operation, "hash", content) == existing
    service._replay.side_effect = [None, existing]
    session.scalar.return_value = None
    assert await service._save(session, tenant, business, actor, 0, operation, "hash", content) == existing
    service._replay.side_effect = [None, None]
    with pytest.raises(AuthError, match="CONTEXT_VERSION_CONFLICT"):
        await service._save(session, tenant, business, actor, 0, operation, "hash", content)
    service._replay.side_effect = None
    service._replay.return_value = None
    session.scalar.return_value = 1
    session.execute.side_effect = [
        result(),
        result({"version": 1, "document": content.model_dump(mode="json"), "created_at": datetime.now(UTC)}),
        result(),
    ]
    assert (await service._save(session, tenant, business, actor, 0, operation, "hash", content)).version == 1


@pytest.mark.asyncio
async def test_restore_replay_missing_and_source(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    session = Mock()
    service = service_with(session)
    monkeypatch.setattr(service, "_owner", AsyncMock())
    payload = ContextRestore(expected_version=1, target_version=1, operation_id=operation)
    existing = ContextRead(version=2)
    replay = AsyncMock(return_value=existing)
    source = AsyncMock()
    save = AsyncMock(return_value=existing)
    monkeypatch.setattr(service, "_replay", replay)
    monkeypatch.setattr(service, "_version", source)
    monkeypatch.setattr(service, "_save", save)
    assert await service.restore(tenant, business, actor, payload) == existing
    replay.return_value = None
    source.return_value = None
    with pytest.raises(AuthError, match="CONTEXT_VERSION_NOT_FOUND"):
        await service.restore(tenant, business, actor, payload)
    source.return_value = {"document": ContextContent().model_dump(mode="json")}
    assert await service.restore(tenant, business, actor, payload) == existing
    save.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_delegates_validated_content(monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    service = service_with(Mock())
    monkeypatch.setattr(service, "_owner", AsyncMock())
    save = AsyncMock(return_value=ContextRead(version=1))
    monkeypatch.setattr(service, "_save", save)
    payload = ContextUpdate(expected_version=0, operation_id=operation)
    assert (await service.update(tenant, business, actor, payload)).version == 1
    assert isinstance(save.await_args.args[-1], ContextContent)
