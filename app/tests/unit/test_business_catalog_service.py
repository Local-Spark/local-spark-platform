"""The replay after acquiring an operation lock must return the persisted result."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.schemas.business_catalog import CatalogRead, CatalogUpdate
from app.services.business_catalog import BusinessCatalogService


async def test_catalog_rechecks_replay_after_waiting_for_the_operation_lock(monkeypatch):
    session = Mock(execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    service = BusinessCatalogService(Mock(transaction=transaction))
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", AsyncMock())
    replay = CatalogRead(version=7)
    monkeypatch.setattr(service, "_replay", AsyncMock(side_effect=[None, replay]))
    result = await service.update(uuid4(), uuid4(), uuid4(), CatalogUpdate(operation_id=uuid4(), expected_version=0))
    assert result == replay
    assert "pg_advisory_xact_lock" in str(session.execute.await_args.args[0])
    assert session.execute.await_count == 1


def _result(row=None, rows=None):
    mappings = Mock()
    mappings.one_or_none.return_value = row
    mappings.one.return_value = row
    mappings.all.return_value = rows or []
    return Mock(mappings=Mock(return_value=mappings))


def _service(session):
    @asynccontextmanager
    async def transaction(*_args):
        yield session

    return BusinessCatalogService(Mock(transaction=transaction))


async def test_catalog_reads_history_and_replay_conflicts(monkeypatch):
    from datetime import UTC, datetime

    import pytest

    from app.services.auth import AuthError
    from app.services.business_catalog import _digest

    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = CatalogUpdate(operation_id=uuid4(), expected_version=0)
    created = datetime.now(UTC)
    row = {
        "business_id": business,
        "version": 1,
        "document": {"offerings": [], "promotions": []},
        "created_at": created,
        "request_hash": _digest(payload),
    }
    session = Mock(execute=AsyncMock())
    service = _service(session)
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", AsyncMock())
    session.execute.return_value = _result()
    with pytest.raises(AuthError, match="CATALOG_VERSION_NOT_FOUND"):
        await service.read(tenant, business, actor, 1)
    session.execute.return_value = _result(row)
    assert (await service.read(tenant, business, actor)).version == 1
    session.execute.return_value = _result(rows=[{"version": 1, "created_at": created, "actor_id": actor}])
    assert (await service.history(tenant, business, actor))[0].actor_id == actor
    session.execute.return_value = _result(row)
    with pytest.raises(AuthError, match="CATALOG_OPERATION_CONFLICT"):
        await service._replay(session, tenant, uuid4(), payload)
    with pytest.raises(AuthError, match="CATALOG_OPERATION_CONFLICT"):
        await service._replay(session, tenant, business, payload.model_copy(update={"expected_version": 1}))
    assert (await service._replay(session, tenant, business, payload)).version == 1


async def test_catalog_mutation_replay_stale_archive_and_success(monkeypatch):
    from datetime import UTC, datetime

    import pytest

    from app.services.auth import AuthError

    session = Mock(execute=AsyncMock(), scalar=AsyncMock())
    service = _service(session)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = CatalogUpdate(operation_id=uuid4(), expected_version=0)
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", AsyncMock())
    replay = AsyncMock(return_value=CatalogRead(version=1))
    monkeypatch.setattr(service, "_replay", replay)
    assert (await service.update(tenant, business, actor, payload)).version == 1
    replay.return_value = None
    session.scalar.return_value = None
    with pytest.raises(AuthError, match="CATALOG_VERSION_CONFLICT"):
        await service.update(tenant, business, actor, payload)
    session.scalar.return_value = 2
    source = AsyncMock(return_value={"document": {"offerings": [{"id": str(uuid4())}], "promotions": []}})
    monkeypatch.setattr(service, "_version", source)
    with pytest.raises(AuthError, match="CATALOG_ARCHIVE_REQUIRED"):
        await service.update(tenant, business, actor, payload)
    source.return_value = {"document": {"offerings": [], "promotions": []}}
    session.execute.return_value = _result(
        {"version": 2, "document": {"offerings": [], "promotions": []}, "created_at": datetime.now(UTC)}
    )
    assert (await service.update(tenant, business, actor, payload)).version == 2
