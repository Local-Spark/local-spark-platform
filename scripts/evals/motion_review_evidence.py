"""Extract auditable visual evidence from a local, trusted evaluation render.

The result describes sampled frames and technical measurements, not creative quality.
No process in this module performs a network call or runs a model.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image


class EvidenceError(ValueError):
    """A render or its evidence did not satisfy the laboratory contract."""


LIMITATIONS = [
    "Frames only, no perceptual audio; measurements do not assess audio quality or synchronization.",
    "Sampled frames do not establish the quality of motion between samples or creative correctness.",
    "Frame timestamps are requested seek times, not measured presentation timestamps.",
]
MAX_FRAMES = 130
MAX_DURATION_MS = 60_000
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/private/tmp"}


def _hash(file: Path) -> str:
    result = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _run(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(args, env=_ENV, capture_output=True, timeout=timeout, check=True)
    except (OSError, subprocess.SubprocessError):
        # ffmpeg output may contain paths or other private metadata; never propagate it.
        raise EvidenceError("local_media_tool_failed") from None


def _tool(tools: dict[str, str], name: str) -> str:
    value = tools.get(name)
    if not isinstance(value, str) or not Path(value).is_absolute() or not os.access(value, os.X_OK):
        raise EvidenceError("invalid_media_tool")
    return value


def _write_new(file: Path, data: bytes) -> None:
    with os.fdopen(os.open(file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _fps(value: Any) -> float:
    try:
        result = float(Fraction(value))
    except (ValueError, ZeroDivisionError, TypeError, OverflowError):
        raise EvidenceError("invalid_video_fps") from None
    if not math.isfinite(result) or not 1 <= result <= 120:
        raise EvidenceError("invalid_video_fps")
    return result


def _last_frame(duration_ms: int, fps: float) -> int:
    # Millisecond-rounded durations can be slightly above the true CFR end.
    # Rounding the nominal count prevents inventing an extra frame at EOF.
    count = max(1, round(duration_ms * fps / 1000))
    return int((count - 1) * 1000 / fps)


def _volume(value: bytes, name: bytes) -> float | None:
    match = re.search(rb"\b" + name + rb":\s*(-?(?:\d+(?:\.\d+)?|inf))\s*dB", value)
    if not match:
        return None
    number = float(match.group(1))
    return number if math.isfinite(number) else None


def _image(data: bytes, width: int, height: int) -> None:
    if len(data) > 20 * 1024 * 1024:
        raise EvidenceError("invalid_frame")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG" or image.width > 720 or image.width < 1 or image.height < 1:
                raise EvidenceError("invalid_frame")
            # Account for integer scaling rounding.
            if abs(image.height / image.width - height / width) > 0.03:
                raise EvidenceError("invalid_frame")
            image.verify()
    except (OSError, ValueError, Image.DecompressionBombError):
        raise EvidenceError("invalid_frame") from None


def extract_evidence(
    video: Path,
    expected_sha256: str,
    tools: dict[str, str],
    output: Path,
    *,
    extra_times_ms: list[int] | None = None,
) -> dict[str, Any]:
    """Decode a render, sample frames, and persist an immutable evidence manifest."""
    video = Path(video).resolve(strict=True)
    output = Path(output)
    if not _SHA.fullmatch(expected_sha256) or not video.is_file() or _hash(video) != expected_sha256:
        raise EvidenceError("video_hash_mismatch")
    ffmpeg, ffprobe = _tool(tools, "ffmpeg"), _tool(tools, "ffprobe")
    try:
        raw = _run(
            [
                ffprobe,
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_entries",
                "stream=codec_type,width,height,avg_frame_rate,duration:format=duration",
                "-of",
                "json",
                str(video),
            ]
        ).stdout
        probe = json.loads(raw)
        streams = probe["streams"]
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        if len(video_streams) != 1:
            raise EvidenceError("invalid_video_streams")
        stream = video_streams[0]
        width, height = int(stream["width"]), int(stream["height"])
        duration = float(stream.get("duration") or probe["format"]["duration"])
        fps = _fps(stream["avg_frame_rate"])
        if not (1 <= width <= 8192 and 1 <= height <= 8192 and math.isfinite(duration)):
            raise EvidenceError("invalid_video_metadata")
        duration_ms = round(duration * 1000)
        if not 1 <= duration_ms <= MAX_DURATION_MS:
            raise EvidenceError("invalid_video_duration")
        audio = any(item.get("codec_type") == "audio" for item in streams)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        if isinstance(error, EvidenceError):
            raise
        raise EvidenceError("invalid_video_metadata") from None

    if extra_times_ms is None:
        extra_times_ms = []
    if (
        not isinstance(extra_times_ms, list)
        or len(extra_times_ms) > MAX_FRAMES
        or any(type(item) is not int or item < 0 or item >= duration_ms for item in extra_times_ms)
    ):
        raise EvidenceError("invalid_extra_times")
    # Last frame is the final nominal frame start, not the end-of-stream timestamp.
    final_ms = _last_frame(duration_ms, fps)
    if any(item > final_ms for item in extra_times_ms):
        raise EvidenceError("invalid_extra_times")
    times = sorted(set(range(0, final_ms + 1, 500)) | {final_ms} | set(extra_times_ms))
    if len(times) > MAX_FRAMES:
        raise EvidenceError("too_many_frames")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not output.is_dir() or any(output.iterdir()):
        raise EvidenceError("output_must_be_empty")

    _run(
        [
            ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-err_detect",
            "explode",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-f",
            "null",
            "-",
        ],
        timeout=300,
    )
    mean = peak = None
    if audio:
        measurement = _run(
            [
                ffmpeg,
                "-nostdin",
                "-v",
                "info",
                "-protocol_whitelist",
                "file,pipe",
                "-i",
                str(video),
                "-map",
                "0:a:0",
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ],
            timeout=300,
        )
        mean, peak = _volume(measurement.stderr, b"mean_volume"), _volume(measurement.stderr, b"max_volume")
    frames = []
    for index, timestamp in enumerate(times):
        data = _run(
            [
                ffmpeg,
                "-nostdin",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-ss",
                f"{timestamp / 1000:.3f}",
                "-i",
                str(video),
                "-map",
                "0:v:0",
                "-frames:v",
                "1",
                "-vf",
                "scale='min(720,iw)':-1",
                "-c:v",
                "png",
                "-f",
                "image2pipe",
                "pipe:1",
            ]
        ).stdout
        _image(data, width, height)
        frame_id = f"f{index:04d}"
        filename = f"{frame_id}.png"
        _write_new(output / filename, data)
        frames.append(
            {
                "frame_id": frame_id,
                "timestamp_ms": timestamp,
                "path": filename,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    if _hash(video) != expected_sha256:
        raise EvidenceError("video_changed_during_extraction")
    manifest: dict[str, Any] = {
        "version": 1,
        "video_sha256": expected_sha256,
        "duration_ms": duration_ms,
        "width": width,
        "height": height,
        "fps": fps,
        "frames": frames,
        "technical": {"audio_present": audio, "decode_ok": True, "audio_mean_db": mean, "audio_peak_db": peak},
        "limitations": LIMITATIONS.copy(),
    }
    verify_evidence(manifest, output)
    _write_new(output / "evidence.json", (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
    return manifest


def verify_evidence(manifest: dict[str, Any], root: Path) -> None:
    """Reject altered or malformed frame evidence; callers must pin the manifest separately."""
    try:
        if (
            set(manifest)
            != {
                "version",
                "video_sha256",
                "duration_ms",
                "width",
                "height",
                "fps",
                "frames",
                "technical",
                "limitations",
            }
            or manifest["version"] != 1
        ):
            raise EvidenceError("invalid_evidence")
        if not isinstance(manifest["video_sha256"], str) or not _SHA.fullmatch(manifest["video_sha256"]):
            raise EvidenceError("invalid_evidence")
        duration, width, height, fps = (manifest[k] for k in ("duration_ms", "width", "height", "fps"))
        if (
            type(duration) is not int
            or not 1 <= duration <= MAX_DURATION_MS
            or type(width) is not int
            or type(height) is not int
            or not 1 <= width <= 8192
            or not 1 <= height <= 8192
            or type(fps) not in (int, float)
            or not math.isfinite(fps)
            or not 1 <= fps <= 120
        ):
            raise EvidenceError("invalid_evidence")
        technical = manifest["technical"]
        if (
            set(technical) != {"audio_present", "decode_ok", "audio_mean_db", "audio_peak_db"}
            or type(technical["audio_present"]) is not bool
            or technical["decode_ok"] is not True
        ):
            raise EvidenceError("invalid_evidence")
        for field in ("audio_mean_db", "audio_peak_db"):
            number = technical[field]
            if number is not None and (type(number) not in (int, float) or not math.isfinite(number)):
                raise EvidenceError("invalid_evidence")
            if not technical["audio_present"] and number is not None:
                raise EvidenceError("invalid_evidence")
        if manifest["limitations"] != LIMITATIONS:
            raise EvidenceError("invalid_evidence")
        frames = manifest["frames"]
        if not isinstance(frames, list) or not 1 <= len(frames) <= MAX_FRAMES:
            raise EvidenceError("invalid_evidence")
        previous = -1
        for index, frame in enumerate(frames):
            if set(frame) != {"frame_id", "timestamp_ms", "path", "sha256"}:
                raise EvidenceError("invalid_evidence")
            expected_id = f"f{index:04d}"
            timestamp = frame["timestamp_ms"]
            if (
                frame["frame_id"] != expected_id
                or frame["path"] != f"{expected_id}.png"
                or type(timestamp) is not int
                or not previous < timestamp < duration
                or not isinstance(frame["sha256"], str)
                or not _SHA.fullmatch(frame["sha256"])
            ):
                raise EvidenceError("invalid_evidence")
            file = Path(root) / frame["path"]
            if file.is_symlink() or not file.is_file():
                raise EvidenceError("invalid_evidence")
            data = file.read_bytes()
            if hashlib.sha256(data).hexdigest() != frame["sha256"]:
                raise EvidenceError("evidence_hash_mismatch")
            _image(data, width, height)
            previous = timestamp
        timestamps = {frame["timestamp_ms"] for frame in frames}
        last = _last_frame(duration, fps)
        required = set(range(0, last + 1, 500)) | {last}
        if not required.issubset(timestamps):
            raise EvidenceError("invalid_evidence")
    except (KeyError, TypeError, OSError):
        raise EvidenceError("invalid_evidence") from None
