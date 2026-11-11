"""Offline provenance and media checks; every child process is replaced with a fake."""

from __future__ import annotations

import copy
import json
import os
import signal
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from scripts.evals import motion_declarative_render as bridge
from scripts.evals import motion_eval as base


def put(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@pytest.fixture(autouse=True)
def forbid_real_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", Mock(side_effect=AssertionError("real process forbidden in unit test")))


@pytest.fixture
def pinned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "source"
    contents = {name: name.encode() for name in bridge.CODE}
    contents["renderer/prepare.py"] = b"def prepare(value):\n    return {'unchanged': value}\n"
    monkeypatch.setattr(bridge, "CODE", {name: base.digest(data) for name, data in contents.items()})
    monkeypatch.setattr(base, "ROOT", tmp_path / "repository")
    for name, data in contents.items():
        put(source / "code" / name, data)
        if name.startswith("current/"):
            put(base.ROOT / "app/assets/motion_renderer" / Path(name).name, data)
    return source


@pytest.fixture
def tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    paths = {}
    for name in ("node", "ffmpeg", "ffprobe", "chromium"):
        path = tmp_path / "tools" / name
        put(path, f"synthetic executable {name}".encode())
        path.chmod(0o700)
        paths[name] = str(path)
    monkeypatch.setattr(bridge, "HISTORICAL_TOOLS", {key: paths[key] for key in ("ffmpeg", "ffprobe", "chromium")})
    package = tmp_path / "playwright"
    put(package / "package.json", b'{"name":"synthetic"}')
    put(package / "index.js", b"synthetic package entry")
    put(package / "lib/helper.js", b"synthetic dependency")
    monkeypatch.setattr(bridge, "PLAYWRIGHT", package)
    return paths


def audio_metadata() -> dict[str, Any]:
    return {
        "streams": [
            {
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo",
                "time_base": "1/48000",
                "start_pts": 0,
                "duration_ts": 48000,
                "extradata_hash": "SHA256:" + "b" * 64,
            }
        ],
        "packets": [
            {
                "pts": -1024,
                "dts": -1024,
                "duration": 1024,
                "size": 128,
                "flags": "KD",
                "data_hash": "SHA256:" + "a" * 64,
                "side_data_list": [
                    {
                        "side_data_type": "Skip Samples",
                        "skip_samples": 1024,
                        "discard_padding": 0,
                        "skip_reason": 0,
                        "discard_reason": 0,
                    }
                ],
            }
        ],
    }


def video_metadata() -> dict[str, Any]:
    return {
        "streams": [
            {
                "codec_name": "h264",
                "width": 720,
                "height": 1280,
                "pix_fmt": "yuv420p",
                "avg_frame_rate": "30/1",
                "r_frame_rate": "30/1",
                "time_base": "1/15360",
                "start_pts": 0,
                "duration_ts": 1024,
                "nb_frames": "2",
            }
        ],
        "frames": [
            {"pts": 0, "best_effort_timestamp": 0, "pkt_duration": 512},
            {"pts": 512, "best_effort_timestamp": 512, "pkt_duration": 512},
        ],
    }


def test_pinned_source_executes_exact_verified_bytes(pinned: Path) -> None:
    value = {"fixture": [1, 2, 3]}
    assert bridge.prepare_payload(pinned, value) == {"unchanged": value}


@pytest.mark.parametrize("name", tuple(bridge.CODE))
def test_modified_or_missing_renderer_is_rejected(pinned: Path, name: str) -> None:
    (pinned / "code" / name).write_bytes(b"changed")
    with pytest.raises(base.EvalError, match="historical_renderer_changed"):
        bridge.verify_code(pinned)
    (pinned / "code" / name).unlink()
    with pytest.raises(base.EvalError, match="historical_renderer_changed"):
        bridge.verify_code(pinned)


def test_current_compiler_must_match_original(pinned: Path) -> None:
    (base.ROOT / "app/assets/motion_renderer/compiler.cjs").write_bytes(b"different compiler")
    with pytest.raises(base.EvalError, match="current_renderer_differs_from_baseline"):
        bridge.prepare_payload(pinned, {})


def test_prepare_rechecks_bytes_before_executing(pinned: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def change_after_check(source: Path) -> None:
        (source / "code/renderer/prepare.py").write_bytes(b"raise RuntimeError('must never run')")

    monkeypatch.setattr(bridge, "verify_code", change_after_check)
    with pytest.raises(base.EvalError, match="historical_renderer_changed"):
        bridge.prepare_payload(pinned, {})


def test_prepare_rejects_wrong_result(pinned: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"def prepare(value):\n    return []\n"
    (pinned / "code/renderer/prepare.py").write_bytes(content)
    monkeypatch.setitem(bridge.CODE, "renderer/prepare.py", base.digest(content))
    with pytest.raises(base.EvalError, match="historical_prepare_invalid"):
        bridge.prepare_payload(pinned, {})


def test_tool_identity_covers_transitive_playwright_code(tools: dict[str, str]) -> None:
    before = bridge.verify_tools(tools)
    assert set(before) == {*tools, "playwright"}
    assert before["ffmpeg"]["sha256"] == base.digest(Path(tools["ffmpeg"]).read_bytes())
    (bridge.PLAYWRIGHT / "lib/helper.js").write_bytes(b"changed dependency")
    assert bridge.verify_tools(tools)["playwright"] != before["playwright"]


@pytest.mark.parametrize("failure", ["missing", "not_executable", "different_path", "missing_package", "external"])
def test_tools_fail_closed(tools: dict[str, str], tmp_path: Path, failure: str) -> None:
    expected = "declarative_tool_missing"
    if failure == "missing":
        del tools["node"]
    elif failure == "not_executable":
        Path(tools["node"]).chmod(0o600)
    elif failure == "different_path":
        tools["ffmpeg"] = tools["node"]
        expected = "historical_tool_path_mismatch"
    elif failure == "missing_package":
        (bridge.PLAYWRIGHT / "index.js").unlink()
        expected = "historical_playwright_missing"
    else:
        external = tmp_path / "outside.js"
        external.write_bytes(b"untracked dependency")
        (bridge.PLAYWRIGHT / "linked.js").symlink_to(external)
        expected = "historical_playwright_external_dependency"
    with pytest.raises(base.EvalError, match=expected):
        bridge.verify_tools(tools)


def test_command_uses_clean_environment_and_no_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    process = Mock(returncode=0)
    process.communicate.return_value = (b"private output", b"private diagnostic")
    factory = Mock(return_value=process)
    monkeypatch.setattr(subprocess, "Popen", factory)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-inherited")
    args = ["/local/tool", "literal; $(not-a-command)"]
    assert bridge.command(args, timeout=17) == b"private output"
    assert factory.call_args.args == (args,)
    assert "shell" not in factory.call_args.kwargs
    assert factory.call_args.kwargs["start_new_session"] is True
    assert set(factory.call_args.kwargs["env"]) == {"PATH", "LANG", "LC_ALL", "TMPDIR"}
    process.communicate.assert_called_once_with(timeout=17)


@pytest.mark.parametrize("group_gone", [False, True])
def test_timeout_kills_whole_process_group(monkeypatch: pytest.MonkeyPatch, group_gone: bool) -> None:
    process = Mock(pid=456, returncode=-9)
    process.communicate.side_effect = [subprocess.TimeoutExpired("private", 2), (b"", b"private token")]
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    kill = Mock(side_effect=ProcessLookupError if group_gone else None)
    monkeypatch.setattr(os, "killpg", kill)
    with pytest.raises(base.EvalError, match="^declarative_local_tool_failed$"):
        bridge.command(["/local/tool"], timeout=2)
    kill.assert_called_once_with(456, signal.SIGKILL)
    assert process.communicate.call_count == 2


@pytest.mark.parametrize("failure", ["spawn", "exit"])
def test_process_failures_do_not_disclose_diagnostics(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    process = Mock(returncode=1)
    process.communicate.return_value = (b"sensitive stdout", b"sensitive stderr")
    factory = Mock(side_effect=OSError("sensitive path")) if failure == "spawn" else Mock(return_value=process)
    monkeypatch.setattr(subprocess, "Popen", factory)
    with pytest.raises(base.EvalError, match="^declarative_local_tool_failed$"):
        bridge.command(["/local/tool"])


def test_failure_diagnostic_is_bounded_private_and_not_overwritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = Mock(returncode=1)
    process.communicate.return_value = (b"a" * 20000, b"b" * 20000)
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    diagnostic = tmp_path / "renderer-error.log"
    with pytest.raises(base.EvalError, match="^declarative_local_tool_failed$"):
        bridge.command(["/local/tool"], diagnostic=diagnostic)
    assert diagnostic.read_bytes() == b"a" * 16000 + b"\n" + b"b" * 16000
    assert diagnostic.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        bridge.command(["/local/tool"], diagnostic=diagnostic)


def test_audio_evidence_includes_preroll_skip_samples_and_pcm(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = Mock(side_effect=[base.json_bytes(audio_metadata()), b"decoded samples"])
    monkeypatch.setattr(bridge, "command", mock)
    result = bridge.audio_signature(Path("fixture.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
    assert result["packets"][0]["pts"] == -1024
    assert result["packets"][0]["side_data_list"][0]["skip_samples"] == 1024
    assert result["pcm_sha256"] == base.digest(b"decoded samples")
    for call in mock.call_args_list:
        args = call.args[0]
        assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
    assert "-show_data_hash" in mock.call_args_list[0].args[0]
    assert "pcm_s16le" in mock.call_args_list[1].args[0]


@pytest.mark.parametrize("size", [317, 294, 6])
def test_ffprobe44_decimal_packet_size_matches_integer_evidence(
    monkeypatch: pytest.MonkeyPatch,
    size: int,
) -> None:
    metadata = audio_metadata()
    metadata["packets"][0]["size"] = str(size)
    integer_metadata = copy.deepcopy(metadata)
    integer_metadata["packets"][0]["size"] = size
    mock = Mock(side_effect=[base.json_bytes(metadata), b"same pcm", base.json_bytes(integer_metadata), b"same pcm"])
    monkeypatch.setattr(bridge, "command", mock)
    tools = {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}
    legacy = bridge.audio_signature(Path("legacy.mp4"), tools)
    modern = bridge.audio_signature(Path("modern.mp4"), tools)
    assert legacy == modern
    assert type(legacy["packets"][0]["size"]) is int
    assert legacy["packets"][0]["size"] == size
    assert legacy["packets"][0]["pts"] == -1024
    assert legacy["packets"][0]["side_data_list"][0]["skip_samples"] == 1024


@pytest.mark.parametrize("size", [True, False, 0, -1, 1.0, "+1", "-1", " 1", "1 ", "1.0", "1e3", "١", "01", "", None])
def test_packet_size_rejects_ambiguous_coercions(monkeypatch: pytest.MonkeyPatch, size: object) -> None:
    metadata = audio_metadata()
    metadata["packets"][0]["size"] = size
    mock = Mock(return_value=base.json_bytes(metadata))
    monkeypatch.setattr(bridge, "command", mock)
    with pytest.raises(base.EvalError, match="^audio_packet_evidence_missing$"):
        bridge.audio_signature(Path("invalid.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
    assert mock.call_count == 1


@pytest.mark.parametrize("failure", ["json", "root", "stream", "timebase", "packets", "hash", "pts", "pcm"])
def test_incomplete_audio_evidence_never_proves_equality(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    metadata = audio_metadata()
    expected = "audio_packet_evidence_missing"
    raw: bytes | None = None
    if failure == "json":
        raw, expected = b"invalid JSON", "audio_metadata_invalid"
    elif failure == "root":
        raw, expected = b"[]", "audio_metadata_invalid"
    elif failure == "stream":
        metadata["streams"] = None
        expected = "baseline_aac_required"
    elif failure == "timebase":
        del metadata["streams"][0]["time_base"]
        expected = "audio_stream_evidence_missing"
    elif failure == "packets":
        metadata["packets"] = None
        expected = "baseline_aac_required"
    elif failure == "hash":
        metadata["packets"][0]["data_hash"] = "not-a-hash"
    elif failure == "pts":
        del metadata["packets"][0]["pts"]
    else:
        expected = "decoded_audio_missing"
    mock = Mock(side_effect=[raw if raw is not None else base.json_bytes(metadata), b""])
    monkeypatch.setattr(bridge, "command", mock)
    with pytest.raises(base.EvalError, match=expected):
        bridge.audio_signature(Path("fixture.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})


@pytest.mark.parametrize("change", [None, "packet", "pts", "duration", "skip", "pcm", "baseline", "visual"])
def test_freeze_uses_stream_copy_and_rejects_every_difference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str | None,
) -> None:
    baseline, visual, output = (tmp_path / name for name in ("baseline.mp4", "visual.mp4", "final.mp4"))
    baseline.write_bytes(b"original AAC/video")
    visual.write_bytes(b"new visual")
    signature = {"stream": {}, "packets": audio_metadata()["packets"], "pcm_sha256": "0" * 64, "pcm_bytes": 32}
    changed = copy.deepcopy(signature)
    if change == "packet":
        changed["packets"][0]["data_hash"] = "SHA256:" + "c" * 64
    elif change in {"pts", "duration"}:
        changed["packets"][0][change] += 1
    elif change == "skip":
        changed["packets"][0]["side_data_list"][0]["skip_samples"] += 1
    elif change == "pcm":
        changed["pcm_sha256"] = "1" * 64
    monkeypatch.setattr(bridge, "audio_signature", Mock(side_effect=[signature, changed]))

    def remux(args: list[str]) -> bytes:
        assert args[-1] == str(output)
        assert args[args.index("-c") + 1] == "copy"
        assert [args[index + 1] for index, arg in enumerate(args) if arg == "-map"] == ["0:v:0", "1:a:0"]
        assert "-n" in args and "-shortest" not in args
        assert args.count("-protocol_whitelist") == 2
        output.write_bytes(b"visual plus exact original AAC")
        if change in {"baseline", "visual"}:
            (baseline if change == "baseline" else visual).write_bytes(b"modified during remux")
        return b""

    monkeypatch.setattr(bridge, "command", remux)
    if change:
        error = "audio_freeze_input_changed" if change in {"baseline", "visual"} else "frozen_audio_mismatch"
        with pytest.raises(base.EvalError, match=error):
            bridge.freeze_audio(baseline, visual, output, {"ffmpeg": "ffmpeg"})
    else:
        proof = bridge.freeze_audio(baseline, visual, output, {"ffmpeg": "ffmpeg"})
        assert proof["baseline_sha256"] == base.digest(baseline.read_bytes())
        assert proof["output_sha256"] == base.digest(output.read_bytes())
        assert proof["pcm_equal"] is True and proof["aac_packets_and_timing_equal"] is True
        assert proof["perceptual_listening"] == "not_performed"
    assert output.exists()  # A failed artifact remains available for diagnosis; it is never marked equal.
    with pytest.raises(base.EvalError, match="audio_destination_exists"):
        bridge.freeze_audio(baseline, visual, output, {"ffmpeg": "ffmpeg"})


def test_video_signature_covers_every_frame_and_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = Mock(side_effect=[base.json_bytes(video_metadata()), b"SHA256=" + b"a" * 64 + b"\n"])
    monkeypatch.setattr(bridge, "command", mock)
    result = bridge.video_signature(Path("fixture.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
    assert result["rgb24_sha256"] == "a" * 64
    assert result["frames"] == [
        {"pts": 0, "best_effort_timestamp": 0, "duration": 512},
        {"pts": 512, "best_effort_timestamp": 512, "duration": 512},
    ]
    decode = mock.call_args_list[1].args[0]
    assert decode[decode.index("-pix_fmt") + 1] == "rgb24"
    assert decode[decode.index("-fps_mode") + 1] == "passthrough"
    assert "-frames:v" not in decode and "-t" not in decode


@pytest.mark.parametrize("shape", ["legacy", "both"])
def test_ffprobe44_pkt_pts_matches_modern_frame_timestamps(monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
    modern = video_metadata()
    legacy = copy.deepcopy(modern)
    for frame in legacy["frames"]:
        frame["pkt_pts"] = frame["pts"]
        if shape == "legacy":
            del frame["pts"]
    decoded = b"SHA256=" + b"a" * 64 + b"\n"
    mock = Mock(side_effect=[base.json_bytes(legacy), decoded, base.json_bytes(modern), decoded])
    monkeypatch.setattr(bridge, "command", mock)
    tools = {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}
    assert bridge.video_signature(Path("legacy.mp4"), tools) == bridge.video_signature(Path("modern.mp4"), tools)
    requested = mock.call_args_list[0].args[0]
    entries = requested[requested.index("-show_entries") + 1]
    assert "frame=pts,pkt_pts," in entries


@pytest.mark.parametrize(
    "fields",
    [
        {"pts": 0, "pkt_pts": 1},
        {"pts": None, "pkt_pts": 0},
        {"pts": 0, "pkt_pts": None},
        {"pts": "0"},
        {"pkt_pts": "0"},
        {"pts": 0.0},
        {"pkt_pts": 0.0},
        {"pts": False, "pkt_pts": 0},
        {"pts": 0, "pkt_pts": False},
        {},
    ],
)
def test_frame_timestamps_reject_conflicts_and_coercions(
    monkeypatch: pytest.MonkeyPatch,
    fields: dict[str, object],
) -> None:
    metadata = video_metadata()
    metadata["frames"][0] = {"best_effort_timestamp": 0, "pkt_duration": 512, **fields}
    mock = Mock(return_value=base.json_bytes(metadata))
    monkeypatch.setattr(bridge, "command", mock)
    with pytest.raises(base.EvalError, match="^video_frame_evidence_missing$"):
        bridge.video_signature(Path("invalid.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
    assert mock.call_count == 1


@pytest.mark.parametrize("failure", ["json", "root", "streams", "frames", "count", "pts", "duration", "hash"])
def test_video_signature_requires_complete_evidence(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    metadata = video_metadata()
    raw: bytes | None = None
    expected = "video_evidence_missing"
    if failure == "json":
        raw, expected = b"{", "video_metadata_invalid"
    elif failure == "root":
        raw, expected = b"[]", "video_metadata_invalid"
    elif failure == "streams":
        metadata["streams"] = []
    elif failure == "frames":
        metadata["frames"] = []
    elif failure == "count":
        metadata["streams"][0]["nb_frames"] = "3"
    elif failure == "pts":
        del metadata["frames"][1]["pts"]
        expected = "video_frame_evidence_missing"
    elif failure == "duration":
        metadata["frames"][1]["pkt_duration"] = 0
        expected = "video_frame_evidence_missing"
    else:
        expected = "decoded_video_hash_missing"
    monkeypatch.setattr(
        bridge, "command", Mock(side_effect=[raw or base.json_bytes(metadata), b"missing decoded hash"])
    )
    with pytest.raises(base.EvalError, match=expected):
        bridge.video_signature(Path("fixture.mp4"), {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})


@pytest.mark.parametrize(
    "change", [None, "tuple", "hash", "compiler", "duration", "frames", "audio", "tools", "code", "trace"]
)
def test_render_validates_trace_and_preserves_inputs(
    pinned: Path,
    tools: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    change: str | None,
) -> None:
    run = pinned.parent
    target = run / "reel1c/v1"
    target.mkdir(parents=True)
    put(run / "reel1c/v0/render.mp4", b"baseline video")
    prepared: dict[str, Any] = {"scenes": [{"duration_ms": 1000}], "profile": {"fps": 30}}
    if change == "tuple":
        # The actual historical Python preparer returns composition.scenes as a tuple.
        prepared["scenes"] = tuple(prepared["scenes"])
    original_prepared = copy.deepcopy(prepared)
    original_code = (pinned / "code/renderer/render.cjs").read_bytes()
    frozen = Mock()

    def fake_freeze(baseline: Path, visual: Path, destination: Path, _tools: dict[str, str]) -> dict[str, bool]:
        frozen(baseline, visual, destination)
        destination.write_bytes(b"frozen output")
        return {"pcm_equal": True, "aac_packets_and_timing_equal": True}

    def fake_render(args: list[str], *, timeout: int, diagnostic: Path) -> bytes:
        assert timeout == 960 and args[:2] == [tools["node"], str(pinned / "code/renderer/render.cjs")]
        assert diagnostic == target / "renderer-error.log"
        assert json.loads(Path(args[2]).read_bytes()) == json.loads(base.json_bytes(original_prepared))
        output = Path(args[3])
        assert output.stat().st_mode & 0o777 == 0o700
        (output / "page-1.mp4").write_bytes(b"new visual")
        trace: dict[str, Any] = {
            "compiler_sha256": bridge.CODE["current/compiler.cjs"],
            "runtime_sha256": bridge.CODE["current/runtime.cjs"],
            "pages": [
                {
                    "output_sha256": base.digest(b"new visual"),
                    "logical_ms": 1000,
                    "encoded_frames": 30,
                    "encoded_ms": 1000,
                    "audio_mode": "mix",
                }
            ],
        }
        if change == "hash":
            trace["pages"][0]["output_sha256"] = "0" * 64
        elif change == "compiler":
            trace["compiler_sha256"] = "0" * 64
        elif change == "duration":
            trace["pages"][0]["logical_ms"] = 999
        elif change == "frames":
            trace["pages"][0]["encoded_frames"] = 29
        elif change == "audio":
            trace["pages"][0]["audio_mode"] = "silent"
        elif change == "tools":
            Path(tools["ffmpeg"]).write_bytes(b"changed executable")
        elif change == "code":
            (pinned / "code/renderer/render.cjs").write_bytes(b"changed driver")
        put(output / "trace.json", b"[]" if change == "trace" else base.json_bytes(trace))
        return b""

    monkeypatch.setattr(bridge, "command", fake_render)
    monkeypatch.setattr(bridge, "freeze_audio", fake_freeze)
    if change and change != "tuple":
        expected = {"tools": "declarative_tools_changed_during_render", "code": "historical_renderer_changed"}
        with pytest.raises(base.EvalError, match=expected.get(change, "declarative_render_mismatch")):
            bridge.render(run, target, prepared, tools)
        frozen.assert_not_called()
        assert not (target / "audio-preservation.json").exists()
    else:
        bridge.render(run, target, prepared, tools)
        frozen.assert_called_once_with(
            run / "reel1c/v0/render.mp4", target / "render/page-1.mp4", target / "render.mp4"
        )
        assert json.loads((target / "audio-preservation.json").read_bytes())["pcm_equal"] is True
        assert (target / "trace.json").read_bytes() == (target / "render/trace.json").read_bytes()
        assert (pinned / "code/renderer/render.cjs").read_bytes() == original_code
    assert prepared == original_prepared
    assert (run / "reel1c/v0/render.mp4").read_bytes() == b"baseline video"


@pytest.mark.parametrize("prepared", [{}, {"scenes": [None]}, {"scenes": [{"duration_ms": 1000}], "profile": None}])
def test_render_rejects_missing_single_reel_contract(
    pinned: Path,
    tools: dict[str, str],
    prepared: dict[str, Any],
) -> None:
    with pytest.raises(base.EvalError, match="historical_single_reel_required"):
        bridge.render(pinned.parent, pinned.parent / "target", prepared, tools)
