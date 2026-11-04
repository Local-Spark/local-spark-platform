"""Disposable DB tests of an inactive retry prototype."""

import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_contacts_guard import _call, _revoke, _setup

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]


async def _second(admin, google, params):
    effect, event = uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_provider_pilots SET cap_usd_micros=200 WHERE id=:id"), {"id": google.pilot}
        )
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:event,:tenant,'reference.provider_effect_requested',jsonb_build_object(
            'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
            'operation_id',CAST(:effect AS text)))"""),
            {
                "event": event,
                "tenant": google.tenant,
                "business": str(google.business),
                "actor": str(google.actor),
                "effect": str(effect),
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
           credential_version,field_mask,reserved_usd_micros,state,parent_google_effect_id,source_batch_mac,request_event_id)
          SELECT :new,tenant_id,business_id,actor_id,search_id,pilot_id,provider,:mac,key_version,tariff_version,
            credential_version,field_mask,reserved_usd_micros,'pending',parent_google_effect_id,source_batch_mac,:event
          FROM reference_provider_effects WHERE id=:previous"""),
            {"new": effect, "event": event, "previous": params["effect"], "mac": "d" * 64},
        )
        await connection.execute(
            text("""INSERT INTO reference_contacts_effect_links
          (tenant_id,business_id,lookup_id,effect_id,attempt_no,previous_effect_id)
          VALUES(:tenant,:business,:lookup,:effect,2,:previous)"""),
            {
                "tenant": google.tenant,
                "business": google.business,
                "lookup": params["lookup"],
                "effect": effect,
                "previous": params["effect"],
            },
        )
        allowed = await connection.scalar(
            text("""SELECT has_function_privilege('meu_braco_direito_correlator',
          'public.reference_contacts_not_dispatched(uuid,uuid,uuid,uuid)','EXECUTE')""")
        )
        assert allowed is False
        await connection.execute(
            text("""GRANT EXECUTE ON FUNCTION public.reference_contacts_not_dispatched(
          uuid,uuid,uuid,uuid) TO meu_braco_direito_correlator""")
        )
    return {**params, "effect": effect, "event": event, "mac": "d" * 64}


async def _proof(worker, google, params, token):
    async with worker.transaction(google.tenant, google.actor) as session:
        return await session.scalar(
            text("""SELECT public.reference_contacts_not_dispatched(
          :business,:lookup,:effect,:token)"""),
            {**params, "token": token},
        )


async def _revoke_proof(admin):
    async with admin.begin() as connection:
        await connection.execute(
            text("""REVOKE EXECUTE ON FUNCTION public.reference_contacts_not_dispatched(
          uuid,uuid,uuid,uuid) FROM meu_braco_direito_correlator""")
        )


async def test_retry_requires_durable_fenced_non_dispatch_and_new_budget(admin, api, seeded, settings):
    google, worker, _, _, _, first = await _setup(admin, api, seeded, settings)
    try:
        second = await _second(admin, google, first)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)
        started = await _call(worker, google, first)
        assert started["created"] is True
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_FAILURE_INVALID"):
            await _proof(worker, google, first, uuid4())
        proof = await _proof(worker, google, first, UUID(started["executor_token"]))
        assert await _proof(worker, google, first, UUID(started["executor_token"])) == proof
        results = await asyncio.gather(_call(worker, google, second), _call(worker, google, second))
        assert sorted(row["created"] for row in results) == [False, True]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 180
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE effect_id=:id"), {"id": first["effect"]}
                )
                == "uncertain"
            )
            assert await connection.scalar(text("SELECT count(*) FROM reference_contacts_failure_proofs")) == 1
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.contacts_not_dispatched'")
                )
                == 1
            )
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)


async def test_ambiguous_effect_cannot_be_reclassified_or_retried(admin, api, seeded, settings):
    google, worker, _, _, _, first = await _setup(admin, api, seeded, settings)
    try:
        second = await _second(admin, google, first)
        started = await _call(worker, google, first)
        async with worker.transaction(google.tenant, google.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": first["effect"], "token": UUID(started["executor_token"])},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_FAILURE_INVALID"):
            await _proof(worker, google, first, UUID(started["executor_token"]))
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 140
            assert await connection.scalar(text("SELECT count(*) FROM reference_contacts_failure_proofs")) == 0
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)


@pytest.mark.parametrize("state", ["failed_definitive", "completed_filtered"])
async def test_status_without_failure_proof_never_unlocks_retry(admin, api, seeded, settings, state):
    google, worker, _, _, _, first = await _setup(admin, api, seeded, settings)
    try:
        second = await _second(admin, google, first)
        assert (await _call(worker, google, first))["created"] is True
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_effects SET state=:state WHERE id=:id"),
                {"state": state, "id": first["effect"]},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)


async def test_other_owner_cannot_assume_prior_executor_in_draft(admin, api, seeded, settings):
    google, worker, _, _, _, first = await _setup(admin, api, seeded, settings)
    try:
        await _second(admin, google, first)
        started = await _call(worker, google, first)
        async with admin.begin() as connection:
            await connection.execute(
                text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
                {"tenant": google.tenant, "actor": seeded["a2"]},
            )
        other = replace(google, actor=seeded["a2"])
        with pytest.raises(DBAPIError):
            await _proof(worker, other, first, UUID(started["executor_token"]))
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_contacts_failure_proofs")) == 0
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)


@pytest.mark.parametrize("field,changed,original", [("state", "claimed", "uncertain"), ("reserved_usd_micros", 39, 40)])
async def test_retry_rejects_missing_or_changed_prior_hold(admin, api, seeded, settings, field, changed, original):
    google, worker, _, _, _, first = await _setup(admin, api, seeded, settings)
    try:
        second = await _second(admin, google, first)
        started = await _call(worker, google, first)
        await _proof(worker, google, first, UUID(started["executor_token"]))
        async with admin.begin() as connection:
            await connection.execute(
                text(f"UPDATE reference_cost_reservations SET {field}=:value WHERE effect_id=:id"),
                {"id": first["effect"], "value": changed},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_RETRY_BLOCKED"):
            await _call(worker, google, second)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTACTS_FAILURE_INVALID"):
            await _proof(worker, google, first, UUID(started["executor_token"]))
        async with admin.begin() as connection:
            await connection.execute(
                text(f"UPDATE reference_cost_reservations SET {field}=:value WHERE effect_id=:id"),
                {"id": first["effect"], "value": original},
            )
        assert (await _call(worker, google, second))["created"] is True
    finally:
        await worker.close()
        await _revoke(admin)
        await _revoke_proof(admin)
