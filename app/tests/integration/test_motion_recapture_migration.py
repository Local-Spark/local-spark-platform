"""Qualify the additive event constraint in the existing _test database, rolled back."""

import importlib
import os
import re

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration


async def test_recapture_migration_preserves_existing_events_and_rolls_back():
    url = os.environ["TEST_ADMIN_DATABASE_URL"]
    assert (make_url(url).database or "").endswith("_test")
    engine = create_async_engine(url)
    migration = importlib.import_module("migrations.versions.0117_motion_recapture_events")
    definition = text("""SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check'""")

    def apply(connection, direction):
        with Operations.context(MigrationContext.configure(connection)):
            getattr(migration, direction)()

    try:
        async with engine.connect() as connection:
            before = await connection.scalar(definition)
            assert before
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            await connection.rollback()
            transaction = await connection.begin()
            try:
                await connection.run_sync(apply, "upgrade")
                after = await connection.scalar(definition)
                existing = set(re.findall(r"'([^']+)'::text", before))
                new = {"motion.storyboard_recapture_requested", "motion.storyboard_recapture_started"}
                assert existing and existing | new <= set(re.findall(r"'([^']+)'::text", after))
                for kind in new:
                    assert await connection.scalar(
                        text(f"SELECT {after} FROM (VALUES (:kind)) e(event_type)"), {"kind": kind}
                    )
                assert not await connection.scalar(
                    text(f"SELECT {after} FROM (VALUES (:kind)) e(event_type)"), {"kind": "invalid.unknown_event"}
                )
                await connection.run_sync(apply, "downgrade")
                restricted = await connection.scalar(definition)
                for kind in new:
                    assert not await connection.scalar(
                        text(f"SELECT {restricted} FROM (VALUES (:kind)) e(event_type)"), {"kind": kind}
                    )
            finally:
                await transaction.rollback()
            assert await connection.scalar(definition) == before
            assert await connection.scalar(text("SELECT version_num FROM alembic_version")) == revision
    finally:
        await engine.dispose()
