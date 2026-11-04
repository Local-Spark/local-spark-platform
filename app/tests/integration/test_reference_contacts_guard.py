"""Inactive contacts effects are tied to one candidate per Place ID/cycle."""

import asyncio
from dataclasses import replace
from importlib import import_module
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.apify_place_contacts import ApifyPlaceContacts
from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.services.reference_contacts_budget_guard import (
    ContactsGuardContext,
    ContactsGuardError,
    DatabaseContactsBudgetGuard,
)
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard
from app.tests.integration.test_reference_discovery import create_business
from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _commit
from app.tests.integration.test_reference_jev_budget_guard import _google_started, _jev_intent

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]
_SIGNATURE = "uuid,uuid,uuid,uuid,text,uuid,bigint,text,text,text,text"
_SQL = text("""SELECT public.reference_contacts_claim(:business,:lookup,:effect,:event,:mac,:pilot,:amount,
  :key,:tariff,:credential,:class)""")


async def _setup(admin, api, seeded, settings):
    google, gg, worker = await _google_started(admin, api, seeded, settings, cap=150)
    candidate = uuid4()
    data = SimilarityInput(("cafe",), None, (SimilarityCandidate(candidate, "fixture", ("cafe",)),))
    jev, request = await _jev_intent(admin, worker, google, gg.execution_token(), data)
    jg = DatabaseJevBudgetGuard(worker, jev)
    assert await jg.claim(jev.effect, request)
    batch = _params(google, jev, gg, jg, candidate)
    await _commit(worker, google, batch)
    cycle, shortlist_event, effect, event, lookup = (uuid4() for _ in range(5))
    shortlist_operation = uuid4()
    tariff = "contacts-test-" + uuid4().hex
    params = {
        "business": google.business,
        "lookup": lookup,
        "effect": effect,
        "event": event,
        "mac": "c" * 64,
        "pilot": google.pilot,
        "amount": 40,
        "key": "contacts-key",
        "tariff": tariff,
        "credential": "contacts-credential",
        "class": "apify-place-contacts:1.2.3",
    }
    async with admin.begin() as connection:
        assert not await connection.scalar(
            text(f"""SELECT has_function_privilege('meu_braco_direito_correlator',
          'public.reference_contacts_claim({_SIGNATURE})','EXECUTE')""")
        )
        await connection.execute(
            text(
                f"GRANT EXECUTE ON FUNCTION public.reference_contacts_claim({_SIGNATURE}) "
                "TO meu_braco_direito_correlator"
            )
        )
        await connection.execute(
            text("""INSERT INTO reference_real_cycles(tenant_id,business_id,id)
          VALUES(:tenant,:business,:cycle)"""),
            {"tenant": google.tenant, "business": google.business, "cycle": cycle},
        )
        await connection.execute(
            text("""UPDATE reference_provider_searches
          SET cycle_id=:cycle,radius_km=5,identity_key_version='fixture-key'
          WHERE tenant_id=:tenant AND business_id=:business AND id=:search"""),
            {"tenant": google.tenant, "business": google.business, "search": google.search, "cycle": cycle},
        )
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:id,:tenant,'reference.private_shortlist_prepared',jsonb_build_object(
            'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
            'operation_id',CAST(:op AS text)))"""),
            {
                "id": shortlist_event,
                "tenant": google.tenant,
                "business": str(google.business),
                "actor": str(google.actor),
                "op": str(shortlist_operation),
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_private_shortlist_headers
          (tenant_id,business_id,batch_id,actor_id,operation_id,event_id)
          VALUES(:tenant,:business,:batch,:actor,:op,:event)"""),
            {
                "tenant": google.tenant,
                "business": google.business,
                "batch": batch["batch"],
                "actor": google.actor,
                "op": shortlist_operation,
                "event": shortlist_event,
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_private_shortlist
          (tenant_id,business_id,batch_id,candidate_id,position) VALUES(:tenant,:business,:batch,:candidate,1)"""),
            {"tenant": google.tenant, "business": google.business, "batch": batch["batch"], "candidate": candidate},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active) VALUES(:v,'apify',:class,1,true)"""),
            {"v": tariff, "class": params["class"]},
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
          VALUES(:effect,:tenant,:business,:actor,:search,:pilot,'apify',:mac,:key,:tariff,:credential,:class,
            :amount,'pending',:google,:source,:event)"""),
            {
                **params,
                "tenant": google.tenant,
                "actor": google.actor,
                "search": google.search,
                "google": google.effect,
                "source": jev.source_batch_mac,
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_contacts_lookups
          (tenant_id,business_id,id,actor_id,cycle_id,search_id,batch_id,candidate_id,place_id)
          VALUES(:tenant,:business,:lookup,:actor,:cycle,:search,:batch,:candidate,'fake-place')"""),
            {
                **params,
                "tenant": google.tenant,
                "actor": google.actor,
                "cycle": cycle,
                "search": google.search,
                "batch": batch["batch"],
                "candidate": candidate,
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id)
          VALUES(:tenant,:business,:lookup,:effect)"""),
            {**params, "tenant": google.tenant},
        )
    return google, worker, cycle, batch, candidate, params


async def _call(worker, google, params):
    async with worker.transaction(google.tenant, google.actor) as session:
        return await session.scalar(_SQL, params)


async def _revoke(admin):
    async with admin.begin() as connection:
        await connection.execute(
            text(
                f"REVOKE EXECUTE ON FUNCTION public.reference_contacts_claim({_SIGNATURE}) "
                "FROM meu_braco_direito_correlator"
            )
        )


async def test_contacts_is_one_effect_per_cycle_and_holds_uncertain_cost(admin, api, seeded, settings):
    google, worker, cycle, batch, candidate, params = await _setup(admin, api, seeded, settings)
    try:
        first = await _call(worker, google, params)
        assert first["created"] is True and (await _call(worker, google, params))["created"] is False
        with pytest.raises(DBAPIError):
            async with admin.begin() as connection:
                await connection.execute(
                    text("""INSERT INTO reference_contacts_lookups
                  (tenant_id,business_id,id,actor_id,cycle_id,search_id,batch_id,candidate_id,place_id)
                  VALUES(:tenant,:business,:id,:actor,:cycle,:search,:batch,:candidate,'fake-place')"""),
                    {
                        "tenant": google.tenant,
                        "business": google.business,
                        "id": uuid4(),
                        "actor": google.actor,
                        "cycle": cycle,
                        "search": google.search,
                        "batch": batch["batch"],
                        "candidate": candidate,
                    },
                )
        with pytest.raises(DBAPIError):
            async with worker.transaction(google.tenant, google.actor) as session:
                await session.scalar(
                    text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                    {"effect": params["effect"], "token": uuid4()},
                )
        async with worker.transaction(google.tenant, google.actor) as session:
            assert (
                await session.scalar(
                    text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                    {"effect": params["effect"], "token": UUID(first["executor_token"])},
                )
                == "uncertain"
            )
        assert (await _call(worker, google, params))["state"] == "uncertain"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 140
    finally:
        await worker.close()
        await _revoke(admin)


async def test_contacts_guard_binds_request_credential_and_refuses_inspection(admin, api, seeded, settings):
    google, worker, cycle, batch, candidate, params = await _setup(admin, api, seeded, settings)
    context = ContactsGuardContext(
        tenant=google.tenant,
        business=google.business,
        actor=google.actor,
        cycle=cycle,
        batch=batch["batch"],
        candidate=candidate,
        place_id="fake-place",
        lookup=params["lookup"],
        effect=params["effect"],
        event=params["event"],
        pilot=google.pilot,
        context_version=1,
        key=google.key,
        key_version=params["key"],
        tariff_version=params["tariff"],
        credential_version=params["credential"],
        reserved_usd_micros=40,
        build="1.2.3",
        provider_actor_id="actor-id",
    )
    token = SecretStr("synthetic-key")
    request = ApifyPlaceContacts._request(
        "POST",
        "https://api.apify.com/v2/acts/actor-id/runs",
        token,
        params={
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.00004",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        },
        body={
            "placeIds": ["fake-place"],
            "scrapeContacts": True,
            "maxCrawledPlacesPerSearch": 1,
            "language": "pt-BR",
        },
    )
    binding = ApifyPlaceContacts._bind(request, token, "actor-id")
    guard = DatabaseContactsBudgetGuard(worker, context)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE reference_provider_effects SET request_mac=:mac WHERE id=:effect"),
            {"mac": guard._request_mac(binding), "effect": context.effect},
        )
    try:
        with pytest.raises(ContactsGuardError, match="CONTACTS_ACTOR_BINDING_INVALID"):
            guard._request_mac(replace(binding, provider_actor_id="other"))
        assert await guard.claim_submission(uuid4(), binding) is False
        with pytest.raises(ContactsGuardError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
            await guard.submission_uncertain(context.effect, binding)
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_INTENT_INVALID"):
            await DatabaseContactsBudgetGuard(worker, context).claim_submission(
                context.effect, replace(binding, credential=SecretStr("different-key"))
            )
        assert await guard.claim_submission(context.effect, binding) is True
        assert await guard.claim_submission(context.effect, binding) is False
        with pytest.raises(ContactsGuardError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
            await guard.submission_uncertain(uuid4(), binding)
        await guard.submission_uncertain(context.effect, binding)
        assert await DatabaseContactsBudgetGuard(worker, context).claim_submission(context.effect, binding) is False
        assert await guard.claim_inspection(uuid4(), None) is False
        with pytest.raises(ContactsGuardError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
            await guard.inspection_uncertain(uuid4(), None)
    finally:
        await worker.close()
        await _revoke(admin)


async def test_contacts_claim_is_single_use_under_concurrency(admin, api, seeded, settings):
    google, worker, _, _, _, params = await _setup(admin, api, seeded, settings)
    try:
        results = await asyncio.gather(_call(worker, google, params), _call(worker, google, params))
        assert sorted(item["created"] for item in results) == [False, True]
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 140
    finally:
        await worker.close()
        await _revoke(admin)


async def test_contacts_rejects_forged_event_mac_and_other_tenant(admin, api, seeded, settings):
    google, worker, _, _, _, params = await _setup(admin, api, seeded, settings)
    duplicate = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          SELECT :new,tenant_id,event_type,payload FROM outbox_events WHERE id=:original"""),
            {"new": duplicate, "original": params["event"]},
        )
    try:
        for changed in ({"event": duplicate}, {"mac": "d" * 64}, {"pilot": uuid4()}, {"amount": 1}):
            with pytest.raises(DBAPIError):
                await _call(worker, google, {**params, **changed})
        with pytest.raises(DBAPIError):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_SQL, params)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
    finally:
        await worker.close()
        await _revoke(admin)


@pytest.mark.parametrize("changed", ["place", "context", "pilot", "shortlist_event"])
async def test_contacts_blocks_wrong_source_changed_context_and_pilot_limit(admin, api, seeded, settings, changed):
    google, worker, _, batch, _, params = await _setup(admin, api, seeded, settings)
    statements = {
        "place": ("UPDATE reference_contacts_lookups SET place_id='other' WHERE id=:id", params["lookup"]),
        "context": ("UPDATE business_context_heads SET version=2 WHERE business_id=:id", google.business),
        "pilot": ("UPDATE reference_provider_pilots SET cap_usd_micros=139 WHERE id=:id", google.pilot),
        "shortlist_event": (
            "UPDATE reference_private_shortlist_headers SET operation_id=gen_random_uuid() WHERE batch_id=:id",
            batch["batch"],
        ),
    }
    try:
        statement, identifier = statements[changed]
        async with admin.begin() as connection:
            await connection.execute(text(statement), {"id": identifier})
        with pytest.raises(
            DBAPIError,
            match={"pilot": "REFERENCE_PILOT_BUDGET_EXCEEDED", "context": "REFERENCE_CONTEXT_STALE"}.get(
                changed, "REFERENCE_CONTACTS_SOURCE_INVALID"
            ),
        ):
            await _call(worker, google, params)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 100
    finally:
        await worker.close()
        await _revoke(admin)


async def test_place_id_index_accepts_multibyte_at_technical_limit_and_rejects_overflow(admin, api, seeded, settings):
    google, worker, cycle, batch, candidate, params = await _setup(admin, api, seeded, settings)
    query = text("""INSERT INTO reference_contacts_lookups
      (tenant_id,business_id,id,actor_id,cycle_id,search_id,batch_id,candidate_id,place_id)
      VALUES(:tenant,:business,:id,:actor,:cycle,:search,:batch,:candidate,:place)""")
    data = {
        "tenant": google.tenant,
        "business": google.business,
        "actor": google.actor,
        "cycle": cycle,
        "search": google.search,
        "batch": batch["batch"],
        "candidate": candidate,
    }
    long_place = "".join(chr(0x4E00 + index) for index in range(2048))
    try:
        async with admin.begin() as connection:
            await connection.execute(query, {**data, "id": uuid4(), "place": long_place})
            await connection.execute(
                text("""INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id)
              VALUES(:tenant,:business,:id,:place)"""),
                {"tenant": google.tenant, "business": google.business, "id": uuid4(), "place": long_place},
            )
            await connection.execute(
                text("""INSERT INTO reference_filtered_batch_candidates
              (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,reputation_score,
               reputation_formula_version)
              VALUES(:tenant,:business,:actor,:batch,:candidate,2,:place,5,'penalized-3.4-v1')"""),
                {**data, "candidate": uuid4(), "place": long_place},
            )
        for place in (long_place, long_place + "x"):
            with pytest.raises(DBAPIError):
                async with admin.begin() as connection:
                    await connection.execute(query, {**data, "id": uuid4(), "place": place})
        with pytest.raises(DBAPIError):
            async with admin.begin() as connection:
                await connection.execute(
                    text("""INSERT INTO reference_provider_places
                  (tenant_id,business_id,id,place_id) VALUES(:tenant,:business,:id,:place)"""),
                    {"tenant": google.tenant, "business": google.business, "id": uuid4(), "place": long_place},
                )
        with pytest.raises(DBAPIError):
            async with admin.begin() as connection:
                await connection.execute(
                    text("""INSERT INTO reference_filtered_batch_candidates
                  (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,reputation_score,
                   reputation_formula_version)
                  VALUES(:tenant,:business,:actor,:batch,:candidate,3,:place,5,'penalized-3.4-v1')"""),
                    {**data, "candidate": uuid4(), "place": long_place},
                )
    finally:
        await worker.close()
        await _revoke(admin)


async def test_downgrade_refuses_long_existing_id_without_losing_data(admin, seeded):
    business = await create_business(admin, seeded["t1"])
    long_place = "".join(chr(0x4E00 + index) for index in range(2048))
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id)
          VALUES(:tenant,:business,:id,:place)"""),
            {"tenant": seeded["t1"], "business": business, "id": uuid4(), "place": long_place},
        )
    async with admin.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("ALTER TABLE reference_provider_tariffs DISABLE TRIGGER USER"))
            await connection.execute(
                text("DELETE FROM reference_provider_tariffs WHERE field_mask LIKE 'apify-place-contacts:%'")
            )
            with pytest.raises(DBAPIError, match="REFERENCE_PLACE_ID_PREVENTS_AUTOMATIC_DOWNGRADE"):
                async with connection.begin_nested():

                    def downgrade(sync):
                        migration = import_module("migrations.versions.0095_reference_contacts_guard")
                        with Operations.context(MigrationContext.configure(sync)):
                            migration.downgrade()

                    await connection.run_sync(downgrade)
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM reference_provider_places WHERE place_id=:place"), {"place": long_place}
                )
                == 1
            )
        finally:
            await transaction.rollback()
