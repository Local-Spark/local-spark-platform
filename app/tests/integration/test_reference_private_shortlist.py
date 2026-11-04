"""The future shortlist cannot be read, written or published by runtime."""

from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _commit, _linked

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]


async def seed_header_if_needed(connection, google, batch):
    exists = await connection.scalar(
        text("SELECT to_regclass('public.reference_private_shortlist_headers') IS NOT NULL")
    )
    if exists:
        event, operation = uuid4(), uuid4()
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:event,:tenant,'reference.private_shortlist_prepared',jsonb_build_object(
                'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
                'operation_id',CAST(:operation AS text)))"""),
            {
                "event": event,
                "tenant": google.tenant,
                "business": str(google.business),
                "actor": str(google.actor),
                "operation": str(operation),
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_private_shortlist_headers
          (tenant_id,business_id,batch_id,actor_id,operation_id,event_id)
          VALUES(:tenant,:business,:batch,:actor,:operation,:event)"""),
            {
                "tenant": google.tenant,
                "business": google.business,
                "batch": batch,
                "actor": google.actor,
                "operation": operation,
                "event": event,
            },
        )


async def test_private_shortlist_is_bounded_linked_and_downgrade_protected(admin, api, seeded, settings, database):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    values = _params(google, jev, gg, jg, candidate)
    try:
        await _commit(worker, google, values)
        params = {
            "tenant": google.tenant,
            "business": google.business,
            "batch": values["batch"],
            "candidate": candidate,
        }
        async with admin.begin() as connection:
            await seed_header_if_needed(connection, google, values["batch"])
            second = uuid4()
            await connection.execute(
                text("""INSERT INTO reference_filtered_batch_candidates
              (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,reputation_score,
               reputation_formula_version) VALUES(:tenant,:business,:actor,:batch,:candidate,2,'second-place',8,
               'penalized-3.4-v1')"""),
                {**params, "actor": google.actor, "candidate": second},
            )
            await connection.execute(
                text("""INSERT INTO reference_private_shortlist
              (tenant_id,business_id,batch_id,candidate_id,position)
              VALUES(:tenant,:business,:batch,:candidate,1)"""),
                params,
            )
            invalid = (
                {**params, "candidate": uuid4(), "position": 2},
                {**params, "candidate": second, "position": 11},
                {**params, "candidate": second, "position": 1},
                {**params, "tenant": seeded["t2"], "position": 2},
            )
            for entry in invalid:
                with pytest.raises(DBAPIError):
                    async with connection.begin_nested():
                        await connection.execute(
                            text("""INSERT INTO reference_private_shortlist
                          (tenant_id,business_id,batch_id,candidate_id,position)
                          VALUES(:tenant,:business,:batch,:candidate,:position)"""),
                            entry,
                        )
            with pytest.raises(DBAPIError, match="REFERENCE_SHORTLIST_PREVENTS_AUTOMATIC_DOWNGRADE"):
                async with connection.begin_nested():
                    await connection.run_sync(_downgrade)
            assert await connection.scalar(text("SELECT count(*) FROM reference_private_shortlist")) == 1
        for db in (database, worker):
            with pytest.raises(DBAPIError):
                async with db.transaction(google.tenant, google.actor) as session:
                    await session.execute(text("SELECT * FROM reference_private_shortlist"))
            with pytest.raises(DBAPIError):
                async with db.transaction(google.tenant, google.actor) as session:
                    await session.execute(text("DELETE FROM reference_private_shortlist"))
    finally:
        await worker.close()


def _downgrade(connection):
    migration = import_module("migrations.versions.0083_reference_final_publication")
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
