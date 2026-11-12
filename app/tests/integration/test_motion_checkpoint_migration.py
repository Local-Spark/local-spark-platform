"""Exercise the additive event constraint on the existing dedicated _test, then roll back."""

import importlib
import re

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

pytestmark = pytest.mark.integration


async def test_checkpoint_event_constraint_preserves_old_events_and_supports_downgrade(admin):
    migration = importlib.import_module("migrations.versions.0118_motion_checkpoint_events")
    definition = text("""SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check'""")

    def apply(connection, direction):
        with Operations.context(MigrationContext.configure(connection)):
            getattr(migration, direction)()

    async with admin.connect() as connection:
        before = await connection.scalar(definition)
        revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        await connection.rollback()
        transaction = await connection.begin()
        try:
            await connection.run_sync(apply, "upgrade")
            after = await connection.scalar(definition)
            assert set(re.findall(r"'([^']+)'::text", before)) <= set(re.findall(r"'([^']+)'::text", after))
            kinds = {"motion.plan_ready", "motion.plan_approved", "motion.render_ready", "motion.render_approved"}
            for kind in kinds:
                assert await connection.scalar(
                    text(f"SELECT {after} FROM (VALUES (:kind)) e(event_type)"), {"kind": kind}
                )
            assert not await connection.scalar(text(f"SELECT {after} FROM (VALUES ('invalid.unknown')) e(event_type)"))
            await connection.run_sync(apply, "downgrade")
            restricted = await connection.scalar(definition)
            for kind in kinds:
                assert not await connection.scalar(
                    text(f"SELECT {restricted} FROM (VALUES (:kind)) e(event_type)"), {"kind": kind}
                )
            assert await connection.scalar(
                text(f"SELECT {restricted} FROM (VALUES ('motion.requested')) e(event_type)")
            )
        finally:
            await transaction.rollback()
        assert await connection.scalar(definition) == before
        assert await connection.scalar(text("SELECT version_num FROM alembic_version")) == revision
