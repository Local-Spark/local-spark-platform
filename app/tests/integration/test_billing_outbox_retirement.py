"""P9 preserves audit history before removing the unconsumed billing outbox."""

from datetime import UTC, datetime
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.billing import commercial_event

pytestmark = pytest.mark.integration
migration = import_module("migrations.versions.0038_retire_billing_outbox")


def _apply(connection, direction):
    with Operations.context(MigrationContext.configure(connection)):
        getattr(migration, direction)()


async def _restore_head(admin):
    async with admin.begin() as connection:
        if await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is not None:
            await connection.run_sync(lambda sync: _apply(sync, "upgrade"))


async def test_outbox_retirement_preserves_missing_history_and_safe_rollback(admin, database, seeded):
    existing_id, missing_id, audit_only_id = uuid4(), uuid4(), uuid4()
    existing_operation, missing_operation, audit_only_operation, job_id = [uuid4() for _ in range(4)]
    existing_at = datetime(2024, 1, 2, 3, 4, tzinfo=UTC)
    missing_at = datetime(2024, 2, 3, 4, 5, tzinfo=UTC)
    audit_only_at = datetime(2024, 3, 4, 5, 6, tzinfo=UTC)
    try:
        async with admin.begin() as connection:
            assert await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is None
            await connection.run_sync(lambda sync: _apply(sync, "downgrade"))
            await connection.execute(
                text("""INSERT INTO billing_audit(id,tenant_id,operation_id,action,actor_id,created_at)
                  VALUES(:id,:tenant,:operation,'sponsorship.created',:actor,:created)"""),
                {
                    "id": existing_id,
                    "tenant": seeded["t1"],
                    "operation": existing_operation,
                    "actor": seeded["a1"],
                    "created": existing_at,
                },
            )
            await connection.execute(
                text("""INSERT INTO billing_audit(id,tenant_id,operation_id,action,actor_id,created_at)
                  VALUES(:id,:tenant,:operation,'checkout.opened',:actor,:created)"""),
                {
                    "id": audit_only_id,
                    "tenant": seeded["t1"],
                    "operation": audit_only_operation,
                    "actor": seeded["a1"],
                    "created": audit_only_at,
                },
            )
            # A matching audit event already has its actor; it must not be overwritten.
            await connection.execute(
                text("""INSERT INTO billing_outbox(id,tenant_id,operation_id,event_type,created_at)
                  VALUES(:id,:tenant,:operation,'sponsorship.created',:created)"""),
                {
                    "id": uuid4(),
                    "tenant": seeded["t1"],
                    "operation": existing_operation,
                    "created": existing_at,
                },
            )
            await connection.execute(
                text("""INSERT INTO billing_outbox(id,tenant_id,operation_id,event_type,state,created_at)
                  VALUES(:id,:tenant,:operation,'subscription.reconciled','delivered',:created)"""),
                {
                    "id": missing_id,
                    "tenant": seeded["t2"],
                    "operation": missing_operation,
                    "created": missing_at,
                },
            )
            await connection.execute(
                text("""INSERT INTO billing_jobs(id,tenant_id,actor_id,livemode,kind,dedupe_key)
                  VALUES(:id,:tenant,:actor,false,'reconcile','migration-history-test')"""),
                {"id": job_id, "tenant": seeded["t1"], "actor": seeded["a1"]},
            )
            await connection.execute(
                text("""INSERT INTO billing_accounts(tenant_id,livemode,status,subscription_id,customer_id)
                  VALUES(:tenant,false,'active','sub_migration_history','cus_migration_history')"""),
                {"tenant": seeded["t1"]},
            )
            await connection.run_sync(lambda sync: _apply(sync, "upgrade"))
            assert await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is None
            rows = (await connection.execute(text("SELECT * FROM billing_audit"))).mappings().all()
            by_id = {row["id"]: row for row in rows}
            assert len(rows) == 3
            assert by_id[existing_id]["actor_id"] == seeded["a1"]
            assert by_id[existing_id]["created_at"] == existing_at
            assert by_id[audit_only_id]["created_at"] == audit_only_at
            assert dict(by_id[missing_id]) == {
                "id": missing_id,
                "tenant_id": seeded["t2"],
                "actor_id": None,
                "operation_id": missing_operation,
                "action": "subscription.reconciled",
                "created_at": missing_at,
            }
            assert await connection.scalar(text("SELECT id FROM billing_jobs")) == job_id
            assert await connection.scalar(text("SELECT customer_id FROM billing_accounts")) == "cus_migration_history"
            await connection.run_sync(lambda sync: _apply(sync, "downgrade"))
            flags = (
                await connection.execute(
                    text("""SELECT relrowsecurity,relforcerowsecurity FROM pg_class
                      WHERE oid='public.billing_outbox'::regclass""")
                )
            ).one()
            assert tuple(flags) == (True, True)
            assert set(
                (
                    await connection.execute(
                        text("""SELECT policyname FROM pg_policies
                          WHERE schemaname='public' AND tablename='billing_outbox'""")
                    )
                ).scalars()
            ) == {"billing_processor", "billing_read", "billing_staff_event"}
            assert await connection.scalar(text("SELECT count(*) FROM billing_audit")) == 3
            assert await connection.scalar(text("SELECT count(*) FROM billing_outbox WHERE state='pending'")) == 3

        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM billing_audit")) == 2
            assert await session.scalar(text("SELECT count(*) FROM billing_outbox")) == 2
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM billing_audit")) == 1
            assert await session.scalar(text("SELECT count(*) FROM billing_outbox")) == 1
        async with database.transaction(seeded["t2"], seeded["a1"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM billing_audit")) == 0
            assert await session.scalar(text("SELECT count(*) FROM billing_outbox")) == 0
        with pytest.raises(DBAPIError):
            async with database.transaction(seeded["t1"], seeded["a1"]) as session:
                await session.execute(
                    text("""INSERT INTO billing_outbox(id,tenant_id,operation_id,event_type)
                      VALUES(:id,:tenant,:operation,'owner.injected')"""),
                    {"id": uuid4(), "tenant": seeded["t1"], "operation": uuid4()},
                )
    finally:
        await _restore_head(admin)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is None
        assert await connection.scalar(text("SELECT count(*) FROM billing_audit")) == 3


async def test_retirement_aborts_before_drop_when_legacy_operation_conflicts_across_tenants(admin, seeded):
    operation, outbox_id = uuid4(), uuid4()
    try:
        async with admin.begin() as connection:
            await connection.run_sync(lambda sync: _apply(sync, "downgrade"))
            await connection.execute(
                text("""INSERT INTO billing_audit(id,tenant_id,operation_id,action)
                  VALUES(:id,:tenant,:operation,'subscription.updated')"""),
                {"id": uuid4(), "tenant": seeded["t2"], "operation": operation},
            )
            await connection.execute(
                text("""INSERT INTO billing_outbox(id,tenant_id,operation_id,event_type)
                  VALUES(:id,:tenant,:operation,'subscription.updated')"""),
                {"id": outbox_id, "tenant": seeded["t1"], "operation": operation},
            )
            with pytest.raises(DBAPIError, match="not fully represented"):
                async with connection.begin_nested():
                    await connection.run_sync(lambda sync: _apply(sync, "upgrade"))
            assert await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is not None
            assert await connection.scalar(text("SELECT count(*) FROM billing_audit")) == 1
            await connection.execute(text("DELETE FROM billing_outbox WHERE id=:id"), {"id": outbox_id})
    finally:
        # Deliberately conflicting fixtures cannot be preserved under the existing unique key.
        async with admin.begin() as connection:
            if await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is not None:
                await connection.execute(text("DELETE FROM billing_outbox WHERE id=:id"), {"id": outbox_id})
        await _restore_head(admin)


async def test_financial_events_remain_idempotent_audited_and_tenant_scoped_without_outbox(
    admin, billing_database, database, seeded
):
    operation = uuid4()
    for _ in range(2):
        async with billing_database.transaction(seeded["t1"], seeded["a1"]) as session:
            await commercial_event(session, seeded["t1"], operation, "subscription.reconciled", None)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT to_regclass('public.billing_outbox')")) is None
        assert await connection.scalar(text("SELECT count(*) FROM billing_audit")) == 1
    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        assert await session.scalar(text("SELECT operation_id FROM billing_audit")) == operation
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM billing_audit")) == 0
    with pytest.raises(DBAPIError):
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            await commercial_event(session, seeded["t1"], uuid4(), "owner.injected", seeded["a1"])
