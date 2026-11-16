"""The exclusive operator is checked before any cross-business discovery."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.business import AccessDenied
from app.services.creation_lab_access import lab_businesses, require_lab_access
from app.tests.unit.test_core import access_token


@pytest.mark.parametrize("configured", [False, True])
async def test_other_account_cannot_even_query_staff(settings, configured):
    settings.creation_lab_actor_id = uuid4() if configured else None
    session = AsyncMock()
    with pytest.raises(AuthError, match="CREATION_LAB_ACCESS_DENIED"):
        await require_lab_access(session, settings, uuid4(), "admin.creation_lab.access")
    session.scalar.assert_not_awaited()
    session.execute.assert_not_awaited()


async def test_revoked_operator_cannot_access(settings):
    actor = uuid4()
    settings.creation_lab_actor_id = actor
    session = AsyncMock()
    session.scalar.return_value = False
    with pytest.raises(AccessDenied):
        await require_lab_access(session, settings, actor, "admin.creation_lab.access")
    session.execute.assert_not_awaited()


@pytest.mark.parametrize("count", [0, 1, 2])
async def test_discovery_is_audited_paginated_and_search_is_literal(settings, count):
    actor = uuid4()
    settings.creation_lab_actor_id = actor
    session = AsyncMock()
    session.scalar.return_value = True
    rows = [{"id": uuid4(), "tenant_id": uuid4(), "name": "Business", "organization_name": "Org"} for _ in range(count)]
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    session.execute.side_effect = [None, result]
    after = uuid4()
    page = await lab_businesses(session, settings, actor, "a!_%", 1, after)
    assert page["items"] == rows[:1]
    assert page["next_cursor"] == (str(rows[0]["id"]) if count > 1 else None)
    assert session.execute.await_args_list[0].args[1] == {
        "actor": actor,
        "action": "admin.creation_lab.businesses.read",
    }
    assert session.execute.await_args_list[1].args[1] == {"query": "%a!!!_!%%", "limit": 2, "after": after}


def test_access_and_discovery_http(client, settings, fake_database):
    actor = uuid4()
    settings.creation_lab_actor_id = actor
    session = AsyncMock()
    session.scalar.return_value = True
    result = MagicMock()
    result.mappings.return_value.all.return_value = []
    session.execute.return_value = result

    @asynccontextmanager
    async def transaction(tenant, actual_actor):
        assert tenant.int == 0 and actual_actor == actor
        yield session

    fake_database.transaction = transaction
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    response = client.get("/api/v1/admin/creation-lab/access", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"allowed": True, "trace_retention_days": 7}
    assert response.headers["Cache-Control"] == "no-store"
    response = client.get("/api/v1/admin/creation-lab/businesses?query=test&limit=1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}
    assert client.get("/api/v1/admin/creation-lab/access").status_code == 401
    settings.creation_lab_actor_id = None
    assert client.get("/api/v1/admin/creation-lab/access", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/creation-lab/businesses", headers=headers).status_code == 403
