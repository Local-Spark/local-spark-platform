from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.owner_references import ReferenceCreate
from app.services.auth import AuthError
from app.services.owner_references import OwnerReferencesService, _request_hash
from app.services.whatsapp_materials import WhatsAppMaterialsService


@pytest.fixture
def setup_service(monkeypatch):
    session = AsyncMock()
    database = MagicMock()

    @asynccontextmanager
    async def transaction(*args):
        yield session

    database.transaction = transaction
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    return OwnerReferencesService(database), session


def rows(*, one=None, one_or_none=None, all=None):
    result = MagicMock()
    result.mappings.return_value.one.return_value = one
    result.mappings.return_value.one_or_none.return_value = one_or_none
    result.mappings.return_value.all.return_value = all
    return result


@pytest.fixture
def record():
    return {"id": uuid4(), "instagram_handle": "cafe", "note": None, "created_at": datetime.now(UTC)}


async def test_create_success_duplicate_and_replay(setup_service, record):
    service, session = setup_service
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    payload = ReferenceCreate(operation_id=uuid4(), instagram="@cafe")
    session.scalar.return_value = payload.operation_id
    session.execute.side_effect = [rows(one_or_none=record), MagicMock(), MagicMock()]
    assert (await service.create(tenant, business, actor, payload)).instagram_handle == "cafe"
    session.execute.side_effect = [rows(one_or_none=None)]
    with pytest.raises(AuthError, match="REFERENCE_ALREADY_EXISTS"):
        await service.create(tenant, business, actor, payload)
    session.scalar.return_value = None
    digest = _request_hash("create", {"instagram": "cafe", "note": None})
    session.execute.side_effect = [rows(one={"request_hash": digest}), rows(one=record)]
    assert (await service.create(tenant, business, actor, payload)).id == record["id"]
    session.execute.side_effect = [rows(one={"request_hash": "different"})]
    with pytest.raises(AuthError, match="REFERENCE_OPERATION_CONFLICT"):
        await service.create(tenant, business, actor, payload)


async def test_list_and_remove(setup_service, record):
    service, session = setup_service
    tenant, business, actor, operation = uuid4(), uuid4(), uuid4(), uuid4()
    session.execute.return_value = rows(all=[record])
    assert (await service.list(tenant, business, actor))[0].id == record["id"]
    session.scalar.side_effect = [None, operation, record["id"], None]
    session.execute.side_effect = [MagicMock(), MagicMock()]
    await service.remove(tenant, business, actor, record["id"], operation)
    session.scalar.side_effect = [None, uuid4(), None]
    with pytest.raises(AuthError, match="REFERENCE_NOT_FOUND"):
        await service.remove(tenant, business, actor, uuid4(), uuid4())
    session.scalar.side_effect = [None, None]
    digest = _request_hash("remove", {"reference_id": str(record["id"])})
    session.execute.side_effect = [rows(one={"request_hash": digest})]
    await service.remove(tenant, business, actor, record["id"], operation)
