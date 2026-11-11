"""Pinned local renderer bridge for the historical synthetic declarative evaluation."""

from __future__ import annotations

import json
import math
import os
import re
import signal
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from scripts.evals import motion_eval as base
from scripts.evals import motion_review_eval as review

CODE = {
    "renderer/prepare.py": "543f557248ae4a2e18a592cea97cb789b10b24ed7a2582bd78923ba4cb864c9c",
    "renderer/render.cjs": "06702f3393efba3c7757c990f31118aacacbb22c0f9d3a086929a4e52d9bcba7",
    "current/compiler.cjs": "c971a7d80e1c7cd453f88fd33c94f64d70467ee57b78a3a4deb63339dd302316",
    "current/runtime.cjs": "3f25934534d950bfb5c30889a53f93d60e78b582bccb72d1b2c1cc977bcec0cd",
}
HISTORICAL_TOOLS = {
    "chromium": "/Users/israelsilva/Library/Caches/ms-playwright/chromium_headless_shell-1248/"
    "chrome-headless-shell-mac-arm64/chrome-headless-shell",
    "ffmpeg": "/private/tmp/local-spark-hyperframes-tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v9.0",
    "ffprobe": "/private/tmp/local-spark-ffprobe/node_modules/@w6s/ffprobe-static/bin/darwin/arm64/ffprobe",
}
PLAYWRIGHT = Path("/Users/israelsilva/PycharmProjects/local-spark-web/node_modules/playwright-core")


def checked_bytes(path: Path, expected: str, error: str) -> bytes:
    try:
        data = path.read_bytes()
    except OSError:
        raise base.EvalError(error) from None
    if base.digest(data) != expected:
        raise base.EvalError(error)
    return data


def verify_code(source: Path) -> None:
    for name, expected in CODE.items():
        checked_bytes(source / "code" / name, expected, "historical_renderer_changed")
    for name in ("compiler", "runtime"):
        current = base.ROOT / f"app/assets/motion_renderer/{name}.cjs"
        checked_bytes(current, CODE[f"current/{name}.cjs"], "current_renderer_differs_from_baseline")


def prepare_payload(source: Path, trusted: dict[str, Any]) -> dict[str, Any]:
    verify_code(source)
    path = source / "code/renderer/prepare.py"
    # Compile the exact verified bytes; neither a later read nor a bytecode cache is executed.
    code = checked_bytes(path, CODE["renderer/prepare.py"], "historical_renderer_changed")
    module = ModuleType("pinned_declarative_prepare")
    module.__file__ = str(path)
    exec(compile(code, str(path), "exec"), module.__dict__)
    result = module.prepare(trusted)
    if not isinstance(result, dict):
        raise base.EvalError("historical_prepare_invalid")
    return cast(dict[str, Any], result)


def verify_tools(tools: dict[str, str]) -> dict[str, dict[str, str]]:
    """Identify the actual dependencies used by the unmodified historical driver."""
    identities: dict[str, dict[str, str]] = {}
    for name in ("node", "ffmpeg", "ffprobe", "chromium"):
        path = Path(tools.get(name, "")).resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise base.EvalError("declarative_tool_missing")
        if name in HISTORICAL_TOOLS and path != Path(HISTORICAL_TOOLS[name]).resolve():
            raise base.EvalError("historical_tool_path_mismatch")
        identities[name] = {"path": str(path), "sha256": base.digest(path.read_bytes())}
    package = PLAYWRIGHT.resolve()
    if not (package / "package.json").is_file() or not (package / "index.js").is_file():
        raise base.EvalError("historical_playwright_missing")
    manifest = []
    for entry in sorted(package.rglob("*")):
        if not entry.resolve().is_relative_to(package):
            raise base.EvalError("historical_playwright_external_dependency")
        if entry.is_file():
            manifest.append({"path": entry.relative_to(package).as_posix(), "sha256": base.digest(entry.read_bytes())})
    identities["playwright"] = {"path": str(package), "sha256": base.digest(base.json_bytes(manifest))}
    return identities


def command(args: list[str], *, timeout: int = 120, diagnostic: Path | None = None) -> bytes:
    stdout, stderr = b"", b""
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/private/tmp"},
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
            raise
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, args)
    except (OSError, subprocess.SubprocessError):
        if diagnostic is not None:
            base.immutable(diagnostic, stdout[-16000:] + b"\n" + stderr[-16000:])
        raise base.EvalError("declarative_local_tool_failed") from None
    return stdout


def audio_signature(video: Path, tools: dict[str, str]) -> dict[str, Any]:
    raw = command(
        [
            tools["ffprobe"],
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-select_streams",
            "a:0",
            "-show_streams",
            "-show_packets",
            "-show_data_hash",
            "sha256",
            "-of",
            "json",
            str(video),
        ]
    )
    try:
        metadata = json.loads(raw)
    except (ValueError, UnicodeError):
        raise base.EvalError("audio_metadata_invalid") from None
    if not isinstance(metadata, dict):
        raise base.EvalError("audio_metadata_invalid")
    streams = metadata.get("streams", [])
    packets = metadata.get("packets", [])
    if (
        not isinstance(streams, list)
        or len(streams) != 1
        or not isinstance(streams[0], dict)
        or streams[0].get("codec_name") != "aac"
        or not isinstance(packets, list)
        or not packets
    ):
        raise base.EvalError("baseline_aac_required")
    stream = streams[0]
    keys = (
        "codec_name",
        "sample_rate",
        "channels",
        "channel_layout",
        "time_base",
        "start_pts",
        "duration_ts",
        "extradata_hash",
    )
    if (
        not re.fullmatch(r"[1-9][0-9]*", str(stream.get("sample_rate", "")))
        or not re.fullmatch(r"[1-9][0-9]*/[1-9][0-9]*", str(stream.get("time_base", "")))
        or any(type(stream.get(key)) is not int for key in ("channels", "start_pts", "duration_ts"))
        or stream["channels"] <= 0
        or stream["duration_ts"] <= 0
    ):
        raise base.EvalError("audio_stream_evidence_missing")
    packet_keys = ("pts", "dts", "duration", "size", "flags", "data_hash", "side_data_list")
    normalized_packets = []
    for packet in packets:
        if not isinstance(packet, dict):
            raise base.EvalError("audio_packet_evidence_missing")
        size = packet.get("size")
        # FFprobe 4.4 emits decimal strings here; do not coerce timestamps or permissive numeric forms.
        if isinstance(size, str) and re.fullmatch(r"[1-9][0-9]*", size):
            size = int(size)
        if (
            any(type(packet.get(key)) is not int for key in ("pts", "dts", "duration"))
            or type(size) is not int
            or packet["duration"] <= 0
            or size <= 0
            or not isinstance(packet.get("flags"), str)
            or not re.fullmatch(r"SHA256:[0-9a-fA-F]{64}", str(packet.get("data_hash", "")))
            or not isinstance(packet.get("side_data_list", []), list)
            or any(not isinstance(side, dict) for side in packet.get("side_data_list", []))
        ):
            raise base.EvalError("audio_packet_evidence_missing")
        normalized_packets.append({**{key: packet.get(key) for key in packet_keys}, "size": size})
    pcm = command(
        [
            tools["ffmpeg"],
            "-nostdin",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(video),
            "-map",
            "0:a:0",
            "-c:a",
            "pcm_s16le",
            "-f",
            "s16le",
            "pipe:1",
        ]
    )
    if not pcm:
        raise base.EvalError("decoded_audio_missing")
    return {
        "stream": {key: stream.get(key) for key in keys},
        "packets": normalized_packets,
        "pcm_sha256": base.digest(pcm),
        "pcm_bytes": len(pcm),
    }


def video_signature(video: Path, tools: dict[str, str]) -> dict[str, Any]:
    """Compare every decoded frame and presentation time without claiming visual quality."""
    raw = command(
        [
            tools["ffprobe"],
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-select_streams",
            "v:0",
            "-show_streams",
            "-show_frames",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt,avg_frame_rate,r_frame_rate,time_base,start_pts,duration_ts,nb_frames:"
            "frame=pts,pkt_pts,best_effort_timestamp,duration,pkt_duration",
            "-of",
            "json",
            str(video),
        ]
    )
    try:
        metadata = json.loads(raw)
    except (ValueError, UnicodeError):
        raise base.EvalError("video_metadata_invalid") from None
    if not isinstance(metadata, dict):
        raise base.EvalError("video_metadata_invalid")
    streams, frames = metadata.get("streams"), metadata.get("frames")
    if (
        not isinstance(streams, list)
        or len(streams) != 1
        or not isinstance(streams[0], dict)
        or not isinstance(frames, list)
        or not frames
    ):
        raise base.EvalError("video_evidence_missing")
    stream = streams[0]
    keys = (
        "codec_name",
        "width",
        "height",
        "pix_fmt",
        "avg_frame_rate",
        "r_frame_rate",
        "time_base",
        "start_pts",
        "duration_ts",
        "nb_frames",
    )
    if (
        any(key not in stream for key in keys)
        or any(type(stream[key]) is not int for key in ("width", "height", "start_pts", "duration_ts"))
        or any(stream[key] <= 0 for key in ("width", "height", "duration_ts"))
        or str(stream["nb_frames"]) != str(len(frames))
        or any(
            not re.fullmatch(r"[1-9][0-9]*/[1-9][0-9]*", str(stream[key]))
            for key in ("avg_frame_rate", "r_frame_rate", "time_base")
        )
    ):
        raise base.EvalError("video_evidence_missing")
    timing = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise base.EvalError("video_frame_evidence_missing")
        duration = frame.get("duration", frame.get("pkt_duration"))
        pts = frame.get("pts", frame.get("pkt_pts"))
        if (
            type(pts) is not int
            or any(key in frame and type(frame[key]) is not int for key in ("pts", "pkt_pts"))
            or ("pts" in frame and "pkt_pts" in frame and frame["pts"] != frame["pkt_pts"])
            or type(frame.get("best_effort_timestamp")) is not int
            or type(duration) is not int
            or duration <= 0
        ):
            raise base.EvalError("video_frame_evidence_missing")
        timing.append({"pts": pts, "best_effort_timestamp": frame["best_effort_timestamp"], "duration": duration})
    decoded = command(
        [
            tools["ffmpeg"],
            "-nostdin",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-an",
            "-pix_fmt",
            "rgb24",
            "-fps_mode",
            "passthrough",
            "-f",
            "hash",
            "-hash",
            "sha256",
            "pipe:1",
        ]
    )
    if not re.fullmatch(rb"SHA256=[0-9a-fA-F]{64}\s*", decoded):
        raise base.EvalError("decoded_video_hash_missing")
    return {
        "stream": {key: stream[key] for key in keys},
        "frames": timing,
        "rgb24_sha256": decoded.decode("ascii").strip().split("=", 1)[1].lower(),
    }


def freeze_audio(baseline: Path, visual: Path, destination: Path, tools: dict[str, str]) -> dict[str, Any]:
    if destination.exists():
        raise base.EvalError("audio_destination_exists")
    baseline_sha = base.digest(baseline.read_bytes())
    visual_sha = base.digest(visual.read_bytes())
    before = audio_signature(baseline, tools)
    command(
        [
            tools["ffmpeg"],
            "-nostdin",
            "-v",
            "error",
            "-n",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(visual),
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(baseline),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c",
            "copy",
            "-map_metadata",
            "-1",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )
    after = audio_signature(destination, tools)
    if baseline_sha != base.digest(baseline.read_bytes()) or visual_sha != base.digest(visual.read_bytes()):
        raise base.EvalError("audio_freeze_input_changed")
    if before != after:
        raise base.EvalError("frozen_audio_mismatch")
    return {
        "baseline_sha256": baseline_sha,
        "visual_sha256": visual_sha,
        "output_sha256": base.digest(destination.read_bytes()),
        "aac_packets_and_timing_equal": True,
        "pcm_equal": True,
        "signature_sha256": base.digest(base.json_bytes(before)),
        "perceptual_listening": "not_performed",
    }


def render(run: Path, target: Path, prepared: dict[str, Any], tools: dict[str, str]) -> None:
    source = run / "source"
    verify_code(source)
    tool_identities = verify_tools(tools)
    scenes = prepared.get("scenes", [])
    profile = prepared.get("profile")
    if (
        not isinstance(scenes, (list, tuple))
        or len(scenes) != 1
        or not isinstance(scenes[0], dict)
        or type(scenes[0].get("duration_ms")) is not int
        or scenes[0]["duration_ms"] <= 0
        or not isinstance(profile, dict)
        or profile.get("fps") != 30
    ):
        raise base.EvalError("historical_single_reel_required")
    config = target / "prepared.json"
    base.immutable(config, base.json_bytes(prepared))
    output = target / "render"
    output.mkdir(mode=0o700)
    command(
        [tools["node"], str(source / "code/renderer/render.cjs"), str(config), str(output)],
        timeout=960,
        diagnostic=target / "renderer-error.log",
    )
    verify_code(source)
    if verify_tools(tools) != tool_identities:
        raise base.EvalError("declarative_tools_changed_during_render")
    try:
        trace = review.read_json(output / "trace.json")
    except (OSError, ValueError, UnicodeError):
        raise base.EvalError("declarative_render_mismatch") from None
    if not isinstance(trace, dict):
        raise base.EvalError("declarative_render_mismatch")
    video = output / "page-1.mp4"
    duration = scenes[0]["duration_ms"]
    frames = math.ceil(duration * 30 / 1000)
    pages = trace.get("pages", [])
    if (
        not isinstance(pages, list)
        or len(pages) != 1
        or not isinstance(pages[0], dict)
        or pages[0].get("output_sha256") != base.digest(video.read_bytes())
        or pages[0].get("logical_ms") != duration
        or pages[0].get("encoded_frames") != frames
        or pages[0].get("encoded_ms") != frames * 1000 / 30
        or pages[0].get("audio_mode") != "mix"
        or any(trace.get(f"{name}_sha256") != CODE[f"current/{name}.cjs"] for name in ("compiler", "runtime"))
    ):
        raise base.EvalError("declarative_render_mismatch")
    proof = freeze_audio(run / "reel1c/v0/render.mp4", video, target / "render.mp4", tools)
    base.immutable(target / "audio-preservation.json", base.json_bytes(proof))
    review.snapshot(output / "trace.json", target / "trace.json")
