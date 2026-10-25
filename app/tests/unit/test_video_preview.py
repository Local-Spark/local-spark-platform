"""The video recipe keeps source media bounded and produces timed, private MP4 bytes."""

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.adapters import video_preview as module
from app.adapters.static_preview import PreviewRenderError


def _image() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), "#55aa44").save(buffer, "PNG")
    return buffer.getvalue()


def test_frames_use_authorized_photo_and_factual_caption(tmp_path):
    module._write_frames(
        tmp_path,
        business_name="Hot Dog da Ana",
        statement="Cachorro-quente artesanal: R$ 20,00 hoje.",
        brand_color="#e65024",
        photo=_image(),
    )
    with Image.open(tmp_path / "scene0.png") as first:
        assert first.size == (1080, 1920)
        assert first.getpixel((100, 500))[1] > 100
    with Image.open(tmp_path / "scene1.png") as fact:
        assert fact.size == (1080, 1920)
    with Image.open(tmp_path / "scene2.png") as call_to_action:
        assert call_to_action.size == (1080, 1920)
    module._write_frames(tmp_path, business_name="Ana", statement="Fato válido.", brand_color="#ffffff", photo=None)
    assert (tmp_path / "scene0.png").is_file()
    module._write_frames(
        tmp_path,
        business_name="Ana",
        statement="Fato válido.",
        brand_color="#e65024",
        photo=None,
        video_overlay=True,
    )
    with Image.open(tmp_path / "scene0.png") as overlay:
        assert overlay.mode == "RGBA" and overlay.getpixel((100, 500))[3] == 0


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"brand_color": "orange"}, "PREVIEW_BRAND_INVALID"),
        ({"business_name": " "}, "PREVIEW_TEXT_OVERFLOW"),
        ({"statement": "palavra " * 300}, "PREVIEW_TEXT_OVERFLOW"),
        ({"photo": b"bad"}, "PREVIEW_SOURCE_INVALID"),
        ({"photo": b"x" * (5 * 1024 * 1024 + 1)}, "PREVIEW_SOURCE_TOO_LARGE"),
    ],
)
def test_frames_reject_unusable_content(tmp_path, changes, code):
    values = dict(business_name="Ana", statement="Fato válido.", brand_color="#e65024", photo=None)
    with pytest.raises(PreviewRenderError, match=code):
        module._write_frames(tmp_path, **(values | changes))


def test_frames_reject_decompression_size(tmp_path, monkeypatch):
    raw = Mock()
    raw.__enter__ = Mock(return_value=raw)
    raw.__exit__ = Mock(return_value=False)
    raw.width, raw.height = 6000, 5000
    monkeypatch.setattr(module.Image, "open", Mock(return_value=raw))
    with pytest.raises(PreviewRenderError, match="PREVIEW_SOURCE_TOO_LARGE"):
        module._write_frames(tmp_path, business_name="Ana", statement="Fato válido.", brand_color="#e65024", photo=b"x")


class FakeProcess:
    def __init__(self, output: Path, data: bytes | None, returncode: int = 0) -> None:
        self.output, self.data, self.returncode = output, data, returncode
        self.kill = Mock()

    async def communicate(self):
        if self.data is not None:
            self.output.write_bytes(self.data)
        return b"", b""


async def test_video_recipe_encodes_timed_mp4(monkeypatch):
    calls = []

    async def spawn(*args, **_):
        calls.append(args)
        return FakeProcess(Path(args[-1]), b"mp4-data")

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    result = await module.render_video_preview(
        business_name="Ana", statement="Cachorro-quente artesanal.", brand_color="#e65024", source_image=_image()
    )
    assert result.data == b"mp4-data" and result.mime_type == "video/mp4"
    assert len(result.sha256) == 64
    assert "libx264" in calls[0]
    assert "concat=n=3:v=1:a=0" in calls[0][calls[0].index("-filter_complex") + 1]
    assert module.VIDEO_DURATION_MS == 8000


async def test_video_recipe_uses_bounded_source_clip_and_mutes_audio(monkeypatch):
    calls = []
    probe = AsyncMock()
    monkeypatch.setattr(module, "_probe_source_video", probe)

    async def spawn(*args, **_):
        calls.append(args)
        assert Path(args[args.index("-stream_loop") + 5]).read_bytes() == b"video-data"
        return FakeProcess(Path(args[-1]), b"mp4-data")

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    result = await module.render_video_preview(
        business_name="Ana",
        statement="Fato válido.",
        brand_color="#e65024",
        source_image=None,
        source_video=b"video-data",
    )
    assert result.mime_type == "video/mp4" and result.data == b"mp4-data"
    probe.assert_awaited_once()
    assert "-an" in calls[0] and "-stream_loop" in calls[0]
    assert "overlay=0:0" in calls[0][calls[0].index("-filter_complex") + 1]


@pytest.mark.parametrize("video", [b"", b"x" * (50 * 1024 * 1024 + 1)])
async def test_video_recipe_rejects_oversized_or_empty_source(video):
    with pytest.raises(PreviewRenderError, match="PREVIEW_SOURCE_TOO_LARGE"):
        await module.render_video_preview(
            business_name="Ana",
            statement="Fato válido.",
            brand_color="#e65024",
            source_image=None,
            source_video=video,
        )


async def test_video_recipe_rejects_two_sources():
    with pytest.raises(PreviewRenderError, match="PREVIEW_MATERIAL_INVALID"):
        await module.render_video_preview(
            business_name="Ana",
            statement="Fato válido.",
            brand_color="#e65024",
            source_image=b"image",
            source_video=b"video",
        )


async def test_video_probe_accepts_bounded_dimensions(monkeypatch, tmp_path):
    process = Mock(returncode=0)
    process.communicate = AsyncMock(return_value=(b'{"streams":[{"width":640,"height":480}]}', b""))
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    await module._probe_source_video(tmp_path / "source.mp4")


@pytest.mark.parametrize(
    "payload,returncode",
    [
        (b"not-json", 0),
        (b'{"streams":[]}', 0),
        (b'{"streams":[{}]}', 0),
        (b'{"streams":[{"width":640,"height":480}]}', 1),
        (b'{"streams":[{"width":"640","height":480}]}', 0),
        (b'{"streams":[{"width":640,"height":"480"}]}', 0),
        (b'{"streams":[{"width":0,"height":480}]}', 0),
        (b'{"streams":[{"width":640,"height":0}]}', 0),
        (json.dumps({"streams": [{"width": 5000, "height": 5000}]}).encode(), 0),
    ],
)
async def test_video_probe_rejects_invalid_or_oversized_stream(monkeypatch, tmp_path, payload, returncode):
    process = Mock(returncode=returncode)
    process.communicate = AsyncMock(return_value=(payload, b""))
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    with pytest.raises(PreviewRenderError, match="PREVIEW_SOURCE_VIDEO_INVALID"):
        await module._probe_source_video(tmp_path / "source.mp4")


@pytest.mark.parametrize("problem", ["missing", "timeout"])
async def test_video_probe_reports_missing_binary_or_timeout(monkeypatch, tmp_path, problem):
    if problem == "missing":
        monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(side_effect=FileNotFoundError()))
    else:
        process = Mock(returncode=None)
        process.communicate = AsyncMock(return_value=(b"", b""))
        monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))

        async def wait_for(coroutine, *, timeout):
            await coroutine
            raise TimeoutError()

        monkeypatch.setattr(module.asyncio, "wait_for", wait_for)
    with pytest.raises(
        PreviewRenderError,
        match="VIDEO_RENDER_UNAVAILABLE" if problem == "missing" else "VIDEO_RENDER_TIMEOUT",
    ) as error:
        await module._probe_source_video(tmp_path / "source.mp4")
    assert error.value.retryable is (problem == "timeout")


@pytest.mark.parametrize(
    ("outcome", "code"),
    [
        ("missing_binary", "VIDEO_RENDER_UNAVAILABLE"),
        ("timeout", "VIDEO_RENDER_TIMEOUT"),
        ("nonzero", "VIDEO_RENDER_FAILED"),
        ("missing_output", "VIDEO_RENDER_FAILED"),
        ("empty", "VIDEO_RENDER_SIZE_INVALID"),
        ("large", "VIDEO_RENDER_SIZE_INVALID"),
    ],
)
async def test_video_recipe_reports_render_failures(monkeypatch, outcome, code):
    monkeypatch.setattr(module, "_write_frames", Mock())

    async def spawn(*args, **_):
        if outcome == "missing_binary":
            raise FileNotFoundError()
        data = None if outcome == "missing_output" else b""
        if outcome == "large":
            data = b"x" * (module.MAX_VIDEO_BYTES + 1)
        return FakeProcess(Path(args[-1]), data, 1 if outcome == "nonzero" else 0)

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    if outcome == "timeout":

        async def wait_for(coroutine, *, timeout):
            await coroutine
            raise TimeoutError()

        monkeypatch.setattr(module.asyncio, "wait_for", wait_for)
    with pytest.raises(PreviewRenderError, match=code) as error:
        await module.render_video_preview(
            business_name="Ana", statement="Fato válido.", brand_color="#e65024", source_image=None
        )
    assert error.value.retryable is (outcome == "timeout")
