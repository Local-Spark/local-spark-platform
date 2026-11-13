"""Isolation command, byte identities, bounded outputs and cleanup of motion attempts."""

import asyncio
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from app.adapters import motion_html_renderer as motion


def asset(**changes):
    data = b"synthetic audio source"
    return replace(
        motion.RenderAsset("assets/track.wav", "audio/wav", data, hashlib.sha256(data).hexdigest()), **changes
    )


def bundle(**changes):
    return replace(
        motion.RenderBundle(
            "<!doctype html><body>Example</body>",
            "window.seek=()=>{}",
            (),
            {"mode": "silent", "tracks": []},
            64,
            64,
            30,
            1000,
            (0, 500, 999),
        ),
        **changes,
    )


def track(**changes):
    return {
        "asset_id": "assets/track.wav",
        "offset_ms": 0,
        "trim_start_ms": 0,
        "trim_end_ms": 1000,
        "volume": 0.1,
        **changes,
    }


def output(config):
    video = b"\x00\x00\x00\x20ftyp" + b"synthetic"
    png = b"\x89PNG\r\n\x1a\n" + b"synthetic"
    frames = [
        {
            "frame_index": index,
            "ms": round(index * 1000 / 30),
            "pts_seconds": f"{index / 30:.6f}",
            "size": len(png),
            "sha256": hashlib.sha256(png).hexdigest(),
        }
        for index in config["sample_frames"]
    ]
    header = {
        "version": 1,
        "video": {"size": len(video), "sha256": hashlib.sha256(video).hexdigest()},
        "frames": frames,
        "diagnostics": {
            "frame_count": 30,
            "width": 64,
            "height": 64,
            "sandbox": True,
            "seccomp": 2,
            "host_seccomp_filters": 1,
            "renderer_seccomp_filters": 2,
            "denied_requests": 0,
            "evidence_source": "decoded_mp4",
            "config_sha256": hashlib.sha256(json.dumps(config).encode()).hexdigest(),
        },
    }
    return header, video + png * len(frames)


def packed(header, data):
    return json.dumps(header).encode() + b"\n" + data


def test_prepare_preserves_bytes_and_restricts_files(tmp_path):
    item = asset()
    config = motion._prepare(bundle(assets=(item,), audio={"mode": "mix", "tracks": [track()]}), tmp_path / "input")
    assert config["sample_frames"] == [0, 15, 29]
    assert config["audio"]["tracks"][0]["volume"] == 0.1
    assert (tmp_path / "input/asset-0").read_bytes() == item.data
    assert (tmp_path / "input/asset-0").stat().st_mode & 0o777 == 0o444
    assert (tmp_path / "input").stat().st_mode & 0o777 == 0o555
    assert config["html_sha256"] == hashlib.sha256(bundle().html.encode()).hexdigest()


def test_default_samples_cover_twenty_decoded_frames_and_short_piece(tmp_path):
    cfg = motion._prepare(bundle(sample_times_ms=()), tmp_path / "normal")
    assert len(cfg["sample_frames"]) == 20 and cfg["sample_frames"][0] == 0 and cfg["sample_frames"][-1] == 29
    short = motion._prepare(bundle(duration_ms=1, sample_times_ms=()), tmp_path / "short")
    assert short["sample_frames"] == [0]
    near = motion._prepare(bundle(sample_times_ms=(0, 1)), tmp_path / "near")
    assert near["sample_frames"] == [0]


@pytest.mark.parametrize(
    "changes",
    [
        {"width": True},
        {"height": 63},
        {"width": 65},
        {"height": 65},
        {"fps": 24},
        {"duration_ms": 0},
        {"html": ""},
        {"html": "x" * (2 * 1024 * 1024 + 1)},
        {"scene_init": ""},
        {"scene_init": "x" * (1024 * 1024 + 1)},
        {"assets": tuple(asset(id=f"assets/{i}") for i in range(33))},
        {"assets": (asset(id="../escape"),)},
        {"assets": (asset(), asset())},
        {"assets": (asset(mime_type="text/html"),)},
        {"assets": (asset(data=b""),)},
        {"assets": (asset(sha256="wrong"),)},
        {"assets": (asset(sha256="0" * 64),)},
        {"sample_times_ms": tuple(range(65))},
        {"sample_times_ms": (0, 0)},
        {"sample_times_ms": (1000,)},
    ],
)
def test_rejects_invalid_bundle_before_container(tmp_path, changes):
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_INPUT"):
        motion._prepare(bundle(**changes), tmp_path / "input")
    assert not (tmp_path / "input").exists()


def test_input_aggregate_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(motion, "MAX_INPUT_BYTES", 5)
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_INPUT"):
        motion._prepare(bundle(assets=(asset(),)), tmp_path / "input")


@pytest.mark.parametrize(
    "plan",
    [
        {},
        {"mode": "silent", "tracks": None},
        {"mode": "silent", "tracks": [track()]},
        {"mode": "mix", "tracks": []},
        {"mode": "mix", "tracks": [track()] * 17},
        {"mode": "mix", "tracks": [None]},
        {"mode": "mix", "tracks": [{}]},
        *[
            {"mode": "mix", "tracks": [track(**changes)]}
            for changes in (
                {"asset_id": 3},
                {"asset_id": "missing"},
                {"offset_ms": 1},
                {"trim_start_ms": 1000},
                {"volume": True},
                {"volume": "0.1"},
                {"volume": -0.1},
                {"volume": float("nan")},
                {"volume": 0.0000001},
            )
        ],
    ],
)
def test_audio_contract_is_bounded_and_does_not_coerce(plan):
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_INPUT"):
        motion._audio(plan, {"assets/track.wav": asset()}, 1000)


def test_audio_requires_audio_asset():
    with pytest.raises(motion.MotionRenderError):
        motion._audio({"mode": "mix", "tracks": [track()]}, {"assets/track.wav": asset(mime_type="image/png")}, 1000)


def test_audio_accepts_original_mp4_without_asr_resampling():
    source = asset(id="assets/source.mp4", mime_type="video/mp4")
    plan = {"mode": "mix", "tracks": [track(asset_id=source.id)]}
    assert motion._audio(plan, {source.id: source}, 1000) == plan


def test_result_protocol_preserves_video_evidence_identities(tmp_path):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    result = motion._decode(packed(header, data), config)
    assert result.sha256 == header["video"]["sha256"]
    assert [(frame.frame_index, frame.ms, frame.pts_seconds) for frame in result.evidence] == [
        (0, 0, "0.000000"),
        (15, 500, "0.500000"),
        (29, 967, "0.966667"),
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda h: h.update(version=2),
        lambda h: h.update(extra=True),
        lambda h: h.update(video=None),
        lambda h: h["video"].update(size=-1),
        lambda h: h["video"].update(size=True),
        lambda h: h["video"].update(size=motion.MAX_VIDEO_BYTES + 1),
        lambda h: h["video"].update(size=100000),
        lambda h: h["video"].update(sha256="0" * 64),
        lambda h: h.update(frames=None),
        lambda h: h.update(frames=[]),
        lambda h: h.update(diagnostics=None),
        lambda h: h["diagnostics"].update(frame_count=29),
        lambda h: h["diagnostics"].update(width=128),
        lambda h: h["diagnostics"].update(height=128),
        lambda h: h["diagnostics"].update(sandbox=False),
        lambda h: h["diagnostics"].update(seccomp=0),
        lambda h: h["diagnostics"].update(denied_requests=1),
        lambda h: h["frames"].__setitem__(0, None),
        lambda h: h["frames"][0].update(extra=True),
        lambda h: h["frames"][0].update(frame_index=1),
        lambda h: h["frames"][0].update(pts_seconds=1),
        lambda h: h["frames"][0].update(pts_seconds="nan"),
        lambda h: h["frames"][0].update(pts_seconds="0.100000"),
        lambda h: h["frames"][0].update(ms=1),
        lambda h: h["frames"][0].update(size=True),
        lambda h: h["frames"][0].update(size=1),
        lambda h: h["frames"][0].update(size=9 * 1024 * 1024),
        lambda h: h["frames"][0].update(size=10000),
        lambda h: h["frames"][0].update(sha256="0" * 64),
    ],
)
def test_result_protocol_rejects_wrong_identities_geometry_timestamps_and_limits(tmp_path, mutation):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    mutation(header)
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_OUTPUT"):
        motion._decode(packed(header, data), config)


@pytest.mark.parametrize("data", [b"", b"x" * 65537 + b"\n", b"not-json\n", b"[]\n", b"\xff\n"])
def test_malformed_result_header(tmp_path, data):
    config = motion._prepare(bundle(), tmp_path / "input")
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_OUTPUT"):
        motion._decode(data, config)


@pytest.mark.parametrize("kind", ["extra", "video_magic", "png_magic", "evidence_limit"])
def test_bad_binary_payload(tmp_path, monkeypatch, kind):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    if kind == "extra":
        data += b"extra"
    elif kind == "video_magic":
        data = b"x" * 8 + data[8:]
        header["video"]["sha256"] = hashlib.sha256(data[: header["video"]["size"]]).hexdigest()
    elif kind == "png_magic":
        offset = header["video"]["size"]
        data = data[:offset] + b"x" * 8 + data[offset + 8 :]
    else:
        monkeypatch.setattr(motion, "MAX_EVIDENCE_BYTES", 1)
    with pytest.raises(motion.MotionRenderError, match="MOTION_RENDER_INVALID_OUTPUT"):
        motion._decode(packed(header, data), config)


async def test_command_bounds_stdout_stderr_and_actual_process_lifetime():
    env = {"PATH": "/usr/bin:/bin"}
    assert await motion._command([sys.executable, "-c", "print('ok')"], env=env, timeout=5, limit=10) == b"ok\n"
    for code, expected in [
        ("raise SystemExit(1)", "EXECUTION_FAILED"),
        ("print('x'*100)", "OUTPUT_LIMIT"),
        ("import sys; sys.stderr.write('x'*9000)", "OUTPUT_LIMIT"),
    ]:
        with pytest.raises(motion.MotionRenderError, match=expected):
            await motion._command([sys.executable, "-c", code], env=env, timeout=5, limit=10)
    with pytest.raises(motion.MotionRenderError, match="UNAVAILABLE"):
        await motion._command(["/nonexistent/motion-tool"], env=env, timeout=1, limit=10)
    with pytest.raises(motion.MotionRenderError, match="TIMEOUT"):
        await motion._command([sys.executable, "-c", "import time; time.sleep(5)"], env=env, timeout=0, limit=10)
    task = asyncio.create_task(
        motion._command([sys.executable, "-c", "import time; time.sleep(5)"], env=env, timeout=5, limit=10)
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize(
    "changes",
    [
        {"image": "renderer:latest"},
        {"docker_executable": Path("docker")},
        {"docker_socket": Path("socket")},
        {"scratch_directory": Path("relative")},
        {"scratch_directory": Path("/shared/../outside")},
        {"scratch_directory": Path("/shared,readonly")},
        {"scratch_directory": Path('/shared"quoted')},
        {"scratch_directory": Path("/shared\nline")},
        {"timeout_seconds": 0},
        {"timeout_seconds": 901},
    ],
)
def test_configuration_requires_immutable_image_explicit_local_socket_and_deadline(changes):
    config = {
        "image": "sha256:" + "0" * 64,
        "docker_executable": Path("/usr/bin/docker"),
        "docker_socket": Path("/run/docker.sock"),
    }
    with pytest.raises(motion.MotionRenderError, match="INVALID_CONFIGURATION"):
        motion.IsolatedMotionRenderer(**{**config, **changes})


@pytest.mark.parametrize(
    "kind", ["success", "fingerprints", "bad_container", "render_failure", "bad_output", "create_failure"]
)
@pytest.mark.parametrize("shared", [False, True])
async def test_container_flags_credentials_and_cleanup(monkeypatch, tmp_path, kind, shared):
    calls = []
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-container-or-docker")

    async def fake(args, **kwargs):
        calls.append(args)
        assert "OPENAI_API_KEY" not in kwargs["env"]
        assert set(kwargs["env"]) == {"PATH", "HOME", "DOCKER_CONFIG", "LANG"}
        if "create" in args:
            mount = next(arg for arg in args if arg.startswith("type=bind,"))
            input_path = Path(mount.split(",src=", 1)[1].split(",dst=", 1)[0])
            if shared:
                assert input_path.parent.parent == tmp_path
            assert input_path.name == "input" and mount.endswith(",dst=/input,readonly")
            assert all(
                flag in args
                for flag in [
                    "--pull=never",
                    "--log-driver=none",
                    "--network=none",
                    "--read-only",
                    "--user=65532:65532",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "--pids-limit=256",
                    "--memory=4g",
                    "--cpus=2",
                ]
            )
            assert f"--security-opt=seccomp={motion.SECCOMP}" in args
            assert not any("docker.sock" in arg for arg in args[args.index("create") + 1 :])
            if kind == "create_failure":
                raise motion.MotionRenderError("CREATE_FAILED")
            return b"not-an-id" if kind == "bad_container" else b"a" * 64 + b"\n"
        if "start" in args:
            if kind == "render_failure":
                raise motion.MotionRenderError("RENDER_FAILED")
            if kind == "bad_output":
                return b"bad"
            mount = next(arg for arg in calls[0] if arg.startswith("type=bind,"))
            input_path = Path(mount.split(",src=", 1)[1].split(",dst=", 1)[0])
            config = json.loads((input_path / "config.json").read_text())
            header, data = output(config)
            if kind == "fingerprints":
                assert config["fingerprint_frames"] is True
                header["diagnostics"].update(frame_fingerprints=["a" * 64] * 30, fingerprint_environment="b" * 64)
            return packed(header, data)
        assert args[-3:] == ["rm", "--force", "a" * 64]
        return b"a" * 64 + b"\n"

    monkeypatch.setattr(motion, "_command", fake)
    renderer = motion.IsolatedMotionRenderer(
        image="sha256:" + "0" * 64,
        docker_executable=Path("/usr/bin/docker"),
        docker_socket=Path("/run/docker.sock"),
        scratch_directory=tmp_path if shared else None,
    )
    if kind in {"success", "fingerprints"}:
        result = await renderer.render(bundle(fingerprint_frames=kind == "fingerprints"), operation_id=uuid4())
        assert result.evidence[-1].ms == 967
        if kind == "fingerprints":
            assert result.diagnostics["executor_image"] == renderer.image
            assert len(result.diagnostics["frame_fingerprints"]) == 30
    else:
        with pytest.raises(motion.MotionRenderError):
            await renderer.render(bundle(), operation_id=uuid4())
    assert len(calls) == (1 if kind in {"bad_container", "create_failure"} else 3)
    assert not list(tmp_path.iterdir())


async def test_unavailable_shared_directory_fails_before_creating_a_container(tmp_path, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("No Docker call without a usable shared directory")

    monkeypatch.setattr(motion, "_command", forbidden)
    renderer = motion.IsolatedMotionRenderer(
        image="sha256:" + "0" * 64,
        docker_executable=Path("/usr/bin/docker"),
        docker_socket=Path("/run/docker.sock"),
        scratch_directory=tmp_path / "missing",
    )
    with pytest.raises(motion.MotionRenderError, match="SCRATCH_UNAVAILABLE"):
        await renderer.render(bundle(), operation_id=uuid4())


def test_explicit_seccomp_blocks_kernel_and_host_socket_surfaces():
    profile = json.loads(motion.SECCOMP.read_text())
    assert profile["defaultAction"] == "SCMP_ACT_ERRNO"
    allowed = {name for rule in profile["syscalls"] if rule["action"] == "SCMP_ACT_ALLOW" for name in rule["names"]}
    assert not allowed.intersection({"io_uring_setup", "io_uring_enter", "io_uring_register", "ptrace", "socketcall"})
    socket_rules = [rule for rule in profile["syscalls"] if "socket" in rule["names"]]
    assert {rule["args"][0]["value"] for rule in socket_rules} == {1, 2, 10}


@pytest.mark.parametrize(
    "notice,expected",
    [
        ({"event": "motion.render.failed", "code": "MOTION_RENDER_BROWSER_SANDBOX_FAILED"}, "BROWSER_SANDBOX_FAILED"),
        ({"event": "motion.render.failed", "code": "private-content"}, "EXECUTION_FAILED"),
        ({"event": "motion.render.failed", "code": []}, "EXECUTION_FAILED"),
        ({"event": "other", "code": "private-content"}, "EXECUTION_FAILED"),
        ([], "EXECUTION_FAILED"),
    ],
)
async def test_only_allowlisted_runner_error_codes_leave_process_boundary(notice, expected):
    code = "import sys; sys.stderr.write(" + repr(json.dumps(notice)) + "); raise SystemExit(1)"
    with pytest.raises(motion.MotionRenderError, match=expected):
        await motion._command([sys.executable, "-c", code], env={"PATH": "/usr/bin:/bin"}, timeout=5, limit=10)


def test_private_data_is_absent_from_dataclass_repr():
    source = bundle(html="private html", scene_init="private js", assets=(asset(data=b"private audio"),))
    assert (
        "private html" not in repr(source) and "private js" not in repr(source) and "private audio" not in repr(source)
    )
    frame = motion.RenderedFrame(0, b"private png", "0" * 64)
    result = motion.RenderedMotion(b"private video", "0" * 64, (frame,), {})
    assert "private png" not in repr(result) and "private video" not in repr(result)


def test_evidence_must_come_from_decoded_final_mp4(tmp_path):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    header["diagnostics"]["evidence_source"] = "browser_screenshot"
    with pytest.raises(motion.MotionRenderError, match="INVALID_OUTPUT"):
        motion._decode(packed(header, data), config)


def test_output_must_bind_exact_input_and_code(tmp_path):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    header["diagnostics"]["config_sha256"] = "0" * 64
    with pytest.raises(motion.MotionRenderError, match="INVALID_OUTPUT"):
        motion._decode(packed(header, data), config)


def test_invalid_unicode_is_rejected_before_container(tmp_path):
    with pytest.raises(motion.MotionRenderError, match="INVALID_INPUT"):
        motion._prepare(bundle(html="\ud800"), tmp_path / "input")


@pytest.mark.parametrize("own,child", [(None, 2), (1, None), (True, 2), (1, 1), (0, 1)])
def test_result_requires_proven_additional_sandbox_filter(tmp_path, own, child):
    config = motion._prepare(bundle(), tmp_path / "input")
    header, data = output(config)
    header["diagnostics"].update(host_seccomp_filters=own, renderer_seccomp_filters=child)
    with pytest.raises(motion.MotionRenderError, match="INVALID_OUTPUT"):
        motion._decode(packed(header, data), config)


async def test_output_overflow_reaps_child_with_more_than_a_pipe_buffer():
    # A large write fills asyncio's pipe buffer; wait-before-drain used to hang.
    with pytest.raises(motion.MotionRenderError, match="OUTPUT_LIMIT"):
        await asyncio.wait_for(
            motion._command(
                [sys.executable, "-c", "import os,time; os.write(1,b'x'*4000000); time.sleep(10)"],
                env={"PATH": "/usr/bin:/bin"},
                timeout=3,
                limit=10,
            ),
            timeout=5,
        )


@pytest.mark.parametrize("changes", [{"fingerprint_frames": 1}, {"fingerprint_frames": True, "frames_only": True}])
def test_fingerprints_require_full_decoded_video_not_storyboard_or_truthy_flags(tmp_path, changes):
    with pytest.raises(motion.MotionRenderError, match="INVALID_INPUT"):
        motion._prepare(bundle(**changes), tmp_path / "invalid-fingerprint")
