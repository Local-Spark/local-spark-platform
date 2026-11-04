"""The new contract authorizes service use without reviving old provider permissions."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.editorial_proposals import ProposalDraft, ProposalRequest
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.visual_consent import VisualConsentService
from app.services.visual_context import VisualContextService
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_proposals import _asset, _business, _fact
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("legacy_state", ["missing", "revoked", "active"])
async def test_one_contract_drives_briefing_and_visual_preview_without_provider_permissions(
    admin, database, seeded, settings, legacy_state
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    key = Fernet.generate_key().decode()
    config = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "service_agreement_required": legacy_state != "active",
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("synthetic-key"),
            "editorial_daily_token_limit": 100000,
            "visual_ai_mode": "fake",
            "visual_ai_monthly_budget_usd_micros": 100,
        }
    )
    async with admin.begin() as connection:
        params = {"tenant": tenant, "business": business, "actor": actor}
        await connection.execute(
            text("""INSERT INTO whatsapp_channel_links
              (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
              VALUES(:tenant,:business,:actor,:sender,:proof,clock_timestamp()-interval '1 minute')"""),
            {**params, "sender": "b" * 64, "proof": uuid4()},
        )
        if legacy_state != "missing":
            for table in (
                "whatsapp_processing_consents",
                "editorial_ai_consents",
                "intent_jev_consents",
                "visual_ai_consents",
            ):
                if legacy_state == "active" and table == "intent_jev_consents":
                    continue
                await connection.execute(
                    text(f"""INSERT INTO {table}(tenant_id,business_id,actor_id,revoked_at)
                      VALUES(:tenant,:business,:actor,
                        CASE WHEN :revoked THEN clock_timestamp()-interval '1 minute' END)"""),
                    {**params, "revoked": legacy_state == "revoked"},
                )
            await connection.execute(
                text("""INSERT INTO visual_consent_gates(tenant_id,business_id,state)
                  VALUES(:tenant,:business,:state)"""),
                {**params, "state": "revoked" if legacy_state == "revoked" else "active"},
            )
    if legacy_state != "active":
        accepted = await ServiceAgreementService(config, database).accept(
            tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
        assert accepted["accepted"] and accepted["access_active"]
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    async with admin.begin() as connection:
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()}
        await connection.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
              VALUES(:tenant,:business,1,1)"""),
            params,
        )
        await connection.execute(
            text("""INSERT INTO business_brand_kit_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:document AS jsonb))"""),
            {
                **params,
                "hash": "a" * 64,
                "document": json.dumps({"kit_id": "cafe-pausas", "kit_version": 1, "overrides": _overrides()}),
            },
        )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(config, correlator=True)
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    provider = SimpleNamespace(propose=AsyncMock())

    async def propose(data, operation, *, prepared_request):
        fact = data["confirmed_facts"][0]
        return (
            ProposalDraft(
                title="Conheça nosso croissant",
                format="photo",
                angle="Apresente o croissant",
                fact_ids=[UUID(fact["id"])],
                hypotheses=[],
                questions=[],
                scene_plan=["fact", "cta"],
                art_text="Nosso croissant",
                caption="Conheça nosso croissant",
                cta="Envie uma mensagem",
                creative_brief={
                    "objective": "Divulgar o produto",
                    "concept": "Pausa com croissant",
                    "visual_direction": "Valorizar o produto",
                    "hierarchy": "Nome e chamada",
                    "photo_use": "Valorizar a fotografia disponível",
                },
            ),
            10,
            10,
        )

    provider.propose.side_effect = propose
    try:
        activities = ContentCandidateActivities(config, database, worker, interpreter=interpreter)
        proposal = UUID(await activities.request_candidate_proposal(str(source)))
        await claim_proposals(worker, uuid4())
        assert (
            await EditorialProposalService(config, worker, provider, owner_database=database).run(proposal)
            == "completed"
        )
        provider.propose.assert_awaited_once()
        context = await VisualContextService(config, database).capture(
            tenant, business, actor, proposal, candidate=True
        )
        assert context.proposal_id == proposal and context.format == "photo"
        if legacy_state == "active":
            await ServiceAgreementService(config, database).accept(
                tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
            )
            after = await VisualContextService(config, database).capture(
                tenant, business, actor, proposal, candidate=True
            )
            assert after.fingerprint == context.fingerprint
        owner_service = MediaPreviewService(config, database, store)
        preview = await owner_service.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        assert await MediaPreviewService(config, worker, store, database).render(preview.id, claim.fence) == "completed"
        store.put.assert_awaited_once()
        assert (await owner_service.file_key(tenant, business, actor, preview.id)).endswith(".jpg")
        with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
            await VisualConsentService(config, database).set(tenant, business, actor, False)
        with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
            await EditorialProposalService(config, database).set_consent(tenant, business, actor, False)
        async with admin.connect() as connection:
            for table in (
                "whatsapp_processing_consents",
                "editorial_ai_consents",
                "intent_jev_consents",
                "visual_ai_consents",
            ):
                expected = int(
                    legacy_state != "missing" and not (legacy_state == "active" and table == "intent_jev_consents")
                )
                assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == expected
                if legacy_state == "revoked":
                    assert await connection.scalar(text(f"SELECT bool_and(revoked_at IS NOT NULL) FROM {table}"))
            if legacy_state == "revoked":
                assert await connection.scalar(text("SELECT state FROM visual_consent_gates")) == "revoked"
            assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='finished'")) == 1
    finally:
        await worker.close()


async def test_new_contract_epoch_cancels_old_queued_jobs_and_only_allows_fresh_request(
    admin, database, seeded, settings
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _fact(admin, tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO editorial_ai_consents(tenant_id,business_id,actor_id,generation)
              VALUES(:tenant,:business,:actor,7)"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id,accepted_at)
              VALUES(:tenant,:business,:actor,clock_timestamp()-interval '1 minute')"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
    key = Fernet.generate_key().decode()
    config = settings.model_copy(
        update={
            "editorial_ai_mode": "openai",
            "editorial_daily_token_limit": 100000,
            "meta_encryption_key": SecretStr(key),
            "openai_api_key": SecretStr("synthetic-key"),
        }
    )
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    briefing = await EditorialBriefingService(config, database, interpreter).prepare(
        tenant, business, actor, source, uuid4()
    )
    assert briefing.state == "prepared"
    owner = EditorialProposalService(config, database)
    payload = ProposalRequest(operation_id=uuid4(), source_asset_id=source)
    old = await owner.request(tenant, business, actor, payload, briefing_id=briefing.id)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_ai_consents SET revoked_at=clock_timestamp() WHERE tenant_id=:tenant"),
            {"tenant": tenant},
        )
    await ServiceAgreementService(config, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    with pytest.raises(AuthError, match="EDITORIAL_REQUEST_CANCELLED"):
        await owner.request(tenant, business, actor, payload, briefing_id=briefing.id)
    fresh = await owner.request(
        tenant, business, actor, ProposalRequest(operation_id=uuid4(), source_asset_id=source), briefing_id=briefing.id
    )
    async with admin.connect() as connection:
        assert await connection.scalar(
            text("SELECT consent_generation FROM editorial_proposals WHERE id=:id"), {"id": fresh.id}
        ) == -int(SERVICE_AGREEMENT_HASH[:15], 16)
        assert await connection.scalar(text("SELECT generation FROM editorial_ai_consents")) == 7
        assert await connection.scalar(text("SELECT revoked_at IS NOT NULL FROM editorial_ai_consents"))
    provider = SimpleNamespace(propose=AsyncMock())

    async def propose(data, _proposal, *, prepared_request):
        fact = data["confirmed_facts"][0]
        return (
            ProposalDraft(
                title="Conheça nosso croissant",
                format="photo",
                angle="Apresente o croissant",
                fact_ids=[UUID(fact["id"])],
                hypotheses=[],
                questions=[],
                scene_plan=["fact", "cta"],
                art_text="Nosso croissant",
                caption="Conheça nosso croissant",
                cta="Envie mensagem",
                creative_brief={
                    "objective": "Divulgar o produto",
                    "concept": "Pausa com croissant",
                    "visual_direction": "Valorizar o produto",
                    "hierarchy": "Nome e chamada",
                    "photo_use": "Valorizar a fotografia disponível",
                },
            ),
            10,
            10,
        )

    provider.propose.side_effect = propose
    worker = Database(config, correlator=True)
    try:
        await claim_proposals(worker, uuid4())
        service = EditorialProposalService(config, worker, provider, owner_database=database)
        assert await service.run(old.id) == "rejected"
        provider.propose.assert_not_awaited()
        assert await service.run(fresh.id) == "completed"
        provider.propose.assert_awaited_once()
    finally:
        await worker.close()


async def test_new_contract_does_not_reauthorize_old_proposal_without_original_visual_consent(
    admin, database, seeded, settings
):
    from app.tests.integration.test_content_delivery import _visual_candidate_case

    cfg, app_db, worker, tenant, business, actor, proposal, _, _, _ = await _visual_candidate_case(
        admin, seeded, settings, database, render_preview=False
    )
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET model='test-provider-v1' WHERE id=:id"), {"id": proposal}
        )
        for table in (
            "whatsapp_processing_consents",
            "editorial_ai_consents",
            "intent_jev_consents",
            "visual_ai_consents",
        ):
            await connection.execute(text(f"DELETE FROM {table} WHERE tenant_id=:tenant"), {"tenant": tenant})
        await connection.execute(text("DELETE FROM visual_consent_gates WHERE tenant_id=:tenant"), {"tenant": tenant})
    try:
        await ServiceAgreementService(cfg, app_db).accept(
            tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
        store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
        owner = MediaPreviewService(cfg, app_db, store)
        with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
            await owner.request_candidate(
                tenant,
                business,
                actor,
                PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
            )
        store.put.assert_not_awaited()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM editorial_ai_consents")) == 0
    finally:
        await worker.close()
        await app_db.close()
