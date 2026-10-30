"""Review confirmation is linked to the exact visual file and rechecked at publication."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.content_deliveries import ContentDecision, VisualReviewConfirmation
from app.services.auth import AuthError
from app.services.content_deliveries import ContentDeliveryService, claim_publications, publish_fake
from app.services.media_previews import MediaPreviewService
from app.tests.integration.test_media_previews import _accepted_case

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("tamper", [False, True])
async def test_full_piece_requires_complete_review_of_exact_hash_before_publish(
    admin, seeded, settings, monkeypatch, tamper
):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    cfg = settings.model_copy(update={"visual_ai_mode": "fake"})
    owner, worker = Database(cfg), Database(cfg, correlator=True)
    preview, delivery = uuid4(), uuid4()
    service = ContentDeliveryService(cfg, owner, worker)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO media_previews
                  (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,render_key,
                   context_version,script_version,fact_ids,state,object_key,sha256,width,height,
                   expires_at,mime_type,candidate,generation_mode,visual_fingerprint,visual_recipe)
                  VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:render,
                   1,1,'[]'::jsonb,'completed','private/fixture.jpg',:sha,1024,1280,
                   now()+interval '1 day','image/jpeg',true,'visual_fake',:fingerprint,'full_piece_v1')"""),
                {
                    "id": preview,
                    "tenant": tenant,
                    "business": business,
                    "proposal": proposal,
                    "actor": actor,
                    "operation": uuid4(),
                    "hash": "b" * 64,
                    "render": "c" * 64,
                    "sha": "d" * 64,
                    "fingerprint": "f" * 64,
                },
            )
            await connection.execute(
                text("""INSERT INTO content_deliveries
                  (id,tenant_id,business_id,actor_id,source_event_id,preview_id,kind,recipient_hash,
                   recipient_ciphertext,message_body,provider_message_id,decision_state,caption,expires_at)
                  VALUES(:id,:tenant,:business,:actor,:event,:preview,'candidate',:sender,
                   'synthetic','synthetic',:message,'pending','synthetic',now()+interval '1 day')"""),
                {
                    "id": delivery,
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "event": uuid4(),
                    "preview": preview,
                    "sender": "e" * 64,
                    "message": f"fake-whatsapp/{delivery}",
                },
            )
        sha = "d" * 64
        monkeypatch.setattr(
            "app.services.media_previews.MediaPreviewService._validate_visual", AsyncMock(return_value=False)
        )
        monkeypatch.setattr("app.services.media_previews.MediaPreviewService.file_key", AsyncMock(return_value="x"))
        monkeypatch.setattr(
            "app.services.content_deliveries.authorize_visual_copy",
            AsyncMock(return_value=SimpleNamespace(valid_until=None)),
        )
        previews = await MediaPreviewService(cfg, owner).list(tenant, business, actor)
        assert next(item for item in previews if item.id == preview).sha256 == sha
        with pytest.raises(AuthError):
            await MediaPreviewService(cfg, owner).list(tenant, business, seeded["a2"])
        with pytest.raises(AuthError, match="VISUAL_REVIEW_REQUIRED"):
            await service.decide(
                tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
            )
        confirmation = VisualReviewConfirmation(
            preview_sha256="a" * 64,
            price_and_terms=True,
            spelling=True,
            identity=True,
            fidelity=True,
            legibility=True,
        )
        with pytest.raises(AuthError, match="VISUAL_REVIEW_MISMATCH"):
            await service.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(operation_id=uuid4(), decision="approve", visual_review=confirmation),
            )
        confirmation = confirmation.model_copy(update={"preview_sha256": sha})
        accepted = await service.decide(
            tenant,
            business,
            actor,
            delivery,
            ContentDecision(operation_id=uuid4(), decision="approve", visual_review=confirmation),
        )
        assert accepted.decision_state == "approved"
        async with admin.connect() as connection:
            recorded = await connection.scalar(
                text("SELECT visual_review_confirmation FROM content_deliveries WHERE id=:id"), {"id": delivery}
            )
        assert recorded == confirmation.model_dump(mode="json")
        publication = (await claim_publications(worker, uuid4()))[0]
        if tamper:
            async with admin.begin() as connection:
                await connection.execute(
                    text("""UPDATE content_deliveries SET visual_review_confirmation=
                      jsonb_set(visual_review_confirmation,'{fidelity}','false'::jsonb) WHERE id=:id"""),
                    {"id": delivery},
                )
        assert await publish_fake(cfg, owner, worker, *publication) == ("failed" if tamper else "published")
    finally:
        await worker.close()
        await owner.close()
