"""Bounded FFmpeg recipe for a silent, captioned photo-motion reel preview."""

import asyncio
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia
from app.adapters.static_preview import PreviewRenderError, _fit, _ink

VIDEO_TEMPLATE_VERSION = 2
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_DURATIONS = (2, 4, 2)
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
                fitted = ImageOps.fit(ImageOps.exif_transpose(raw).convert("RGB"), (VIDEO_WIDTH, 1400))
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise PreviewRenderError("PREVIEW_SOURCE_INVALID") from exc
        base.paste(fitted, (0, 160))
    draw = ImageDraw.Draw(base)
    draw.rectangle((0, 0, VIDEO_WIDTH, 160), fill=brand_color)
    _caption(draw, title, top=38, color=_ink(brand_color), max_height=100)
    draw.rectangle((0, 1560, VIDEO_WIDTH, VIDEO_HEIGHT), fill="#172036")
    _caption(draw, "Conheça nosso trabalho", top=1650, color="#ffffff")
    base.save(folder / "scene0.png")

    fact = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), brand_color)
    draw = ImageDraw.Draw(fact)
    _caption(draw, title, top=200, color=_ink(brand_color), max_height=180)
    draw.rounded_rectangle((52, 560, 1028, 1480), radius=44, fill="#ffffff")
    _caption(draw, statement, top=765, color="#172036", max_height=520)
    fact.save(folder / "scene1.png")

    closing = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), "#172036")
    draw = ImageDraw.Draw(closing)
    draw.rounded_rectangle((52, 530, 1028, 1450), radius=44, fill=brand_color)
    _caption(draw, "Entre em contato para saber mais", top=795, color=_ink(brand_color), max_height=520)
    _caption(draw, title, top=1640, color="#ffffff", max_height=170)
    closing.save(folder / "scene2.png")


async def _probe_source_video(path: Path) -> None:
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
            "stream=width,height",
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
        streams = json.loads(stdout).get("streams", [])
        first = streams[0]
        width, height = first["width"], first["height"]
    except (ValueError, UnicodeDecodeError, AttributeError, IndexError, KeyError, TypeError) as exc:
        raise PreviewRenderError("PREVIEW_SOURCE_VIDEO_INVALID") from exc
    if (
        process.returncode != 0
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width < 1
        or height < 1
        or width * height > MAX_SOURCE_PIXELS
    ):
        raise PreviewRenderError("PREVIEW_SOURCE_VIDEO_INVALID")


async def render_video_preview(
    *,
    business_name: str,
    statement: str,
    brand_color: str,
    source_image: bytes | None,
    source_video: bytes | None = None,
) -> FetchedMedia:
    """Burn timed factual text into an eight-second, muted H.264 MP4."""
    if source_image is not None and source_video is not None:
        raise PreviewRenderError("PREVIEW_MATERIAL_INVALID")
    if source_video is not None and (not source_video or len(source_video) > 50 * 1024 * 1024):
        raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
    with tempfile.TemporaryDirectory(prefix="video-preview-") as temporary:
        folder = Path(temporary)
        await asyncio.to_thread(
            _write_frames,
            folder,
            business_name=business_name,
            statement=statement,
            brand_color=brand_color,
            photo=source_image,
            video_overlay=source_video is not None,
        )
        args = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-max_alloc", "268435456"]
        if source_video is not None:
            source_path = folder / "source.mp4"
            await asyncio.to_thread(source_path.write_bytes, source_video)
            await _probe_source_video(source_path)
            args.extend(
                [
                    "-protocol_whitelist",
                    "file,pipe",
                    "-stream_loop",
                    "-1",
                    "-t",
                    str(VIDEO_DURATIONS[0]),
                    "-i",
                    str(source_path),
                ]
            )
        for index, seconds in enumerate(VIDEO_DURATIONS):
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
            filters.append(
                "[0:v]fps=24,scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,setsar=1,trim=duration=2,setpts=PTS-STARTPTS[clip]"
            )
        for index, seconds in enumerate(VIDEO_DURATIONS):
            if source_video is not None and index == 0:
                filters.append(
                    "[clip][1:v]overlay=0:0:shortest=1,format=yuv420p,"
                    "fade=t=in:st=0:d=0.2,fade=t=out:st=1.8:d=0.2,setpts=PTS-STARTPTS[v0]"
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
