"""A completed visual candidate does not authorize stale factual copy."""

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.db.session import Database
from app.schemas.content_deliveries import ContentDecision
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.content_deliveries import ContentDeliveryService, claim_publications, publish_fake
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.whatsapp_ingest import sender_hash
from app.tests.integration.test_content_delivery import _review
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("scenario", ["before_approval", "after_approval", "request_changes"])
async def test_visual_copy_deadline_is_enforced_before_approval_and_publication(
    admin, database, seeded, settings, monkeypatch, scenario
):
    today = datetime.now(UTC).date()
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings, price_valid_until=today)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    async with admin.begin() as connection:
        p = {"tenant": tenant, "business": business, "actor": actor, "id": admission.proposal}
        proposal = (
            (await connection.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), p)).mappings().one()
        )
        await connection.execute(text("UPDATE businesses SET timezone='UTC' WHERE id=:business"), p)
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            p,
        )
        await connection.execute(
            text(
                "UPDATE whatsapp_channel_links SET sender_hash=:sender "
                "WHERE tenant_id=:tenant AND business_id=:business"
            ),
            {**p, "sender": sender_hash(cfg, "+5511999999999")},
        )
        cipher = Fernet(cfg.meta_encryption_key.get_secret_value().encode())
        await connection.execute(
            text("UPDATE whatsapp_material_events SET ciphertext=:cipher WHERE id=:id"),
            {
                "id": proposal["source_asset_id"],
                "cipher": cipher.encrypt(json.dumps({"from": "5511999999999"}).encode()).decode(),
            },
        )
        source = proposal["source_asset_id"]
    worker = Database(cfg, correlator=True)
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    try:
        owner = MediaPreviewService(cfg, database, store)
        preview = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        rendered = await MediaPreviewService(cfg, worker, store, database).render(preview.id, claim.fence)
        if rendered != "completed":
            async with admin.connect() as connection:
                code = await connection.scalar(
                    text("SELECT error_code FROM media_previews WHERE id=:id"), {"id": preview.id}
                )
            pytest.fail(f"visual preview failed: {code}")
        deliveries = ContentDeliveryService(cfg, database, worker)
        async with admin.connect() as connection:
            sha = await connection.scalar(text("SELECT sha256 FROM media_previews WHERE id=:id"), {"id": preview.id})
        review = _review(sha)
        delivery = await deliveries.record(source, preview.id)
        assert delivery is not None
        assert "Uma pausa com croissant" in (await deliveries.list(tenant, business, actor))[0].message_body
        future = datetime.combine(today + timedelta(days=1), datetime.min.time(), UTC) + timedelta(minutes=1)
        with pytest.raises(AuthError, match="CANDIDATE_SCHEDULE_INVALID"):
            await deliveries.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(operation_id=uuid4(), decision="approve", scheduled_at=future, visual_review=review),
            )

        class ExpiredClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(tz) + timedelta(days=2)

        if scenario in {"before_approval", "request_changes"}:
            with monkeypatch.context() as changed:
                changed.setattr("app.services.visual_copy_authorization.datetime", ExpiredClock)
                # The visual fingerprint itself is still unchanged; the fact's
                # deadline must be checked separately at the approval boundary.
                assert await owner.file_key(tenant, business, actor, preview.id)
                if scenario == "request_changes":
                    requested = await deliveries.decide(
                        tenant,
                        business,
                        actor,
                        delivery,
                        ContentDecision(operation_id=uuid4(), decision="request_changes", note="Atualize o preço"),
                    )
                    assert requested.decision_state == "changes_requested"
                    return
                with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
                    await deliveries.decide(
                        tenant,
                        business,
                        actor,
                        delivery,
                        ContentDecision(operation_id=uuid4(), decision="approve", visual_review=review),
                    )
        accepted = await deliveries.decide(
            tenant,
            business,
            actor,
            delivery,
            ContentDecision(operation_id=uuid4(), decision="approve", visual_review=review),
        )
        assert accepted.decision_state == "approved"
        publication = (await claim_publications(worker, uuid4()))[0]
        if scenario == "after_approval":
            monkeypatch.setattr("app.services.visual_copy_authorization.datetime", ExpiredClock)
        assert await publish_fake(cfg, database, worker, *publication) == (
            "failed" if scenario == "after_approval" else "published"
        )
    finally:
        await worker.close()
