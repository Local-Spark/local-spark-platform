"""Failures before and after reservation cannot trigger a second paid request."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.adapters.material_media import MaterialError
from app.services import audio_transcription as module
from app.services.audio_transcription import AudioTranscriptionService


def service_with(settings, monkeypatch, rows, *, eligible=True, seconds=2):
    session = Mock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock(side_effect=[True, True, 0, True])

    @asynccontextmanager
    async def opened():
        yield session

    session.begin = opened
    database = Mock(sessions=opened)
    config = settings.model_copy(
        update={
            "audio_transcription_mode": "openai",
            "openai_api_key": SecretStr("test"),
            "audio_daily_seconds_limit": 10,
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )
    store = Mock(get_audio=AsyncMock(return_value=b"ogg"))
    processor = Mock(settings=config, database=database, store=store)
    processor._eligible = AsyncMock(return_value=eligible)
    provider = Mock(transcribe=AsyncMock(return_value="olá"))
    service = AudioTranscriptionService(processor, provider)
    service._row = AsyncMock(side_effect=rows)
    monkeypatch.setattr(module, "normalize_audio", AsyncMock(return_value=(b"wav", seconds)))
    return service, session, processor, provider


def audio_row(**changes):
    return {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "kind": "audio",
        "object_key": "audio/file",
        "transcription_state": None,
        "delete_requested_at": None,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "event_expires": datetime.now(UTC) + timedelta(days=1),
        "created_at": datetime.now(UTC),
        "sender_hash": "a" * 64,
        **changes,
    }


async def test_disabled_and_rejection_replay(settings, monkeypatch):
    service, _, _, _ = service_with(settings, monkeypatch, [None])
    service.processor.settings.audio_transcription_mode = "disabled"
    assert await service.run(uuid4()) == "disabled"
    service._row = AsyncMock(side_effect=[None, audio_row(transcription_state="rejected")])
    assert await service._reject(uuid4(), "AUDIO_INVALID") == "skipped"
    assert await service._reject(uuid4(), "AUDIO_INVALID") == "skipped"


@pytest.mark.parametrize(
    "first,eligibility",
    [
        (None, True),
        (audio_row(kind="text"), True),
        (audio_row(transcription_state="completed"), True),
        (audio_row(), False),
    ],
)
async def test_initial_guard_skips(settings, monkeypatch, first, eligibility):
    service, _, _, provider = service_with(settings, monkeypatch, [first], eligible=eligibility)
    assert await service.run(uuid4()) == "skipped"
    provider.transcribe.assert_not_awaited()


async def test_missing_key_and_preflight_failure(settings, monkeypatch):
    first = audio_row(object_key=None)
    service, _, _, _ = service_with(settings, monkeypatch, [first, first])
    assert await service.run(uuid4()) == "rejected"
    row = audio_row()
    service, _, _, _ = service_with(settings, monkeypatch, [row, row])
    module.normalize_audio.side_effect = MaterialError("AUDIO_INVALID")
    assert await service.run(uuid4()) == "rejected"


async def test_preflight_retryable_storage_error_keeps_unsubmitted(settings, monkeypatch):
    service, _, _, provider = service_with(settings, monkeypatch, [audio_row()])
    service.processor.store.get_audio.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await service.run(uuid4())
    provider.transcribe.assert_not_awaited()


async def test_post_preflight_recheck_prevents_submission(settings, monkeypatch):
    service, _, _, provider = service_with(settings, monkeypatch, [audio_row(), None])
    assert await service.run(uuid4()) == "skipped"
    provider.transcribe.assert_not_awaited()


async def test_changed_state_after_preflight_prevents_submission(settings, monkeypatch):
    service, _, _, provider = service_with(
        settings, monkeypatch, [audio_row(), audio_row(transcription_state="submitted")]
    )
    assert await service.run(uuid4()) == "skipped"
    provider.transcribe.assert_not_awaited()


async def test_revocation_during_preflight_prevents_reservation(settings, monkeypatch):
    row = audio_row()
    service, session, processor, provider = service_with(settings, monkeypatch, [row, row])
    processor._eligible.side_effect = [True, False]
    assert await service.run(uuid4()) == "skipped"
    assert processor._eligible.await_count == 2
    provider.transcribe.assert_not_awaited()
    assert all(
        "INSERT INTO audio_transcription_usage" not in str(call.args[0]) for call in session.execute.await_args_list
    )


async def test_lost_asset_after_provider_is_uncertain(settings, monkeypatch):
    row = audio_row()
    service, _, _, provider = service_with(settings, monkeypatch, [row, row, None])
    assert await service.run(uuid4()) == "uncertain"
    provider.transcribe.assert_awaited_once()


async def test_completed_elsewhere_after_provider_is_uncertain(settings, monkeypatch):
    row = audio_row()
    service, _, _, _ = service_with(settings, monkeypatch, [row, row, audio_row(transcription_state="completed")])
    assert await service.run(uuid4()) == "uncertain"


async def test_revoked_after_provider_discards_transcript(settings, monkeypatch):
    row = audio_row()
    service, _, processor, _ = service_with(settings, monkeypatch, [row, row, row])
    processor._eligible.side_effect = [True, True, False]
    assert await service.run(uuid4()) == "uncertain"


@pytest.mark.parametrize(
    "change",
    [
        {"delete_requested_at": datetime.now(UTC)},
        {"expires_at": datetime.now(UTC) - timedelta(seconds=1)},
    ],
)
async def test_expired_or_deleted_audio_is_not_eligible(settings, monkeypatch, change):
    row = audio_row(**change)
    service, session, processor, _ = service_with(settings, monkeypatch, [])
    assert await service._eligible(session, row) is False
    processor._eligible.assert_not_awaited()


async def test_audio_requires_explicit_separate_consent(settings, monkeypatch):
    service, session, processor, _ = service_with(settings, monkeypatch, [])
    session.scalar = AsyncMock(return_value=False)
    assert await service._eligible(session, audio_row()) is False
    processor._eligible.assert_awaited_once()
