"""Second Jev effect uses the same budget and cannot bypass shortlist proof."""

import asyncio
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _commit, _linked
from app.tests.integration.test_reference_private_shortlist import seed_header_if_needed

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]
_SIGNATURE = "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,uuid,text,bigint"
_SQL = text("""SELECT public.reference_reco_claim(:effect,:event,:mac,:business,:search,:pilot,:amount,:key,:tariff,
  :credential,:mask,:google,:similarity,:batch,:shortlist,:context)""")


async def test_recommendation_claim_is_separate_budgeted_fenced_and_inactive_by_default(admin, api, seeded, settings):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    filtered = _params(google, jev, gg, jg, candidate)
    try:
        await _commit(worker, google, filtered)
        effect, event = uuid4(), uuid4()
        params = {
            "effect": effect,
            "event": event,
            "mac": "b" * 64,
            "business": google.business,
            "search": google.search,
            "pilot": google.pilot,
            "amount": 1,
            "key": jev.key_version,
            "tariff": jev.tariff_version,
            "credential": jev.credential_version,
            "mask": "jev-model:jev-test-model",
            "google": google.effect,
            "similarity": jev.effect,
            "batch": filtered["batch"],
            "shortlist": "c" * 64,
            "context": 1,
        }
        async with admin.begin() as connection:
            await seed_header_if_needed(connection, google, filtered["batch"])
            await connection.execute(
                text("UPDATE reference_provider_pilots SET cap_usd_micros=101 WHERE id=:id"), {"id": google.pilot}
            )
            await connection.execute(
                text("""INSERT INTO reference_private_shortlist
              (tenant_id,business_id,batch_id,candidate_id,position) VALUES(:tenant,:business,:batch,:candidate,1)"""),
                {
                    "tenant": google.tenant,
                    "business": google.business,
                    "batch": filtered["batch"],
                    "candidate": candidate,
                },
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
              (tenant_id,business_id,actor_id,id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
               credential_version,field_mask,reserved_usd_micros,state,parent_google_effect_id,source_batch_mac,
               request_event_id,purpose,recommendation_batch_id,shortlist_mac)
              VALUES(:tenant,:business,:actor,:effect,:search,:pilot,'jev',:mac,:key,:tariff,:credential,:mask,
                :amount,'pending',:google,:source,:event,'recommendation',:batch,:shortlist)"""),
                {**params, "tenant": google.tenant, "actor": google.actor, "source": jev.source_batch_mac},
            )

        async def claim(values):
            async with worker.transaction(google.tenant, google.actor) as session:
                return await session.scalar(_SQL, values)

        with pytest.raises(DBAPIError):
            await claim(params)
        async with worker.transaction(google.tenant, google.actor) as session:
            with pytest.raises(DBAPIError, match="REFERENCE_JEV_PURPOSE_INVALID"):
                await session.scalar(
                    text("""SELECT public.reference_jev_claim(
                  :effect,:event,:mac,:business,:search,:pilot,:amount,:key,:tariff,:credential,:mask,
                  :google,:token,:source,:context)"""),
                    {**params, "token": gg.execution_token(), "source": jev.source_batch_mac},
                )
        # Only the dedicated disposable test database grants this unfinished guard.
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    f"GRANT EXECUTE ON FUNCTION public.reference_reco_claim({_SIGNATURE}) "
                    "TO meu_braco_direito_correlator"
                )
            )
        for bad in (
            {"shortlist": "d" * 64},
            {"batch": uuid4()},
            {"google": uuid4()},
            {"similarity": uuid4()},
            {"event": uuid4()},
            {"context": 2},
        ):
            with pytest.raises(DBAPIError):
                await claim({**params, **bad})
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_effects SET source_batch_mac=:mac WHERE id=:id"),
                {"mac": "f" * 64, "id": jev.effect},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_RECO_LINK_INVALID"):
            await claim(params)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_effects SET source_batch_mac=:mac WHERE id=:id"),
                {"mac": jev.source_batch_mac, "id": jev.effect},
            )
            await connection.execute(
                text("UPDATE reference_provider_pilots SET cap_usd_micros=100 WHERE id=:id"), {"id": google.pilot}
            )
        with pytest.raises(DBAPIError, match="REFERENCE_PILOT_BUDGET_EXCEEDED"):
            await claim(params)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_provider_pilots SET cap_usd_micros=101 WHERE id=:id"), {"id": google.pilot}
            )

        async def run():
            return await claim(params)

        outcomes = await asyncio.gather(run(), run())
        assert sorted(result["created"] for result in outcomes) == [False, True]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": google.tenant, "actor": google.actor},
            )
        assert (await claim(params))["created"] is False
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 101
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 3
            with pytest.raises(DBAPIError, match="REFERENCE_RECO_PREVENTS_AUTOMATIC_DOWNGRADE"):
                async with connection.begin_nested():
                    await connection.run_sync(_downgrade)
    finally:
        await worker.close()
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    f"REVOKE EXECUTE ON FUNCTION public.reference_reco_claim({_SIGNATURE}) "
                    "FROM meu_braco_direito_correlator"
                )
            )


def _downgrade(connection):
    migration = import_module("migrations.versions.0089_reference_reco_guard")
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
