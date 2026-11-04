"""Synthetic, fenced filtered storage; no real provider calls."""

import json
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard
from app.services.reference_jev_request_mac import jev_request_mac
from app.tests.integration.test_reference_jev_budget_guard import _google_started, _jev_intent

pytestmark = pytest.mark.integration

_SQL = text("""SELECT public.reference_filtered_commit_evidence_inner(
  :business,:search,:batch,:google,:google_event,:google_token,
  :jev,:jev_event,:jev_token,:source,:context,CAST(:candidates AS jsonb))""")
_SIGNATURE = (
    "public.reference_filtered_commit_evidence_inner(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb)"
)


@pytest.fixture(autouse=True)
async def revoke_historical_grant_after_test(admin):
    try:
        yield
    finally:
        async with admin.begin() as connection:
            await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {_SIGNATURE} FROM meu_braco_direito_correlator"))


async def _allow_in_disposable_test_db(admin):
    async with admin.begin() as connection:
        await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIGNATURE} TO meu_braco_direito_correlator"))


async def _start(admin, api, seeded, settings):
    async with admin.begin() as connection:
        await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {_SIGNATURE} FROM meu_braco_direito_correlator"))
    google_context, google, worker = await _google_started(admin, api, seeded, settings)
    candidate = uuid4()
    input_data = SimilarityInput(("cafe",), None, (SimilarityCandidate(candidate, "fake", ("cafe",)),))
    async with admin.connect() as connection:
        has_intent_creator = await connection.scalar(
            text("""SELECT to_regprocedure(
          'public.reference_jev_intent(uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint)'
          ) IS NOT NULL""")
        )
    jev_context, request = await _jev_intent(
        admin, worker, google_context, google.execution_token(), input_data, create=has_intent_creator
    )
    if not has_intent_creator:
        mac = jev_request_mac(
            jev_context.key,
            key_version=jev_context.key_version,
            tariff_version=jev_context.tariff_version,
            credential_version=jev_context.credential_version,
            tenant=jev_context.tenant,
            business=jev_context.business,
            actor=jev_context.actor,
            search=jev_context.search,
            effect=jev_context.effect,
            pilot=jev_context.pilot,
            parent_google_effect=jev_context.parent_google_effect,
            source_batch_mac=jev_context.source_batch_mac,
            context_version=jev_context.context_version,
            reserved_usd_micros=jev_context.reserved_usd_micros,
            request=request,
        )
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO reference_provider_effects
              (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,
               tariff_version,credential_version,field_mask,reserved_usd_micros,state,parent_google_effect_id,
               source_batch_mac)
              VALUES(:id,:tenant,:business,:actor,:search,:pilot,'jev',:mac,:key,:tariff,:credential,
                'jev-model:jev-test-model',:amount,'pending',:parent,:batch)"""),
                {
                    "id": jev_context.effect,
                    "tenant": jev_context.tenant,
                    "business": jev_context.business,
                    "actor": jev_context.actor,
                    "search": jev_context.search,
                    "pilot": jev_context.pilot,
                    "mac": mac,
                    "key": jev_context.key_version,
                    "tariff": jev_context.tariff_version,
                    "credential": jev_context.credential_version,
                    "amount": jev_context.reserved_usd_micros,
                    "parent": jev_context.parent_google_effect,
                    "batch": jev_context.source_batch_mac,
                },
            )
            await connection.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,'reference.provider_effect_requested',jsonb_build_object(
                'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
                'operation_id',CAST(:effect AS text)))"""),
                {
                    "id": jev_context.event,
                    "tenant": jev_context.tenant,
                    "business": str(jev_context.business),
                    "actor": str(jev_context.actor),
                    "effect": str(jev_context.effect),
                },
            )
    jev = DatabaseJevBudgetGuard(worker, jev_context)
    assert await jev.claim(jev_context.effect, request)
    return google_context, jev_context, google, jev, worker, candidate


def _params(google, jev, google_guard, jev_guard, candidate):
    return {
        "business": google.business,
        "search": google.search,
        "batch": uuid4(),
        "google": google.effect,
        "google_event": google.event,
        "google_token": google_guard.execution_token(),
        "jev": jev.effect,
        "jev_event": jev.event,
        "jev_token": jev_guard.execution_token(),
        "source": jev.source_batch_mac,
        "context": 1,
        "candidates": json.dumps(
            [
                {
                    "candidate_id": str(candidate),
                    "place_id": "fake-place",
                    "reputation_score": "8.25",
                    "reputation_formula_version": "penalized-3.4-v1",
                }
            ]
        ),
    }


async def _commit(worker, google, params):
    async with worker.transaction(google.tenant, google.actor) as session:
        return await session.scalar(_SQL, params)


async def test_fenced_commit_is_private_atomic_and_exactly_replayable(admin, api, seeded, settings, database):
    google, jev, gg, jg, worker, candidate = await _start(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        with pytest.raises(DBAPIError):
            await _commit(worker, google, params)
        await _allow_in_disposable_test_db(admin)
        assert await _commit(worker, google, params) == params["batch"]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_searches SET state='completed' WHERE id=:search"),
                {"search": google.search},
            )
        assert await _commit(worker, google, params) == params["batch"]
        altered = json.loads(params["candidates"])
        altered[0]["reputation_score"] = "8.26"
        with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_REPLAY_CONFLICT"):
            await _commit(worker, google, {**params, "candidates": json.dumps(altered)})
        async with database.transaction(google.tenant, google.actor) as session:
            with pytest.raises(DBAPIError):
                await session.execute(text("SELECT * FROM reference_filtered_batches"))
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batch_candidates")) == 1
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM reference_provider_effects WHERE state='completed_filtered'")
                )
                == 2
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM reference_cost_reservations WHERE state='uncertain'")
                )
                == 2
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.filtered_committed'")
                )
                == 1
            )
            with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_PREVENTS_AUTOMATIC_DOWNGRADE"):
                async with connection.begin_nested():
                    await connection.run_sync(_downgrade)
    finally:
        await worker.close()


def _downgrade(connection):
    migration = import_module("migrations.versions.0079_reference_filtered_batch")
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()


async def test_invalid_fences_events_and_raw_fields_never_commit(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _start(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        await _allow_in_disposable_test_db(admin)
        raw = json.loads(params["candidates"])
        raw[0]["rating"] = 4.8
        duplicate = json.loads(params["candidates"])
        duplicate.append(dict(duplicate[0]))
        for changes in (
            {"google_token": uuid4()},
            {"jev_token": uuid4()},
            {"google_event": uuid4()},
            {"jev_event": uuid4()},
            {"search": uuid4()},
            {"source": "b" * 64},
            {"context": 2},
            {"candidates": json.dumps(raw)},
            {"candidates": json.dumps(raw * 21)},
            {"candidates": json.dumps(duplicate)},
        ):
            with pytest.raises(DBAPIError):
                await _commit(worker, google, {**params, **changes})
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations WHERE state='claimed'"))
                == 2
            )
        with pytest.raises(DBAPIError):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_SQL, params)
    finally:
        await worker.close()


async def test_already_admitted_effects_finish_after_owner_revocation(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _start(admin, api, seeded, settings)
    params = _params(google, jev, gg, jg, candidate)
    try:
        await _allow_in_disposable_test_db(admin)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": google.tenant, "actor": google.actor},
            )
        assert await _commit(worker, google, params) == params["batch"]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_searches SET state='completed' WHERE id=:search"),
                {"search": google.search},
            )
        assert await _commit(worker, google, params) == params["batch"]
    finally:
        await worker.close()
