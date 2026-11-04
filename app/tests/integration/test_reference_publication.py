"""Publish synthetic, already-fenced provider outputs using restricted roles."""

import asyncio
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.reference_filtered_commit import FilteredCommitContext
from app.services.reference_publication import (
    CompletedContacts,
    CompletedEffect,
    CompletedRecommendation,
    PublicationProjection,
    publish_reference_shortlist,
)
from app.tests.integration.test_reference_discovery import access_token
from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _commit, _linked
from app.tests.integration.test_reference_real_selection import _result

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]
_SIGNATURE = "public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb)"


@pytest.fixture
async def prepared(admin, api, seeded, settings):
    google, jev, gg, jg, worker, first = await _linked(admin, api, seeded, settings)
    values = _params(google, jev, gg, jg, first)
    async with admin.connect() as conn:
        originally_allowed = await conn.scalar(
            text("SELECT has_function_privilege('meu_braco_direito_correlator',:f,'EXECUTE')"), {"f": _SIGNATURE}
        )
    try:
        await _commit(worker, google, values)
        base = f"/api/v1/organizations/{google.tenant}/businesses/{google.business}"
        address = await api.put(
            base + "/address",
            headers={"Authorization": f"Bearer {access_token(settings, google.actor)}"},
            json={
                "operation_id": str(uuid4()),
                "expected_version": 0,
                "address": {"street": "Rua Ficticia", "number": "10", "city": "São Paulo", "state_code": "SP"},
            },
        )
        assert address.status_code == 200
        cycle = uuid4()
        extra = [uuid4() for _ in range(12)]
        async with admin.begin() as conn:
            params = {"t": google.tenant, "b": google.business, "cycle": cycle, "s": google.search}
            await conn.execute(
                text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:t,:b,:cycle)"), params
            )
            await conn.execute(text("INSERT INTO reference_real_heads VALUES(:t,:b,:cycle)"), params)
            await conn.execute(
                text(
                    "UPDATE reference_provider_searches SET cycle_id=:cycle,radius_km=5,"
                    "identity_key_version='synthetic-v1' WHERE id=:s"
                ),
                params,
            )
            await conn.execute(
                text("UPDATE reference_provider_effects SET request_event_id=:event WHERE id=:id"),
                {"event": google.event, "id": google.effect},
            )
            for n, candidate in enumerate(extra, start=1):
                await conn.execute(
                    text("""INSERT INTO reference_filtered_batch_candidates
                  (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,
                   reputation_score,reputation_formula_version)
                  VALUES(:t,:b,:a,:batch,:id,:position,:place,:score,'penalized-3.4-v1')"""),
                    {
                        **params,
                        "a": google.actor,
                        "batch": values["batch"],
                        "id": candidate,
                        "position": n + 1,
                        "place": f"synthetic-publication-{n}",
                        "score": str(n / 2),
                    },
                )
            await conn.execute(text("SELECT set_config('app.tenant_id',:v,true)"), {"v": str(google.tenant)})
            await conn.execute(text("SELECT set_config('app.actor_id',:v,true)"), {"v": str(google.actor)})
            own = await conn.scalar(text("SELECT reference_prepare_business_identity(:b)"), {"b": google.business})
            await conn.execute(
                text("""UPDATE reference_provider_searches SET business_name=:name,business_row_version=:row,
              business_address_version=:address,business_location_version=:location,
              business_identity_mac=:mac WHERE id=:s"""),
                {
                    "name": own["name"],
                    "row": own["row_version"],
                    "address": own["address_version"],
                    "location": own["location_version"],
                    "mac": "f" * 64,
                    "s": google.search,
                },
            )
            await conn.execute(text(f"REVOKE EXECUTE ON FUNCTION {_SIGNATURE} FROM meu_braco_direito_correlator"))
            review_event = uuid4()
            await conn.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              SELECT :event,tenant_id,'reference.own_business_match_recorded',jsonb_build_object(
                'business_id',business_id::text,'actor_id',actor_id::text,'operation_id',operation_id::text)
              FROM reference_provider_searches WHERE id=:search"""),
                {"event": review_event, "search": google.search},
            )
            await conn.execute(
                text("""INSERT INTO reference_own_business_reviews
              (tenant_id,business_id,search_id,batch_id,original_actor,request_hash,status,possible_place_ids,event_id)
              VALUES(:t,:b,:s,:batch,:a,:hash,'resolved','{}',:event)"""),
                {**params, "batch": values["batch"], "a": google.actor, "hash": "f" * 64, "event": review_event},
            )
            ordered = [first, *reversed(extra[3:])]
            await conn.scalar(
                text("SELECT reference_prepare_shortlist(:b,:s,:batch,:operation,:ids)"),
                {**params, "batch": values["batch"], "operation": uuid4(), "ids": ordered},
            )
        context = FilteredCommitContext(
            tenant=google.tenant,
            business=google.business,
            actor=google.actor,
            search=google.search,
            batch=values["batch"],
            google_effect=google.effect,
            google_event=google.event,
            google_token=gg.execution_token(),
            jev_effect=jev.effect,
            jev_event=jev.event,
            jev_token=jg.execution_token(),
            source_batch_mac=values["source"],
            context_version=1,
        )
        yield context, worker, cycle, ordered
    finally:
        async with admin.begin() as conn:
            await conn.execute(text(f"REVOKE EXECUTE ON FUNCTION {_SIGNATURE} FROM meu_braco_direito_correlator"))
            if originally_allowed:
                await conn.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIGNATURE} TO meu_braco_direito_correlator"))
        await worker.close()


async def _allow(admin):
    async with admin.begin() as conn:
        await conn.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIGNATURE} TO meu_braco_direito_correlator"))


async def test_publication_is_private_atomic_replayable_and_preserves_score_history(admin, api, settings, prepared):
    ctx, worker, cycle, ordered = prepared
    projection = PublicationProjection(operation_id=uuid4())
    with pytest.raises(DBAPIError):
        await publish_reference_shortlist(worker, ctx, projection)
    await _allow(admin)
    first, second = await asyncio.gather(
        publish_reference_shortlist(worker, ctx, projection), publish_reference_shortlist(worker, ctx, projection)
    )
    assert first == second
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_provider_result_candidates")) == 10
        assert await conn.scalar(text("SELECT count(*) FROM reference_filtered_batch_candidates")) == 10
        assert await conn.scalar(text("SELECT count(*) FROM reference_publication_operations")) == 1
        assert (
            await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.results_published'")) == 1
        )
        assert (
            await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations WHERE actual_usd_micros IS NULL"))
            == 2
        )
    base = f"/api/v1/organizations/{ctx.tenant}/businesses/{ctx.business}/reference-results"
    headers = {"Authorization": f"Bearer {access_token(settings, ctx.actor)}"}
    response = await api.get(base, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["discovery_available"] is False and data["cycle_review"] is None
    assert data["searches"][0]["recommendation_status"] == "unavailable"
    top = data["searches"][0]["candidates"][0]
    assert top["candidate_id"] == str(ordered[0]) and top["reputation_score"] == "8.25"
    assert top["instagram_handle"] is None and top["jev_recommendation_rank"] is None
    payload = {
        "operation_id": str(uuid4()),
        "cycle_id": str(cycle),
        "selection": [{"result_id": str(first), "candidate_id": str(ordered[0])}],
    }
    selected = await api.post(base + "/selection", headers=headers, json=payload)
    assert selected.status_code == 200
    assert (await api.post(base + "/selection", headers=headers, json=payload)).json() == selected.json()
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE reference_filtered_batch_candidates SET reputation_score=1"))
    assert (await api.get(base, headers=headers)).json()["selected"][0]["reputation_score"] == "8.25"
    with pytest.raises(DBAPIError, match="REFERENCE_PUBLICATION_CONFLICT"):
        await publish_reference_shortlist(worker, ctx, PublicationProjection(operation_id=uuid4()))


async def test_invalid_fence_context_and_client_input_never_publish(admin, api, settings, prepared, seeded):
    ctx, worker, cycle, ordered = prepared
    await _allow(admin)
    projection = PublicationProjection(operation_id=uuid4())
    with pytest.raises(DBAPIError, match="REFERENCE_PUBLICATION_FENCE_INVALID"):
        await publish_reference_shortlist(worker, replace(ctx, google_token=uuid4()), projection)
    with pytest.raises(DBAPIError):
        await publish_reference_shortlist(worker, replace(ctx, tenant=seeded["t2"], actor=seeded["a2"]), projection)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE business_context_heads SET version=2 WHERE business_id=:b"), {"b": ctx.business}
        )
    with pytest.raises(DBAPIError, match="REFERENCE_(PUBLICATION_CONTEXT_STALE|SEARCH_CONTEXT_INVALID)"):
        await publish_reference_shortlist(worker, ctx, projection)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_provider_results")) == 0
    url = f"/api/v1/organizations/{ctx.tenant}/businesses/{ctx.business}/reference-results/selection"
    payload = {
        "operation_id": str(uuid4()),
        "cycle_id": str(cycle),
        "selection": [{"result_id": str(uuid4()), "candidate_id": str(ordered[0]), "reputation_score": "10"}],
    }
    assert (
        await api.post(url, headers={"Authorization": f"Bearer {access_token(settings, ctx.actor)}"}, json=payload)
    ).status_code == 422


async def _completed_outputs(admin, ctx, ordered):
    reco, contacts, revent, cevent, rtoken, ctoken, lookup = [uuid4() for _ in range(7)]
    async with admin.begin() as conn:
        for effect, event in ((reco, revent), (contacts, cevent)):
            await conn.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:event,:t,'reference.provider_effect_requested',jsonb_build_object(
                'business_id',CAST(:b AS text),'actor_id',CAST(:a AS text),'operation_id',CAST(:id AS text)))"""),
                {"event": event, "t": ctx.tenant, "b": str(ctx.business), "a": str(ctx.actor), "id": str(effect)},
            )
        await conn.execute(
            text("""INSERT INTO reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
           credential_version,field_mask,reserved_usd_micros,state,executor_token,parent_google_effect_id,
           source_batch_mac,request_event_id,purpose,recommendation_batch_id,shortlist_mac)
          SELECT :id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
            credential_version,field_mask,reserved_usd_micros,'running',:token,parent_google_effect_id,
            source_batch_mac,:event,'recommendation',:batch,:mac FROM reference_provider_effects WHERE id=:source"""),
            {
                "id": reco,
                "token": rtoken,
                "event": revent,
                "batch": ctx.batch,
                "mac": "a" * 64,
                "source": ctx.jev_effect,
            },
        )
        await conn.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES('publication-apify','apify','apify-place-contacts:1.0.0',1,true) ON CONFLICT DO NOTHING""")
        )
        await conn.execute(
            text("""INSERT INTO reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
           credential_version,field_mask,reserved_usd_micros,state,executor_token,parent_google_effect_id,
           source_batch_mac,request_event_id)
          SELECT :id,tenant_id,business_id,actor_id,search_id,pilot_id,'apify',request_mac,key_version,
            'publication-apify',
            credential_version,'apify-place-contacts:1.0.0',1,'running',:token,parent_google_effect_id,
            source_batch_mac,:event FROM reference_provider_effects WHERE id=:source"""),
            {"id": contacts, "token": ctoken, "event": cevent, "source": ctx.jev_effect},
        )
        await conn.execute(
            text("""INSERT INTO reference_contacts_lookups
          (tenant_id,business_id,id,actor_id,cycle_id,search_id,batch_id,candidate_id,place_id)
          SELECT c.tenant_id,c.business_id,:id,c.actor_id,s.cycle_id,s.id,c.batch_id,c.candidate_id,c.place_id
          FROM reference_filtered_batch_candidates c JOIN reference_provider_searches s
            ON s.tenant_id=c.tenant_id AND s.business_id=c.business_id AND s.id=:search
          WHERE c.batch_id=:batch AND c.candidate_id=:candidate"""),
            {"id": lookup, "search": ctx.search, "batch": ctx.batch, "candidate": ordered[0]},
        )
        await conn.execute(
            text("""INSERT INTO reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id)
          VALUES(:t,:b,:lookup,:effect)"""),
            {"t": ctx.tenant, "b": ctx.business, "lookup": lookup, "effect": contacts},
        )
    return PublicationProjection(
        operation_id=uuid4(),
        recommendation=CompletedRecommendation(
            effect=CompletedEffect(effect_id=reco, event_id=revent, executor_token=rtoken),
            candidate_ids=tuple(ordered[:3]),
        ),
        contacts=(
            CompletedContacts(
                candidate_id=ordered[0],
                effect=CompletedEffect(effect_id=contacts, event_id=cevent, executor_token=ctoken),
                handles=("first_profile", "main_profile"),
                primary_handle="main_profile",
            ),
        ),
    )


async def test_provider_outputs_publish_only_three_highlights_and_trust_primary_profile(admin, api, settings, prepared):
    ctx, worker, cycle, ordered = prepared
    await _allow(admin)
    projection = await _completed_outputs(admin, ctx, ordered)
    result = await publish_reference_shortlist(worker, ctx, projection)
    assert await publish_reference_shortlist(worker, ctx, projection) == result
    url = f"/api/v1/organizations/{ctx.tenant}/businesses/{ctx.business}/reference-results"
    data = (await api.get(url, headers={"Authorization": f"Bearer {access_token(settings, ctx.actor)}"})).json()
    candidates = data["searches"][0]["candidates"]
    assert [x["jev_recommendation_rank"] for x in candidates] == [1, 2, 3, *([None] * 7)]
    assert candidates[0]["instagram_handle"] == "main_profile" and candidates[0]["profile_source"] == "apify"
    async with admin.connect() as conn:
        assert (
            await conn.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE state='completed_published'"))
            == 2
        )
        assert (
            await conn.scalar(text("SELECT count(*) FROM reference_cost_reservations WHERE actual_usd_micros IS NULL"))
            == 2
        )


async def test_wrong_profile_fence_rolls_back_recommendation_completion_and_whole_result(admin, prepared):
    ctx, worker, cycle, ordered = prepared
    await _allow(admin)
    projection = await _completed_outputs(admin, ctx, ordered)
    bad_contact = projection.contacts[0].model_copy(
        update={"effect": projection.contacts[0].effect.model_copy(update={"executor_token": uuid4()})}
    )
    with pytest.raises(DBAPIError, match="REFERENCE_PUBLICATION_CONTACTS_INVALID"):
        await publish_reference_shortlist(worker, ctx, projection.model_copy(update={"contacts": (bad_contact,)}))
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_provider_results")) == 0
        assert (
            await conn.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE state='completed_published'"))
            == 0
        )
    assert await publish_reference_shortlist(worker, ctx, projection)


async def test_overlap_reuses_profiles_from_another_radius_without_a_new_apify_effect(admin, api, settings, prepared):
    ctx, worker, cycle, ordered = prepared
    previous, candidates, places = await _result(admin, ctx.tenant, ctx.business, ctx.actor, cycle, 20)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE reference_provider_places SET place_id='fake-place' WHERE id=:id"), {"id": places[0]}
        )
        await conn.execute(
            text("""INSERT INTO reference_provider_profile_options
          (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
          VALUES(:t,:b,:result,:candidate,'cached_profile',1,false,'apify','unverified')"""),
            {"t": ctx.tenant, "b": ctx.business, "result": previous, "candidate": candidates[0]},
        )
    await _allow(admin)
    published = await publish_reference_shortlist(worker, ctx, PublicationProjection(operation_id=uuid4()))
    url = f"/api/v1/organizations/{ctx.tenant}/businesses/{ctx.business}/reference-results"
    data = (await api.get(url, headers={"Authorization": f"Bearer {access_token(settings, ctx.actor)}"})).json()
    found = [c for s in data["searches"] for c in s["candidates"] if c["result_id"] == str(published)]
    assert found[0]["instagram_handle"] == "cached_profile" and found[0]["place_identity"] == str(places[0])
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_provider_effects WHERE provider='apify'")) == 0


async def test_first_publication_freezes_missing_old_choices_and_selection_requires_explicit_decision(
    admin, api, settings, prepared, seeded
):
    ctx, worker, new_cycle, ordered = prepared
    old_cycle = uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:t,:b,:id)"),
            {"t": ctx.tenant, "b": ctx.business, "id": old_cycle},
        )
    old_result, old_candidates, old_places = await _result(admin, ctx.tenant, ctx.business, ctx.actor, old_cycle, 5)
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_selected VALUES(:t,:b,:place,:result,:candidate)"),
            {
                "t": ctx.tenant,
                "b": ctx.business,
                "place": old_places[0],
                "result": old_result,
                "candidate": old_candidates[0],
            },
        )
    await _allow(admin)
    result = await publish_reference_shortlist(worker, ctx, PublicationProjection(operation_id=uuid4()))
    base = f"/api/v1/organizations/{ctx.tenant}/businesses/{ctx.business}/reference-results"
    headers = {"Authorization": f"Bearer {access_token(settings, ctx.actor)}"}
    snapshot = (await api.get(base, headers=headers)).json()
    assert snapshot["cycle_review"] == {
        "cycle_id": str(new_cycle),
        "first_result_id": str(result),
        "required_place_ids": [str(old_places[0])],
    }
    payload = {
        "operation_id": str(uuid4()),
        "cycle_id": str(new_cycle),
        "selection": [{"result_id": str(result), "candidate_id": str(ordered[0])}],
    }
    assert (await api.post(base + "/selection", headers=headers, json=payload)).json()[
        "error_code"
    ] == "REFERENCE_CYCLE_DECISION_INCOMPLETE"
    decision = {"place_identity": str(old_places[0]), "action": "keep"}
    payload |= {"first_result_id": str(result), "decisions": [decision]}
    assert (await api.post(base + "/selection", headers=headers, json=payload)).json()[
        "error_code"
    ] == "REFERENCE_CYCLE_DECISION_SELECTION_MISMATCH"
    payload["selection"].append({"result_id": str(old_result), "candidate_id": str(old_candidates[0])})
    confirmed = await api.post(base + "/selection", headers=headers, json=payload)
    assert confirmed.status_code == 200 and len(confirmed.json()["selection"]) == 2
    assert (await api.post(base + "/selection", headers=headers, json=payload)).json() == confirmed.json()
    assert (await api.get(base, headers=headers)).json()["cycle_review"] is None
    # A second active owner sees the same result and can change the selection.
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": ctx.tenant, "a": seeded["viewer"]},
        )
    other = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    assert (await api.get(base, headers=other)).json()["selected"] == (await api.get(base, headers=headers)).json()[
        "selected"
    ]
    changed = {
        "operation_id": str(uuid4()),
        "cycle_id": str(new_cycle),
        "selection": [{"result_id": str(result), "candidate_id": str(ordered[0])}],
    }
    second = await api.post(base + "/selection", headers=other, json=changed)
    assert second.status_code == 200 and second.json()["locked_until"] == confirmed.json()["locked_until"]
    wrong = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    assert (await api.get(base, headers=wrong)).status_code == 403
    assert (await api.post(base + "/selection", headers=wrong, json=changed)).status_code == 403
