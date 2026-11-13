"""Bounded HTML motion execution in a separately pinned, credential-free container.

The caller owns admission, immutable snapshots, operation identity and publication.
This adapter never calls a model, downloads an image or decides creative quality.
"""

import asyncio
import hashlib
import json
import math
import re
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import NotRequired, TypedDict
from uuid import UUID

from app.services.auth import AuthError
from app.services.motion_elements import runtime_bytes as element_runtime_bytes
from app.services.motion_movement import movement_bytes
from app.services.motion_structural_floor import MECHANISM_RUNTIME, uses_structural_runtime

MECHANISMS_SOURCE = Path(__file__).resolve().parents[1] / "assets/motion_html_renderer/mechanisms-v1.js"

MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_VIDEO_BYTES = 128 * 1024 * 1024
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
MAX_HEADER_BYTES = 262144
MAX_OUTPUT_BYTES = MAX_VIDEO_BYTES + MAX_EVIDENCE_BYTES + MAX_HEADER_BYTES
ASSET_ID = re.compile(r"assets/[A-Za-z0-9_.-]{1,80}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
IMAGE = re.compile(r"(?:[a-zA-Z0-9./:_-]+@)?sha256:[a-f0-9]{64}\Z")
SECCOMP = Path(__file__).resolve().parents[1] / "assets/motion_html_renderer/seccomp.json"
RUNNER_FAILURES = frozenset(
    {
        "MOTION_RENDER_OS_ISOLATION_FAILED",
        "MOTION_RENDER_BROWSER_SANDBOX_FAILED",
        "MOTION_RENDER_BROWSER_SANDBOX_UNPROVEN",
        "MOTION_RENDER_PROFILE_INVALID",
        "MOTION_RENDER_INPUT_LIMIT",
        "MOTION_RENDER_INPUT_CHANGED",
        "MOTION_RENDER_ASSET_INVALID",
        "MOTION_RENDER_AUDIO_INVALID",
        "MOTION_RENDER_MEDIA_FAILED",
        "MOTION_RENDER_ROUTE_PROBE_FAILED",
        "MOTION_RENDER_BROWSER_VIOLATION",
        "MOTION_RENDER_BROWSER_TIMEOUT",
        "MOTION_RENDER_SEEK_MISSING",
        "MOTION_RENDER_DEADLINE",
        "MOTION_RENDER_FRAME_LIMIT",
        "MOTION_RENDER_EVIDENCE_LIMIT",
        "MOTION_RENDER_OUTPUT_INVALID",
        "MOTION_RENDER_TIMESTAMPS_INVALID",
    }
)


class MotionRenderError(Exception):
    """Stable, content-free operational failure."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RenderAsset:
    id: str
    mime_type: str
    data: bytes = field(repr=False)
    sha256: str


@dataclass(frozen=True, slots=True)
class RenderBundle:
    html: str = field(repr=False)
    scene_init: str = field(repr=False)
    assets: tuple[RenderAsset, ...]
    audio: dict[str, object]
    width: int
    height: int
    fps: int
    duration_ms: int
    sample_times_ms: tuple[int, ...] = ()
    movement_runtime_sha256: str | None = None
    element_runtime_sha256: str | None = None
    frames_only: bool = False
    fingerprint_frames: bool = False


@dataclass(frozen=True, slots=True)
class RenderedFrame:
    ms: int
    png: bytes = field(repr=False)
    sha256: str
    frame_index: int = 0
    pts_seconds: str = ""


@dataclass(frozen=True, slots=True)
class RenderedMotion:
    mp4: bytes = field(repr=False)
    sha256: str
    evidence: tuple[RenderedFrame, ...]
    diagnostics: dict[str, object]


class RenderConfig(TypedDict):
    version: int
    width: int
    height: int
    fps: int
    duration_ms: int
    html_sha256: str
    scene_sha256: str
    assets: list[dict[str, str]]
    audio: dict[str, object]
    sample_frames: list[int]
    fingerprint_frames: NotRequired[bool]


def _integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    return value


def _audio(plan: dict[str, object], assets: dict[str, RenderAsset], duration: int) -> dict[str, object]:
    if plan.get("version") == "motion-audio-v2":
        return _audio_v2(plan, assets, duration)
    if set(plan) != {"mode", "tracks"} or not isinstance(plan["tracks"], list):
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    tracks = plan["tracks"]
    if plan["mode"] == "silent" and tracks == []:
        return {"mode": "silent", "tracks": []}
    if plan["mode"] != "mix" or not 1 <= len(tracks) <= 16:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    result = []
    for track in tracks:
        if not isinstance(track, dict) or set(track) != {
            "asset_id",
            "offset_ms",
            "trim_start_ms",
            "trim_end_ms",
            "volume",
        }:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        asset_id = track["asset_id"]
        if (
            not isinstance(asset_id, str)
            or asset_id not in assets
            or not (assets[asset_id].mime_type.startswith("audio/") or assets[asset_id].mime_type == "video/mp4")
        ):
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        offset = _integer(track["offset_ms"], 0, duration)
        start = _integer(track["trim_start_ms"], 0, 60000)
        end = _integer(track["trim_end_ms"], start + 1, 60000)
        volume = track["volume"]
        if offset + end - start > duration or type(volume) not in (int, float) or not 0 <= volume <= 1:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        if not float(volume * 1000000).is_integer():
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        result.append(
            {"asset_id": asset_id, "offset_ms": offset, "trim_start_ms": start, "trim_end_ms": end, "volume": volume}
        )
    return {"mode": "mix", "tracks": result}


def _audio_v2(plan: dict[str, object], assets: dict[str, RenderAsset], duration: int) -> dict[str, object]:
    if set(plan) != {"version", "mode", "tracks", "ducking"} or plan["mode"] != "mix":
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    tracks = plan["tracks"]
    if not isinstance(tracks, list) or not 1 <= len(tracks) <= 16:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    plain = []
    for track in tracks:
        if not isinstance(track, dict) or set(track) != {
            "asset_id",
            "offset_ms",
            "trim_start_ms",
            "trim_end_ms",
            "volume",
            "role",
            "fade_in_ms",
            "fade_out_ms",
        }:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        if not isinstance(track["role"], str) or track["role"] not in {"original", "music", "effect"}:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        fade_in = _integer(track["fade_in_ms"], 0, 60000)
        fade_out = _integer(track["fade_out_ms"], 0, 60000)
        start = _integer(track["trim_start_ms"], 0, 60000)
        end = _integer(track["trim_end_ms"], start + 1, 60000)
        if fade_in + fade_out > end - start:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        if track["role"] == "original":
            if (
                track["asset_id"] != "assets/source.mp4"
                or track["offset_ms"] != 0
                or start != 0
                or track["volume"] != 1
                or fade_in
                or fade_out
            ):
                raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        elif track["asset_id"] == "assets/source.mp4":
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        plain.append({key: track[key] for key in ("asset_id", "offset_ms", "trim_start_ms", "trim_end_ms", "volume")})
    _audio({"mode": "mix", "tracks": plain}, assets, duration)
    originals = sum(track["role"] == "original" for track in tracks)
    if originals > 1 or (originals == 1 and tracks[0]["role"] != "original"):
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    duck = plan["ducking"]
    if duck is not None:
        if (
            not isinstance(duck, dict)
            or set(duck) != {"threshold", "ratio", "attack_ms", "release_ms"}
            or originals != 1
            or not any(track["role"] == "music" for track in tracks)
        ):
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        for key, low, high in (("threshold", 0.00097563, 1), ("ratio", 1, 20)):
            value = duck[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        _integer(duck["attack_ms"], 1, 2000)
        _integer(duck["release_ms"], 5, 9000)
    return plan


def _prepare(bundle: RenderBundle, directory: Path) -> RenderConfig:
    width, height = _integer(bundle.width, 64, 1920), _integer(bundle.height, 64, 1920)
    duration = _integer(bundle.duration_ms, 1, 60000)
    if width % 2 or height % 2 or bundle.fps != 30 or len(bundle.assets) > 32:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    try:
        html, scene = bundle.html.encode(), bundle.scene_init.encode()
    except UnicodeEncodeError as exc:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT") from exc
    if not scene:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    if bundle.movement_runtime_sha256 is not None:
        try:
            runtime = movement_bytes(bundle.movement_runtime_sha256)
        except AuthError as exc:
            raise MotionRenderError("MOTION_RENDER_MOVEMENT_VERSION_UNAVAILABLE") from exc
        scene = runtime + b"\n;\n" + scene
    if "MechanismsV1.seek" in bundle.scene_init:
        scene = MECHANISMS_SOURCE.read_bytes() + b"\n;\n" + scene
    elif uses_structural_runtime(bundle.scene_init):
        scene = MECHANISM_RUNTIME.encode() + b"\n;\n" + scene
    if bundle.element_runtime_sha256 is not None:
        elements = element_runtime_bytes()
        if hashlib.sha256(elements).hexdigest() != bundle.element_runtime_sha256:
            raise MotionRenderError("MOTION_RENDER_ELEMENTS_VERSION_UNAVAILABLE")
        scene = elements + b"\n;\n" + scene
    if not 1 <= len(html) <= 2 * 1024 * 1024 or not 1 <= len(scene) <= 1024 * 1024:
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    assets: dict[str, RenderAsset] = {}
    total = len(html) + len(scene)
    entries: list[dict[str, str]] = []
    for asset in bundle.assets:
        if (
            not ASSET_ID.fullmatch(asset.id)
            or asset.id in assets
            or asset.mime_type
            not in {
                "video/mp4",
                "image/png",
                "image/jpeg",
                "font/ttf",
                "font/woff2",
                "audio/wav",
                "audio/ogg",
                "audio/mpeg",
            }
        ):
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        if (
            not asset.data
            or not SHA256.fullmatch(asset.sha256)
            or hashlib.sha256(asset.data).hexdigest() != asset.sha256
        ):
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        assets[asset.id] = asset
        total += len(asset.data)
        if total > MAX_INPUT_BYTES:
            raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
        entries.append(
            {"id": asset.id, "mime_type": asset.mime_type, "sha256": asset.sha256, "file": f"asset-{len(entries)}"}
        )
    audio = _audio(bundle.audio, assets, duration)
    if type(bundle.frames_only) is not bool or (bundle.frames_only and not bundle.sample_times_ms):
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    if type(bundle.fingerprint_frames) is not bool or (bundle.fingerprint_frames and bundle.frames_only):
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    samples = bundle.sample_times_ms
    if len(samples) > 64 or len(set(samples)) != len(samples):
        raise MotionRenderError("MOTION_RENDER_INVALID_INPUT")
    for sample in samples:
        _integer(sample, 0, duration - 1)
    frame_count = (duration * 30 + 999) // 1000
    sample_frames = (
        sorted({sample * 30 // 1000 for sample in samples})
        if samples
        else sorted({round(index * (frame_count - 1) / 19) for index in range(20)})
    )
    config: RenderConfig = {
        "version": 2 if bundle.frames_only else 1,
        "width": width,
        "height": height,
        "fps": 30,
        "duration_ms": duration,
        "html_sha256": hashlib.sha256(html).hexdigest(),
        "scene_sha256": hashlib.sha256(scene).hexdigest(),
        "assets": entries,
        "audio": audio,
        "sample_frames": sample_frames,
    }
    if bundle.fingerprint_frames:
        config["fingerprint_frames"] = True
    directory.mkdir(mode=0o755)
    for name, data in [("index.html", html), ("scene.js", scene), ("config.json", json.dumps(config).encode())]:
        target = directory / name
        target.write_bytes(data)
        target.chmod(0o444)
    for entry, asset in zip(entries, bundle.assets, strict=True):
        target = directory / entry["file"]
        target.write_bytes(asset.data)
        target.chmod(0o444)
    directory.chmod(0o555)
    return config


def _decode(data: bytes, expected: RenderConfig) -> RenderedMotion:
    line, separator, payload = data.partition(b"\n")
    if not separator or len(line) > (MAX_HEADER_BYTES if expected.get("fingerprint_frames") else 65536):
        raise MotionRenderError("MOTION_RENDER_INVALID_OUTPUT")
    try:
        header = json.loads(line)
        if (
            not isinstance(header, dict)
            or set(header) != {"version", "video", "frames", "diagnostics"}
            or header["version"] != expected["version"]
        ):
            raise ValueError
        video, frames, diagnostics = header["video"], header["frames"], header["diagnostics"]
        if not isinstance(video, dict) or set(video) != {"size", "sha256"} or not isinstance(frames, list):
            raise ValueError
        if (
            not isinstance(diagnostics, dict)
            or diagnostics.get("frame_count") != (int(expected["duration_ms"]) * 30 + 999) // 1000
        ):
            raise ValueError
        if diagnostics.get("width") != expected["width"] or diagnostics.get("height") != expected["height"]:
            raise ValueError
        if diagnostics.get("config_sha256") != hashlib.sha256(json.dumps(expected).encode()).hexdigest():
            raise ValueError
        if expected.get("fingerprint_frames"):
            hashes = diagnostics.get("frame_fingerprints")
            environment = diagnostics.get("fingerprint_environment")
            if (
                not isinstance(hashes, list)
                or len(hashes) != diagnostics["frame_count"]
                or any(not isinstance(item, str) or not SHA256.fullmatch(item) for item in hashes)
                or not isinstance(environment, str)
                or not SHA256.fullmatch(environment)
            ):
                raise ValueError
        own_filters, renderer_filters = (
            diagnostics.get("host_seccomp_filters"),
            diagnostics.get("renderer_seccomp_filters"),
        )
        if type(own_filters) is not int or type(renderer_filters) is not int or not 1 <= own_filters < renderer_filters:
            raise ValueError
        if (
            diagnostics.get("sandbox") is not True
            or diagnostics.get("seccomp") != 2
            or diagnostics.get("denied_requests") != 0
            or diagnostics.get("evidence_source")
            != ("browser_keyframes" if expected["version"] == 2 else "decoded_mp4")
        ):
            raise ValueError
        if expected["version"] == 1 and expected["audio"].get("version") == "motion-audio-v2":
            metrics = diagnostics.get("audio_measurements")
            if (
                not isinstance(metrics, dict)
                or set(metrics) != {"integrated_lufs", "sample_peak_dbfs", "peak_kind", "source"}
                or metrics["peak_kind"] != "sample"
                or metrics["source"] != "decoded_output"
                or type(metrics["integrated_lufs"]) not in (int, float)
                or not math.isfinite(metrics["integrated_lufs"])
                or (
                    metrics["sample_peak_dbfs"] is not None
                    and (
                        type(metrics["sample_peak_dbfs"]) not in (int, float)
                        or not math.isfinite(metrics["sample_peak_dbfs"])
                    )
                )
            ):
                raise ValueError
        size = video["size"]
        minimum = 0 if expected["version"] == 2 else 1
        if type(size) is not int or not minimum <= size <= MAX_VIDEO_BYTES or size > len(payload):
            raise ValueError
        mp4, remaining = payload[:size], payload[size:]
        digest = hashlib.sha256(mp4).hexdigest()
        if (
            digest != video["sha256"]
            or (bool(mp4) if expected["version"] == 2 else mp4[4:8] != b"ftyp")
            or len(frames) != len(expected["sample_frames"])
        ):
            raise ValueError
        evidence = []
        used = 0
        for frame, index in zip(frames, expected["sample_frames"], strict=True):
            if not isinstance(frame, dict) or set(frame) != {"ms", "frame_index", "pts_seconds", "size", "sha256"}:
                raise ValueError
            if frame["frame_index"] != index or not isinstance(frame["pts_seconds"], str):
                raise ValueError
            pts = frame["pts_seconds"]
            if not re.fullmatch(r"\d{1,2}\.\d{6}", pts) or abs(float(pts) * 1000 - index * 1000 / 30) > 0.5:
                raise ValueError
            ms = round(float(pts) * 1000)
            if frame["ms"] != ms:
                raise ValueError
            count = frame["size"]
            if type(count) is not int or not 8 <= count <= 8 * 1024 * 1024 or count > len(remaining):
                raise ValueError
            png, remaining = remaining[:count], remaining[count:]
            used += count
            if (
                used > MAX_EVIDENCE_BYTES
                or not png.startswith(b"\x89PNG\r\n\x1a\n")
                or hashlib.sha256(png).hexdigest() != frame["sha256"]
            ):
                raise ValueError
            evidence.append(RenderedFrame(ms=ms, png=png, sha256=frame["sha256"], frame_index=index, pts_seconds=pts))
        if remaining:
            raise ValueError
        return RenderedMotion(mp4=mp4, sha256=digest, evidence=tuple(evidence), diagnostics=diagnostics)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise MotionRenderError("MOTION_RENDER_INVALID_OUTPUT") from exc


async def _command(args: list[str], *, env: dict[str, str], timeout: int, limit: int) -> bytes:
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
    except OSError as exc:
        raise MotionRenderError("MOTION_RENDER_UNAVAILABLE") from exc

    async def read(stream: asyncio.StreamReader | None, maximum: int) -> bytes:
        assert stream is not None
        chunks, size = [], 0
        while chunk := await stream.read(65536):
            size += len(chunk)
            if size > maximum:
                raise MotionRenderError("MOTION_RENDER_OUTPUT_LIMIT")
            chunks.append(chunk)
        return b"".join(chunks)

    tasks = [asyncio.create_task(read(process.stdout, limit)), asyncio.create_task(read(process.stderr, 8192))]
    try:
        async with asyncio.timeout(timeout):
            output, error = await asyncio.gather(*tasks)
            if await process.wait() != 0:
                try:
                    notice = json.loads(error)
                except (ValueError, UnicodeDecodeError):
                    notice = None
                if isinstance(notice, dict) and notice.get("event") == "motion.render.failed":
                    code = notice.get("code")
                    if isinstance(code, str) and code in RUNNER_FAILURES:
                        raise MotionRenderError(code)
                raise MotionRenderError("MOTION_RENDER_EXECUTION_FAILED")
            return output
    except TimeoutError as exc:
        raise MotionRenderError("MOTION_RENDER_TIMEOUT") from exc
    finally:
        if process.returncode is None:
            process.kill()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # wait() can deadlock when a cancelled/bounded reader left a full pipe.
        # The child is stopped first; drain its remaining bounded OS buffers while
        # reaping it, instead of waiting for readers that no longer consume data.
        await process.communicate()


class IsolatedMotionRenderer:
    def __init__(
        self,
        *,
        image: str,
        docker_executable: Path,
        docker_socket: Path,
        timeout_seconds: int = 900,
        scratch_directory: Path | None = None,
    ):
        if not IMAGE.fullmatch(image) or not docker_executable.is_absolute() or not docker_socket.is_absolute():
            raise MotionRenderError("MOTION_RENDER_INVALID_CONFIGURATION")
        if not 1 <= timeout_seconds <= 900:
            raise MotionRenderError("MOTION_RENDER_INVALID_CONFIGURATION")
        if scratch_directory is not None and (
            not scratch_directory.is_absolute()
            or ".." in scratch_directory.parts
            or any(char in str(scratch_directory) for char in ',"\r\n')
        ):
            raise MotionRenderError("MOTION_RENDER_INVALID_CONFIGURATION")
        self.image = image
        self.docker_executable = docker_executable
        self.docker_socket = docker_socket
        self.timeout_seconds = timeout_seconds
        self.scratch_directory = scratch_directory

    async def render(self, bundle: RenderBundle, *, operation_id: UUID) -> RenderedMotion:
        try:
            workspace = tempfile.TemporaryDirectory(prefix="motion-render-", dir=self.scratch_directory)
        except OSError as exc:
            raise MotionRenderError("MOTION_RENDER_SCRATCH_UNAVAILABLE") from exc
        with workspace as temporary:
            folder = Path(temporary)
            config = _prepare(bundle, folder / "input")
            docker_config = folder / "docker"
            docker_config.mkdir(mode=0o700)
            env = {"PATH": "/usr/bin:/bin", "HOME": str(folder), "DOCKER_CONFIG": str(docker_config), "LANG": "C.UTF-8"}
            prefix = [str(self.docker_executable), "--host", f"unix://{self.docker_socket}"]
            create = [
                *prefix,
                "create",
                "--pull=never",
                "--name",
                f"motion-render-{operation_id.hex}",
                "--label",
                "meu-braco-direito.motion-render=1",
                "--log-driver=none",
                "--network=none",
                "--read-only",
                "--user=65532:65532",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                f"--security-opt=seccomp={SECCOMP}",
                "--pids-limit=256",
                "--memory=4g",
                "--memory-swap=4g",
                "--cpus=2",
                "--shm-size=128m",
                "--ipc=private",
                "--init",
                "--ulimit=core=0:0",
                "--ulimit=nofile=1024:1024",
                "--ulimit=fsize=134217728:134217728",
                "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=2147483648,mode=1777",
                "--mount",
                f"type=bind,src={folder / 'input'},dst=/input,readonly",
                "--env=HOME=/tmp/home",
                "--env=TMPDIR=/tmp",
                "--env=LANG=C.UTF-8",
                "--entrypoint=/usr/local/bin/node",
                self.image,
                "/opt/renderer/runner.cjs",
            ]
            container = (await _command(create, env=env, timeout=30, limit=1024)).decode().strip()
            if not SHA256.fullmatch(container):
                raise MotionRenderError("MOTION_RENDER_INVALID_CONTAINER")
            try:
                output = await _command(
                    [*prefix, "start", "--attach", container],
                    env=env,
                    timeout=self.timeout_seconds,
                    limit=MAX_OUTPUT_BYTES,
                )
                result = _decode(output, config)
                if bundle.fingerprint_frames:
                    result = replace(result, diagnostics={**result.diagnostics, "executor_image": self.image})
                return result
            finally:
                # The ID comes only from this successful create; never remove a pre-existing name.
                await _command([*prefix, "rm", "--force", container], env=env, timeout=30, limit=1024)
