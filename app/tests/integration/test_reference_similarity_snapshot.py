import asyncio
import json
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _linked

pytestmark = pytest.mark.integration
_SIG = (
    "public.reference_filtered_commit_with_similarity("
    "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb,jsonb)"
)
_SQL = text("""SELECT public.reference_filtered_commit_with_similarity(
 :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
 :source,:context,CAST(:candidates AS jsonb),CAST(:judgments AS jsonb))""")


async def setup(admin, api, seeded, settings):
    async with admin.begin() as connection:
        assert not await connection.scalar(
            text("SELECT has_function_privilege('meu_braco_direito_app',:sig,'EXECUTE')"), {"sig": _SIG}
        )
        assert not await connection.scalar(
            text("SELECT has_function_privilege('meu_braco_direito_correlator',:sig,'EXECUTE')"), {"sig": _SIG}
        )
        await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIG} TO meu_braco_direito_correlator"))
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    # The older shared fixture predates the persisted Google request_event_id.
    # Materialize the existing synthetic event link required by the current intent.
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_provider_effects SET request_event_id=:event WHERE id=:effect"),
            {"event": google.event, "effect": google.effect},
        )
    values = _params(google, jev, gg, jg, candidate)
    items = [
        {"candidate_id": str(candidate), "judgment": "match", "similarity_level": "high"},
        {"candidate_id": str(uuid4()), "judgment": "no_match", "similarity_level": "low"},
        {"candidate_id": str(uuid4()), "judgment": "uncertain", "similarity_level": "unknown"},
    ]
    values["judgments"] = json.dumps(items)
    return google, worker, values, items


async def commit(worker, google, values, actor=None, tenant=None):
    async with worker.transaction(tenant or google.tenant, actor or google.actor) as session:
        return await session.scalar(_SQL, values)


async def finish(admin, worker):
    await worker.close()
    async with admin.begin() as connection:
        await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {_SIG} FROM meu_braco_direito_correlator"))


async def test_atomic_private_ordered_snapshot_and_idempotent_replay(admin, api, seeded, settings, database):
    google, worker, values, items = await setup(admin, api, seeded, settings)
    try:
        assert (
            await asyncio.gather(commit(worker, google, values), commit(worker, google, values))
            == [values["batch"]] * 2
        )
        async with admin.connect() as connection:
            rows = (
                await connection.execute(
                    text("""SELECT candidate_id,declared_google_position,judgment,similarity_level
                 FROM reference_similarity_snapshot_items ORDER BY declared_google_position""")
                )
            ).all()
            assert [
                (str(r.candidate_id), r.declared_google_position, r.judgment, r.similarity_level) for r in rows
            ] == [(x["candidate_id"], i, x["judgment"], x["similarity_level"]) for i, x in enumerate(items, 1)]
            assert (
                await connection.scalar(text("SELECT judgment_schema FROM reference_similarity_snapshots"))
                == "jev-similarity-level-v1"
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.filtered_committed'")
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM reference_cost_reservations WHERE state='uncertain'")
                )
                == 2
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.similarity_snapshot_recorded'")
                )
                == 1
            )
            event = (
                await connection.execute(
                    text("SELECT payload FROM outbox_events WHERE event_type='reference.similarity_snapshot_recorded'")
                )
            ).scalar_one()
            assert set(event) == {"business_id", "actor_id", "operation_id"}
            assert event["operation_id"] == str(values["batch"])
            columns = (
                (
                    await connection.execute(
                        text("""SELECT column_name FROM information_schema.columns
              WHERE table_name IN ('reference_similarity_snapshots','reference_similarity_snapshot_items')""")
                    )
                )
                .scalars()
                .all()
            )
            assert not {
                "name",
                "rating",
                "rating_count",
                "latitude",
                "longitude",
                "types",
                "raw",
                "probabilities",
            } & set(columns)
        async with database.transaction(google.tenant, google.actor) as session:
            with pytest.raises(DBAPIError):
                await session.execute(text("SELECT * FROM reference_similarity_snapshot_items"))
        for change in (list(reversed(items)), [{**items[0], "similarity_level": "low"}, *items[1:]]):
            with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_REPLAY_CONFLICT"):
                await commit(worker, google, values | {"judgments": json.dumps(change)})
    finally:
        await finish(admin, worker)


async def test_invalid_projection_rolls_back_both_effects_and_reservations(admin, api, seeded, settings):
    google, worker, values, items = await setup(admin, api, seeded, settings)
    try:
        for invalid in (
            [{**items[0], "raw": "untrusted"}],
            [items[0], items[0]],
            [{**items[0], "similarity_level": "unvalidated"}],
            [{**items[0], "judgment": "uncertain"}],
        ):
            with pytest.raises(DBAPIError):
                await commit(worker, google, values | {"judgments": json.dumps(invalid)})
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_MAPPING_INVALID"):
            await commit(
                worker, google, values | {"judgments": json.dumps([{**items[0], "similarity_level": "unknown"}])}
            )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
            assert await connection.scalar(text("SELECT count(*) FROM reference_similarity_snapshots")) == 0
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE state='running'"))
                == 2
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations WHERE state='claimed'"))
                == 2
            )
    finally:
        await finish(admin, worker)


async def test_fence_and_tenant_are_checked_before_committing(admin, api, seeded, settings):
    google, worker, values, _ = await setup(admin, api, seeded, settings)
    try:
        for bad in ({"google_token": uuid4()}, {"jev_token": uuid4()}, {"source": "b" * 64}):
            with pytest.raises(DBAPIError):
                await commit(worker, google, values | bad)
        with pytest.raises(DBAPIError):
            await commit(worker, google, values, actor=seeded["a2"], tenant=seeded["t2"])
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_similarity_snapshots")) == 0
    finally:
        await finish(admin, worker)


async def test_legacy_path_blocks_new_commits_but_preserves_exact_replay(admin, api, seeded, settings):
    old_sql = text("""SELECT public.reference_filtered_commit(
      :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
      :source,:context,CAST(:candidates AS jsonb))""")

    google, worker, values, _ = await setup(admin, api, seeded, settings)
    inner = (
        "public.reference_filtered_commit_evidence_inner("
        "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb)"
    )
    inner_sql = text(str(old_sql).replace("reference_filtered_commit(", "reference_filtered_commit_evidence_inner("))
    try:
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_REQUIRED"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(old_sql, values)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batches")) == 0
        # Seed a pre-existing historical commit through a grant local to this test only.
        async with admin.begin() as connection:
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {inner} TO meu_braco_direito_correlator"))
        try:
            async with worker.transaction(google.tenant, google.actor) as session:
                assert await session.scalar(inner_sql, values) == values["batch"]
        finally:
            async with admin.begin() as connection:
                await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {inner} FROM meu_braco_direito_correlator"))
        async with worker.transaction(google.tenant, google.actor) as session:
            assert await session.scalar(old_sql, values) == values["batch"]
        altered = json.loads(values["candidates"])
        altered[0]["reputation_score"] = "9.99"
        with pytest.raises(DBAPIError, match="REFERENCE_FILTERED_REPLAY_CONFLICT"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(old_sql, values | {"candidates": json.dumps(altered)})
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_LEGACY_UNVERIFIED"):
            await commit(worker, google, values)
    finally:
        await finish(admin, worker)


async def test_downgrade_refuses_to_delete_snapshot(admin, api, seeded, settings):
    google, worker, values, _ = await setup(admin, api, seeded, settings)
    try:
        await commit(worker, google, values)
        module = import_module("migrations.versions.0099_similarity_snapshot")

        def downgrade(sync):
            with Operations.context(MigrationContext.configure(sync)):
                module.downgrade()

        async with admin.connect() as connection:
            async with connection.begin():
                with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_PREVENTS_AUTOMATIC_DOWNGRADE"):
                    async with connection.begin_nested():
                        await connection.run_sync(downgrade)
            assert await connection.scalar(text("SELECT count(*) FROM reference_similarity_snapshots")) == 1
    finally:
        await finish(admin, worker)


async def test_private_recovery_reuses_stored_evidence_and_never_certifies_source_order(admin, api, seeded, settings):
    google, worker, values, items = await setup(admin, api, seeded, settings)
    signature = "public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid)"
    sql = text("SELECT public.reference_similarity_snapshot_recovery(:business,:search,:google,:google_event)")
    try:
        async with admin.begin() as connection:
            for role in ("meu_braco_direito_app", "meu_braco_direito_correlator"):
                assert not await connection.scalar(
                    text("SELECT has_function_privilege(:role,:sig,'EXECUTE')"), {"role": role, "sig": signature}
                )
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {signature} TO meu_braco_direito_correlator"))
        async with worker.transaction(google.tenant, google.actor) as session:
            assert await session.scalar(sql, values) is None
        await commit(worker, google, values)
        async with worker.transaction(google.tenant, google.actor) as session:
            recovered = await session.scalar(sql, values)
        assert recovered["batch_id"] == str(values["batch"])
        assert recovered["source_order_verified"] is False
        assert recovered["provider_response_verified"] is False
        assert recovered["filtered_candidates"] == [
            {
                "candidate_id": items[0]["candidate_id"],
                "filtered_position": 1,
                "place_id": "fake-place",
                "reputation_score": 8.25,
                "reputation_formula_version": "penalized-3.4-v1",
            }
        ]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=version+1 WHERE tenant_id=:t AND business_id=:b"),
                {"t": google.tenant, "b": google.business},
            )
        async with worker.transaction(google.tenant, google.actor) as session:
            assert await session.scalar(sql, values) == recovered
        assert recovered["judgments"] == [
            {**item, "declared_google_position": index} for index, item in enumerate(items, 1)
        ]
        assert "token" not in json.dumps(recovered)
        with pytest.raises(DBAPIError, match="REFERENCE_RECOVERY_INVALID"):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(sql, values)
    finally:
        async with admin.begin() as connection:
            await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {signature} FROM meu_braco_direito_correlator"))
        await finish(admin, worker)


async def test_recovery_rejects_impostor_event_and_corrupt_effect_hold(admin, api, seeded, settings):
    google, worker, values, _ = await setup(admin, api, seeded, settings)
    signature = "public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid)"
    sql = text("SELECT public.reference_similarity_snapshot_recovery(:business,:search,:google,:google_event)")
    try:
        async with admin.begin() as connection:
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {signature} TO meu_braco_direito_correlator"))
        await commit(worker, google, values)
        fake_event = uuid4()
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              SELECT :fake,tenant_id,event_type,payload FROM outbox_events WHERE id=:original"""),
                {"fake": fake_event, "original": values["google_event"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_RECOVERY_INVALID"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(sql, values | {"google_event": fake_event})
        async with admin.begin() as connection:
            old_hash = await connection.scalar(
                text("SELECT request_hash FROM reference_cost_reservations WHERE effect_id=:e"), {"e": values["jev"]}
            )
            await connection.execute(
                text("UPDATE reference_cost_reservations SET request_hash=:bad WHERE effect_id=:e"),
                {"bad": "b" * 64, "e": values["jev"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_RECOVERY_INVALID"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(sql, values)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_cost_reservations SET request_hash=:old WHERE effect_id=:e"),
                {"old": old_hash, "e": values["jev"]},
            )
            await connection.execute(
                text("""UPDATE outbox_events SET payload=jsonb_set(payload,'{actor_id}',
              to_jsonb(CAST(:actor AS text))) WHERE id=:event"""),
                {"actor": str(seeded["a2"]), "event": values["jev_event"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_RECOVERY_INVALID"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(sql, values)
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE outbox_events SET payload=jsonb_set(payload,'{actor_id}',"
                    "to_jsonb(CAST(:actor AS text))) WHERE id=:event"
                ),
                {"actor": str(google.actor), "event": values["jev_event"]},
            )
            await connection.execute(
                text("DELETE FROM audit_events WHERE action='reference.similarity_snapshot_recorded'")
            )
        with pytest.raises(DBAPIError, match="REFERENCE_SIMILARITY_RECOVERY_INVALID"):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(sql, values)
    finally:
        async with admin.begin() as connection:
            await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {signature} FROM meu_braco_direito_correlator"))
        await finish(admin, worker)
