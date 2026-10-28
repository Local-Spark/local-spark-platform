"""A synthetic WhatsApp-to-review journey using real Temporal and PostgreSQL.

The text interpreter and private storage are local stubs. No Meta, OpenAI or
other paid provider is called; the resulting image is explicitly a simulation.
"""

import asyncio
import io
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text
from temporalio.client import Client
from temporalio.worker import Worker

from app.adapters.brand_overlay import render_brand_overlay
from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.adapters.visual_ai import OpenAIVisualProvider
from app.db.session import Database
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.content_deliveries import ContentDecision
from app.services.brand_kits import BrandKitService
from app.services.business_catalog import BusinessCatalogService
from app.services.business_collection import BusinessCollectionService
from app.services.content_deliveries import ContentDeliveryService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import dispatch_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import dispatch_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_consent import VisualConsentService
from app.tests.integration.test_brand_kits import _draft, _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.unit.test_business_collection_contract import upload
from app.workflows.content_activities import ContentCandidateActivities
from app.workflows.content_candidate import ContentCandidateWorkflow
from app.workflows.editorial_activities import EditorialActivities
from app.workflows.editorial_proposal import EditorialProposalWorkflow
from app.workflows.media_activities import MediaPreviewActivities
from app.workflows.media_preview import StaticPreviewWorkflow

pytestmark = [pytest.mark.integration, pytest.mark.temporal]


async def test_synthetic_content_reaches_private_visual_preview_through_real_temporal(
    admin, database, seeded, settings, monkeypatch
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    queue = f"test-visual-e2e-{uuid4()}"
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "fake",
            "visual_ai_monthly_budget_usd_micros": 100,
            "editorial_ai_mode": "disabled",
            "intent_ai_mode": "disabled",
            "temporal_task_queue": queue,
        }
    )
    paid_visual = AsyncMock(side_effect=AssertionError("paid visual provider must not be called"))
    paid_editorial = AsyncMock(side_effect=AssertionError("paid editorial provider must not be called"))
    monkeypatch.setattr(OpenAIVisualProvider, "generate", paid_visual)
    monkeypatch.setattr(OpenAIEditorialProvider, "propose", paid_editorial)
    overlay = Mock(wraps=render_brand_overlay)
    monkeypatch.setattr("app.services.visual_brand_finish.render_brand_overlay", overlay)

    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    event_ciphertext = Fernet(key.encode()).encrypt(json.dumps({"from": "5511999999999"}).encode()).decode()
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE whatsapp_material_events SET ciphertext=:cipher WHERE id=:id"),
            {"cipher": event_ciphertext, "id": source},
        )

    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    offering = UUID(catalog["offerings"][0]["id"])
    store = Store()
    await BusinessCollectionService(cfg, database, store).upload(
        tenant, business, actor, upload(item_id=str(offering), space_kind=None)
    )
    kits = BrandKitService(cfg, database, store)
    draft = await kits.draft(
        tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(0, _overrides("Café teste")))
    )
    assert draft.draft is not None
    confirmed = await kits.confirm(
        tenant, business, actor, BrandKitConfirmRequest(operation_id=uuid4(), expected_version=draft.draft.version)
    )
    assert confirmed.confirmed is not None
    await VisualConsentService(cfg, database).set(tenant, business, actor, True)

    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", offering, "content_request", "photo"))
    )
    database_worker = Database(cfg, correlator=True)
    candidate = ContentCandidateActivities(cfg, database, database_worker, interpreter=interpreter)
    editorial = EditorialActivities(EditorialProposalService(cfg, database_worker, owner_database=database))
    media = MediaPreviewActivities(MediaPreviewService(cfg, database_worker, store, database))
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    activities = [
        candidate.request_candidate_proposal,
        candidate.candidate_proposal_state,
        candidate.request_candidate_preview,
        candidate.candidate_preview_state,
        candidate.deliver_candidate_preview,
        candidate.deliver_candidate_clarification,
        candidate.deliver_briefing_clarification,
        editorial.generate_editorial_proposal,
        media.render_static_preview,
    ]
    handle = None
    result_task = None
    try:
        async with Worker(
            client,
            task_queue=queue,
            workflows=[ContentCandidateWorkflow, EditorialProposalWorkflow, StaticPreviewWorkflow],
            activities=activities,
        ):
            handle = await client.start_workflow(
                ContentCandidateWorkflow.run, str(source), id=f"test-content-visual/{source}", task_queue=queue
            )
            result_task = asyncio.create_task(handle.result())
            dispatcher = uuid4()
            async with asyncio.timeout(45):
                while not result_task.done():
                    await dispatch_proposals(database_worker, client, cfg, dispatcher)
                    await dispatch_previews(database_worker, client, cfg, dispatcher)
                    await asyncio.sleep(0.1)
                assert await result_task == "candidate_delivered"

        review = ContentDeliveryService(cfg, database, database_worker)
        deliveries = await review.list(tenant, business, actor)
        assert len(deliveries) == 1 and deliveries[0].kind == "candidate"
        assert deliveries[0].decision_state == "pending" and deliveries[0].preview_id is not None
        previews = await MediaPreviewService(cfg, database, store).list(tenant, business, actor)
        assert len(previews) == 1 and previews[0].id == deliveries[0].preview_id
        assert previews[0].generation_mode == "visual_fake" and previews[0].state == "completed"
        object_key = await MediaPreviewService(cfg, database, store).file_key(tenant, business, actor, previews[0].id)
        with Image.open(io.BytesIO(store.objects[object_key])) as image:
            assert image.format == "JPEG" and image.size == (1024, 1280)
            assert all(value < 100 for value in image.getpixel((4, 4)))
        assert overlay.call_count == 1 and overlay.call_args.kwargs["kit"].brand_name == "Café teste"
        assert store.reads > 0  # The authorized synthetic item photo reached the render pipeline.
        decision = await review.decide(
            tenant, business, actor, deliveries[0].id, ContentDecision(operation_id=uuid4(), decision="approve")
        )
        assert decision.decision_state == "approved"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
            assert await connection.scalar(text("SELECT count(*) FROM content_deliveries")) == 1
        async with database.transaction(seeded["t2"], seeded["a2"]) as other:
            assert await other.scalar(text("SELECT count(*) FROM media_previews")) == 0
        paid_visual.assert_not_awaited()
        paid_editorial.assert_not_awaited()
    finally:
        if result_task is not None and not result_task.done():
            result_task.cancel()
            if handle is not None:
                await handle.cancel()
        await database_worker.close()
