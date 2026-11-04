"""The new search parent is tenant-isolated and has no runtime writer."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_parent_is_owner_readable_but_not_runtime_writable(admin, api, seeded, settings, database):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, search, operation = await create_business(admin, tenant), uuid4(), uuid4()
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    params = {
        "id": search,
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "operation": operation,
        "mac": "a" * 64,
    }
    insert = text("""INSERT INTO reference_provider_searches
      (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state)
      VALUES(:id,:tenant,:business,:actor,:operation,1,:mac,'pending')""")
    async with admin.begin() as connection:
        await connection.execute(insert, params)
    async with database.transaction(tenant, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_provider_searches")) == 1
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_provider_searches")) == 0
    async with database.transaction(tenant, seeded["viewer"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_provider_searches")) == 0
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(insert, {**params, "id": uuid4(), "operation": uuid4()})
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(text("UPDATE reference_provider_searches SET state='completed'"))


async def test_parent_requires_valid_mac_state_and_business_context(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    insert = text("""INSERT INTO reference_provider_searches
      (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state)
      VALUES(:id,:tenant,:business,:actor,:operation,:version,:mac,:state)""")
    params = {
        "id": uuid4(),
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "operation": uuid4(),
        "version": 1,
        "mac": "a" * 64,
        "state": "pending",
    }
    async with admin.begin() as connection:
        for changes in ({"mac": "x" * 64}, {"state": "arbitrary"}, {"version": 99}):
            with pytest.raises(DBAPIError):
                async with connection.begin_nested():
                    await connection.execute(insert, {**params, **changes})
