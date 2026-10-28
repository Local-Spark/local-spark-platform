"""Disconnecting a channel preserves the business's service permissions."""

import asyncio
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION
from app.services.visual_consent_gate import VisualConsentGate
from app.services.whatsapp_link import WhatsAppLinkService
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_attempts import preview

pytestmark = pytest.mark.integration


async def test_disconnect_does_not_revoke_the_channel_or_audio_consent(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE whatsapp_processing_consents SET audio_transcription_accepted_at=now()
          WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business},
        )
    service = WhatsAppLinkService(settings, database, None)
    assert await service.disconnect(tenant, business, actor) == {"status": "disconnected"}
    assert await service.disconnect(tenant, business, actor) == {"status": "disconnected"}
    async with admin.connect() as connection:
        link = await connection.scalar(
            text("""SELECT active FROM whatsapp_channel_links
          WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business},
        )
        consent = (
            await connection.execute(
                text("""SELECT revoked_at,audio_transcription_accepted_at
          FROM whatsapp_processing_consents WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
        ).one()
        assert link is False and consent.revoked_at is None and consent.audio_transcription_accepted_at is not None
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.disconnect(tenant, business, seeded["viewer"])


async def test_disconnect_waits_for_visual_work_and_unknown_audio(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    operation = uuid4()
    await gate.admit(tenant, business, actor, await preview(admin, tenant, business, actor), operation, 1)
    service = WhatsAppLinkService(settings, database, None)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await service.disconnect(tenant, business, actor)
    await gate.finish(tenant, business, actor, operation, 1)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,'whatsapp.audio_submitted',:event)"""),
            {"tenant": tenant, "actor": actor, "operation": uuid4(), "event": uuid4()},
        )
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await service.disconnect(tenant, business, actor)


async def test_connect_and_confirmation_require_current_agreement(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_profiles SET phone_verified=true
          WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business},
        )
    cfg = settings.model_copy(
        update={"service_agreement_required": True, "meta_webhook_mode": "cloud", "meta_public_phone": "+5511988887777"}
    )
    service = WhatsAppLinkService(cfg, database, database)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await service.start(tenant, business, actor)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await service.confirm(tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO service_agreement_acceptances
          (tenant_id,business_id,actor_id,version,notice_hash) VALUES(:tenant,:business,:actor,:version,:hash)"""),
            {
                "tenant": tenant,
                "business": business,
                "actor": actor,
                "version": SERVICE_AGREEMENT_VERSION,
                "hash": SERVICE_AGREEMENT_HASH,
            },
        )
    assert await service.start(tenant, business, actor) == {"status": "linked"}


async def test_disconnect_during_proof_cannot_reactivate_channel(admin, database, seeded, settings, monkeypatch):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("UPDATE whatsapp_channel_links SET active=false WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
    cfg = settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_public_phone": "+5511988887777",
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )
    service = WhatsAppLinkService(cfg, database, database)
    assert (await service.start(tenant, business, actor))["status"] == "pending"
    entered, resume = asyncio.Event(), asyncio.Event()

    async def proof(*args):
        entered.set()
        await resume.wait()
        return uuid4()

    monkeypatch.setattr(service, "_find_proof", proof)
    confirmation = asyncio.create_task(service.confirm(tenant, business, actor))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        assert await service.disconnect(tenant, business, actor) == {"status": "disconnected"}
    finally:
        resume.set()
    with pytest.raises(AuthError, match="WHATSAPP_LINK_RETRY"):
        await confirmation
    assert not (await service.status(tenant, business, actor))["linked"]
