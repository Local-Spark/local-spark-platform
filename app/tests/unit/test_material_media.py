"""Bounds and failure modes at the Meta/S3 media boundary."""

import base64
import hashlib
import io
import json
from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.adapters import material_media as module
from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore, MetaMediaClient


def png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 2)).save(output, format="PNG")
    return output.getvalue()


@pytest.mark.parametrize(
    "url,allowed",
    [
        ("https://lookaside.fbsbx.com/file", True),
        ("https://graph.facebook.com:443/file", True),
        ("https://cdn.fbcdn.net/file", True),
        ("http://lookaside.fbsbx.com/file", False),
        ("https://lookaside.fbsbx.com:444/file", False),
        ("https://user@lookaside.fbsbx.com/file", False),
        ("https://user:password@lookaside.fbsbx.com/file", False),
        ("https://evil.example/file", False),
        ("https://lookaside.fbsbx.com:bad/file", False),
    ],
)
def test_meta_download_url_is_strict(url, allowed):
    assert module.safe_meta_url(url) is allowed


def test_hash_formats():
    digest = hashlib.sha256(b"file").hexdigest()
    assert module._check_hash(digest, digest.upper())
    assert module._check_hash(digest, base64.b64encode(bytes.fromhex(digest)).decode())
    assert not module._check_hash(digest, "incorrect")


async def test_image_validation():
    valid = FetchedMedia(png(), "image/png", "hash")
    await module.inspect_media(valid, "image")
    with pytest.raises(MaterialError, match="MEDIA_TYPE_MISMATCH"):
        await module.inspect_media(FetchedMedia(valid.data, "image/jpeg", "hash"), "image")
    with pytest.raises(MaterialError, match="MEDIA_INVALID"):
        await module.inspect_media(FetchedMedia(b"bad", "image/png", "hash"), "image")


async def test_image_rejects_pixel_bombs(monkeypatch):
    picture = MagicMock(width=10_000, height=10_000)
    picture.__enter__.return_value = picture
    monkeypatch.setattr(module.Image, "open", Mock(return_value=picture))
    with pytest.raises(MaterialError, match="MEDIA_DIMENSIONS_EXCEEDED"):
        await module.inspect_media(FetchedMedia(b"compressed", "image/png", "hash"), "image")
    monkeypatch.setattr(module.Image, "open", Mock(side_effect=Image.DecompressionBombError("too many pixels")))
    with pytest.raises(MaterialError, match="MEDIA_INVALID"):
        await module.inspect_media(FetchedMedia(b"compressed", "image/png", "hash"), "image")


@pytest.mark.parametrize(
    "kind,streams,returncode,error",
    [
        ("audio", [{"codec_type": "audio"}], 0, None),
        ("video", [{"codec_type": "video"}], 0, None),
        ("audio", [{"codec_type": "video"}], 0, "MEDIA_INVALID"),
        ("audio", [{"codec_type": "audio"}], 1, "MEDIA_INVALID"),
        ("audio", "broken", 0, "MEDIA_INVALID"),
    ],
)
async def test_audio_video_inspection(monkeypatch, kind, streams, returncode, error):
    process = Mock(returncode=returncode)
    process.communicate = AsyncMock(return_value=(json.dumps({"streams": streams}).encode(), b""))
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    media = FetchedMedia(b"sample", "audio/ogg", "hash")
    if error:
        with pytest.raises(MaterialError, match=error):
            await module.inspect_media(media, kind)
    else:
        await module.inspect_media(media, kind)


@pytest.mark.parametrize("missing_binary", [False, True])
async def test_inspection_unavailable(monkeypatch, missing_binary):
    process = Mock(returncode=None)
    process.kill = Mock()
    process.communicate = AsyncMock(side_effect=[TimeoutError(), (b"", b"")])
    spawn = AsyncMock(side_effect=FileNotFoundError() if missing_binary else None, return_value=process)
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(MaterialError, match="MEDIA_INSPECTION_UNAVAILABLE"):
        await module.inspect_media(FetchedMedia(b"sample", "audio/ogg", "hash"), "audio")
    if missing_binary:
        process.kill.assert_not_called()
    else:
        process.kill.assert_called_once()


def configured(settings):
    return settings.model_copy(
        update={
            "meta_access_token": SecretStr("token"),
            "meta_graph_version": "v25.0",
            "meta_phone_number_id": "1234",
        }
    )


@pytest.mark.parametrize(
    "changes,media_id,kind,code",
    [
        ({"meta_access_token": None}, "123", "image", "META_MEDIA_NOT_CONFIGURED"),
        ({"meta_graph_version": None}, "123", "image", "META_MEDIA_NOT_CONFIGURED"),
        ({"meta_phone_number_id": None}, "123", "image", "META_MEDIA_NOT_CONFIGURED"),
        ({}, "abc", "image", "MEDIA_ID_INVALID"),
        ({}, "123", "text", "MEDIA_ID_INVALID"),
    ],
)
async def test_meta_media_configuration(settings, changes, media_id, kind, code):
    with pytest.raises(MaterialError, match=code):
        await MetaMediaClient(configured(settings).model_copy(update=changes)).fetch(media_id, kind)


@pytest.mark.parametrize(
    "metadata,status,body,expected",
    [
        ({"url": "https://evil.example/f", "mime_type": "image/png"}, 200, png(), "MEDIA_METADATA_INVALID"),
        ({"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/gif"}, 200, png(), "MEDIA_METADATA_INVALID"),
        (
            {"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/png", "file_size": 6_000_000},
            200,
            png(),
            "MEDIA_TOO_LARGE",
        ),
        (
            {"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/png", "sha256": "0" * 64},
            200,
            png(),
            "MEDIA_CHECKSUM_MISMATCH",
        ),
        ({"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/png"}, 200, b"", "MEDIA_INVALID"),
        ({"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/png"}, 200, png(), None),
        ([], 200, png(), "MEDIA_METADATA_INVALID"),
        ({}, 503, png(), "META_MEDIA_UNAVAILABLE"),
    ],
)
async def test_meta_fetch_metadata_and_body(settings, monkeypatch, metadata, status, body, expected):
    real_client = httpx.AsyncClient

    def answer(request):
        if request.url.host == "graph.facebook.com":
            if status == 503:
                return httpx.Response(503)
            return httpx.Response(status, json=metadata)
        return httpx.Response(200, content=body)

    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(answer), **kwargs),
    )
    action = MetaMediaClient(configured(settings)).fetch("123", "image")
    if expected:
        with pytest.raises(MaterialError, match=expected):
            await action
    else:
        result = await action
        assert result.data == body
        assert result.sha256 == hashlib.sha256(body).hexdigest()


@pytest.mark.parametrize(
    "download_status,limit,error", [(503, 5_000_000, "META_MEDIA_UNAVAILABLE"), (200, 4, "MEDIA_TOO_LARGE")]
)
async def test_meta_fetch_download_errors(settings, monkeypatch, download_status, limit, error):
    real_client = httpx.AsyncClient
    monkeypatch.setitem(module.MAX_BYTES, "image", limit)

    def answer(request):
        if request.url.host == "graph.facebook.com":
            return httpx.Response(200, json={"url": "https://lookaside.fbsbx.com/f", "mime_type": "image/png"})
        return httpx.Response(download_status, content=png())

    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(answer), **kwargs),
    )
    with pytest.raises(MaterialError, match=error):
        await MetaMediaClient(configured(settings)).fetch("123", "image")


async def test_store_configuration_upload_and_sign(settings, monkeypatch):
    store = MaterialStore(settings)
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_NOT_CONFIGURED"):
        await store.put("file", FetchedMedia(b"ok", "image/png", "hash"))
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_NOT_CONFIGURED"):
        await store.signed_url("file", "image/png")
    config = settings.model_copy(
        update={
            "material_storage_bucket": "bucket",
            "material_storage_endpoint": "http://private:9000",
            "material_storage_public_endpoint": "https://public.example",
            "material_storage_access_key": SecretStr("key"),
            "material_storage_secret_key": SecretStr("secret"),
        }
    )
    store = MaterialStore(config)
    create = Mock()
    monkeypatch.setattr(module.boto3, "client", create)
    await store.put("file", FetchedMedia(b"ok", "image/png", "hash"))
    assert create.call_args.kwargs["endpoint_url"] == "http://private:9000"
    create.return_value.generate_presigned_url.return_value = "https://public.example/signed"
    assert await store.signed_url("file", "image/png") == "https://public.example/signed"
    assert create.call_args.kwargs["endpoint_url"] == "https://public.example"
    create.return_value.put_object.side_effect = RuntimeError("storage down")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await store.put("file", FetchedMedia(b"ok", "image/png", "hash"))
    create.return_value.generate_presigned_url.side_effect = RuntimeError("signing unavailable")
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await store.signed_url("file", "image/png")


async def test_media_failure_has_stable_api_response(client):
    response = await client.app.exception_handlers[MaterialError](None, MaterialError("MATERIAL_STORAGE_UNAVAILABLE"))
    assert response.status_code == 503
    assert response.body == b'{"error_code":"MATERIAL_STORAGE_UNAVAILABLE"}'
