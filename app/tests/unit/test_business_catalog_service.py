"""The replay after acquiring an operation lock must return the persisted result."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.schemas.business_catalog import CatalogRead, CatalogUpdate
from app.services.business_catalog import BusinessCatalogService, _digest
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges


async def test_catalog_rechecks_replay_after_waiting_for_the_operation_lock(monkeypatch):
    session = Mock(execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    replay = CatalogRead(version=7)
    monkeypatch.setattr(BusinessCatalogService, "_replay", AsyncMock(side_effect=[None, replay]))
    result = await BusinessCatalogService._save_in_session(
        session, uuid4(), uuid4(), uuid4(), CatalogUpdate(operation_id=uuid4(), expected_version=0)
    )
    assert result == replay
    assert "pg_advisory_xact_lock" in str(session.execute.await_args.args[0])
    assert session.execute.await_count == 1


async def test_catalog_applied_operation_replays_without_a_second_write(monkeypatch):
    session = Mock(execute=AsyncMock(), scalar=AsyncMock())
    original = CatalogRead(version=3)
    monkeypatch.setattr(BusinessCatalogService, "_replay", AsyncMock(return_value=original))
    result = await BusinessCatalogService._save_in_session(
        session, uuid4(), uuid4(), uuid4(), CatalogUpdate(operation_id=uuid4(), expected_version=2)
    )
    assert result == original
    session.execute.assert_not_awaited()
    session.scalar.assert_not_awaited()


async def test_catalog_deferred_apply_preserves_archive_invariant(monkeypatch):
    import pytest

    from app.services.auth import AuthError

    session = Mock(execute=AsyncMock(), scalar=AsyncMock(return_value=2))
    payload = CatalogUpdate(operation_id=uuid4(), expected_version=1)
    monkeypatch.setattr(BusinessCatalogService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(
        BusinessCatalogService,
        "_version",
        AsyncMock(return_value={"document": {"offerings": [{"id": str(uuid4())}], "promotions": []}}),
    )
    with pytest.raises(AuthError, match="CATALOG_ARCHIVE_REQUIRED"):
        await BusinessCatalogService._save_in_session(session, uuid4(), uuid4(), uuid4(), payload)


async def test_catalog_rejects_stale_version_before_enqueue(monkeypatch):
    import pytest

    from app.services.auth import AuthError

    session = Mock(execute=AsyncMock())
    service = _service(session)
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", AsyncMock())
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(BusinessCatalogService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(BusinessCatalogService, "_version", AsyncMock(return_value=None))
    enqueue = AsyncMock()
    monkeypatch.setattr(VisualPendingChanges, "enqueue_in_session", enqueue)
    payload = CatalogUpdate(operation_id=uuid4(), expected_version=1)
    with pytest.raises(AuthError, match="CATALOG_VERSION_CONFLICT"):
        await service.update(uuid4(), uuid4(), uuid4(), payload)
    enqueue.assert_not_awaited()


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
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value=None))
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


async def test_catalog_pending_read_and_authenticated_apply(monkeypatch):
    import pytest

    from app.services.auth import AuthError

    tenant, business, actor, operation = uuid4(), uuid4(), uuid4(), uuid4()
    payload = CatalogUpdate(operation_id=operation, expected_version=0)
    session = Mock(execute=AsyncMock())
    service = _service(session)
    owner = AsyncMock()
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", owner)
    monkeypatch.setattr(BusinessCatalogService, "_version", AsyncMock(return_value=None))
    pending = {"operation_id": operation, "status": "failed", "error_code": "CATALOG_VERSION_CONFLICT"}
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value=pending))
    assert (await service.read(tenant, business, actor)).pending_change.error_code == "CATALOG_VERSION_CONFLICT"
    row = {
        "payload": payload.model_dump(mode="json"),
        "actor_id": actor,
        "operation_id": operation,
        "request_hash": _digest(payload),
    }
    save = AsyncMock()
    monkeypatch.setattr(BusinessCatalogService, "_save_in_session", save)
    for invalid in ({**row, "operation_id": uuid4()}, {**row, "request_hash": "x" * 64}):
        with pytest.raises(AuthError, match="VISUAL_CHANGE_OPERATION_CONFLICT"):
            await BusinessCatalogService.apply_pending_in_session(session, tenant, business, invalid)
    await BusinessCatalogService.apply_pending_in_session(session, tenant, business, row)
    owner.assert_awaited_with(session, tenant, business, actor)
    save.assert_awaited_once_with(session, tenant, business, actor, payload)


async def test_catalog_mutation_replay_stale_archive_and_success(monkeypatch):
    from datetime import UTC, datetime

    import pytest

    from app.services.auth import AuthError

    session = Mock(execute=AsyncMock(), scalar=AsyncMock())
    service = _service(session)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = CatalogUpdate(operation_id=uuid4(), expected_version=0)
    monkeypatch.setattr("app.services.business_catalog.require_catalog_owner", AsyncMock())
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(VisualPendingChanges, "enqueue_in_session", AsyncMock(return_value=False))
    replay = AsyncMock(return_value=CatalogRead(version=1))
    monkeypatch.setattr(BusinessCatalogService, "_replay", replay)
    assert (await service.update(tenant, business, actor, payload)).version == 1
    replay.return_value = None
    monkeypatch.setattr(BusinessCatalogService, "_version", AsyncMock(return_value=None))
    session.scalar.return_value = None
    with pytest.raises(AuthError, match="CATALOG_VERSION_CONFLICT"):
        await service.update(tenant, business, actor, payload)
    session.scalar.return_value = 2
    source = AsyncMock(
        return_value={
            "version": 0,
            "created_at": None,
            "document": {"offerings": [{"id": str(uuid4()), "kind": "product", "name": "Café"}], "promotions": []},
        }
    )
    monkeypatch.setattr(BusinessCatalogService, "_version", source)
    with pytest.raises(AuthError, match="CATALOG_ARCHIVE_REQUIRED"):
        await service.update(tenant, business, actor, payload)
    source.return_value = {"version": 0, "created_at": None, "document": {"offerings": [], "promotions": []}}
    session.execute.return_value = _result(
        {"version": 2, "document": {"offerings": [], "promotions": []}, "created_at": datetime.now(UTC)}
    )
    assert (await service.update(tenant, business, actor, payload)).version == 2
