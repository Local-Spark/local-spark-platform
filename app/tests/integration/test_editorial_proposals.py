"""Owner consent, fixed context, paid quota and tenant isolation on real PostgreSQL."""

import asyncio
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError
from app.db.session import Database
from app.schemas.editorial_proposals import ProposalDraft, ProposalRequest
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
    provider.propose.return_value = (
        ProposalDraft(
            title="Um detalhe do negócio",
            format="story",
            angle="Apresente este ponto do negócio ao público.",
            fact_ids=[],
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
                                    "id": str(uuid4()),
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
        assert await worker.run(requested.id) == "completed"
        assert (await service.list(tenant, business, actor))[0].document.format == "photo"
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
