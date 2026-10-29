"""Changing the verified delivery number does not invalidate an attributed source."""

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.db.session import Database
from app.schemas.media_previews import PreviewRequest
from app.services.content_deliveries import ContentDeliveryService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.phone_verification import PhoneVerificationService
from app.services.visual_context import VisualContextService
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_link import WhatsAppLinkService
from app.tests.integration.test_visual_admission import _ready
from app.tests.integration.test_visual_effect_guard import guarded_case as guarded_case
from app.tests.integration.test_visual_source_invalidation import PausingStore

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("relink_during_creation", [False, True])
@pytest.mark.parametrize("second_owner_relinks", [False, True])
async def test_phone_change_preserves_admitted_preview_and_delivers_to_new_verified_channel(
    admin, database, seeded, settings, monkeypatch, relink_during_creation, second_owner_relinks
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    link_actor = seeded["a2"] if second_owner_relinks else actor
    if second_owner_relinks:
        async with admin.begin() as connection:
            await connection.execute(
                text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
                {"tenant": tenant, "actor": link_actor},
            )
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_monthly_budget_usd_micros": 100,
            "phone_verify_mode": "twilio",
            "meta_webhook_mode": "cloud",
            "meta_public_phone": "+5511988887777",
        }
    )
    context = VisualContextService(cfg, database)
    before = await context.capture(tenant, business, actor, admission.proposal, candidate=True)
    source = before.source_asset_id
    worker = Database(cfg, correlator=True)
    store = PausingStore()
    phone_provider = AsyncMock()
    phone_provider.start.return_value = "VE" + "b" * 32
    phone_provider.check.return_value = True
    phones = PhoneVerificationService(cfg, database, phone_provider)
    links = WhatsAppLinkService(cfg, database, object())
    proof = AsyncMock(return_value=uuid4())
    monkeypatch.setattr(links, "_find_proof", proof)

    async def verify_and_relink():
        assert await phones.start(tenant, business, link_actor) == {"status": "pending"}
        assert await phones.confirm(tenant, business, link_actor, "123456") == {"status": "verified"}
        assert (await links.start(tenant, business, link_actor))["status"] == "pending"
        assert await links.confirm(tenant, business, link_actor) == {"status": "linked"}
        assert (await context.capture(tenant, business, actor, admission.proposal, candidate=True)) == before

    try:
        owner = MediaPreviewService(cfg, database, store)
        preview = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        renderer = MediaPreviewService(cfg, worker, store, database)
        task = asyncio.create_task(renderer.render(preview.id, claim.fence))
        try:
            await asyncio.wait_for(store.entered.wait(), 20)
            result = await phones.update_phone(tenant, business, link_actor, "+5521999999999")
            assert not result["verified"]
            assert not (await links.status(tenant, business, actor))["linked"]
            assert (await context.capture(tenant, business, actor, admission.proposal, candidate=True)) == before
            if relink_during_creation:
                await verify_and_relink()
        finally:
            store.release.set()
        assert await asyncio.wait_for(task, 20) == "completed"
        assert await owner.file_key(tenant, business, actor, preview.id, review=True) == store.preview_key
        deliveries = ContentDeliveryService(cfg, database, worker)
        if not relink_during_creation:
            # The output remains private and reviewable while no destination
            # is active. Channel absence only postpones its fake delivery.
            assert await deliveries.record(source, preview.id) is None
            await verify_and_relink()
        delivery = await deliveries.record(source, preview.id)
        assert delivery is not None
        async with admin.connect() as connection:
            record = (
                (await connection.execute(text("SELECT * FROM content_deliveries WHERE id=:id"), {"id": delivery}))
                .mappings()
                .one()
            )
            assert record["actor_id"] == link_actor
            assert record["recipient_hash"] == sender_hash(cfg, "+5521999999999")
            cipher = Fernet(cfg.meta_encryption_key.get_secret_value().encode())
            assert cipher.decrypt(record["recipient_ciphertext"].encode()).decode() == "+5521999999999"
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        phone_provider.start.assert_awaited_once_with("+5521999999999")
        phone_provider.check.assert_awaited_once()
        proof.assert_awaited_once()
    finally:
        await worker.close()


async def test_second_owner_relink_during_guarded_provider_call_preserves_original_creation(
    admin, database, seeded, monkeypatch, guarded_case
):
    c = guarded_case
    other = seeded["a2"]
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": c.tenant, "actor": other},
        )
    config = c.cfg.model_copy(
        update={"phone_verify_mode": "twilio", "meta_webhook_mode": "cloud", "meta_public_phone": "+5511988887777"}
    )
    provider = AsyncMock()
    provider.start.return_value = "VE" + "b" * 32
    provider.check.return_value = True
    phones = PhoneVerificationService(config, database, provider)
    links = WhatsAppLinkService(config, database, object())
    monkeypatch.setattr(links, "_find_proof", AsyncMock(return_value=uuid4()))
    entered, release = asyncio.Event(), asyncio.Event()

    async def pause_provider(_):
        entered.set()
        await release.wait()
        return c.result

    c.provider.generate.side_effect = pause_provider
    task = asyncio.create_task(c.service.run(c.scope))
    try:
        await asyncio.wait_for(entered.wait(), 10)
        await phones.update_phone(c.tenant, c.business, other, "+5521999999999")
        assert await phones.start(c.tenant, c.business, other) == {"status": "pending"}
        assert await phones.confirm(c.tenant, c.business, other, "123456") == {"status": "verified"}
        assert (await links.start(c.tenant, c.business, other))["status"] == "pending"
        assert await links.confirm(c.tenant, c.business, other) == {"status": "linked"}
        # Source reads remain authorized by the original actor's membership
        # and durable business attribution, independent from the new link owner.
        assert await c.guard.current(
            c.scope,
            (
                await c.service.brand.prepare(
                    c.tenant, c.business, c.actor, c.scope.proposal, c.scope.operation, candidate=True
                )
            ).request,
        )
    finally:
        release.set()
    assert await asyncio.wait_for(task, 20) == "completed"
    c.provider.generate.assert_awaited_once()
    assert await c.owner_media.file_key(c.tenant, c.business, c.actor, c.preview.id, review=True)
    delivery = await ContentDeliveryService(config, database, c.worker).record(c.preview.source_asset_id, c.preview.id)
    assert delivery is not None
    async with admin.connect() as connection:
        row = (
            (await connection.execute(text("SELECT * FROM content_deliveries WHERE id=:id"), {"id": delivery}))
            .mappings()
            .one()
        )
        assert row["actor_id"] == other
        assert row["recipient_hash"] == sender_hash(config, "+5521999999999")
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1


async def test_completed_preview_with_legacy_channel_fingerprint_remains_reviewable(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    worker, store = Database(cfg, correlator=True), AsyncMock()
    try:
        owner = MediaPreviewService(cfg, database, store)
        preview = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        assert await MediaPreviewService(cfg, worker, store, database).render(preview.id, claim.fence) == "completed"
        async with admin.begin() as connection:
            # Old digests included mutable linked_at and cannot be reconstructed
            # after relink. Review uses the preserved result's durable proof,
            # without rewriting its historical identity to the new algorithm.
            await connection.execute(
                text("UPDATE media_previews SET visual_fingerprint=:old WHERE id=:id"),
                {"id": preview.id, "old": "0" * 64},
            )
        assert await owner.file_key(tenant, business, actor, preview.id, review=True)
        assert [item.id for item in await owner.list(tenant, business, actor)] == [preview.id]
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT visual_fingerprint FROM media_previews WHERE id=:id"), {"id": preview.id}
                )
                == "0" * 64
            )
    finally:
        await worker.close()
