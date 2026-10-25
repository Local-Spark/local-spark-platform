"""Audio boundaries and provider submission remain bounded and explicit."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters import audio_transcription as module
from app.adapters.audio_transcription import OpenAIAudioTranscriber, normalize_audio
from app.adapters.material_media import MaterialError, MaterialStore


@pytest.mark.parametrize(
    "duration,code",
    [
        ("bad", "AUDIO_INVALID"),
        ("nan", "AUDIO_DURATION_INVALID"),
        ("0", "AUDIO_DURATION_INVALID"),
        ("181", "AUDIO_DURATION_INVALID"),
    ],
)
async def test_preflight_rejects_bad_duration(monkeypatch, duration, code):
    monkeypatch.setattr(module, "_command", AsyncMock(return_value=duration.encode()))
    with pytest.raises(MaterialError, match=code):
        await normalize_audio(b"input")


async def test_preflight_converts_short_audio_and_caps_output(monkeypatch):
    async def command(*args):
        if args[0] == "ffprobe":
            return b"2.2\n"
        module.Path(args[-1]).write_bytes(b"wav")
        return b""

    monkeypatch.setattr(module, "_command", command)
    assert await normalize_audio(b"input") == (b"wav", 3)

    async def oversized(*args):
        if args[0] == "ffprobe":
            return b"1"
        module.Path(args[-1]).write_bytes(b"x" * 25_000_001)
        return b""

    monkeypatch.setattr(module, "_command", oversized)
    with pytest.raises(MaterialError, match="AUDIO_SIZE_EXCEEDED"):
        await normalize_audio(b"input")


@pytest.mark.parametrize("problem", ["missing", "timeout", "bad_exit"])
async def test_command_fails_closed(monkeypatch, problem):
    if problem == "missing":
        monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(side_effect=FileNotFoundError()))
    else:
        process = Mock(returncode=None if problem == "timeout" else 1)
        process.communicate = AsyncMock(
            side_effect=[TimeoutError(), (b"", b"")] if problem == "timeout" else None, return_value=(b"", b"")
        )
        process.kill = Mock()
        monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    with pytest.raises(
        MaterialError, match="AUDIO_INVALID" if problem == "bad_exit" else "AUDIO_CONVERSION_UNAVAILABLE"
    ):
        await module._command("ffprobe")


async def test_command_returns_bounded_output(monkeypatch):
    process = Mock(returncode=0)
    process.communicate = AsyncMock(return_value=(b"ready", b""))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    assert await module._command("ffprobe") == b"ready"


async def test_storage_download_is_bounded_and_closes_body(settings, monkeypatch):
    store = MaterialStore(settings.model_copy(update={"material_storage_bucket": "test"}))
    body = Mock()
    body.read.return_value = b"wav"
    client = Mock()
    client.get_object.return_value = {"ContentLength": 3, "Body": body}
    monkeypatch.setattr(store, "_client", lambda: client)
    assert await store.get_audio("key") == b"wav"
    body.close.assert_called_once()
    client.get_object.return_value = {"ContentLength": 20_000_000, "Body": body}
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_audio("key")
    body.read.return_value = b"x" * (16 * 1024 * 1024 + 1)
    client.get_object.return_value = {"ContentLength": 0, "Body": body}
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_audio("key")
    client.get_object.side_effect = RuntimeError("storage")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await store.get_audio("key")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_NOT_CONFIGURED"):
        await MaterialStore(settings).get_audio("key")


async def test_store_bounded_image_download(settings, monkeypatch):
    from unittest.mock import Mock

    from pydantic import SecretStr

    from app.adapters.material_media import MAX_BYTES, MaterialStore

    store = MaterialStore(settings)
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_NOT_CONFIGURED"):
        await store.get_image("image")
    configured = settings.model_copy(
        update={
            "material_storage_bucket": "bucket",
            "material_storage_access_key": SecretStr("key"),
            "material_storage_secret_key": SecretStr("secret"),
        }
    )
    store = MaterialStore(configured)
    client = Mock()
    monkeypatch.setattr(store, "_client", lambda: client)
    body = Mock()
    body.read.return_value = b"image"
    client.get_object.return_value = {"Body": body, "ContentLength": 5}
    assert await store.get_image("image") == b"image"
    body.close.assert_called_once()
    assert body.read.call_args.args == (MAX_BYTES["image"] + 1,)
    client.get_object.return_value["ContentLength"] = MAX_BYTES["image"] + 1
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_image("image")
    client.get_object.return_value["ContentLength"] = 5
    body.read.return_value = b"x" * (MAX_BYTES["image"] + 1)
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_image("image")
    client.get_object.side_effect = RuntimeError("unavailable")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await store.get_image("image")


async def test_store_bounded_video_download(settings, monkeypatch):
    from app.adapters.material_media import MAX_BYTES

    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_NOT_CONFIGURED"):
        await MaterialStore(settings).get_video("video")
    store = MaterialStore(settings.model_copy(update={"material_storage_bucket": "bucket"}))
    client, body = Mock(), Mock()
    body.read.return_value = b"mp4"
    client.get_object.return_value = {"Body": body, "ContentLength": 3}
    monkeypatch.setattr(store, "_client", lambda: client)
    assert await store.get_video("video") == b"mp4"
    assert body.read.call_args.args == (MAX_BYTES["video"] + 1,)
    body.close.assert_called_once()
    client.get_object.return_value["ContentLength"] = MAX_BYTES["video"] + 1
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_video("video")
    client.get_object.return_value["ContentLength"] = 0
    body.read.return_value = b"x" * (MAX_BYTES["video"] + 1)
    with pytest.raises(MaterialError, match="MEDIA_SIZE_EXCEEDED"):
        await store.get_video("video")
    client.get_object.side_effect = RuntimeError("storage")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await store.get_video("video")


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"text": "  Olá  "}, "Olá"),
        ({"text": " "}, None),
        ({"text": 1}, None),
        ([], None),
        ({"text": "x" * 16001}, None),
    ],
)
async def test_provider_response_validation(settings, monkeypatch, payload, expected):
    config = settings.model_copy(
        update={
            "audio_transcription_mode": "openai",
            "openai_api_key": SecretStr("test"),
            "audio_daily_seconds_limit": 60,
        }
    )
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    client = AsyncMock()
    client.post.return_value = response
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=client)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(module.httpx, "AsyncClient", factory)
    provider = OpenAIAudioTranscriber(config)
    if expected is None:
        with pytest.raises(MaterialError, match="AUDIO_PROVIDER_INVALID"):
            await provider.transcribe(b"wav", uuid4())
    else:
        assert await provider.transcribe(b"wav", uuid4()) == expected
        assert client.post.call_args.kwargs["data"] == {"model": "gpt-transcribe"}


async def test_provider_disabled_and_uncertain(settings, monkeypatch):
    with pytest.raises(MaterialError, match="AUDIO_PROVIDER_DISABLED"):
        await OpenAIAudioTranscriber(settings).transcribe(b"wav", uuid4())
    config = settings.model_copy(update={"audio_transcription_mode": "openai"})
    with pytest.raises(MaterialError, match="AUDIO_PROVIDER_DISABLED"):
        await OpenAIAudioTranscriber(config).transcribe(b"wav", uuid4())
    client = AsyncMock()
    client.post.side_effect = httpx.ConnectError("network")
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=client)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(module.httpx, "AsyncClient", factory)
    with pytest.raises(MaterialError, match="AUDIO_PROVIDER_UNCERTAIN"):
        await OpenAIAudioTranscriber(config.model_copy(update={"openai_api_key": SecretStr("test")})).transcribe(
            b"wav", uuid4()
        )
