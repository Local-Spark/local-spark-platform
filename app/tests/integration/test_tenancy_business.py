import asyncio
import importlib
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.schemas.business import BusinessCreate
from app.services.business import (
    AccessDenied,
    BusinessAlreadyExists,
    IdempotencyConflict,
    create_business,
    list_businesses,
)
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


async def test_concurrent_distinct_commands_create_at_most_one_business(database, seeded, admin):
    async def request(index):
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            return await create_business(
                session, seeded["t1"], seeded["a1"], f"distinct-{index}", BusinessCreate(name=f"Dog {index}")
            )

    results = await asyncio.gather(*(request(index) for index in range(12)), return_exceptions=True)
    assert sum(not isinstance(result, BaseException) for result in results) == 1
    assert sum(isinstance(result, BusinessAlreadyExists) for result in results) == 11
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM businesses")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM idempotency_records")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM audit_events")) == 1


async def test_rejected_creation_leaves_no_partial_reservation_when_error_is_caught(database, seeded, admin):
    tenant, actor = seeded["t1"], seeded["a1"]
    async with database.transaction(tenant, actor) as session:
        await create_business(session, tenant, actor, "first-command", BusinessCreate(name="First"))
    async with database.transaction(tenant, actor) as session:
        with pytest.raises(BusinessAlreadyExists):
            await create_business(session, tenant, actor, "rejected-command", BusinessCreate(name="Second"))
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM idempotency_records")) == 1
        assert not await connection.scalar(
            text("SELECT EXISTS(SELECT 1 FROM idempotency_records WHERE tenant_id=:tenant AND key='rejected-command')"),
            {"tenant": tenant},
        )


async def test_legacy_writer_race_rolls_back_reservation_even_when_conflict_is_caught(database, seeded, admin):
    tenant, actor, winner = seeded["t1"], seeded["a1"], uuid4()
    entered, resume = asyncio.Event(), asyncio.Event()

    async def request():
        async with database.transaction(tenant, actor) as session:
            execute = session.execute

            async def pause_business_insert(statement, *args, **kwargs):
                if "INSERT INTO businesses" in str(statement):
                    entered.set()
                    await resume.wait()
                return await execute(statement, *args, **kwargs)

            session.execute = pause_business_insert
            with pytest.raises(BusinessAlreadyExists):
                await create_business(session, tenant, actor, "racing-command", BusinessCreate(name="Delayed"))

    task = asyncio.create_task(request())
    try:
        await asyncio.wait_for(entered.wait(), 5)
        async with admin.begin() as connection:
            await connection.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES (:id,:tenant,'Legacy','UTC')"),
                {"id": winner, "tenant": tenant},
            )
    finally:
        resume.set()
        await asyncio.wait_for(task, 5)
    async with admin.connect() as connection:
        assert (
            await connection.scalar(text("SELECT id FROM businesses WHERE tenant_id=:tenant"), {"tenant": tenant})
            == winner
        )
        assert await connection.scalar(text("SELECT count(*) FROM idempotency_records")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM audit_events")) == 0


async def test_database_constraint_rejects_second_business_even_outside_api(database, seeded, admin):
    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        await create_business(session, seeded["t1"], seeded["a1"], "first-business", BusinessCreate(name="Dog"))
    with pytest.raises(IntegrityError):
        async with admin.begin() as connection:
            await connection.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES (:id,:tenant,'Second','UTC')"),
                {"id": uuid4(), "tenant": seeded["t1"]},
            )


async def test_migration_rejects_legacy_duplicates_without_deleting_them(admin, seeded):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    migration = importlib.import_module("migrations.versions.0057_one_business_per_tenant")

    def upgrade(connection):
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

    async with admin.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("ALTER TABLE businesses DROP CONSTRAINT one_business_per_tenant"))
            for name in ("One", "Two"):
                await connection.execute(
                    text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES (:id,:tenant,:name,'UTC')"),
                    {"id": uuid4(), "tenant": seeded["t1"], "name": name},
                )
            with pytest.raises(DBAPIError, match="ONE_BUSINESS_PER_TENANT_REQUIRES_LEGACY_REVIEW"):
                async with connection.begin_nested():
                    await connection.run_sync(upgrade)
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM businesses WHERE tenant_id=:tenant"), {"tenant": seeded["t1"]}
                )
                == 2
            )
        finally:
            await transaction.rollback()


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
    response = await api.post("/api/v1/businesses", headers=headers, json={"name": "Store"})
    assert response.status_code == 201
    other = await api.post(
        "/api/v1/businesses", headers={**headers, "Idempotency-Key": "create-another"}, json={"name": "Other"}
    )
    assert other.status_code == 409 and other.json()["error_code"] == "BUSINESS_ALREADY_EXISTS"
    first = (await api.get("/api/v1/businesses?limit=2", headers=headers)).json()
    second = (await api.get(f"/api/v1/businesses?after={first['items'][0]['id']}&limit=2", headers=headers)).json()
    assert len(first["items"]) == 1 and not second["items"]
    assert first["next_cursor"] is None and second["next_cursor"] is None
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
    with pytest.raises(BusinessAlreadyExists):
        async with database.transaction(tenant, actor) as session:
            await create_business(session, tenant, actor, "service-create-2", BusinessCreate(name="Cafe"))
    async with database.transaction(tenant, actor) as session:
        page1 = await list_businesses(session, tenant, actor, 1, None)
        empty = await list_businesses(session, tenant, actor, 1, first.business.id)
    assert page1.next_cursor is None
    assert [item.id for item in page1.items] == [first.business.id]
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
