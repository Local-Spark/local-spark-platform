"""The simulated visual journey exercises real source and role checks, with no paid calls."""

import asyncio
import json
from dataclasses import replace
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
from app.services.content_deliveries import ContentDeliveryService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_consent import VisualConsentService
from app.services.visual_context import VisualContextService
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def test_visual_fake_preview_uses_fenced_attempt_and_blocks_revoked_access(
    admin, database, seeded, settings, monkeypatch
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "fake",
            "visual_ai_monthly_budget_usd_micros": 100,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    encrypted_event = Fernet(key.encode()).encrypt(json.dumps({"from": "5511999999999"}).encode()).decode()
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE whatsapp_material_events SET ciphertext=:cipher WHERE id=:id"),
            {"cipher": encrypted_event, "id": source},
        )
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    async with admin.begin() as conn:
        p = {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()}
        await conn.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
          VALUES(:tenant,:business,1,1)"""),
            p,
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
          VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:document AS jsonb))"""),
            {
                **p,
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
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        await claim_proposals(worker, uuid4())
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal) == "completed"
        consent = VisualConsentService(cfg, database)
        await consent.set(tenant, business, actor, True)
        owner_service = MediaPreviewService(cfg, database, store)
        body = PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake")
        preview, concurrent_replay = await asyncio.gather(
            owner_service.request_candidate(tenant, business, actor, body),
            owner_service.request_candidate(tenant, business, actor, body),
        )
        assert preview.id == concurrent_replay.id
        assert preview.generation_mode == "visual_fake" and preview.state == "pending"
        assert (await owner_service.request_candidate(tenant, business, actor, body)).id == preview.id
        claim = (await claim_previews(worker, uuid4()))[0]
        service = MediaPreviewService(cfg, worker, store, database)
        assert await service.render(preview.id, claim.fence) == "completed"
        assert store.put.await_count == 1
        assert (await owner_service.file_key(tenant, business, actor, preview.id)).endswith(".jpg")
        assert [p.id for p in await owner_service.list(tenant, business, actor)] == [preview.id]
        deliveries = ContentDeliveryService(cfg, database, worker)
        delivery = await deliveries.record(source, preview.id)
        assert delivery is not None
        approved = await deliveries.decide(
            tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
        )
        assert approved.decision_state == "approved"
        # A reused operation with a different prepared source fingerprint is a
        # conflict, even when both requests race to create a preview.
        other = PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake")
        original = await VisualContextService(cfg, database).capture(tenant, business, actor, proposal, candidate=True)
        changed = replace(original, fingerprint="d" * 64)
        with monkeypatch.context() as mock:
            mock.setattr(VisualContextService, "capture", AsyncMock(side_effect=[original, changed]))
            outcomes = await asyncio.gather(
                owner_service.request_candidate(tenant, business, actor, other),
                owner_service.request_candidate(tenant, business, actor, other),
                return_exceptions=True,
            )
        assert sum(not isinstance(result, Exception) for result in outcomes) == 1
        conflict = next(result for result in outcomes if isinstance(result, AuthError))
        assert conflict.code == "PREVIEW_OPERATION_CONFLICT"
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM visual_ai_attempts WHERE preview_id=:id"), {"id": preview.id}
                )
                == 1
            )
            assert (
                await conn.scalar(
                    text("SELECT actual_usd_micros FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant}
                )
                == 0
            )
        inflight = await owner_service.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        queued = await owner_service.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        queued_before_regrant = await owner_service.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        claims = {item.id: item for item in await claim_previews(worker, uuid4())}
        entered, release = asyncio.Event(), asyncio.Event()

        async def block_upload(*_):
            entered.set()
            await release.wait()

        store.put.side_effect = block_upload
        task = asyncio.create_task(service.render(inflight.id, claims[inflight.id].fence))
        try:
            await asyncio.wait_for(entered.wait(), 20)
            assert (await consent.set(tenant, business, actor, False))["state"] == "revocation_pending"
            visible_while_pending = {item.id for item in await owner_service.list(tenant, business, actor)}
            assert inflight.id in visible_while_pending and queued.id not in visible_while_pending
            assert await service.render(queued.id, claims[queued.id].fence) == "failed"
        finally:
            release.set()
        assert await task == "completed"
        assert (await consent.status(tenant, business, actor))["state"] == "revoked"
        assert (await owner_service.file_key(tenant, business, actor, inflight.id)).endswith(".jpg")
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await owner_service.file_key(tenant, business, actor, preview.id)
        assert [item.id for item in await owner_service.list(tenant, business, actor)] == [inflight.id]
        # Re-granting allows new work, but neither invalidates the previously
        # completed preview nor restarts a job queued under the old grant.
        await consent.set(tenant, business, actor, True)
        assert (await owner_service.file_key(tenant, business, actor, inflight.id)).endswith(".jpg")
        calls_before = store.put.await_count
        assert await service.render(queued_before_regrant.id, claims[queued_before_regrant.id].fence) == "failed"
        assert store.put.await_count == calls_before
    finally:
        await worker.close()
