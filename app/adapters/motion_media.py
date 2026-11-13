"""Local, bounded inspection and optional audio extraction for motion inputs.

This adapter does not fetch media or transcribe speech. Container metadata is not
proof that every frame decodes or that a dishonest duration is accurate.
"""

import asyncio
import hashlib
import json
import math
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from app.adapters.material_media import FetchedMedia, MaterialError

MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_DURATION_SECONDS = 60
MAX_PIXELS = 3840 * 2160
MAX_PROBE_BYTES = 128 * 1024
# 60 seconds of mono 16-bit PCM at 16 kHz, plus room for a WAV header.
MAX_WAV_BYTES = 60 * 16000 * 2 + 4096
COMMAND_TIMEOUT_SECONDS = 30
CLEANUP_TIMEOUT_SECONDS = 2


@dataclass(frozen=True)
class MotionVideoInfo:
    duration_seconds: float
    width: int
    height: int
    fps: float
    rotation: int
    video_codec: str
    audio_codec: str | None


async def _command(*args: str, output_limit: int) -> bytes:
    try:
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
    except OSError as exc:
        raise MaterialError("MOTION_MEDIA_TOOL_UNAVAILABLE", retryable=True) from exc

    async def read_and_wait() -> bytes:
        assert process.stdout is not None
        output = bytearray()
        while True:
            chunk = await process.stdout.read(min(65536, output_limit + 1 - len(output)))
            if not chunk:
                break
            output.extend(chunk)
            if len(output) > output_limit:
                raise MaterialError("MOTION_MEDIA_OUTPUT_TOO_LARGE")
        await process.wait()
        if process.returncode != 0:
            raise MaterialError("MOTION_MEDIA_INVALID")
        return bytes(output)

    async def cleanup() -> None:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        # A full stdout pipe can prevent Process.wait() from finishing even after
        # kill. Drain incrementally, without retaining data, before waiting.
        assert process.stdout is not None
        while await process.stdout.read(65536):
            pass
            await process.wait()

    try:
        return await asyncio.wait_for(read_and_wait(), timeout=COMMAND_TIMEOUT_SECONDS)
    except BaseException as exc:
        try:
            await asyncio.wait_for(cleanup(), timeout=CLEANUP_TIMEOUT_SECONDS)
        except TimeoutError:
            # A descendant could retain the pipe after the child is killed.
            # Close the transport to avoid leaving a paused pipe behind.
            process._transport.close()  # type: ignore[attr-defined]
        if isinstance(exc, TimeoutError):
            raise MaterialError("MOTION_MEDIA_TIMEOUT", retryable=True) from exc
        raise


def _positive_number(value: Any) -> float:
    if isinstance(value, bool):
        raise MaterialError("MOTION_MEDIA_INVALID")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MaterialError("MOTION_MEDIA_INVALID") from exc
    if not math.isfinite(number) or number <= 0:
        raise MaterialError("MOTION_MEDIA_INVALID")
    return number


def _parse_probe(raw: bytes) -> MotionVideoInfo:
    try:
        result = json.loads(raw)
        streams = result["streams"]
        container = result["format"]
        if not isinstance(streams, list) or not streams or not all(isinstance(s, dict) for s in streams):
            raise ValueError
        if not isinstance(container, dict):
            raise ValueError
        videos = [s for s in streams if s.get("codec_type") == "video"]
        audios = [s for s in streams if s.get("codec_type") == "audio"]
        if len(videos) != 1 or len(audios) > 1:
            raise ValueError
        video = videos[0]
        video_codec = video["codec_name"]
        audio_codec = audios[0].get("codec_name") if audios else None
        if (
            not isinstance(video_codec, str)
            or not video_codec
            or (audios and (not isinstance(audio_codec, str) or not audio_codec))
        ):
            raise ValueError
        width, height = video["width"], video["height"]
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise ValueError
        if width * height > MAX_PIXELS:
            raise MaterialError("MOTION_MEDIA_DIMENSIONS_EXCEEDED")
        duration = _positive_number(container["duration"])
        if duration > MAX_DURATION_SECONDS:
            raise MaterialError("MOTION_MEDIA_DURATION_EXCEEDED")
        frame_rate = video["avg_frame_rate"]
        if not isinstance(frame_rate, str):
            raise ValueError
        fps = _positive_number(Fraction(frame_rate))
        tags = video.get("tags", {})
        side_data = video.get("side_data_list", [])
        if not isinstance(tags, dict) or not isinstance(side_data, list):
            raise ValueError
        rotations = [s["rotation"] for s in side_data if isinstance(s, dict) and "rotation" in s]
        if not all(isinstance(s, dict) for s in side_data) or len(rotations) > 1:
            raise ValueError
        rotation = float(rotations[0] if rotations else tags.get("rotate", 0))
        if not math.isfinite(rotation) or rotation % 90 != 0:
            raise ValueError
        return MotionVideoInfo(duration, width, height, fps, int(rotation) % 360, video_codec, audio_codec)
    except (TypeError, ValueError, KeyError, IndexError, ZeroDivisionError, OverflowError, UnicodeDecodeError) as exc:
        raise MaterialError("MOTION_MEDIA_INVALID") from exc


async def inspect_supplemental_audio(media: FetchedMedia) -> float:
    """Probe a bounded, previously authorized audio file before any model or render effect."""
    if (
        not media.data
        or len(media.data) > 16 * 1024 * 1024
        or media.mime_type not in {"audio/ogg", "audio/mpeg", "audio/wav"}
        or hashlib.sha256(media.data).hexdigest() != media.sha256
    ):
        raise MaterialError("MOTION_MEDIA_INVALID")
    with tempfile.TemporaryDirectory(prefix="motion-audio-") as folder:
        path = Path(folder) / "input"
        path.write_bytes(media.data)
        raw = await _command(
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name",
            "-of",
            "json",
            str(path),
            output_limit=MAX_PROBE_BYTES,
        )
    try:
        data = json.loads(raw)
        streams = data["streams"]
        if (
            not isinstance(streams, list)
            or len(streams) != 1
            or not isinstance(streams[0], dict)
            or streams[0].get("codec_type") != "audio"
            or not streams[0].get("codec_name")
        ):
            raise ValueError
        return _positive_number(data["format"]["duration"])
    except (TypeError, ValueError, KeyError, UnicodeDecodeError) as exc:
        raise MaterialError("MOTION_MEDIA_INVALID") from exc


async def inspect_and_extract_motion_audio(
    media: FetchedMedia, *, extract_audio: bool = True
) -> tuple[MotionVideoInfo, bytes | None]:
    """Inspect one supplied video and extract its first audio track, if present.

    Never truncate the source or extracted audio; over-limit output fails instead.
    A renderer can inspect without producing the transcription-oriented mono WAV.
    """
    if not media.data:
        raise MaterialError("MOTION_MEDIA_INVALID")
    if len(media.data) > MAX_INPUT_BYTES:
        raise MaterialError("MOTION_MEDIA_SIZE_EXCEEDED")
    if media.mime_type not in {"video/mp4", "video/3gpp"}:
        raise MaterialError("MOTION_MEDIA_TYPE_UNSUPPORTED")
    if hashlib.sha256(media.data).hexdigest() != media.sha256:
        raise MaterialError("MOTION_MEDIA_HASH_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="motion-media-") as folder:
        path = Path(folder) / "input"
        path.write_bytes(media.data)
        probe = await _command(
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-f",
            "mov",
            "-enable_drefs",
            "0",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
            output_limit=MAX_PROBE_BYTES,
        )
        info = _parse_probe(probe)
        if info.audio_codec is None or not extract_audio:
            return info, None
        audio = await _command(
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-protocol_whitelist",
            "file,pipe",
            "-f",
            "mov",
            "-enable_drefs",
            "0",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            "pipe:1",
            output_limit=MAX_WAV_BYTES,
        )
        if not audio:
            raise MaterialError("MOTION_MEDIA_INVALID")
        return info, audio


async def decode_analysis_pcm(media: FetchedMedia) -> bytes:
    """Decode supplied audio/video locally for measurements, never mix or render a piece."""
    formats = {"video/mp4": "mov", "audio/mpeg": "mp3", "audio/wav": "wav", "audio/ogg": "ogg"}
    if (
        media.mime_type not in formats
        or not 0 < len(media.data) <= MAX_INPUT_BYTES
        or hashlib.sha256(media.data).hexdigest() != media.sha256
    ):
        raise MaterialError("MOTION_AUDIO_ANALYSIS_INPUT_INVALID")
    with tempfile.TemporaryDirectory(prefix="motion-audio-analysis-") as folder:
        path = Path(folder) / "input"
        path.write_bytes(media.data)
        pcm = await _command(
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-protocol_whitelist",
            "file,pipe",
            "-f",
            formats[media.mime_type],
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            "-f",
            "s16le",
            "pipe:1",
            output_limit=60 * 16000 * 2,
        )
        if not pcm or len(pcm) % 2:
            raise MaterialError("MOTION_AUDIO_ANALYSIS_PCM_INVALID")
        return pcm
