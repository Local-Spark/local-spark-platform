"""Financial expiry does not interrupt an admitted simulated visual creation."""

import asyncio
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
from app.schemas.content_deliveries import ContentDecision
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.content_deliveries import ContentDeliveryService, claim_publications
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.media_retention import purge_expired_previews
from app.services.visual_consent import VisualConsentService
from app.services.whatsapp_ingest import sender_hash
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_content_delivery import _review
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.integration.test_visual_brand_finish import _editorial_provider
from app.tests.integration.test_visual_source_invalidation import PausingStore
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def test_plan_expiring_during_upload_preserves_completion_and_private_delivery(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "fake",
            "visual_ai_monthly_budget_usd_micros": 100,
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("synthetic-key"),
            "editorial_daily_token_limit": 100000,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text(
                "UPDATE whatsapp_channel_links SET sender_hash=:sender "
                "WHERE tenant_id=:tenant AND business_id=:business"
            ),
            {"tenant": tenant, "business": business, "sender": sender_hash(cfg, "+5511999999999")},
        )
        await connection.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
              VALUES(:tenant,:business,1,1)"""),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO business_brand_kit_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:document AS jsonb))"""),
            {
                "tenant": tenant,
                "business": business,
                "operation": uuid4(),
                "actor": actor,
                "hash": "a" * 64,
                "document": json.dumps({"kit_id": "cafe-pausas", "kit_version": 1, "overrides": _overrides()}),
            },
        )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(cfg, correlator=True)
    store = PausingStore()
    try:
        activities = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activities.request_candidate_proposal(str(source)))
        await claim_proposals(worker, uuid4())
        provider = _editorial_provider()
        assert (
            await EditorialProposalService(cfg, worker, provider, owner_database=database).run(proposal) == "completed"
        )
        provider.propose.assert_awaited_once()
        await VisualConsentService(cfg, database).set(tenant, business, actor, True)
        owner = MediaPreviewService(cfg, database, store)
        preview = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        queued = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        claims = {item.id: item for item in await claim_previews(worker, uuid4())}
        renderer = MediaPreviewService(cfg, worker, store, database)
        task = asyncio.create_task(renderer.render(preview.id, claims[preview.id].fence))
        try:
            await asyncio.wait_for(store.entered.wait(), 20)
            async with admin.begin() as connection:
                await connection.execute(
                    text("""UPDATE billing_sponsorships SET starts_at=now()-interval '2 days',
                      ends_at=now()-interval '1 second' WHERE tenant_id=:tenant"""),
                    {"tenant": tenant},
                )
            assert await renderer.render(queued.id, claims[queued.id].fence) == "failed"
            with pytest.raises(AuthError, match="PLAN_REQUIRED"):
                await owner.request_candidate(
                    tenant,
                    business,
                    actor,
                    PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
                )
        finally:
            store.release.set()
        assert await task == "completed"
        assert store.preview_key is not None and store.preview_key in store.objects
        visible = await owner.list(tenant, business, actor)
        retained = next(item for item in visible if item.id == preview.id)
        assert retained.state == "completed" and not retained.created_before_change
        assert await owner.file_key(tenant, business, actor, preview.id, review=True) == store.preview_key
        deliveries = ContentDeliveryService(cfg, database, worker)
        delivery = await deliveries.record(source, preview.id)
        assert delivery is not None
        async with admin.connect() as connection:
            sha = await connection.scalar(text("SELECT sha256 FROM media_previews WHERE id=:id"), {"id": preview.id})
        with pytest.raises(AuthError, match="VISUAL_BRIEFING_CHANGED"):
            await deliveries.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(operation_id=uuid4(), decision="approve", visual_review=_review(sha)),
            )
        assert await claim_publications(worker, uuid4()) == []
        assert await purge_expired_previews(worker, store, uuid4()) == 0
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM visual_consent_runs WHERE preview_id=:id"), {"id": preview.id}
                )
                == "finished"
            )
            assert (
                await connection.scalar(
                    text("SELECT actual_usd_micros FROM visual_cost_reservations WHERE tenant_id=:tenant"),
                    {"tenant": tenant},
                )
                == 0
            )
    finally:
        await worker.close()
