"""Local candidate delivery and publication remain versioned and owner gated."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.content_deliveries import ContentDecision
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.content_deliveries import (
    ContentDeliveryService,
    apply_candidate_command,
    claim_publications,
    finish_publication_dispatch,
    publish_fake,
    reconcile_publications,
)
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.tests.integration.test_media_previews import _accepted_case
from app.tests.unit.test_core import access_token
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def _candidate_case(admin, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    key = Fernet.generate_key()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    event, sender = uuid4(), "a" * 64
    encrypted = (
        Fernet(key)
        .encrypt(
            json.dumps({"from": "5511999999999", "type": "text", "text": {"body": "Um café para esta tarde"}}).encode()
        )
        .decode()
    )
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE editorial_proposals SET review_state=NULL WHERE id=:id"), {"id": proposal})
        await conn.execute(
            text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id)
              VALUES(:t,:b,:a)"""),
            {"t": tenant, "b": business, "a": actor},
        )
        await conn.execute(
            text("""INSERT INTO whatsapp_channel_links
              (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
              VALUES(:t,:b,:a,:sender,:proof,now()-interval '1 minute')"""),
            {"t": tenant, "b": business, "a": actor, "sender": sender, "proof": uuid4()},
        )
        await conn.execute(
            text("""INSERT INTO whatsapp_material_events
              (id,tenant_id,business_id,kind,ciphertext,sender_hash,state,expires_at)
              VALUES(:id,:t,:b,'text',:cipher,:sender,'processed',now()+interval '7 days')"""),
            {"id": event, "t": tenant, "b": business, "cipher": encrypted, "sender": sender},
        )
        await conn.execute(
            text("""INSERT INTO whatsapp_material_assets(id,tenant_id,business_id,kind,ciphertext)
              VALUES(:id,:t,:b,'text',:cipher)"""),
            {
                "id": event,
                "t": tenant,
                "b": business,
                "cipher": Fernet(key).encrypt(b"Um cafe para esta tarde").decode(),
            },
        )
    app_db, worker_db = Database(cfg), Database(cfg, correlator=True)
    preview = await MediaPreviewService(cfg, app_db).request_candidate(
        tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
    )
    claim = (await claim_previews(worker_db, uuid4()))[0]
    assert await MediaPreviewService(cfg, worker_db, AsyncMock()).render(claim.id, claim.fence) == "completed"
    return cfg, app_db, worker_db, tenant, business, actor, proposal, event, preview.id


async def test_candidate_approval_replay_fake_publish_and_rls(admin, seeded, settings, api):
    cfg, app_db, worker_db, tenant, business, actor, proposal, event, preview = await _candidate_case(
        admin, seeded, settings
    )
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery == await service.record(event, preview)
        assert delivery is not None
        owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
        viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
        path = f"/api/v1/organizations/{tenant}/businesses/{business}/content-deliveries"
        assert (await api.get(path, headers=viewer)).status_code == 403
        assert (await api.get(path, headers=owner)).json()[0]["id"] == str(delivery)
        assert await claim_publications(worker_db, uuid4()) == []
        decision = ContentDecision(operation_id=uuid4(), decision="approve")
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": seeded["viewer"]},
            )
        denied = await api.post(f"{path}/{delivery}/decision", headers=viewer, json=decision.model_dump(mode="json"))
        assert denied.status_code == 403
        assert denied.json()["error_code"] == "CANDIDATE_OWNER_MISMATCH"
        accepted = await api.post(f"{path}/{delivery}/decision", headers=owner, json=decision.model_dump(mode="json"))
        assert accepted.status_code == 200, accepted.text
        first = accepted.json()
        assert first["decision_state"] == "approved"
        assert str((await service.decide(tenant, business, actor, delivery, decision)).id) == first["id"]
        with pytest.raises(AuthError) as error:
            await service.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(operation_id=decision.operation_id, decision="request_changes"),
            )
        assert error.value.code == "CANDIDATE_DECISION_CONFLICT"
        claimed = await claim_publications(worker_db, uuid4())
        assert len(claimed) == 1
        assert await publish_fake(cfg, app_db, worker_db, *claimed[0]) == "published"
        assert await publish_fake(cfg, app_db, worker_db, *claimed[0]) == "skipped"
        assert (await service.list(tenant, business, actor))[0].publication_id == f"fake-instagram/{delivery}"
        assert await claim_publications(worker_db, uuid4()) == []
        async with app_db.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
    finally:
        await worker_db.close()
        await app_db.close()


async def test_changed_context_blocks_approval_and_unapproved_never_publishes(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, proposal, event, preview = await _candidate_case(
        admin, seeded, settings
    )
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery is not None
        assert await claim_publications(worker_db, uuid4()) == []
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE business_context_heads SET version=version+1 WHERE tenant_id=:t AND business_id=:b"),
                {"t": tenant, "b": business},
            )
        with pytest.raises(AuthError):
            await service.decide(
                tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
            )
        assert await claim_publications(worker_db, uuid4()) == []
        assert await reconcile_publications(worker_db) == 0
    finally:
        await worker_db.close()
        await app_db.close()


async def test_processed_text_creates_candidate_without_manual_script_acceptance(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, _ = await _candidate_case(admin, seeded, settings)
    try:
        activities = ContentCandidateActivities(cfg, app_db, worker_db)
        proposal_id = await activities.request_candidate_proposal(str(event))
        assert proposal_id == await activities.request_candidate_proposal(str(event))
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        assert await EditorialProposalService(cfg, worker_db).run(claim.id) == "completed"
        assert await activities.candidate_proposal_state(proposal_id) == "completed"
        preview_id = await activities.request_candidate_preview([str(event), proposal_id])
        assert preview_id == await activities.request_candidate_preview([str(event), proposal_id])
        assert await activities.candidate_preview_state(preview_id) == "pending"
        render_claim = (await claim_previews(worker_db, uuid4()))[0]
        rendered = await MediaPreviewService(cfg, worker_db, AsyncMock()).render(render_claim.id, render_claim.fence)
        assert rendered == "completed"
        assert await activities.deliver_candidate_preview([str(event), preview_id]) == "candidate_delivered"
        assert await activities.deliver_candidate_preview([str(event), preview_id]) == "candidate_delivered"
        delivered = await ContentDeliveryService(cfg, app_db, worker_db).list(tenant, business, actor)
        assert len(delivered) == 1
        assert delivered[0].decision_state == "pending"
        async with admin.connect() as conn:
            review = await conn.scalar(
                text("SELECT review_state FROM editorial_proposals WHERE id=:id"), {"id": proposal_id}
            )
        assert review is None
    finally:
        await worker_db.close()
        await app_db.close()


async def test_without_confirmed_fact_asks_for_clarification(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, _ = await _candidate_case(admin, seeded, settings)
    try:
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE business_context_versions SET document=jsonb_set(document,'{facts}','[]'::jsonb)
                  WHERE tenant_id=:t AND business_id=:b"""),
                {"t": tenant, "b": business},
            )
        activities = ContentCandidateActivities(cfg, app_db, worker_db)
        proposal = await activities.request_candidate_proposal(str(event))
        claim = (await claim_proposals(worker_db, uuid4()))[0]
        assert await EditorialProposalService(cfg, worker_db).run(claim.id) == "rejected"
        assert await activities.candidate_proposal_state(proposal) == "needs_fact"
        assert await activities.deliver_candidate_clarification(str(event)) == "clarification_delivered"
        delivery = (await ContentDeliveryService(cfg, app_db, worker_db).list(tenant, business, actor))[0]
        assert delivery.kind == "clarification"
        assert delivery.preview_id is None
        assert await claim_publications(worker_db, uuid4()) == []
    finally:
        await worker_db.close()
        await app_db.close()


async def test_ambiguous_briefing_records_one_simulated_clarification(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, _ = await _candidate_case(admin, seeded, settings)
    try:
        activities = ContentCandidateActivities(cfg, app_db, worker_db)
        assert await activities.deliver_briefing_clarification(str(event)) == "clarification_delivered"
        assert await activities.deliver_briefing_clarification(str(event)) == "clarification_delivered"
        deliveries = await ContentDeliveryService(cfg, app_db, worker_db).list(tenant, business, actor)
        assert len(deliveries) == 1 and deliveries[0].kind == "clarification"
        async with admin.connect() as conn:
            provider_id = await conn.scalar(
                text("SELECT provider_message_id FROM content_deliveries WHERE id=:id"), {"id": deliveries[0].id}
            )
        assert provider_id.startswith("fake-whatsapp/")
        assert "quer divulgar" in deliveries[0].message_body
        assert deliveries[0].preview_id is None
    finally:
        await worker_db.close()
        await app_db.close()


async def test_command_requires_one_live_candidate_and_changes_are_not_published(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery is not None
        command_event = {"id": uuid4(), "tenant_id": tenant, "business_id": business, "sender_hash": "a" * 64}
        assert await apply_candidate_command(
            cfg, app_db, worker_db, command_event, {"text": {"body": "Pedir ajustes: destacar a imagem"}}
        )
        decision = (await service.list(tenant, business, actor))[0]
        assert decision.decision_state == "changes_requested"
        assert decision.review_note == "destacar a imagem"
        assert await claim_publications(worker_db, uuid4()) == []
        assert not await apply_candidate_command(
            cfg, app_db, worker_db, command_event, {"text": {"body": "Hoje temos café"}}
        )
    finally:
        await worker_db.close()
        await app_db.close()


async def test_decision_rejects_missing_expired_changed_preview_and_late_schedule(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        assert await service.record(uuid4(), preview) is None
        delivery = await service.record(event, preview)
        assert delivery is not None
        approve = ContentDecision(operation_id=uuid4(), decision="approve")
        with pytest.raises(AuthError) as missing:
            await service.decide(tenant, business, actor, uuid4(), approve)
        assert missing.value.code == "CANDIDATE_NOT_FOUND"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_deliveries SET decision_state='expired' WHERE id=:id"), {"id": delivery}
            )
        with pytest.raises(AuthError) as decided:
            await service.decide(tenant, business, actor, delivery, approve)
        assert decided.value.code == "CANDIDATE_DECISION_CONFLICT"
        async with admin.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE content_deliveries SET decision_state='pending',"
                    "expires_at=now()-interval '1 minute' WHERE id=:id"
                ),
                {"id": delivery},
            )
        with pytest.raises(AuthError) as expired:
            await service.decide(tenant, business, actor, delivery, approve)
        assert expired.value.code == "CANDIDATE_EXPIRED"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_deliveries SET expires_at=now()+interval '10 days' WHERE id=:id"),
                {"id": delivery},
            )
            await conn.execute(text("UPDATE media_previews SET state='failed' WHERE id=:id"), {"id": preview})
        with pytest.raises(AuthError) as invalid:
            await service.decide(tenant, business, actor, delivery, approve)
        assert invalid.value.code == "CANDIDATE_INVALID"
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE media_previews SET state='completed' WHERE id=:id"), {"id": preview})
        with pytest.raises(AuthError) as schedule:
            await service.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(
                    operation_id=uuid4(), decision="approve", scheduled_at=datetime.now(UTC) + timedelta(days=8)
                ),
            )
        assert schedule.value.code == "CANDIDATE_SCHEDULE_INVALID"
    finally:
        await worker_db.close()
        await app_db.close()


async def test_dispatch_failure_is_retryable_and_stale_handoff_becomes_unknown(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery is not None
        await service.decide(
            tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
        )
        claim = (await claim_publications(worker_db, uuid4()))[0]
        await finish_publication_dispatch(worker_db, *claim, accepted=False)
        assert (await service.list(tenant, business, actor))[0].publish_state == "pending"
        claim = (await claim_publications(worker_db, uuid4()))[0]
        await finish_publication_dispatch(worker_db, *claim, accepted=True)
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_deliveries SET publish_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": delivery},
            )
        assert await reconcile_publications(worker_db) == 1
        assert (await service.list(tenant, business, actor))[0].publish_state == "unknown"
        assert await claim_publications(worker_db, uuid4()) == []
    finally:
        await worker_db.close()
        await app_db.close()


async def test_publication_blocks_invalidated_candidate(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery is not None
        await service.decide(
            tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
        )
        claim = (await claim_publications(worker_db, uuid4()))[0]
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE business_context_heads SET version=version+1 WHERE tenant_id=:t AND business_id=:b"),
                {"t": tenant, "b": business},
            )
        assert await publish_fake(cfg, app_db, worker_db, *claim) == "failed"
        assert (await service.list(tenant, business, actor))[0].publish_state == "failed"
        production = cfg.model_copy(update={"environment": "production"})
        with pytest.raises(RuntimeError):
            await publish_fake(production, app_db, worker_db, *claim)
    finally:
        await worker_db.close()
        await app_db.close()


async def test_candidate_guards_and_quoted_whatsapp_commands(admin, seeded, settings, monkeypatch):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        async with admin.begin() as conn:
            sha = await conn.scalar(text("SELECT sha256 FROM media_previews WHERE id=:id"), {"id": preview})
            await conn.execute(text("UPDATE media_previews SET sha256=NULL WHERE id=:id"), {"id": preview})
        assert await service.record(event, preview) is None
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE media_previews SET sha256=:sha WHERE id=:id"), {"id": preview, "sha": sha})
        delivery = await service.record(event, preview)
        assert delivery is not None
        command_event = {"id": uuid4(), "tenant_id": tenant, "business_id": business, "sender_hash": "a" * 64}
        assert await apply_candidate_command(
            cfg,
            app_db,
            worker_db,
            command_event,
            {"text": {"body": "Aprovar"}, "context": {"id": f"fake-whatsapp/{delivery}"}},
        )
        assert (await service.list(tenant, business, actor))[0].decision_state == "approved"
        assert await apply_candidate_command(cfg, app_db, worker_db, command_event, {"text": {"body": "Aprovar"}})
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_deliveries SET decision_state='pending' WHERE id=:id"), {"id": delivery}
            )
            await conn.execute(
                text("UPDATE business_context_heads SET version=version+1 WHERE tenant_id=:t AND business_id=:b"),
                {"t": tenant, "b": business},
            )
        assert await apply_candidate_command(
            cfg, app_db, worker_db, {**command_event, "id": uuid4()}, {"text": {"body": "Aprovar"}}
        )
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": seeded["viewer"]},
            )

        async def allow_owner(*_args):
            return None

        monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", allow_owner)
        with pytest.raises(AuthError) as mismatch:
            await service.decide(
                tenant,
                business,
                seeded["viewer"],
                delivery,
                ContentDecision(operation_id=uuid4(), decision="approve"),
            )
        assert mismatch.value.code == "CANDIDATE_OWNER_MISMATCH"
    finally:
        await worker_db.close()
        await app_db.close()


async def test_edited_render_and_expired_handoff_never_publish(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivery = await service.record(event, preview)
        assert delivery is not None
        async with admin.begin() as conn:
            render_key = await conn.scalar(text("SELECT render_key FROM media_previews WHERE id=:id"), {"id": preview})
            await conn.execute(
                text("UPDATE media_previews SET render_key=:key WHERE id=:id"),
                {"id": preview, "key": "0" * 64},
            )
        with pytest.raises(AuthError) as invalid:
            await service.decide(
                tenant,
                business,
                actor,
                delivery,
                ContentDecision(operation_id=uuid4(), decision="approve"),
            )
        assert invalid.value.code == "CANDIDATE_INVALID"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET render_key=:key WHERE id=:id"),
                {"id": preview, "key": render_key},
            )
        await service.decide(
            tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
        )
        claim = (await claim_publications(worker_db, uuid4()))[0]
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_deliveries SET expires_at=now()-interval '1 second' WHERE id=:id"),
                {"id": delivery},
            )
        assert await publish_fake(cfg, app_db, worker_db, *claim) == "skipped"
    finally:
        await worker_db.close()
        await app_db.close()
