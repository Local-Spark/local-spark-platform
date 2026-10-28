"""One explicit business contract authorizes materials and audio without legacy flags."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.services import audio_transcription as audio_module
from app.services.audio_transcription import AudioTranscriptionService
from app.services.auth import AuthError
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_link import WhatsAppLinkService
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.services.whatsapp_processing import MaterialProcessor
from app.services.whatsapp_replies import claim_ack, claim_reply, finish_reply
from app.tests.integration.test_editorial_proposals import _business

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("legacy", [False, True])
async def test_contract_covers_audio_materials_link_and_reply_without_rewriting_history(
    admin, database, seeded, settings, monkeypatch, legacy
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    key = Fernet.generate_key().decode()
    config = settings.model_copy(
        update={
            "service_agreement_required": True,
            "meta_encryption_key": SecretStr(key),
            "meta_webhook_mode": "cloud",
            "meta_public_phone": "+5511888888888",
            "audio_transcription_mode": "openai",
            "audio_daily_seconds_limit": 10,
            "meta_daily_message_limit": 10,
        }
    )
    cipher = Fernet(key.encode())
    number = "5511999999999"
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
        if legacy:
            await connection.execute(
                text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id,revoked_at)
                  VALUES(:tenant,:business,:actor,now()-interval '1 day')"""),
                {"tenant": tenant, "business": business, "actor": actor},
            )
    materials = WhatsAppMaterialsService(config, database)
    assert not (await materials.audio_consent_status(tenant, business, actor))["accepted"]
    await ServiceAgreementService(config, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    assert (await materials.consent_status(tenant, business, actor))["accepted"]
    assert (await materials.audio_consent_status(tenant, business, actor))["accepted"]
    for mutation in (
        materials.accept_consent(tenant, business, actor),
        materials.revoke_consent(tenant, business, actor),
        materials.set_audio_consent(tenant, business, actor, False),
    ):
        with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
            await mutation
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await materials.audio_consent_status(tenant, business, seeded["viewer"])
    async with admin.connect() as connection:
        row = (
            (
                await connection.execute(
                    text("""SELECT revoked_at,audio_transcription_accepted_at FROM whatsapp_processing_consents
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one_or_none()
        )
        assert (row is not None) == legacy
        if row is not None:
            assert row["revoked_at"] is not None and row["audio_transcription_accepted_at"] is None

    # Requesting a link now needs the contract, phone proof and plan, not a second consent.
    links = WhatsAppLinkService(config, database, database)
    assert (await links.start(tenant, business, actor))["status"] == "pending"
    event, audio = uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO whatsapp_channel_links
              (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
              VALUES(:tenant,:business,:actor,:sender,:proof,now()-interval '1 minute')"""),
            {
                "tenant": tenant,
                "business": business,
                "actor": actor,
                "sender": sender_hash(config, number),
                "proof": uuid4(),
            },
        )
        for identity, kind in ((event, "text"), (audio, "audio")):
            await connection.execute(
                text("""INSERT INTO whatsapp_material_events
                  (id,tenant_id,business_id,kind,ciphertext,sender_hash,state,expires_at)
                  VALUES(:id,:tenant,:business,:kind,:ciphertext,:sender,:state,NULL)"""),
                {
                    "id": identity,
                    "tenant": tenant,
                    "business": business,
                    "kind": kind,
                    "ciphertext": cipher.encrypt(
                        json.dumps(
                            {"from": number, "type": "text", "text": {"body": "Hoje o café está 10 reais"}}
                        ).encode()
                    ).decode(),
                    "sender": sender_hash(config, number),
                    "state": "pending" if kind == "text" else "processed",
                },
            )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
              (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type)
              VALUES(:id,:tenant,:business,'audio','encrypted','synthetic/audio','audio/ogg')"""),
            {"id": audio, "tenant": tenant, "business": business},
        )
    worker = Database(config, correlator=True)
    store = AsyncMock()
    store.get_audio.return_value = b"synthetic-ogg"
    processor = MaterialProcessor(config, worker, AsyncMock(), store)
    provider = AsyncMock()
    provider.transcribe.return_value = "Quero um story do café"
    monkeypatch.setattr(audio_module, "normalize_audio", AsyncMock(return_value=(b"synthetic-wav", 3)))
    try:
        assert await processor.process(event) == "processed"
        service = AudioTranscriptionService(processor, provider)
        assert await service.run(audio) == "completed"
        assert await service.run(audio) == "skipped"
        provider.transcribe.assert_awaited_once()
        reply = await claim_reply(worker, config)
        assert reply is not None
        await finish_reply(worker, reply, "accepted", "synthetic-message")
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE editorial_conversation_decisions SET state='confirmed' WHERE id=:id"), {"id": reply.id}
            )
            await connection.execute(
                text("UPDATE editorial_whatsapp_replies SET ack_state='pending' WHERE id=:id"), {"id": reply.id}
            )
        ack = await claim_ack(worker, config)
        assert ack is not None and ack.ack
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"), {"tenant": tenant}
            )
        async with worker.sessions() as session, session.begin():
            assert not await processor._eligible(
                session,
                {
                    "tenant_id": tenant,
                    "business_id": business,
                    "sender_hash": sender_hash(config, number),
                    "created_at": datetime.now(UTC),
                    "expires_at": None,
                },
            )
    finally:
        await worker.close()
