import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.schemas.business import BusinessCreate
from app.services.business import AccessDenied, IdempotencyConflict, create_business, list_businesses
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_creation_replay_and_conflict_are_atomic(api, headers, admin):
    first = await api.post("/api/v1/businesses", headers=headers, json={"name": "Salão"})
    assert first.status_code == 201
    repeated = await api.post("/api/v1/businesses", headers=headers, json={"name": "Salão"})
    assert repeated.status_code == 200
    assert repeated.json()["business"] == first.json()["business"]
    assert repeated.json()["operation_id"] == first.json()["operation_id"]
    conflict = await api.post("/api/v1/businesses", headers=headers, json={"name": "Outro"})
    assert conflict.status_code == 409
    async with admin.connect() as connection:
        for table in ("businesses", "idempotency_records", "audit_events"):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM outbox_events")) == 0


async def test_concurrent_same_command_has_one_effect(database, seeded, admin):
    async def request():
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            return await create_business(
                session, seeded["t1"], seeded["a1"], "same-command", BusinessCreate(name="Dog")
            )

    results = await asyncio.gather(*(request() for _ in range(12)))
    assert len({result.business.id for result in results}) == 1
    assert sum(not result.replayed for result in results) == 1
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM businesses")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM outbox_events")) == 0


async def test_rls_read_write_and_pool_reuse(database, seeded):
    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        await create_business(session, seeded["t1"], seeded["a1"], "create-first", BusinessCreate(name="Private"))
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert not (await session.execute(text("SELECT * FROM businesses"))).all()
        with pytest.raises(AccessDenied):
            await create_business(session, seeded["t1"], seeded["a1"], "forbidden", BusinessCreate(name="No"))
    async with database.sessions() as session:
        assert not (await session.execute(text("SELECT * FROM businesses"))).all()
        role = (
            await session.execute(text("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user"))
        ).one()
        assert role == (False, False)
    with pytest.raises(DBAPIError):
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            await session.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES (:id,:tenant,'bad','UTC')"),
                {"id": uuid4(), "tenant": seeded["t2"]},
            )


async def test_cross_tenant_membership_cannot_be_selected(api, headers, seeded):
    response = await api.get("/api/v1/businesses", headers={**headers, "X-Tenant-ID": str(seeded["t2"])})
    assert response.status_code == 403


async def test_viewer_can_read_but_not_create(api, headers, settings, seeded):
    viewer = {**headers, "Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    assert (await api.get("/api/v1/businesses", headers=viewer)).status_code == 200
    assert (await api.post("/api/v1/businesses", headers=viewer, json={"name": "No"})).status_code == 403


async def test_authorization_rechecked_before_replay(api, headers, seeded, admin):
    assert (await api.post("/api/v1/businesses", headers=headers, json={"name": "Dog"})).status_code == 201
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE actor_id=:actor"), {"actor": seeded["a1"]}
        )
    assert (await api.post("/api/v1/businesses", headers=headers, json={"name": "Dog"})).status_code == 403


async def test_pagination_and_validation(api, headers):
    for number in range(3):
        response = await api.post(
            "/api/v1/businesses",
            headers={**headers, "Idempotency-Key": f"create-business-{number}"},
            json={"name": f"Store {number}"},
        )
        assert response.status_code == 201
    first = (await api.get("/api/v1/businesses?limit=2", headers=headers)).json()
    second = (await api.get(f"/api/v1/businesses?after={first['next_cursor']}&limit=2", headers=headers)).json()
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert second["next_cursor"] is None
    assert (await api.get("/api/v1/businesses?limit=101", headers=headers)).status_code == 422
    assert (await api.post("/api/v1/businesses", headers=headers, json={"name": "  "})).status_code == 422
    assert (await api.get("/health/ready")).status_code == 200


async def test_transaction_rollback_leaves_no_partial_effect(database, seeded, admin):
    with pytest.raises(RuntimeError):
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            await create_business(session, seeded["t1"], seeded["a1"], "rolled-back", BusinessCreate(name="Rollback"))
            raise RuntimeError("simulate failure before commit")
    async with admin.connect() as connection:
        for table in ("businesses", "outbox_events", "audit_events", "idempotency_records"):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0


async def test_service_replay_conflict_and_pagination(database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    async with database.transaction(tenant, actor) as session:
        first = await create_business(session, tenant, actor, "service-create-1", BusinessCreate(name="Dog"))
    async with database.transaction(tenant, actor) as session:
        replay = await create_business(session, tenant, actor, "service-create-1", BusinessCreate(name="Dog"))
    assert replay.replayed
    assert replay.business == first.business
    assert replay.operation_id == first.operation_id
    with pytest.raises(IdempotencyConflict):
        async with database.transaction(tenant, actor) as session:
            await create_business(session, tenant, actor, "service-create-1", BusinessCreate(name="Changed"))
    async with database.transaction(tenant, actor) as session:
        second = await create_business(session, tenant, actor, "service-create-2", BusinessCreate(name="Cafe"))
    async with database.transaction(tenant, actor) as session:
        page1 = await list_businesses(session, tenant, actor, 1, None)
        page2 = await list_businesses(session, tenant, actor, 1, page1.next_cursor)
        empty = await list_businesses(session, tenant, actor, 1, max(first.business.id, second.business.id))
    assert page1.next_cursor == page1.items[0].id
    assert page2.next_cursor is None
    assert {item.id for item in page1.items + page2.items} == {first.business.id, second.business.id}
    assert empty.items == [] and empty.next_cursor is None


async def test_readiness_requires_applied_migration(database, admin):
    assert await database.ready()
    async with admin.begin() as connection:
        current = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        await connection.execute(text("UPDATE alembic_version SET version_num='0009_staff_invitations'"))
    try:
        assert not await database.ready()
    finally:
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE alembic_version SET version_num=:version"), {"version": current})
    async with admin.begin() as connection:
        versions = (await connection.execute(text("DELETE FROM alembic_version RETURNING version_num"))).scalars().all()
    try:
        assert not await database.ready()
    finally:
        async with admin.begin() as connection:
            for version in versions:
                await connection.execute(
                    text("INSERT INTO alembic_version(version_num) VALUES (:version)"), {"version": version}
                )
    assert await database.ready()
