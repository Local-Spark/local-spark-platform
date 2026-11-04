"""The customer supplies only an operation; saved context owns the search scope."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.schemas.reference_execution import ReferenceSearchStart, ReferenceSearchStarted
from app.services import reference_search_start as start
from app.services.auth import AuthError
from app.tests.unit.test_core import access_token
from app.tests.unit.test_reference_execution_wiring import configured


def database(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    inside = []

    @asynccontextmanager
    async def transaction(*args):
        inside.append(True)
        try:
            yield session
        finally:
            inside.pop()

    return SimpleNamespace(transaction=transaction), session, inside


def row(radius=5):
    return {
        "version": 4,
        "document": {
            "preferences": {
                "reference_search": {
                    "scope": "local",
                    "radius_km": radius,
                    "origin": {
                        "method": "device",
                        "coordinates": {"latitude": -23.5, "longitude": -46.6, "confirmed": True},
                    },
                }
            }
        },
    }


def test_start_rejects_client_owned_provider_or_scope_fields():
    for field in ("radius_km", "provider", "budget", "place_id"):
        with pytest.raises(ValidationError):
            ReferenceSearchStart.model_validate({"operation_id": str(uuid4()), field: 5})


async def test_disabled_search_does_not_access_database(settings):
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await start.ReferenceSearchStartService(None, settings).start(
            uuid4(), uuid4(), uuid4(), ReferenceSearchStart(operation_id=uuid4())
        )


@pytest.mark.parametrize(
    "record",
    [
        None,
        {"version": 1, "document": {}},
        {"version": 1, "document": {"preferences": {"reference_search": {"scope": "national"}}}},
        row(10),
    ],
)
async def test_search_requires_a_saved_supported_local_scope(settings, monkeypatch, record):
    db, _, _ = database(record)
    admit = AsyncMock()
    monkeypatch.setattr(start.WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(start, "admit_provider_search", admit)
    with pytest.raises(AuthError, match="REFERENCE_SEARCH_CONTEXT_REQUIRED"):
        await start.ReferenceSearchStartService(db, configured(settings)).start(
            uuid4(), uuid4(), uuid4(), ReferenceSearchStart(operation_id=uuid4())
        )
    admit.assert_not_awaited()


async def test_admission_uses_saved_version_radius_after_releasing_read_transaction(settings, monkeypatch):
    db, _, inside = database(row(20))
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    result = SimpleNamespace(search_id=uuid4(), cycle_id=uuid4(), state="pending")
    owner = AsyncMock()
    ready = configured(settings)

    async def admit(*args):
        assert not inside
        assert args == (
            db,
            ready.reference_provider_hmac_key,
            ready.reference_provider_key_version,
            tenant,
            business,
            actor,
            operation,
            4,
            20,
        )
        return result

    monkeypatch.setattr(start.WhatsAppMaterialsService, "_require_owner", owner)
    monkeypatch.setattr(start, "admit_provider_search", admit)
    response = await start.ReferenceSearchStartService(db, ready).start(
        tenant, business, actor, ReferenceSearchStart(operation_id=operation)
    )
    assert response.search_id == result.search_id and response.cycle_id == result.cycle_id
    owner.assert_awaited_once()


@pytest.mark.parametrize(
    "code",
    [
        "REFERENCE_RADIUS_ALREADY_SEARCHED",
        "REFERENCE_SEARCH_ADMISSION_CONFLICT",
        "REFERENCE_SEARCH_CONTEXT_INVALID",
        "REFERENCE_BUSINESS_IDENTITY_STALE",
        "REFERENCE_BUSINESS_ADDRESS_REQUIRED",
        "REFERENCE_BUSINESS_LOCATION_REQUIRED",
        "unexpected",
    ],
)
async def test_admission_conflicts_are_mapped_without_database_detail(settings, monkeypatch, code):
    db, _, _ = database(row())
    failure = DBAPIError(None, None, Exception(code + " private detail"), False)
    monkeypatch.setattr(start.WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(start, "admit_provider_search", AsyncMock(side_effect=failure))
    with pytest.raises(DBAPIError if code == "unexpected" else AuthError) as caught:
        await start.ReferenceSearchStartService(db, configured(settings)).start(
            uuid4(), uuid4(), uuid4(), ReferenceSearchStart(operation_id=uuid4())
        )
    if code == "unexpected":
        assert caught.value is failure
    else:
        assert caught.value.status == 409 and "private" not in str(caught.value)


def test_start_route_authenticates_and_passes_only_operation(client, settings, monkeypatch):
    tenant, business, actor = [uuid4() for _ in range(3)]
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/reference-results/searches"
    operation = uuid4()
    response = ReferenceSearchStarted(search_id=uuid4(), cycle_id=uuid4(), state="pending")
    invoke = AsyncMock(return_value=response)
    monkeypatch.setattr(start.ReferenceSearchStartService, "start", invoke)
    assert client.post(path, json={"operation_id": str(operation)}).status_code == 401
    result = client.post(
        path,
        json={"operation_id": str(operation)},
        headers={"Authorization": "Bearer " + access_token(settings, actor)},
    )
    assert result.status_code == 200 and result.json() == response.model_dump(mode="json")
    assert invoke.await_args.args[:3] == (tenant, business, actor)
    assert invoke.await_args.args[3].operation_id == operation


async def test_retry_disabled_without_read_or_execution(settings):
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await start.ReferenceSearchStartService(None, settings).retry(
            uuid4(), uuid4(), uuid4(), uuid4(), ReferenceSearchStart(operation_id=uuid4())
        )


async def test_retry_persists_only_search_and_operation_under_requesting_owner(settings):
    from app.tests.unit.test_reference_publication_contracts import _database

    search, operation = uuid4(), uuid4()
    db, session = _database(value={"search_id": str(search), "state": "pending"})
    result = await start.ReferenceSearchStartService(db, configured(settings)).retry(
        uuid4(), uuid4(), uuid4(), search, ReferenceSearchStart(operation_id=operation)
    )
    assert result.search_id == search and result.state == "pending"
    assert session.scalar.await_args.args[1]["operation"] == operation
    assert set(session.scalar.await_args.args[1]) == {"business", "search", "operation"}


@pytest.mark.parametrize(
    "code,status",
    [
        ("REFERENCE_OWNER_INACTIVE", 403),
        ("REFERENCE_RETRY_REQUEST_INVALID", 409),
        ("REFERENCE_RETRY_REQUEST_CONFLICT", 409),
        ("REFERENCE_RETRY_NOT_AVAILABLE", 409),
        ("unexpected", None),
    ],
)
async def test_retry_maps_owner_and_operation_errors(settings, code, status):
    from app.tests.unit.test_reference_publication_contracts import _database

    failure = DBAPIError(None, None, Exception(code + " private detail"), False)
    db, _ = _database(error=failure)
    with pytest.raises(AuthError if status else DBAPIError) as caught:
        await start.ReferenceSearchStartService(db, configured(settings)).retry(
            uuid4(), uuid4(), uuid4(), uuid4(), ReferenceSearchStart(operation_id=uuid4())
        )
    if status:
        assert caught.value.status == status and "private" not in str(caught.value)
    else:
        assert caught.value is failure


def test_retry_route_uses_authenticated_actor_and_explicit_search(client, settings, monkeypatch):
    from app.schemas.reference_execution import ReferenceSearchRetried

    tenant, business, actor, search, operation = [uuid4() for _ in range(5)]
    invoke = AsyncMock(return_value=ReferenceSearchRetried(search_id=search, state="pending"))
    monkeypatch.setattr(start.ReferenceSearchStartService, "retry", invoke)
    result = client.post(
        f"/api/v1/organizations/{tenant}/businesses/{business}/reference-results/searches/{search}/retry",
        json={"operation_id": str(operation)},
        headers={"Authorization": "Bearer " + access_token(settings, actor)},
    )
    assert result.status_code == 200 and result.json() == {"search_id": str(search), "state": "pending"}
    assert invoke.await_args.args[:4] == (tenant, business, actor, search)
    assert invoke.await_args.args[4].operation_id == operation
