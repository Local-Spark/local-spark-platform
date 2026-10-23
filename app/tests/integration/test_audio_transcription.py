"""Real PostgreSQL enforces at-most-once reservations and private transcript storage."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.material_media import MaterialError
from app.db.session import Database
from app.services import audio_transcription as module
from app.services.audio_transcription import AudioTranscriptionService
from app.services.whatsapp_processing import MaterialProcessor

pytestmark = pytest.mark.integration


async def test_audio_reservation_success_replay_budget_and_uncertain(admin, seeded, settings, monkeypatch):
    key = Fernet.generate_key().decode()
    config = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "audio_transcription_mode": "openai",
            "openai_api_key": SecretStr("fake"),
            "audio_daily_seconds_limit": 5,
        }
    )
    tenant, business = seeded["t1"], uuid4()
    events = [uuid4() for _ in range(5)]
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:business,:tenant,'Test','UTC')"),
            {"business": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999',true,'#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_processing_consents
              (tenant_id,business_id,actor_id,audio_transcription_accepted_at)
              VALUES(:tenant,:business,:actor,now())"""),
            {"tenant": tenant, "business": business, "actor": seeded["a1"]},
        )
        for event in events:
            await connection.execute(
                text("""INSERT INTO whatsapp_material_events
                  (id,tenant_id,business_id,kind,ciphertext,expires_at,sender_hash,state)
                  VALUES(:event,:tenant,:business,'audio','encrypted',now()+interval '7 days',:sender,'processed')"""),
                {"event": event, "tenant": tenant, "business": business, "sender": "a" * 64},
            )
            await connection.execute(
                text("""INSERT INTO whatsapp_material_assets
                  (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type)
                  VALUES(:event,:tenant,:business,'audio','encrypted',:key,'audio/ogg')"""),
                {"event": event, "tenant": tenant, "business": business, "key": f"audio/{event}"},
            )
    database = Database(config, correlator=True)
    store = AsyncMock()
    store.get_audio.return_value = b"ogg"
    processor = MaterialProcessor(config, database, AsyncMock(), store)
    processor._eligible = AsyncMock(return_value=True)
    provider = AsyncMock()
    provider.transcribe.return_value = "Promoção amanhã"
    service = AudioTranscriptionService(processor, provider)
    monkeypatch.setattr(module, "normalize_audio", AsyncMock(return_value=(b"wav", 3)))
    try:
        assert await service.run(events[0]) == "completed"
        assert await service.run(events[0]) == "skipped"
        provider.transcribe.assert_awaited_once()
        async with admin.connect() as connection:
            result = (
                await connection.execute(
                    text("""SELECT a.transcript_ciphertext,a.transcription_state,u.reserved_seconds
                      FROM whatsapp_material_assets a JOIN audio_transcription_usage u ON u.event_id=a.id
                      WHERE a.id=:event"""),
                    {"event": events[0]},
                )
            ).one()
        assert Fernet(key.encode()).decrypt(result[0].encode()).decode() == "Promoção amanhã"
        assert (result[1], result[2]) == ("completed", 3)
        assert await service.run(events[1]) == "budget_exceeded"
        assert await service.run(events[1]) == "skipped"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM audio_transcription_usage")) == 1
        provider.transcribe.side_effect = MaterialError("AUDIO_PROVIDER_UNCERTAIN")
        config.audio_daily_seconds_limit = 10
        assert await service.run(events[2]) == "uncertain"
        assert await service.run(events[2]) == "skipped"
        monkeypatch.setattr(module, "normalize_audio", AsyncMock(side_effect=MaterialError("AUDIO_INVALID")))
        assert await service.run(events[3]) == "rejected"
        assert await service.run(events[3]) == "skipped"
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:event"),
                {"event": events[4]},
            )
        assert await service.run(events[4]) == "skipped"
        assert await service.run(uuid4()) == "skipped"
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO audio_transcription_usage
                  (event_id,tenant_id,business_id,reserved_seconds,state,created_at)
                  VALUES(:event,:tenant,:business,1,'submitted',now()-interval '6 minutes')"""),
                {"event": events[4], "tenant": tenant, "business": business},
            )
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET transcription_state='submitted' WHERE id=:event"),
                {"event": events[4]},
            )
        assert await module.reconcile_stale_audio(database) == 1
        assert await module.reconcile_stale_audio(database) == 0
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT transcription_state FROM whatsapp_material_assets WHERE id=:event"),
                    {"event": events[4]},
                )
                == "uncertain"
            )
    finally:
        await database.close()
