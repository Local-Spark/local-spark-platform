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
    module._write_frames(
        tmp_path,
        business_name="Ana",
        statement="Fato válido.",
        brand_color="#e65024",
        photo=None,
        video_overlay=True,
        closing_overlay=True,
        intro_text="Mostre o atendimento",
        cta_text="Converse com a Ana",
    )
    with Image.open(tmp_path / "scene2.png") as closing_overlay:
        assert closing_overlay.mode == "RGBA" and closing_overlay.getpixel((100, 500))[3] == 0


def test_wide_photo_preserves_both_product_edges_and_scene_text(tmp_path):
    photo = Image.new("RGB", (900, 500), "#55aa44")
    photo.paste("#e43b32", (0, 0, 100, 500))
    photo.paste("#3159dc", (800, 0, 900, 500))
    source = io.BytesIO()
    photo.save(source, "PNG")
    module._write_frames(
        tmp_path,
        business_name="Ana",
        statement="Fato confirmado.",
        brand_color="#e65024",
        photo=source.getvalue(),
        intro_text="Veja o preparo",
        cta_text="Peça pelo WhatsApp",
    )
    with Image.open(tmp_path / "scene0.png") as opening:
        assert opening.getpixel((15, 900)) == (228, 59, 50)
        assert opening.getpixel((1065, 900)) == (49, 89, 220)
        opening_bytes = opening.tobytes()
    with Image.open(tmp_path / "scene1.png") as fact:
        fact_bytes = fact.tobytes()
    with Image.open(tmp_path / "scene2.png") as closing:
        closing_bytes = closing.tobytes()
    module._write_frames(
        tmp_path,
        business_name="Ana",
        statement="Fato confirmado.",
        brand_color="#e65024",
        photo=source.getvalue(),
        intro_text="Outro início",
        cta_text="Outro convite",
    )
    with Image.open(tmp_path / "scene0.png") as opening:
        assert opening.tobytes() != opening_bytes
    with Image.open(tmp_path / "scene1.png") as fact:
        assert fact.tobytes() == fact_bytes
    with Image.open(tmp_path / "scene2.png") as closing:
        assert closing.tobytes() != closing_bytes


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
    probe = AsyncMock(return_value=6.0)
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
    filters = calls[0][calls[0].index("-filter_complex") + 1]
    assert "[foreground_source]scale=1080:1400:force_original_aspect_ratio=decrease" in filters
    assert "[background][foreground]overlay=(W-w)/2:160+(1400-h)/2" in filters
    assert "split=2" in filters and "trim=start=4.00:duration=2" in filters
    assert "[clip2][3:v]overlay" in filters


async def test_short_source_clip_uses_a_single_cut_and_brand_closing(monkeypatch):
    calls = []
    monkeypatch.setattr(module, "_probe_source_video", AsyncMock(return_value=2.0))

    async def spawn(*args, **_):
        calls.append(args)
        with Image.open(Path(args[-1]).parent / "scene2.png") as closing:
            assert closing.mode == "RGB"
        return FakeProcess(Path(args[-1]), b"mp4-data")

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    await module.render_video_preview(
        business_name="Ana",
        statement="Fato válido.",
        brand_color="#e65024",
        source_image=None,
        source_video=b"video-data",
    )
    filters = calls[0][calls[0].index("-filter_complex") + 1]
    assert "[prepared]split=2" not in filters and "[clip2]" not in filters


@pytest.mark.parametrize(
    ("emphasis", "opening", "fact", "source_duration", "second_cut"),
    [("photo", 3, 3, 6.0, True), ("text", 1, 5, 5.0, True), ("photo", 3, 3, 5.0, False)],
)
async def test_video_adjustment_changes_scene_timing_and_second_cut(
    monkeypatch, emphasis, opening, fact, source_duration, second_cut
):
    calls = []
    monkeypatch.setattr(module, "_probe_source_video", AsyncMock(return_value=source_duration))

    async def spawn(*args, **_):
        calls.append(args)
        return FakeProcess(Path(args[-1]), b"mp4-data")

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    await module.render_video_preview(
        business_name="Ana",
        statement="Fato válido.",
        brand_color="#e65024",
        source_image=None,
        source_video=b"video-data",
        emphasis=emphasis,
    )
    filters = calls[0][calls[0].index("-filter_complex") + 1]
    assert f"trim=duration={opening}" in filters
    assert f"fade=t=out:st={fact - 0.2}:d=0.2" in filters
    assert ("[prepared]split=2" in filters) is second_cut


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
    process.communicate = AsyncMock(
        return_value=(b'{"streams":[{"width":640,"height":480}],"format":{"duration":"5.50"}}', b"")
    )
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    assert await module._probe_source_video(tmp_path / "source.mp4") == 5.5


@pytest.mark.parametrize(
    "payload,returncode",
    [
        (b"not-json", 0),
        (b'{"streams":[]}', 0),
        (b'{"streams":[{}]}', 0),
        (b'{"streams":[{"width":640,"height":480}]}', 0),
        (b'{"streams":[{"width":640,"height":480}],"format":{"duration":"5"}}', 1),
        (b'{"streams":[{"width":"640","height":480}],"format":{"duration":"5"}}', 0),
        (b'{"streams":[{"width":640,"height":"480"}],"format":{"duration":"5"}}', 0),
        (b'{"streams":[{"width":0,"height":480}],"format":{"duration":"5"}}', 0),
        (b'{"streams":[{"width":640,"height":0}],"format":{"duration":"5"}}', 0),
        (b'{"streams":[{"width":640,"height":480}],"format":{"duration":"0.1"}}', 0),
        (b'{"streams":[{"width":640,"height":480}],"format":{"duration":"nan"}}', 0),
        (json.dumps({"streams": [{"width": 5000, "height": 5000}], "format": {"duration": "5"}}).encode(), 0),
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
