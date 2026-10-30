"""Experimental editorial skill and exact encrypted request trace with fake provider."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError
from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.editorial_proposals import CreativeBrief, ProposalDraft, ProposalRequest
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business, _fact
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def test_disabled_editorial_provider_rejects_without_fixed_copy_or_effect(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _fact(admin, tenant, business, actor)
    proposal = await EditorialProposalService(settings, database).request(
        tenant, business, actor, ProposalRequest(operation_id=uuid4())
    )
    worker = Database(settings, correlator=True)
    provider = SimpleNamespace(propose=AsyncMock())
    try:
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert await EditorialProposalService(settings, worker, provider).run(proposal.id) == "rejected"
        provider.propose.assert_not_awaited()
        async with admin.connect() as connection:
            result = (
                (
                    await connection.execute(
                        text("SELECT state,error_code,document FROM editorial_proposals WHERE id=:id"),
                        {"id": proposal.id},
                    )
                )
                .mappings()
                .one()
            )
            assert result["state"] == "rejected" and result["error_code"] == "EDITORIAL_PROVIDER_DISABLED"
            assert result["document"] is None
            assert await connection.scalar(text("SELECT count(*) FROM editorial_ai_usage")) == 0
            assert await connection.scalar(text("SELECT count(*) FROM editorial_request_traces")) == 0
    finally:
        await worker.close()


@pytest.mark.parametrize("format,skill_id", [("photo", "instagram-feed-v1"), ("story", "instagram-story-v1")])
async def test_editorial_skill_and_encrypted_request_trace_are_source_bound(
    admin, database, seeded, settings, format, skill_id
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("unused-fake"),
            "editorial_daily_token_limit": 100000,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Quero divulgar meu croissant")
    catalog = _payload()
    catalog["promotions"] = []
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])
    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", item, "content_request", format))
    )
    worker = Database(cfg, correlator=True)
    provider = SimpleNamespace(propose=AsyncMock())
    sent = []

    async def propose(data, operation, *, prepared_request):
        sent.append(prepared_request)
        fact = data["confirmed_facts"][0]
        assert data["editorial_skill"]["id"] == skill_id
        return (
            ProposalDraft(
                title="Conheça nosso croissant",
                format=format,
                angle="Apresente o croissant com uma pausa acolhedora",
                fact_ids=[UUID(fact["id"])],
                hypotheses=[],
                questions=[],
                art_text="Nosso croissant",
                caption="Uma pausa especial com nosso croissant",
                cta="Envie uma mensagem",
                creative_brief=CreativeBrief(
                    objective="Apresentar o produto",
                    concept="Pausa acolhedora",
                    visual_direction="Destaque a foto com cores da marca",
                    hierarchy="Produto e convite em destaque",
                    photo_use="Preserve a referência recebida",
                ),
            ),
            120,
            60,
        )

    provider.propose.side_effect = propose
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        service = EditorialProposalService(cfg, worker, provider, owner_database=database)
        assert await service.run(proposal) == "completed"
        owner = EditorialProposalService(cfg, database)
        trace = await owner.get_request_trace(tenant, business, actor, proposal)
        assert trace["trace_status"] == "prepared" and trace["proposal_state"] == "completed"
        assert trace["proposal_error_code"] is None
        assert trace["request"]["body"] == sent[0]
        content = trace["request"]["body"]["input"][1]["content"]
        assert "Quero divulgar meu croissant" in content and skill_id in content
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT document FROM editorial_proposals WHERE id=:id"), {"id": proposal}
                    )
                )
                .mappings()
                .one()
            )
            assert row["document"]["editorial_skill_id"] == skill_id
            assert row["document"]["creative_brief"]["concept"] == "Pausa acolhedora"
            ciphertext = await connection.scalar(
                text("SELECT ciphertext FROM editorial_request_traces WHERE proposal_id=:id"), {"id": proposal}
            )
            assert "Quero divulgar" not in ciphertext
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM editorial_request_traces")) == 0
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await owner.get_request_trace(tenant, business, seeded["viewer"], proposal)
    finally:
        await worker.close()


@pytest.mark.parametrize("failure", ["budget", "input_too_large"])
async def test_rejected_editorial_attempt_creates_neither_trace_nor_provider_effect(
    admin, database, seeded, settings, monkeypatch, failure
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("unused-fake"),
            "editorial_daily_token_limit": 1 if failure == "budget" else 100000,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Quero divulgar meu croissant")
    catalog = _payload()
    catalog["promotions"] = []
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])
    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", item, "content_request", "photo"))
    )
    worker = Database(cfg, correlator=True)
    provider = SimpleNamespace(propose=AsyncMock())
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        service = EditorialProposalService(cfg, worker, provider, owner_database=database)
        if failure == "input_too_large":
            original_inputs = service._inputs

            async def oversized_inputs(session, row):
                result = await original_inputs(session, row)
                assert result is not None
                result[0]["synthetic_padding"] = "x" * 30001
                return result

            monkeypatch.setattr(service, "_inputs", oversized_inputs)
        assert await service.run(proposal) == ("budget_exceeded" if failure == "budget" else "rejected")
        provider.propose.assert_not_awaited()
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM editorial_request_traces WHERE proposal_id=:id"), {"id": proposal}
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM editorial_ai_usage WHERE proposal_id=:id"), {"id": proposal}
                )
                == 0
            )
            assert await connection.scalar(
                text("SELECT error_code FROM editorial_proposals WHERE id=:id"), {"id": proposal}
            ) == ("EDITORIAL_BUDGET_EXCEEDED" if failure == "budget" else "EDITORIAL_INPUT_TOO_LARGE")
    finally:
        await worker.close()


async def test_uncertain_provider_result_keeps_prepared_trace_without_claiming_transmission(
    admin, database, seeded, settings
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("unused-fake"),
            "editorial_daily_token_limit": 100000,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Quero divulgar meu croissant")
    catalog = _payload()
    catalog["promotions"] = []
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])
    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", item, "content_request", "photo"))
    )
    worker = Database(cfg, correlator=True)
    provider = SimpleNamespace(propose=AsyncMock(side_effect=EditorialProviderError("EDITORIAL_PROVIDER_UNCERTAIN")))
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        service = EditorialProposalService(cfg, worker, provider, owner_database=database)
        assert await service.run(proposal) == "uncertain"
        trace = await EditorialProposalService(cfg, database).get_request_trace(tenant, business, actor, proposal)
        assert trace["trace_status"] == "prepared"
        assert trace["proposal_state"] == "uncertain"
        assert trace["proposal_error_code"] == "EDITORIAL_RESULT_UNCERTAIN"
        provider.propose.assert_awaited_once()
    finally:
        await worker.close()
