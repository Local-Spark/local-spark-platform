"""Owner consent, fixed context, paid quota and tenant isolation on real PostgreSQL."""

import asyncio
import json
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError
from app.core.identity import Identity
from app.db.session import Database
from app.schemas.editorial_proposals import ProposalDraft, ProposalRequest, ScriptEdit, ScriptReview
from app.services.administration import editorial_operation_events, editorial_operations, editorial_usage_today
from app.services.auth import AuthError
from app.services.business import AccessDenied
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService, reconcile_stale_proposals
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _business(admin, seeded):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": seeded["t1"], "business": business},
        )
        await connection.execute(
            text("""INSERT INTO billing_sponsorships
          (id,tenant_id,actor_id,idempotency_key,reason)
          VALUES(:id,:tenant,:actor,'editorial-test','Test')"""),
            {"id": uuid4(), "tenant": seeded["t1"], "actor": seeded["a1"]},
        )
    return business


async def _asset(admin, tenant, business, key, *, kind="text", body="Mensagem do negócio"):
    asset = uuid4()
    ciphertext = Fernet(key.encode()).encrypt(body.encode()).decode()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO whatsapp_material_events
          (id,tenant_id,business_id,kind,ciphertext,expires_at,sender_hash,state)
          VALUES(:id,:tenant,:business,:kind,'encrypted',now()+interval '7 days',:sender,'processed')"""),
            {"id": asset, "tenant": tenant, "business": business, "kind": kind, "sender": "b" * 64},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
          (id,tenant_id,business_id,kind,ciphertext) VALUES(:id,:tenant,:business,:kind,:ciphertext)"""),
            {"id": asset, "tenant": tenant, "business": business, "kind": kind, "ciphertext": ciphertext},
        )
    return asset


async def _fact(admin, tenant, business, actor):
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO business_context_heads(tenant_id,business_id,version) VALUES(:tenant,:business,1)"),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,CAST(:doc AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "operation": uuid4(),
                "actor": actor,
                "hash": "f" * 64,
                "doc": json.dumps(
                    {
                        "facts": [
                            {
                                "id": str(uuid4()),
                                "kind": "product",
                                "statement": "Pao artesanal",
                                "source_detail": "Dono",
                                "valid_until": None,
                            }
                        ],
                        "preferences": {"goal": "sales", "tone": None, "avoided_topics": [], "posts_per_week": None},
                    }
                ),
            },
        )


async def test_baseline_request_consent_replay_and_rls(admin, api, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    fact = uuid4()
    saved = await api.put(
        base + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 0,
            "operation_id": str(uuid4()),
            "facts": [
                {
                    "id": str(fact),
                    "kind": "product",
                    "statement": "Cachorro-quente artesanal",
                    "source_detail": "Informado pelo dono",
                }
            ],
            "preferences": {"goal": "sales", "avoided_topics": ["Política"]},
        },
    )
    assert saved.status_code == 200, saved.text
    proposals = base + "/editorial-proposals"
    assert (await api.get(proposals + "/consent", headers=owner)).json() == {
        "accepted": False,
        "provider_enabled": False,
    }
    assert (await api.put(proposals + "/consent", headers=viewer, json={"accepted": True})).status_code == 403
    assert (await api.put(proposals + "/consent", headers=owner, json={"accepted": True})).json() == {
        "accepted": True,
        "provider_enabled": False,
    }
    assert (await api.put(proposals + "/consent", headers=owner, json={"accepted": True})).json() == {
        "accepted": True,
        "provider_enabled": False,
    }
    operation = str(uuid4())
    first = await api.post(proposals, headers=owner, json={"operation_id": operation})
    assert first.status_code == 202, first.text
    assert first.json()["context_version"] == 1
    assert (await api.post(proposals, headers=owner, json={"operation_id": operation})).json() == first.json()
    conflict = await api.post(
        proposals, headers=owner, json={"operation_id": operation, "source_asset_id": str(uuid4())}
    )
    assert conflict.status_code == 409
    assert conflict.json()["error_code"] == "PROPOSAL_OPERATION_CONFLICT"
    assert (await api.post(proposals, headers=viewer, json={"operation_id": str(uuid4())})).status_code == 403
    assert (
        await api.post(proposals, headers=owner, json={"operation_id": str(uuid4()), "source_asset_id": str(uuid4())})
    ).status_code == 404
    assert len((await api.get(proposals, headers=owner)).json()) == 1
    assert (await api.get(proposals, headers=viewer)).status_code == 403
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM editorial_proposals")) == 0
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM editorial_proposals")) == 1
    worker_db = Database(settings, correlator=True)
    try:
        claims = await claim_proposals(worker_db, uuid4())
        assert len(claims) == 1
        await finish_proposal_dispatch(worker_db, claims[0], True)
        service = EditorialProposalService(settings, worker_db)
        assert await service.run(claims[0].id) == "completed"
        assert await service.run(claims[0].id) == "skipped"
        result = (await api.get(proposals, headers=owner)).json()[0]
        assert result["document"]["fact_ids"] == [str(fact)]
        assert result["document"]["hypotheses"] == []
        assert result["context_version"] == 1
        assert result["document"]["script"][0]["fact_ids"] == [str(fact)]
        review_url = proposals + f"/{result['id']}/script-review"
        review_op = str(uuid4())
        review_body = {"operation_id": review_op, "decision": "accepted"}
        assert (await api.post(review_url, headers=viewer, json=review_body)).status_code == 403
        assert (
            await api.post(proposals + f"/{uuid4()}/script-review", headers=owner, json=review_body)
        ).status_code == 404
        reviewed = await api.post(review_url, headers=owner, json=review_body)
        assert reviewed.status_code == 200, reviewed.text
        assert reviewed.json()["review_state"] == "accepted"
        assert (await api.post(review_url, headers=owner, json=review_body)).json() == reviewed.json()
        changed = await api.post(
            review_url, headers=owner, json={**review_body, "decision": "changes_requested", "note": "Outro texto"}
        )
        assert changed.status_code == 409 and changed.json()["error_code"] == "PROPOSAL_OPERATION_CONFLICT"
        again = await api.post(review_url, headers=owner, json={"operation_id": str(uuid4()), "decision": "accepted"})
        assert again.status_code == 409 and again.json()["error_code"] == "SCRIPT_ALREADY_REVIEWED"
        assert (
            await api.post(
                review_url, headers=owner, json={"operation_id": str(uuid4()), "decision": "changes_requested"}
            )
        ).status_code == 422
        assert (await api.get(proposals, headers=owner)).json()[0]["review_state"] == "accepted"
        assert await reconcile_stale_proposals(worker_db) == 0
    finally:
        await worker_db.close()
    assert (await api.put(proposals + "/consent", headers=owner, json={"accepted": False})).json() == {
        "accepted": False,
        "provider_enabled": False,
    }
    assert (await api.put(proposals + "/consent", headers=owner, json={"accepted": False})).json() == {
        "accepted": False,
        "provider_enabled": False,
    }


async def test_script_edit_versions_replay_review_and_preview_fence(admin, api, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    fact_id = uuid4()
    context = await api.put(
        base + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 0,
            "operation_id": str(uuid4()),
            "facts": [
                {
                    "id": str(fact_id),
                    "kind": "product",
                    "statement": "Cachorro-quente artesanal",
                    "source_detail": "Informado pelo dono",
                }
            ],
            "preferences": {"goal": "sales", "avoided_topics": []},
        },
    )
    assert context.status_code == 200, context.text
    proposals_url = base + "/editorial-proposals"
    requested = await api.post(proposals_url, headers=owner, json={"operation_id": str(uuid4())})
    assert requested.status_code == 202, requested.text
    worker = Database(settings, correlator=True)
    try:
        claims = await claim_proposals(worker, uuid4())
        assert len(claims) == 1
        await finish_proposal_dispatch(worker, claims[0], True)
        assert await EditorialProposalService(settings, worker).run(claims[0].id) == "completed"
    finally:
        await worker.close()
    original = (await api.get(proposals_url, headers=owner)).json()[0]
    proposal_id = UUID(original["id"])
    service = EditorialProposalService(settings, database)
    versions_url = proposals_url + f"/{original['id']}/script-versions"
    assert (await api.get(versions_url, headers=viewer)).status_code == 403
    assert (await api.get(proposals_url + f"/{uuid4()}/script-versions", headers=owner)).status_code == 404
    history = (await api.get(versions_url, headers=owner)).json()
    assert [item["version"] for item in history] == [1]
    assert history[0]["document"] == original["document"]
    assert [item.version for item in await service.script_versions(tenant, business, actor, proposal_id)] == [1]
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await service.script_versions(tenant, business, actor, uuid4())
    review_url = proposals_url + f"/{original['id']}/script-review"
    prior_review = str(uuid4())
    assert (
        await api.post(review_url, headers=owner, json={"operation_id": prior_review, "decision": "accepted"})
    ).status_code == 200
    doc = original["document"]
    assert doc is not None
    edited_scenes = [dict(scene) for scene in doc["script"]]
    cta = next(scene for scene in edited_scenes if scene["role"] == "cta")
    cta["on_screen_text"] = "Converse com a gente pelo WhatsApp"
    cta["voiceover"] = "Chame a gente para saber mais."
    edit = {
        "operation_id": str(uuid4()),
        "expected_version": 1,
        "title": "Conheça nosso cachorro-quente",
        "angle": "Mostre o lanche artesanal aos clientes.",
        "script": edited_scenes,
    }
    assert (await api.post(versions_url, headers=viewer, json=edit)).status_code == 403
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await service.edit_script(tenant, business, actor, uuid4(), ScriptEdit.model_validate(edit))
    assert (await api.post(proposals_url + f"/{uuid4()}/script-versions", headers=owner, json=edit)).status_code == 404
    pending = await api.post(proposals_url, headers=owner, json={"operation_id": str(uuid4())})
    assert pending.status_code == 202
    pending_versions = proposals_url + f"/{pending.json()['id']}/script-versions"
    assert (await api.get(pending_versions, headers=owner)).json() == []
    assert await service.script_versions(tenant, business, actor, UUID(pending.json()["id"])) == []
    assert (await api.post(pending_versions, headers=owner, json=edit)).json()["error_code"] == "SCRIPT_NOT_READY"
    with pytest.raises(AuthError, match="SCRIPT_NOT_READY"):
        await service.edit_script(tenant, business, actor, UUID(pending.json()["id"]), ScriptEdit.model_validate(edit))
    altered_provenance = [dict(scene) for scene in edited_scenes]
    altered_provenance[0]["fact_ids"] = []
    assert (
        await api.post(
            versions_url, headers=owner, json={**edit, "operation_id": str(uuid4()), "script": altered_provenance}
        )
    ).json()["error_code"] == "SCRIPT_PROVENANCE_CHANGED"
    with pytest.raises(AuthError, match="SCRIPT_PROVENANCE_CHANGED"):
        await service.edit_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptEdit.model_validate({**edit, "operation_id": str(uuid4()), "script": altered_provenance}),
        )
    unsupported = await api.post(
        versions_url,
        headers=owner,
        json={**edit, "operation_id": str(uuid4()), "title": "Promoção de R$ 5 hoje"},
    )
    assert unsupported.status_code == 409 and unsupported.json()["error_code"] == "SCRIPT_UNCONFIRMED_CLAIM"
    with pytest.raises(AuthError, match="SCRIPT_UNCONFIRMED_CLAIM"):
        await service.edit_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptEdit.model_validate({**edit, "operation_id": str(uuid4()), "title": "Promoção de R$ 5 hoje"}),
        )
    unchanged = await api.post(
        versions_url,
        headers=owner,
        json={
            **edit,
            "operation_id": str(uuid4()),
            "title": doc["title"],
            "angle": doc["angle"],
            "script": doc["script"],
        },
    )
    assert unchanged.status_code == 409 and unchanged.json()["error_code"] == "SCRIPT_UNCHANGED"
    with pytest.raises(AuthError, match="SCRIPT_UNCHANGED"):
        await service.edit_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptEdit.model_validate(
                {
                    **edit,
                    "operation_id": str(uuid4()),
                    "title": doc["title"],
                    "angle": doc["angle"],
                    "script": doc["script"],
                }
            ),
        )
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET expires_at=now()-interval '1 day' WHERE id=:id"),
            {"id": original["id"]},
        )
    assert (await api.post(versions_url, headers=owner, json=edit)).json()["error_code"] == "SCRIPT_NOT_READY"
    with pytest.raises(AuthError, match="SCRIPT_NOT_READY"):
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET expires_at=now()+interval '30 days' WHERE id=:id"),
            {"id": original["id"]},
        )
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
    with pytest.raises(AuthError, match="SCRIPT_CONTEXT_CHANGED"):
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_context_heads SET version=1 WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
        context_row = (
            (
                await connection.execute(
                    text("SELECT * FROM business_context_versions WHERE tenant_id=:tenant AND business_id=:business"),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one()
        )
        await connection.execute(
            text("DELETE FROM business_context_versions WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
    with pytest.raises(AuthError, match="SCRIPT_CONTEXT_CHANGED"):
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,:version,:operation,:actor,:hash,CAST(:document AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "version": 1,
                "operation": context_row["operation_id"],
                "actor": actor,
                "hash": context_row["request_hash"],
                "document": json.dumps(context_row["document"]),
            },
        )
        await connection.execute(
            text("""UPDATE business_context_versions SET document=jsonb_set(document,'{facts}','[]'::jsonb)
              WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business},
        )
    with pytest.raises(AuthError, match="SCRIPT_FACT_EXPIRED"):
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_context_versions SET document=jsonb_set(
              CAST(:document AS jsonb),'{facts,0,valid_until}',to_jsonb((CURRENT_DATE-1)::text))
              WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business, "document": json.dumps(context_row["document"])},
        )
    with pytest.raises(AuthError, match="SCRIPT_FACT_EXPIRED"):
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_context_versions SET document=CAST(:document AS jsonb)
              WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business, "document": json.dumps(context_row["document"])},
        )
    changed = await api.post(versions_url, headers=owner, json=edit)
    assert changed.status_code == 200, changed.text
    assert changed.json()["version"] == 2
    assert (
        await service.edit_script(tenant, business, actor, proposal_id, ScriptEdit.model_validate(edit))
    ).version == 2
    with pytest.raises(AuthError, match="SCRIPT_OPERATION_CONFLICT"):
        await service.edit_script(tenant, business, actor, UUID(pending.json()["id"]), ScriptEdit.model_validate(edit))
    assert (await api.post(versions_url, headers=owner, json=edit)).json() == changed.json()
    assert (await api.post(versions_url, headers=owner, json={**edit, "title": "Outra versão"})).json()[
        "error_code"
    ] == "SCRIPT_OPERATION_CONFLICT"
    assert (await api.post(versions_url, headers=owner, json={**edit, "operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "SCRIPT_VERSION_CONFLICT"
    with pytest.raises(AuthError, match="SCRIPT_VERSION_CONFLICT"):
        await service.edit_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptEdit.model_validate({**edit, "operation_id": str(uuid4())}),
        )
    current = next(
        item for item in (await api.get(proposals_url, headers=owner)).json() if item["id"] == original["id"]
    )
    assert current["script_version"] == 2 and current["review_state"] is None
    history = (await api.get(versions_url, headers=owner)).json()
    assert [item["version"] for item in history] == [1, 2]
    assert [item.version for item in await service.script_versions(tenant, business, actor, proposal_id)] == [1, 2]
    assert history[0]["review_state"] == "accepted"
    assert history[1]["review_state"] is None
    assert (
        await api.post(review_url, headers=owner, json={"operation_id": prior_review, "decision": "accepted"})
    ).json()["error_code"] == "PROPOSAL_OPERATION_CONFLICT"
    with pytest.raises(AuthError, match="PROPOSAL_OPERATION_CONFLICT"):
        await service.review_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptReview(operation_id=UUID(prior_review), decision="accepted"),
        )
    fact_changed = [dict(scene) for scene in edited_scenes]
    next(scene for scene in fact_changed if scene["role"] == "fact")["on_screen_text"] = "Preço R$ 5"
    assert (
        await api.post(
            versions_url,
            headers=owner,
            json={**edit, "operation_id": str(uuid4()), "expected_version": 2, "script": fact_changed},
        )
    ).json()["error_code"] == "SCRIPT_FACT_CHANGED"
    with pytest.raises(AuthError, match="SCRIPT_FACT_CHANGED"):
        await service.edit_script(
            tenant,
            business,
            actor,
            proposal_id,
            ScriptEdit.model_validate(
                {**edit, "operation_id": str(uuid4()), "expected_version": 2, "script": fact_changed}
            ),
        )
    assert (
        await api.post(review_url, headers=owner, json={"operation_id": str(uuid4()), "decision": "accepted"})
    ).status_code == 200
    assert (await api.get(versions_url, headers=owner)).json()[1]["review_state"] == "accepted"
    preview_url = base + "/media-previews"
    preview = await api.post(
        preview_url,
        headers=owner,
        json={"operation_id": str(uuid4()), "proposal_id": original["id"]},
    )
    assert preview.status_code == 202, preview.text
    assert len((await api.get(preview_url, headers=owner)).json()) == 1
    newer_scenes = [dict(scene) for scene in edited_scenes]
    next(scene for scene in newer_scenes if scene["role"] == "cta")["voiceover"] = "Entre em contato com a gente."
    third = await api.post(
        versions_url,
        headers=owner,
        json={**edit, "operation_id": str(uuid4()), "expected_version": 2, "script": newer_scenes},
    )
    assert third.status_code == 200, third.text
    assert (await api.get(preview_url, headers=owner)).json() == []
    assert (
        await api.post(review_url, headers=owner, json={"operation_id": str(uuid4()), "decision": "accepted"})
    ).status_code == 200
    assert (await api.get(preview_url, headers=owner)).json() == []
    final_scenes = [dict(scene) for scene in newer_scenes]
    next(scene for scene in final_scenes if scene["role"] == "cta")["voiceover"] = "Envie uma mensagem para saber mais."
    final_edit = ScriptEdit.model_validate(
        {**edit, "operation_id": str(uuid4()), "expected_version": 3, "script": final_scenes}
    )
    assert (await service.edit_script(tenant, business, actor, proposal_id, final_edit)).version == 4
    assert [item.version for item in await service.script_versions(tenant, business, actor, proposal_id)] == [
        1,
        2,
        3,
        4,
    ]
    alternatives = []
    for phrase in ("Escreva para saber mais.", "Pergunte sobre este trabalho."):
        scenes = [scene.model_copy() for scene in final_edit.script]
        scenes[-1] = scenes[-1].model_copy(update={"voiceover": phrase})
        alternatives.append(
            ScriptEdit(
                operation_id=uuid4(),
                expected_version=4,
                title=final_edit.title,
                angle=final_edit.angle,
                script=scenes,
            )
        )
    raced = await asyncio.gather(
        *(service.edit_script(tenant, business, actor, proposal_id, candidate) for candidate in alternatives),
        return_exceptions=True,
    )
    assert sum(getattr(result, "version", None) == 5 for result in raced) == 1
    assert sum(isinstance(result, AuthError) and result.code == "SCRIPT_VERSION_CONFLICT" for result in raced) == 1
    head = (await service.script_versions(tenant, business, actor, proposal_id))[-1]
    replay_scenes = [scene.model_copy() for scene in head.document.script]
    replay_scenes[-1] = replay_scenes[-1].model_copy(update={"voiceover": "Fale com a equipe agora."})
    replay = ScriptEdit(
        operation_id=uuid4(),
        expected_version=5,
        title=head.document.title,
        angle=head.document.angle,
        script=replay_scenes,
    )
    repeated = await asyncio.gather(
        service.edit_script(tenant, business, actor, proposal_id, replay),
        service.edit_script(tenant, business, actor, proposal_id, replay),
    )
    assert [item.version for item in repeated] == [6, 6]


async def test_paid_reservation_budget_invalid_fact_and_uncertain(admin, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    config = settings.model_copy(
        update={
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("fake"),
            "editorial_daily_token_limit": 30000,
        }
    )
    api_db = Database(config)
    worker_db = Database(config, correlator=True)
    provider = AsyncMock()
    fact_id = uuid4()
    provider.propose.return_value = (
        ProposalDraft(
            title="Promoção incrível do negócio",
            format="story",
            angle="Aproveite a oferta imperdível para você.",
            fact_ids=[fact_id],
            hypotheses=[],
            questions=[],
        ),
        100,
        50,
    )
    api_service = EditorialProposalService(config, api_db)
    worker = EditorialProposalService(config, worker_db, provider)
    try:
        with pytest.raises(Exception) as denied:
            await api_service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        assert "EDITORIAL_AI_CONSENT_REQUIRED" in str(denied.value)
        assert await api_service.set_consent(tenant, business, actor, True) == {
            "accepted": True,
            "provider_enabled": True,
        }
        # Owner-confirmed context is required when there is no material.
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO business_context_heads(tenant_id,business_id,version)
              VALUES(:tenant,:business,1)"""),
                {"tenant": tenant, "business": business},
            )
            await connection.execute(
                text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,CAST(:doc AS jsonb))"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "operation": uuid4(),
                    "actor": actor,
                    "hash": "a" * 64,
                    "doc": json.dumps(
                        {
                            "facts": [
                                {
                                    "id": str(fact_id),
                                    "kind": "product",
                                    "statement": "Pao artesanal",
                                    "source_detail": "Dono",
                                    "valid_until": None,
                                }
                            ],
                            "preferences": {
                                "goal": "sales",
                                "tone": None,
                                "avoided_topics": [],
                                "posts_per_week": None,
                            },
                        }
                    ),
                },
            )
        request = await api_service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(request.id) == "completed"
        provider.propose.assert_awaited_once()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_tokens FROM editorial_ai_usage")) > 0
            assert await connection.scalar(text("SELECT input_tokens FROM editorial_ai_usage")) == 100
            delivered = await connection.scalar(
                text("SELECT document FROM editorial_proposals WHERE id=:id"), {"id": request.id}
            )
            assert delivered["title"] == "Uma história do seu negócio"
            assert delivered["angle"] == "Apresente este ponto do negócio: Pao artesanal."
        config.editorial_daily_token_limit = 1
        request2 = await api_service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        claim2 = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim2, True)
        assert await worker.run(request2.id) == "budget_exceeded"
        assert provider.propose.await_count == 1
    finally:
        await api_db.close()
        await worker_db.close()


async def test_material_source_is_private_and_deletion_removes_derived_idea(admin, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    key = Fernet.generate_key().decode()
    config = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, kind="image", body="Foto do lanche")
    api_db, worker_db = Database(config), Database(config, correlator=True)
    service = EditorialProposalService(config, api_db)
    worker = EditorialProposalService(config, worker_db)
    try:
        assert await service.set_consent(tenant, business, actor, False) == {
            "accepted": False,
            "provider_enabled": False,
        }
        requested = await service.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(requested.id) == "rejected"
        assert (await service.list(tenant, business, actor))[0].error_code == "EDITORIAL_FACTS_REQUIRED"
        materials = WhatsAppMaterialsService(config, api_db)
        assert await materials.delete_material(tenant, business, actor, source) == {"status": "scheduled"}
        assert await service.list(tenant, business, actor) == []
        with pytest.raises(Exception) as missing:
            await service.request(
                tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
            )
        assert "MATERIAL_NOT_FOUND" in str(missing.value)
    finally:
        await api_db.close()
        await worker_db.close()


async def test_queued_proposals_fail_closed_on_access_consent_expiry_and_missing_inputs(admin, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    key = Fernet.generate_key().decode()
    source = await _asset(admin, tenant, business, key)
    config = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    api_db, worker_db = Database(config), Database(config, correlator=True)
    owner = EditorialProposalService(config, api_db)
    worker = EditorialProposalService(config, worker_db)

    async def queued():
        result = await owner.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        return result.id

    try:
        expired = await queued()
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE editorial_proposals SET expires_at=now()-interval '1 second' WHERE id=:id"),
                {"id": expired},
            )
        assert await worker.run(expired) == "rejected"

        no_access = await queued()
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"), {"tenant": tenant}
            )
        assert await worker.run(no_access) == "rejected"
        with pytest.raises(Exception) as denied:
            await owner.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        assert "PLAN_REQUIRED" in str(denied.value)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=NULL WHERE tenant_id=:tenant"), {"tenant": tenant}
            )

        deleted = await queued()
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:id"), {"id": source}
            )
        assert await worker.run(deleted) == "rejected"

        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_requested_at=NULL WHERE id=:id"), {"id": source}
            )
        assert await worker.run(uuid4()) == "skipped"

        paid = config.model_copy(
            update={
                "editorial_ai_mode": "openai",
                "openai_api_key": SecretStr("fake"),
                "editorial_daily_token_limit": 30000,
            }
        )
        paid_owner = EditorialProposalService(paid, api_db)
        paid_worker = EditorialProposalService(paid, worker_db, AsyncMock())
        assert await paid_owner.consent_status(tenant, business, actor) == {"accepted": False, "provider_enabled": True}
        assert await paid_owner.set_consent(tenant, business, actor, True) == {
            "accepted": True,
            "provider_enabled": True,
        }
        assert await paid_owner.consent_status(tenant, business, actor) == {
            "accepted": True,
            "provider_enabled": True,
        }
        assert await paid_owner.set_consent(tenant, business, actor, True) == {
            "accepted": True,
            "provider_enabled": True,
        }
        consented = await paid_owner.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await paid_owner.set_consent(tenant, business, actor, False) == {
            "accepted": False,
            "provider_enabled": True,
        }
        assert await paid_worker.run(consented.id) == "rejected"
        paid_worker.provider.propose.assert_not_awaited()
    finally:
        await api_db.close()
        await worker_db.close()


async def test_paid_failed_or_unverified_output_is_uncertain_and_never_retried(admin, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    key = Fernet.generate_key().decode()
    source = await _asset(admin, tenant, business, key)
    await _fact(admin, tenant, business, actor)
    config = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("fake"),
            "editorial_daily_token_limit": 150000,
        }
    )
    api_db, worker_db = Database(config), Database(config, correlator=True)
    owner = EditorialProposalService(config, api_db)
    provider = AsyncMock()
    worker = EditorialProposalService(config, worker_db, provider)

    async def queued():
        result = await owner.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        return result.id

    try:
        await owner.set_consent(tenant, business, actor, True)
        failure = await queued()
        provider.propose.side_effect = EditorialProviderError("EDITORIAL_PROVIDER_UNCERTAIN")
        assert await worker.run(failure) == "uncertain"
        assert await worker.run(failure) == "skipped"
        provider.propose.side_effect = None
        unsupported = await queued()
        provider.propose.return_value = (
            ProposalDraft(
                title="Preço 999",
                format="photo",
                angle="Mostre este preço incrível.",
                fact_ids=[],
                hypotheses=[],
                questions=[],
            ),
            100,
            25,
        )
        assert await worker.run(unsupported) == "uncertain"
        missing_source = await queued()

        async def delete_during_call(*_):
            async with admin.begin() as connection:
                await connection.execute(text("DELETE FROM editorial_proposals WHERE id=:id"), {"id": missing_source})
            return (
                ProposalDraft(
                    title="Mostre seu trabalho",
                    format="photo",
                    angle="Conte ao público sobre ele.",
                    fact_ids=[],
                    hypotheses=[],
                    questions=[],
                ),
                100,
                25,
            )

        provider.propose.side_effect = delete_during_call
        assert await worker.run(missing_source) == "uncertain"
        assert await worker.run(missing_source) == "skipped"

        stale = await queued()
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE editorial_proposals SET state='submitted',
              updated_at=now()-interval '6 minutes' WHERE id=:id"""),
                {"id": stale},
            )
            await connection.execute(
                text("""INSERT INTO editorial_ai_usage
              (proposal_id,tenant_id,business_id,reserved_tokens,state,created_at)
              VALUES(:id,:tenant,:business,100,'submitted',now()-interval '6 minutes')"""),
                {"id": stale, "tenant": tenant, "business": business},
            )
        assert await reconcile_stale_proposals(worker_db) == 1
        assert await worker.run(stale) == "skipped"
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM editorial_ai_usage WHERE proposal_id=:id"), {"id": stale}
                )
                == "uncertain"
            )
    finally:
        await api_db.close()
        await worker_db.close()


async def test_concurrent_request_same_operation_is_idempotent(admin, seeded, settings):
    business = await _business(admin, seeded)
    db = Database(settings)
    service = EditorialProposalService(settings, db)
    try:
        operation = uuid4()
        first, second = await asyncio.gather(
            *[
                service.request(seeded["t1"], business, seeded["a1"], ProposalRequest(operation_id=operation))
                for _ in range(2)
            ]
        )
        assert first.id == second.id
        assert (
            await service.request(seeded["t1"], business, seeded["a1"], ProposalRequest(operation_id=operation))
        ).id == first.id
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM editorial_proposals")) == 1
    finally:
        await db.close()


async def test_script_review_requires_ready_script_and_unique_operation(admin, api, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-proposals"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    first = (await api.post(base, headers=owner, json={"operation_id": str(uuid4())})).json()
    second = (await api.post(base, headers=owner, json={"operation_id": str(uuid4())})).json()
    operation = str(uuid4())
    body = {"operation_id": operation, "decision": "changes_requested", "note": "Mostrar outro ângulo"}
    url = base + f"/{first['id']}/script-review"
    service = EditorialProposalService(settings, database)
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await service.review_script(tenant, business, actor, uuid4(), ScriptReview.model_validate(body))
    with pytest.raises(AuthError, match="SCRIPT_NOT_READY"):
        await service.review_script(tenant, business, actor, first["id"], ScriptReview.model_validate(body))
    pending = await api.post(url, headers=owner, json=body)
    assert pending.status_code == 409 and pending.json()["error_code"] == "SCRIPT_NOT_READY"
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET state='completed',document=CAST(:doc AS jsonb) WHERE id=:id"),
            {
                "id": first["id"],
                "doc": json.dumps(
                    {
                        "title": "Uma ideia local",
                        "format": "photo",
                        "angle": "Mostre um ponto do negócio.",
                        "fact_ids": [],
                        "hypotheses": [],
                        "questions": [],
                    }
                ),
            },
        )
    empty = await api.post(url, headers=owner, json=body)
    assert empty.status_code == 409 and empty.json()["error_code"] == "SCRIPT_NOT_READY"
    document = {
        "title": "Uma ideia local",
        "format": "photo",
        "angle": "Mostre um ponto do negócio.",
        "fact_ids": [],
        "hypotheses": [],
        "questions": [],
        "script": [
            {
                "role": "cta",
                "visual": "brand_card",
                "on_screen_text": "Fale com o negócio",
                "voiceover": "Entre em contato para saber mais.",
                "fact_ids": [],
                "source_asset_id": None,
            }
        ],
    }
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": first["id"], "doc": json.dumps(document)},
        )
        await connection.execute(
            text("UPDATE editorial_proposals SET state='completed',document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": second["id"], "doc": json.dumps(document)},
        )
    reviewed = await api.post(url, headers=owner, json=body)
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["review_note"] == "Mostrar outro ângulo"
    assert (
        await service.review_script(tenant, business, actor, first["id"], ScriptReview.model_validate(body))
    ).review_note == "Mostrar outro ângulo"
    with pytest.raises(AuthError, match="PROPOSAL_OPERATION_CONFLICT"):
        await service.review_script(
            tenant, business, actor, first["id"], ScriptReview(operation_id=operation, decision="accepted")
        )
    with pytest.raises(AuthError, match="SCRIPT_ALREADY_REVIEWED"):
        await service.review_script(
            tenant, business, actor, first["id"], ScriptReview(operation_id=uuid4(), decision="accepted")
        )
    duplicate = await api.post(base + f"/{second['id']}/script-review", headers=owner, json=body)
    assert duplicate.status_code == 409 and duplicate.json()["error_code"] == "PROPOSAL_OPERATION_CONFLICT"
    with pytest.raises(AuthError, match="PROPOSAL_OPERATION_CONFLICT"):
        await service.review_script(tenant, business, actor, second["id"], ScriptReview.model_validate(body))
    fresh = await service.review_script(
        tenant, business, actor, second["id"], ScriptReview.model_validate({**body, "operation_id": str(uuid4())})
    )
    assert fresh.review_state == "changes_requested"
    assert (await api.get(base, headers=owner)).json()[0]["review_state"] == "changes_requested"


async def test_concurrent_script_reviews_cannot_reuse_operation(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    service = EditorialProposalService(settings, database)
    first, second = await asyncio.gather(
        service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4())),
        service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4())),
    )
    document = json.dumps(
        {
            "title": "Uma ideia local",
            "format": "photo",
            "angle": "Mostre um ponto do negócio.",
            "fact_ids": [],
            "hypotheses": [],
            "questions": [],
            "script": [
                {
                    "role": "cta",
                    "visual": "brand_card",
                    "on_screen_text": "Fale com o negócio",
                    "voiceover": "Entre em contato para saber mais.",
                    "fact_ids": [],
                    "source_asset_id": None,
                }
            ],
        }
    )
    async with admin.begin() as connection:
        await connection.execute(
            text(
                "UPDATE editorial_proposals SET state='completed',document=CAST(:doc AS jsonb) "
                "WHERE id IN (:first,:second)"
            ),
            {"first": first.id, "second": second.id, "doc": document},
        )
    review = ScriptReview(operation_id=uuid4(), decision="accepted")
    outcomes = await asyncio.gather(
        service.review_script(tenant, business, actor, first.id, review),
        service.review_script(tenant, business, actor, second.id, review),
        return_exceptions=True,
    )
    assert (
        sum(isinstance(result, AuthError) and result.code == "PROPOSAL_OPERATION_CONFLICT" for result in outcomes) == 1
    )
    assert sum(not isinstance(result, BaseException) for result in outcomes) == 1


async def test_missing_snapshot_or_source_and_oversized_input_never_call_provider(admin, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    key = Fernet.generate_key().decode()
    config = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    api_db, worker_db = Database(config), Database(config, correlator=True)
    owner, worker = EditorialProposalService(config, api_db), EditorialProposalService(config, worker_db)
    try:
        empty = await owner.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(empty.id) == "rejected"

        missing_context = await owner.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE editorial_proposals SET context_version=1 WHERE id=:id"), {"id": missing_context.id}
            )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(missing_context.id) == "rejected"
    finally:
        await api_db.close()
        await worker_db.close()

    source = await _asset(admin, tenant, business, key, body="🍔" * 4000)
    facts = [
        {
            "id": str(uuid4()),
            "kind": "product",
            "statement": "🍔" * 240,
            "source_detail": "Informado pelo dono",
            "valid_until": None,
        }
        for _ in range(20)
    ]
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_context_heads(tenant_id,business_id,version)
          VALUES(:tenant,:business,1)"""),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO business_context_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
          VALUES(:tenant,:business,1,:operation,:actor,:hash,CAST(:doc AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "operation": uuid4(),
                "actor": actor,
                "hash": "b" * 64,
                "doc": json.dumps(
                    {
                        "facts": facts,
                        "preferences": {"goal": "sales", "tone": None, "avoided_topics": [], "posts_per_week": None},
                    }
                ),
            },
        )
    paid = config.model_copy(
        update={
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("fake"),
            "editorial_daily_token_limit": 30000,
        }
    )
    api_db, worker_db = Database(paid), Database(paid, correlator=True)
    provider = AsyncMock()
    owner, worker = EditorialProposalService(paid, api_db), EditorialProposalService(paid, worker_db, provider)
    try:
        await owner.set_consent(tenant, business, actor, True)
        request = await owner.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(request.id) == "rejected"
        provider.propose.assert_not_awaited()
    finally:
        await api_db.close()
        await worker_db.close()


async def test_unconfirmed_material_abstains_without_spending_and_admin_projection_is_private(
    admin, api, seeded, settings
):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    key = Fernet.generate_key().decode()
    source = await _asset(admin, tenant, business, key, body="Hoje tenho agenda livre às 15h")
    config = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("fake"),
        }
    )
    owner_db, worker_db = Database(config), Database(config, correlator=True)
    provider = AsyncMock()
    owner = EditorialProposalService(config, owner_db)
    worker = EditorialProposalService(config, worker_db, provider)
    try:
        await owner.set_consent(tenant, business, actor, True)
        proposal = await owner.request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source)
        )
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        await finish_proposal_dispatch(worker_db, claim, True)
        assert await worker.run(proposal.id) == "rejected"
        provider.propose.assert_not_awaited()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM editorial_ai_usage")) == 0
            assert (
                await connection.scalar(
                    text("SELECT error_code FROM editorial_proposals WHERE id=:id"), {"id": proposal.id}
                )
                == "EDITORIAL_FACTS_REQUIRED"
            )
        async with owner_db.transaction(tenant, actor) as session:
            with pytest.raises(AccessDenied):
                await editorial_operations(session, actor, tenant, 10)
        path = f"/api/v1/admin/editorial-operations?tenant_id={tenant}&limit=10"
        owner_headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
        assert (await api.get(path, headers=owner_headers)).status_code == 403
        assert (
            await api.get(f"/api/v1/admin/editorial-operations/{proposal.id}/events", headers=owner_headers)
        ).status_code == 403
        async with admin.begin() as connection:
            await connection.execute(
                text("INSERT INTO platform_staff(actor_id,active) VALUES(:actor,true)"), {"actor": seeded["a2"]}
            )
        async with owner_db.transaction(seeded["t2"], seeded["a2"]) as session:
            result = await editorial_operations(session, seeded["a2"], tenant, 10)
            assert len(result["items"]) == 1
            item = result["items"][0]
            assert item["id"] == proposal.id
            assert item["error_code"] == "EDITORIAL_FACTS_REQUIRED"
            assert item["estimated_cost_minor"] is None
            assert "document" not in item and "ciphertext" not in item
            events = await editorial_operation_events(session, seeded["a2"], proposal.id)
            assert [event["action"] for event in events["items"]] == [
                "editorial.proposal_requested",
                "editorial.proposal_dispatching",
                "editorial.proposal_rejected",
            ]
            assert all("created_at" in event for event in events["items"])
            assert (await editorial_operation_events(session, seeded["a2"], uuid4()))["items"] == []
            assert "operation_id" not in events["items"][0]
            assert (
                await session.scalar(text("SELECT document FROM editorial_proposals WHERE id=:id"), {"id": proposal.id})
                is None
            )
            assert (await editorial_operations(session, seeded["a2"], seeded["t2"], 10))["items"] == []
        staff_headers = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
        api._transport.app.state.identity_verifier.authenticate = AsyncMock(
            return_value=Identity(seeded["a2"], settings.jwt_issuer, str(seeded["a2"]), "Test")
        )
        response = await api.get(path, headers=staff_headers)
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["id"] == str(proposal.id)
        events_response = await api.get(
            f"/api/v1/admin/editorial-operations/{proposal.id}/events", headers=staff_headers
        )
        assert events_response.status_code == 200, events_response.text
        assert len(events_response.json()["items"]) == 3
        other_business, other_proposal = uuid4(), uuid4()
        async with admin.begin() as connection:
            operation_id = await connection.scalar(
                text("SELECT operation_id FROM editorial_proposals WHERE id=:id"), {"id": proposal.id}
            )
            await connection.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Second','UTC')"),
                {"id": other_business, "tenant": tenant},
            )
            await connection.execute(
                text("""INSERT INTO editorial_proposals
                  (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version)
                  VALUES(:id,:tenant,:business,:actor,:operation,:digest,0)"""),
                {
                    "id": other_proposal,
                    "tenant": tenant,
                    "business": other_business,
                    "actor": actor,
                    "operation": operation_id,
                    "digest": "a" * 64,
                },
            )
            await connection.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:proposal,'editorial.proposal_requested',:business)"""),
                {"tenant": tenant, "actor": actor, "proposal": other_proposal, "business": other_business},
            )
        other_events = await api.get(
            f"/api/v1/admin/editorial-operations/{other_proposal}/events", headers=staff_headers
        )
        assert [event["action"] for event in other_events.json()["items"]] == ["editorial.proposal_requested"]
        original_events = await api.get(
            f"/api/v1/admin/editorial-operations/{proposal.id}/events", headers=staff_headers
        )
        assert len(original_events.json()["items"]) == 3
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE platform_staff SET active=false WHERE actor_id=:actor"), {"actor": seeded["a2"]}
            )
        assert (await api.get(path, headers=staff_headers)).status_code == 403
        assert (
            await api.get(f"/api/v1/admin/editorial-operations/{proposal.id}/events", headers=staff_headers)
        ).status_code == 403
    finally:
        await owner_db.close()
        await worker_db.close()


async def test_staff_daily_usage_keeps_tenants_private_and_separates_reserved_from_measured(
    admin, api, seeded, settings
):
    business = await _business(admin, seeded)
    other_business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Other','UTC')"),
            {"id": other_business, "tenant": seeded["t2"]},
        )
        await connection.execute(
            text("INSERT INTO platform_staff(actor_id,active) VALUES(:actor,true)"), {"actor": seeded["a2"]}
        )
        for tenant, target, reserved, input_tokens, output_tokens, state in (
            (seeded["t1"], business, 80, 20, 10, "completed"),
            (seeded["t1"], business, 20, None, None, "uncertain"),
            (seeded["t2"], other_business, 25, None, None, "submitted"),
        ):
            await connection.execute(
                text("""INSERT INTO editorial_ai_usage
                  (proposal_id,tenant_id,business_id,reserved_tokens,input_tokens,output_tokens,state)
                  VALUES(:proposal,:tenant,:business,:reserved,:input,:output,:state)"""),
                {
                    "proposal": uuid4(),
                    "tenant": tenant,
                    "business": target,
                    "reserved": reserved,
                    "input": input_tokens,
                    "output": output_tokens,
                    "state": state,
                },
            )
    db = Database(settings)
    try:
        async with db.transaction(seeded["t1"], seeded["a1"]) as session:
            with pytest.raises(AccessDenied):
                await editorial_usage_today(session, seeded["a1"], seeded["t1"], 25, 100)
        async with db.transaction(seeded["t2"], seeded["a2"]) as session:
            all_usage = await editorial_usage_today(session, seeded["a2"], None, 25, 100)
            assert len(all_usage["items"]) == 2
            assert all_usage["period_end"] > all_usage["period_start"]
            first = all_usage["items"][0]
            assert first["tenant_id"] == seeded["t1"]
            assert first["request_count"] == 2
            assert first["reserved_tokens"] == 100
            assert first["observed_tokens"] == 30
            assert first["measured_count"] == 1
            assert first["uncertain_count"] == 1
            assert first["completed_count"] == 1
            assert first["estimated_cost_minor"] is None
            assert first["quota_state"] == "exhausted"
            assert all_usage["items"][1]["in_progress_count"] == 1
            assert all_usage["items"][1]["quota_state"] == "normal"
            assert (await editorial_usage_today(session, seeded["a2"], seeded["t1"], 25, 120))["items"][0][
                "quota_state"
            ] == "warning"
            assert (await editorial_usage_today(session, seeded["a2"], seeded["t1"], 25, 0))["items"][0][
                "quota_state"
            ] == "unconfigured"
            assert (await editorial_usage_today(session, seeded["a2"], uuid4(), 25, 100))["items"] == []
        staff_headers = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
        owner_headers = {"Authorization": f"Bearer {access_token(settings, seeded['a1'])}"}
        assert (await api.get("/api/v1/admin/editorial-usage", headers=owner_headers)).status_code == 403
        api._transport.app.state.identity_verifier.authenticate = AsyncMock(
            return_value=Identity(seeded["a2"], settings.jwt_issuer, str(seeded["a2"]), "Test")
        )
        response = await api.get(
            f"/api/v1/admin/editorial-usage?tenant_id={seeded['t1']}&limit=1", headers=staff_headers
        )
        assert response.status_code == 200, response.text
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["tenant_id"] == str(seeded["t1"])
        assert response.json()["items"][0]["estimated_cost_minor"] is None
        assert (await api.get("/api/v1/admin/editorial-usage?limit=101", headers=staff_headers)).status_code == 422
    finally:
        await db.close()
