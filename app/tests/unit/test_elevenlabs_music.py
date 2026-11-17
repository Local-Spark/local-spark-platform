"""HTTP Music transport is bounded and never retries or prints provider errors."""

import hashlib

import httpx
import pytest

from app.adapters import elevenlabs_music
from app.services.auth import AuthError
from app.tests.unit.test_motion_music import configured


@pytest.mark.parametrize("mode", ["ok", "empty", "large", "error", "timeout", "disabled", "key"])
async def test_single_bounded_submission(settings, monkeypatch, mode):
    cfg = configured(settings)
    if mode == "disabled":
        cfg.elevenlabs_music_execution_enabled = False
    if mode == "key":
        cfg.elevenlabs_api_key = None
    calls = []

    def handle(request):
        calls.append(request)
        assert request.url.host == "api.elevenlabs.io"
        assert request.headers["xi-api-key"] == "synthetic-unit-key"
        if mode == "timeout":
            raise httpx.ReadTimeout("sensitive provider error")
        return httpx.Response(
            429 if mode == "error" else 200,
            content=b"" if mode == "empty" else b"x" * 101 if mode == "large" else b"synthetic",
        )

    client = httpx.AsyncClient
    monkeypatch.setattr(elevenlabs_music, "MAX_MUSIC_BYTES", 100)
    monkeypatch.setattr(
        elevenlabs_music.httpx, "AsyncClient", lambda **kwargs: client(**kwargs, transport=httpx.MockTransport(handle))
    )
    adapter = elevenlabs_music.ElevenLabsMusic(cfg)
    if mode == "ok":
        result = await adapter.generate({"force_instrumental": True})
        assert result.sha256 == hashlib.sha256(b"synthetic").hexdigest()
    else:
        with pytest.raises(AuthError) as error:
            await adapter.generate({"force_instrumental": True})
        assert "sensitive" not in str(error.value)
    assert len(calls) == (0 if mode in {"disabled", "key"} else 1)


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (
            401,
            b'{"detail":{"status":"missing_permissions","message":"private key value"}}',
            "MOTION_MUSIC_HTTP_401_MISSING_PERMISSIONS",
        ),
        (403, b'{"detail":{"status":"invalid_api_key"}}', "MOTION_MUSIC_HTTP_403_INVALID_API_KEY"),
        (429, b'{"detail":{"status":"quota_exceeded"}}', "MOTION_MUSIC_HTTP_429_QUOTA_EXCEEDED"),
        (422, b'{"detail":[{"input":"private"}]}', "MOTION_MUSIC_HTTP_422"),
        (502, b"<html>private</html>", "MOTION_MUSIC_HTTP_502"),
        (400, b'{"detail":{"status":"PRIVATE_VALUE"}}', "MOTION_MUSIC_HTTP_400"),
        (400, b'{"detail":{"status":[]}}', "MOTION_MUSIC_HTTP_400"),
        (500, b"[]", "MOTION_MUSIC_HTTP_500"),
        (503, b"x" * 16385, "MOTION_MUSIC_HTTP_503"),
        (500, b"\xff", "MOTION_MUSIC_HTTP_500"),
    ],
)
async def test_safe_error_category_is_preserved_without_provider_text(settings, monkeypatch, status, body, expected):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, content=body)

    client = httpx.AsyncClient
    monkeypatch.setattr(
        elevenlabs_music.httpx, "AsyncClient", lambda **kwargs: client(**kwargs, transport=httpx.MockTransport(handle))
    )
    with pytest.raises(AuthError) as caught:
        await elevenlabs_music.ElevenLabsMusic(configured(settings)).generate({"model_id": "music_v2_5"})
    assert caught.value.code == expected
    assert str(caught.value) == expected
    assert len(calls) == 1
