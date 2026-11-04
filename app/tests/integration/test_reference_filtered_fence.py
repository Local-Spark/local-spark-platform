"""Exercise the complete durable link with synthetic provider effects only."""

import asyncio
import json
import re
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard
from app.tests.integration.test_reference_filtered_batch_storage import _SQL, _params
from app.tests.integration.test_reference_jev_budget_guard import _google_started, _jev_intent

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]


@pytest.fixture(autouse=True)
def expose_stable_google_fixture_failure(monkeypatch):
    from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard

    original = DatabasePlacesBudgetGuard.claim

    async def claim(self, *args, **kwargs):
        try:
            return await original(self, *args, **kwargs)
        except Exception as error:
            match = re.search(r"REFERENCE_[A-Z_]+", str(error))
            pytest.fail(f"Synthetic Google setup claim failed: {match.group(0) if match else type(error).__name__}")

    monkeypatch.setattr(DatabasePlacesBudgetGuard, "claim", claim)


async def _linked(admin, api, seeded, settings):
    google, gg, worker = await _google_started(admin, api, seeded, settings)
    candidate = uuid4()
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(candidate, "fake", ("cafe",)),))
    jev, request = await _jev_intent(admin, worker, google, gg.execution_token(), input_data)
    jg = DatabaseJevBudgetGuard(worker, jev)
    assert await jg.claim(jev.effect, request)
    return google, jev, gg, jg, worker, candidate


async def _commit(worker, google, params):
    async with worker.transaction(google.tenant, google.actor) as session:
        return await session.scalar(_SQL, params)


async def test_link_rejects_tampering_and_private_inner_has_no_runtime_grant(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        async with admin.begin() as connection:
            fake_event = uuid4()
            await connection.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
                SELECT :fake,tenant_id,event_type,payload FROM outbox_events WHERE id=:original"""),
                {"fake": fake_event, "original": jev.event},
            )
            await connection.execute(
                text("UPDATE reference_provider_effects SET source_batch_mac=:bad WHERE id=:id"),
                {"bad": "b" * 64, "id": google.effect},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_LINK_INVALID"):
            await _commit(worker, google, params)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_effects SET source_batch_mac=:mac WHERE id=:id"),
                {"mac": jev.source_batch_mac, "id": google.effect},
            )
        for changes in (
            {"jev_event": fake_event},
            {"source": "b" * 64},
            {"google_token": uuid4()},
            {"jev_token": uuid4()},
        ):
            with pytest.raises(DBAPIError):
                await _commit(worker, google, {**params, **changes})
        async with worker.transaction(google.tenant, google.actor) as session:
            with pytest.raises(DBAPIError):
                await session.scalar(
                    text("""SELECT public.reference_filtered_commit_inner(
                  NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)""")
                )
        with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_LINK_INVALID"):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_SQL, params)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
    finally:
        await worker.close()


async def test_concurrent_replay_commits_once_and_revocation_does_not_cancel(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": google.tenant, "actor": google.actor},
            )
        assert await asyncio.gather(_commit(worker, google, params), _commit(worker, google, params)) == [
            params["batch"],
            params["batch"],
        ]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_searches SET state='completed' WHERE id=:id"), {"id": google.search}
            )
        assert await _commit(worker, google, params) == params["batch"]
        changed = json.loads(params["candidates"])
        changed[0]["reputation_score"] = "9.00"
        with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_REPLAY_CONFLICT"):
            await _commit(worker, google, {**params, "candidates": json.dumps(changed)})
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.filtered_committed'")
                )
                == 1
            )
            columns = (
                (
                    await connection.execute(
                        text("""SELECT column_name FROM information_schema.columns
                  WHERE table_name IN ('reference_filtered_batches','reference_filtered_batch_candidates')""")
                    )
                )
                .scalars()
                .all()
            )
            assert not {"name", "rating", "rating_count", "latitude", "longitude", "types", "raw"} & set(columns)
    finally:
        await worker.close()


async def test_downgrade_keeps_data_and_revokes_writer(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        assert await _commit(worker, google, params) == params["batch"]
        async with admin.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.run_sync(_downgrade)
                assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batch_candidates")) == 1
                permitted = await connection.scalar(
                    text("""SELECT has_function_privilege(
                  'meu_braco_direito_correlator',
                  'public.reference_filtered_commit(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb)',
                  'EXECUTE')""")
                )
                assert permitted is False
            finally:
                await transaction.rollback()
    finally:
        await worker.close()


def _downgrade(connection):
    latest = import_module("migrations.versions.0099_similarity_snapshot")
    migration = import_module("migrations.versions.0081_reference_filtered_fence")
    with Operations.context(MigrationContext.configure(connection)):
        latest.downgrade()
        migration.downgrade()
