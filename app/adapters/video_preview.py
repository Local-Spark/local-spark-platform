"""Bounded FFmpeg recipe for a silent, captioned photo-motion reel preview."""

import asyncio
import hashlib
import io
import json
import math
import re
import tempfile
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFilter, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia
from app.adapters.static_preview import PreviewRenderError, _fit, _ink

VIDEO_TEMPLATE_VERSION = 3
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_DURATIONS = (2, 4, 2)
VIDEO_DURATIONS_BY_EMPHASIS = {
    "balanced": VIDEO_DURATIONS,
    "photo": (3, 3, 2),
    "text": (1, 5, 2),
}
VIDEO_DURATION_MS = sum(VIDEO_DURATIONS) * 1000
MAX_VIDEO_BYTES = 20 * 1024 * 1024
MAX_SOURCE_PIXELS = 3840 * 2160


def _caption(draw: ImageDraw.ImageDraw, text: str, *, top: int, color: str, max_height: int = 360) -> None:
    lines, font, leading = _fit(draw, text, 900, max_height, 72)
    for index, line in enumerate(lines):
        draw.text((90, top + index * leading), line, font=font, fill=color)


def _write_frames(
    folder: Path,
    *,
    business_name: str,
    statement: str,
    brand_color: str,
    photo: bytes | None,
    video_overlay: bool = False,
    closing_overlay: bool = False,
    intro_text: str = "Conheça nosso trabalho",
    cta_text: str = "Entre em contato para saber mais",
) -> None:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", brand_color):
        raise PreviewRenderError("PREVIEW_BRAND_INVALID")
    title = business_name.strip()
    if not title:
        raise PreviewRenderError("PREVIEW_TEXT_OVERFLOW")
    base = Image.new(
        "RGBA" if video_overlay else "RGB",
        (VIDEO_WIDTH, VIDEO_HEIGHT),
        (0, 0, 0, 0) if video_overlay else "#f5f4f9",
    )
    if photo is not None:
        if len(photo) > 5 * 1024 * 1024:
            raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
        try:
            with Image.open(io.BytesIO(photo)) as raw:
                if raw.width * raw.height > 24_000_000:
                    raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
                original = ImageOps.exif_transpose(raw).convert("RGB")
                backdrop = ImageOps.fit(original, (VIDEO_WIDTH, 1400)).filter(ImageFilter.GaussianBlur(28))
                fitted = ImageOps.contain(original, (VIDEO_WIDTH, 1400), Image.Resampling.LANCZOS)
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise PreviewRenderError("PREVIEW_SOURCE_INVALID") from exc
        base.paste(backdrop, (0, 160))
        base.paste(fitted, ((VIDEO_WIDTH - fitted.width) // 2, 160 + (1400 - fitted.height) // 2))
    draw = ImageDraw.Draw(base)
    draw.rectangle((0, 0, VIDEO_WIDTH, 160), fill=brand_color)
    _caption(draw, title, top=38, color=_ink(brand_color), max_height=100)
    draw.rectangle((0, 1560, VIDEO_WIDTH, VIDEO_HEIGHT), fill="#172036")
    _caption(draw, intro_text, top=1650, color="#ffffff")
    base.save(folder / "scene0.png")

    fact = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), brand_color)
    draw = ImageDraw.Draw(fact)
    _caption(draw, title, top=200, color=_ink(brand_color), max_height=180)
    draw.rounded_rectangle((52, 560, 1028, 1480), radius=44, fill="#ffffff")
    _caption(draw, statement, top=765, color="#172036", max_height=520)
    fact.save(folder / "scene1.png")

    closing = Image.new(
        "RGBA" if closing_overlay else "RGB",
        (VIDEO_WIDTH, VIDEO_HEIGHT),
        (0, 0, 0, 0) if closing_overlay else "#172036",
    )
    draw = ImageDraw.Draw(closing)
    if closing_overlay:
        draw.rectangle((0, 0, VIDEO_WIDTH, 160), fill=brand_color)
        _caption(draw, title, top=38, color=_ink(brand_color), max_height=100)
        draw.rectangle((0, 1460, VIDEO_WIDTH, VIDEO_HEIGHT), fill="#172036")
        _caption(draw, cta_text, top=1560, color="#ffffff", max_height=300)
    else:
        draw.rounded_rectangle((52, 530, 1028, 1450), radius=44, fill=brand_color)
        _caption(draw, cta_text, top=795, color=_ink(brand_color), max_height=520)
        _caption(draw, title, top=1640, color="#ffffff", max_height=170)
    closing.save(folder / "scene2.png")


async def _probe_source_video(path: Path) -> float:
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise PreviewRenderError("VIDEO_RENDER_UNAVAILABLE") from exc
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)
    except TimeoutError as exc:
        process.kill()
        await process.communicate()
        raise PreviewRenderError("VIDEO_RENDER_TIMEOUT", retryable=True) from exc
    try:
        probe = json.loads(stdout)
        streams = probe.get("streams", [])
        first = streams[0]
        width, height = first["width"], first["height"]
        duration = float(probe["format"]["duration"])
    except (ValueError, UnicodeDecodeError, AttributeError, IndexError, KeyError, TypeError) as exc:
        raise PreviewRenderError("PREVIEW_SOURCE_VIDEO_INVALID") from exc
    if (
        process.returncode != 0
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width < 1
        or height < 1
        or width * height > MAX_SOURCE_PIXELS
        or not math.isfinite(duration)
        or duration < 0.5
    ):
        raise PreviewRenderError("PREVIEW_SOURCE_VIDEO_INVALID")
    return duration


async def render_video_preview(
    *,
    business_name: str,
    statement: str,
    brand_color: str,
    source_image: bytes | None,
    source_video: bytes | None = None,
    intro_text: str = "Conheça nosso trabalho",
    cta_text: str = "Entre em contato para saber mais",
    emphasis: Literal["balanced", "photo", "text"] = "balanced",
) -> FetchedMedia:
    """Burn approved scene text into a bounded eight-second, muted H.264 MP4."""
    if source_image is not None and source_video is not None:
        raise PreviewRenderError("PREVIEW_MATERIAL_INVALID")
    if source_video is not None and (not source_video or len(source_video) > 50 * 1024 * 1024):
        raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
    durations = VIDEO_DURATIONS_BY_EMPHASIS[emphasis]
    with tempfile.TemporaryDirectory(prefix="video-preview-") as temporary:
        folder = Path(temporary)
        second_cut: float | None = None
        source_path = folder / "source.mp4"
        if source_video is not None:
            await asyncio.to_thread(source_path.write_bytes, source_video)
            duration = await _probe_source_video(source_path)
            if duration >= durations[0] + durations[2] + 0.5:
                second_cut = min(duration - durations[2], 8.0)
        await asyncio.to_thread(
            _write_frames,
            folder,
            business_name=business_name,
            statement=statement,
            brand_color=brand_color,
            photo=source_image,
            video_overlay=source_video is not None,
            closing_overlay=second_cut is not None,
            intro_text=intro_text,
            cta_text=cta_text,
        )
        args = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-max_alloc", "268435456"]
        if source_video is not None:
            args.extend(
                [
                    "-protocol_whitelist",
                    "file,pipe",
                    "-stream_loop",
                    "-1",
                    "-t",
                    f"{(second_cut + durations[2]) if second_cut is not None else durations[0]:.2f}",
                    "-i",
                    str(source_path),
                ]
            )
        for index, seconds in enumerate(durations):
            args.extend(
                [
                    "-protocol_whitelist",
                    "file,pipe",
                    "-loop",
                    "1",
                    "-framerate",
                    "24",
                    "-t",
                    str(seconds),
                    "-i",
                    str(folder / f"scene{index}.png"),
                ]
            )
        filters = []
        if source_video is not None:
            prepared = "[0:v]fps=24,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
            if second_cut is None:
                filters.append(f"{prepared},trim=duration={durations[0]},setpts=PTS-STARTPTS[clip0]")
            else:
                filters.extend(
                    [
                        f"{prepared},split=2[raw0][raw2]",
                        f"[raw0]trim=duration={durations[0]},setpts=PTS-STARTPTS[clip0]",
                        f"[raw2]trim=start={second_cut:.2f}:duration={durations[2]},setpts=PTS-STARTPTS[clip2]",
                    ]
                )
        for index, seconds in enumerate(durations):
            if source_video is not None and (index == 0 or (index == 2 and second_cut is not None)):
                filters.append(
                    f"[clip{index}][{index + 1}:v]overlay=0:0:shortest=1,format=yuv420p,"
                    f"fade=t=in:st=0:d=0.2,fade=t=out:st={seconds - 0.2}:d=0.2,setpts=PTS-STARTPTS[v{index}]"
                )
            else:
                input_index = index + (1 if source_video is not None else 0)
                filters.append(
                    f"[{input_index}:v]format=yuv420p,fade=t=in:st=0:d=0.2,"
                    f"fade=t=out:st={seconds - 0.2}:d=0.2,setpts=PTS-STARTPTS[v{index}]"
                )
        filters.append("[v0][v1][v2]concat=n=3:v=1:a=0[v]")
        output = folder / "preview.mp4"
        args.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[v]",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-threads",
                "2",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-y",
                str(output),
            ]
        )
        try:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError as exc:
            raise PreviewRenderError("VIDEO_RENDER_UNAVAILABLE") from exc
        try:
            await asyncio.wait_for(process.communicate(), timeout=90)
        except TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise PreviewRenderError("VIDEO_RENDER_TIMEOUT", retryable=True) from exc
        if process.returncode != 0 or not output.is_file():
            raise PreviewRenderError("VIDEO_RENDER_FAILED")
        size = output.stat().st_size
        if size == 0 or size > MAX_VIDEO_BYTES:
            raise PreviewRenderError("VIDEO_RENDER_SIZE_INVALID")
        data = await asyncio.to_thread(output.read_bytes)
        return FetchedMedia(data=data, mime_type="video/mp4", sha256=hashlib.sha256(data).hexdigest())
