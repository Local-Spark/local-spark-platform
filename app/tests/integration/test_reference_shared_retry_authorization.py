"""Disposable tests: another owner may authorize without inheriting a fence."""

import asyncio
import json
from importlib import import_module
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_contacts_guard import _call, _revoke, _setup

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]
_AUTH = "public.reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)"
_FAILURE = "public.reference_contacts_not_dispatched(uuid,uuid,uuid,uuid)"


async def _prepare(admin, api, seeded, settings):
    google, worker, cycle, _, _, first = await _setup(admin, api, seeded, settings)
    async with admin.begin() as connection:
        assert not await connection.scalar(
            text("SELECT has_function_privilege('meu_braco_direito_correlator',:f,'EXECUTE')"), {"f": _AUTH}
        )
        assert not await connection.scalar(
            text(
                "SELECT has_column_privilege('meu_braco_direito_reference_lock', "
                "'public.reference_provider_effects','executor_token','SELECT')"
            )
        )
        await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {_AUTH}, {_FAILURE} TO meu_braco_direito_correlator"))
        await connection.execute(
            text("INSERT INTO reference_real_heads(tenant_id,business_id,cycle_id) VALUES(:tenant,:business,:cycle)"),
            {"tenant": google.tenant, "business": google.business, "cycle": cycle},
        )
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": google.tenant, "actor": seeded["a2"]},
        )
    started = await _call(worker, google, first)
    async with worker.transaction(google.tenant, google.actor) as session:
        await session.scalar(
            text("SELECT public.reference_contacts_not_dispatched(:business,:lookup,:effect,:token)"),
            {**first, "token": UUID(started["executor_token"])},
        )
    return google, worker, first


async def _authorize(worker, google, actor, values):
    async with worker.transaction(google.tenant, actor) as session:
        return await session.scalar(
            text(
                "SELECT public.reference_authorize_shared_contacts_retry("
                ":business,:lookup,:authorization,:operation,:event)"
            ),
            values,
        )


async def _finish(admin, worker):
    await worker.close()
    await _revoke(admin)
    async with admin.begin() as connection:
        await connection.execute(
            text(f"REVOKE EXECUTE ON FUNCTION {_AUTH}, {_FAILURE} FROM meu_braco_direito_correlator")
        )


async def test_other_active_owner_authorizes_new_retry_without_inheriting_executor(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": google.tenant, "actor": google.actor},
            )
        result = await _authorize(worker, google, seeded["a2"], values)
        assert result["created"] is True
        assert (await _authorize(worker, google, seeded["a2"], {**values, "event": uuid4()}))["created"] is False
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        # This is only an old receipt. Future intent/claim must recheck context.
        assert (await _authorize(worker, google, seeded["a2"], values))["created"] is False
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=1 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        assert "token" not in json.dumps(result)
        async with admin.connect() as connection:
            row = (
                await connection.execute(
                    text("SELECT actor_id,previous_effect_id FROM reference_contacts_retry_authorizations")
                )
            ).one()
            assert row.actor_id == seeded["a2"] and row.previous_effect_id == first["effect"]
            assert (
                await connection.scalar(
                    text("SELECT actor_id FROM reference_provider_effects WHERE id=:id"), {"id": first["effect"]}
                )
                == google.actor
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='apify'"))
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.contacts_retry_authorized'")
                )
                == 1
            )
            payload = await connection.scalar(
                text("SELECT payload FROM outbox_events WHERE id=:id"), {"id": UUID(result["event_id"])}
            )
            assert set(payload) == {"business_id", "actor_id", "operation_id"}
        with pytest.raises(DBAPIError, match="REFERENCE_RETRY_ALREADY_AUTHORIZED"):
            await _authorize(
                worker,
                google,
                seeded["a2"],
                {**values, "operation": uuid4(), "authorization": uuid4(), "event": uuid4()},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await _authorize(worker, google, google.actor, values)
    finally:
        await _finish(admin, worker)


async def test_competing_owners_create_only_one_authorization(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)

    def params():
        return {
            "business": google.business,
            "lookup": first["lookup"],
            "authorization": uuid4(),
            "operation": uuid4(),
            "event": uuid4(),
        }

    try:
        results = await asyncio.gather(
            _authorize(worker, google, google.actor, params()),
            _authorize(worker, google, seeded["a2"], params()),
            return_exceptions=True,
        )
        assert sum(isinstance(item, dict) and item["created"] for item in results) == 1
        assert (
            sum(isinstance(item, DBAPIError) and "REFERENCE_RETRY_ALREADY_AUTHORIZED" in str(item) for item in results)
            == 1
        )
    finally:
        await _finish(admin, worker)


async def test_changed_hold_or_context_never_authorizes_retry(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_cost_reservations SET reserved_usd_micros=39 WHERE effect_id=:id"),
                {"id": first["effect"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _authorize(worker, google, seeded["a2"], values)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_cost_reservations SET reserved_usd_micros=40 WHERE effect_id=:id"),
                {"id": first["effect"]},
            )
            await connection.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await _authorize(worker, google, seeded["a2"], values)
    finally:
        await _finish(admin, worker)


async def test_viewer_cross_tenant_and_replay_by_another_owner_are_rejected(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        assert (await _authorize(worker, google, seeded["a2"], values))["created"] is True
        with pytest.raises(DBAPIError, match="REFERENCE_RETRY_AUTH_CONFLICT"):
            await _authorize(worker, google, google.actor, values)
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await _authorize(worker, google, seeded["viewer"], values)
        with pytest.raises(DBAPIError, match="REFERENCE_RETRY_CYCLE_INACTIVE"):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(
                    text(
                        "SELECT public.reference_authorize_shared_contacts_retry("
                        ":business,:lookup,:authorization,:operation,:event)"
                    ),
                    values,
                )
    finally:
        await _finish(admin, worker)


async def test_owner_revocation_wins_before_shared_retry_authorization(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": google.tenant, "actor": seeded["a2"]},
            )
            pending = asyncio.create_task(_authorize(worker, google, seeded["a2"], values))
            await asyncio.sleep(0.15)
            assert not pending.done()
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await asyncio.wait_for(pending, 3)
    finally:
        await _finish(admin, worker)


async def test_migration_rejects_inherited_public_access_to_executor_token(admin):
    module = import_module("migrations.versions.0098_shared_retry_authorization")
    later = import_module("migrations.versions.0099_similarity_snapshot")

    def run_migration(sync, direction):
        with Operations.context(MigrationContext.configure(sync)):
            if direction == "downgrade":
                later.downgrade()
            getattr(module, direction)()

    async with admin.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.run_sync(lambda sync: run_migration(sync, "downgrade"))
            await connection.execute(text("GRANT SELECT(executor_token) ON reference_provider_effects TO PUBLIC"))
            with pytest.raises(DBAPIError, match="UNSAFE_REFERENCE_PROOF_TOKEN_ACCESS"):
                async with connection.begin_nested():
                    await connection.run_sync(lambda sync: run_migration(sync, "upgrade"))
        finally:
            await transaction.rollback()


async def test_expired_cycle_and_tampered_failure_event_fail_closed(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE reference_real_cycles SET confirmed_at=clock_timestamp()-interval '6 months', "
                    "locked_until=clock_timestamp()-interval '1 second' "
                    "WHERE tenant_id=:tenant AND business_id=:business"
                ),
                {"tenant": google.tenant, "business": google.business},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_RETRY_CYCLE_INACTIVE"):
            await _authorize(worker, google, seeded["a2"], values)
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE reference_real_cycles SET locked_until=clock_timestamp()+interval '1 day' "
                    "WHERE tenant_id=:tenant AND business_id=:business"
                ),
                {"tenant": google.tenant, "business": google.business},
            )
            await connection.execute(
                text(
                    "UPDATE outbox_events SET payload=jsonb_set(payload,'{actor_id}',to_jsonb(CAST(:actor AS text))) "
                    "WHERE id=(SELECT event_id FROM reference_contacts_failure_proofs WHERE effect_id=:effect)"
                ),
                {"actor": str(seeded["a2"]), "effect": first["effect"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _authorize(worker, google, seeded["a2"], values)
    finally:
        await _finish(admin, worker)


async def test_conflicting_lookup_and_authorization_replay_fail_closed(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        await _authorize(worker, google, seeded["a2"], values)
        for altered in ({"lookup": uuid4()}, {"authorization": uuid4()}):
            with pytest.raises(DBAPIError, match="REFERENCE_RETRY_AUTH_CONFLICT"):
                await _authorize(worker, google, seeded["a2"], {**values, **altered})
    finally:
        await _finish(admin, worker)


async def test_intermediate_attempt_requires_all_unaltered_failure_proofs(admin, api, seeded, settings):
    from app.tests.integration.test_reference_contacts_retry import _proof, _second

    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    try:
        async with admin.begin() as connection:
            await connection.execute(text(f"REVOKE EXECUTE ON FUNCTION {_FAILURE} FROM meu_braco_direito_correlator"))
        second = await _second(admin, google, first)
        second_started = await _call(worker, google, second)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _authorize(worker, google, seeded["a2"], values)
        await _proof(worker, google, second, UUID(second_started["executor_token"]))
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE outbox_events SET payload=jsonb_set(payload,'{actor_id}',to_jsonb(CAST(:actor AS text))) "
                    "WHERE id=(SELECT event_id FROM reference_contacts_failure_proofs WHERE effect_id=:effect)"
                ),
                {"actor": str(seeded["a2"]), "effect": first["effect"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _authorize(worker, google, seeded["a2"], values)
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE outbox_events SET payload=jsonb_set(payload,'{actor_id}',to_jsonb(CAST(:actor AS text))) "
                    "WHERE id=(SELECT event_id FROM reference_contacts_failure_proofs WHERE effect_id=:effect)"
                ),
                {"actor": str(google.actor), "effect": first["effect"]},
            )
        assert (await _authorize(worker, google, seeded["a2"], values))["created"] is True
    finally:
        await _finish(admin, worker)


async def test_downgrade_rejects_recorded_authorization_without_losing_it(admin, api, seeded, settings):
    google, worker, first = await _prepare(admin, api, seeded, settings)
    values = {
        "business": google.business,
        "lookup": first["lookup"],
        "authorization": uuid4(),
        "operation": uuid4(),
        "event": uuid4(),
    }
    module = import_module("migrations.versions.0098_shared_retry_authorization")
    try:
        await _authorize(worker, google, seeded["a2"], values)
        async with admin.connect() as connection:
            transaction = await connection.begin()
            try:

                def downgrade(sync):
                    with Operations.context(MigrationContext.configure(sync)):
                        module.downgrade()

                with pytest.raises(DBAPIError, match="REFERENCE_SHARED_RETRY_PREVENTS_AUTOMATIC_DOWNGRADE"):
                    async with connection.begin_nested():
                        await connection.run_sync(downgrade)
            finally:
                await transaction.rollback()
        assert (await _authorize(worker, google, seeded["a2"], values))["created"] is False
    finally:
        await _finish(admin, worker)
