"""Local evidence tests use only synthetic media and local tool processes."""

import copy
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.evals import motion_review_evidence as evidence


@pytest.fixture(scope="module")
def tools():
    local_bin = Path(__file__).resolve().parents[2] / ".local/tools/motion-lab/bin"
    found = {}
    for name in ("ffmpeg", "ffprobe"):
        value = os.environ.get(f"MOTION_TEST_{name.upper()}") or shutil.which(name) or local_bin / name
        assert Path(value).is_file() and os.access(value, os.X_OK), f"local {name} required for motion evidence tests"
        found[name] = str(Path(value).resolve())
    return found


@pytest.fixture
def video(tmp_path, tools):
    output = tmp_path / "synthetic.mp4"
    subprocess.run(
        [
            tools["ffmpeg"],
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x96:rate=10:duration=1.2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=500:sample_rate=44100:duration=1.2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(output),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return output


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def test_extract_real_frames_decode_audio_and_verify(video, tools, tmp_path):
    output = tmp_path / "evidence"
    result = evidence.extract_evidence(video, sha(video), tools, output, extra_times_ms=[250, 500])
    assert [f["timestamp_ms"] for f in result["frames"]] == [0, 250, 500, 1000, 1100]
    assert [f["frame_id"] for f in result["frames"]] == ["f0000", "f0001", "f0002", "f0003", "f0004"]
    assert result["duration_ms"] == 1200
    assert result["width"] == 64 and result["height"] == 96 and result["fps"] == 10
    assert result["technical"]["decode_ok"] is True and result["technical"]["audio_present"] is True
    assert result["technical"]["audio_mean_db"] < 0 and result["technical"]["audio_peak_db"] < 0
    assert json.loads((output / "evidence.json").read_text()) == result
    assert "no perceptual audio" in result["limitations"][0]
    evidence.verify_evidence(result, output)
    (output / result["frames"][0]["path"]).write_bytes(b"tampered")
    with pytest.raises(evidence.EvidenceError, match="evidence_hash_mismatch"):
        evidence.verify_evidence(result, output)


def test_reject_invalid_input_and_dirty_output_before_extraction(video, tools, tmp_path):
    output = tmp_path / "out"
    with pytest.raises(evidence.EvidenceError, match="video_hash_mismatch"):
        evidence.extract_evidence(video, "0" * 64, tools, output)
    assert not output.exists()
    with pytest.raises(evidence.EvidenceError, match="invalid_extra_times"):
        evidence.extract_evidence(video, sha(video), tools, output, extra_times_ms=[-1])
    output.mkdir()
    (output / "do-not-overwrite").write_text("original")
    with pytest.raises(evidence.EvidenceError, match="output_must_be_empty"):
        evidence.extract_evidence(video, sha(video), tools, output)
    assert (output / "do-not-overwrite").read_text() == "original"


def test_manifest_validation_rejects_untrusted_paths_and_wrong_order(video, tools, tmp_path):
    root = tmp_path / "evidence"
    result = evidence.extract_evidence(video, sha(video), tools, root)
    changed = copy.deepcopy(result)
    changed["frames"][0]["path"] = "../sensitive.png"
    with pytest.raises(evidence.EvidenceError, match="invalid_evidence"):
        evidence.verify_evidence(changed, root)
    changed = copy.deepcopy(result)
    changed["frames"].reverse()
    with pytest.raises(evidence.EvidenceError, match="invalid_evidence"):
        evidence.verify_evidence(changed, root)
    changed = copy.deepcopy(result)
    changed["technical"]["audio_peak_db"] = float("inf")
    with pytest.raises(evidence.EvidenceError, match="invalid_evidence"):
        evidence.verify_evidence(changed, root)


def test_redacts_tool_errors_and_uses_restricted_environment(monkeypatch):
    def failed(args, **kwargs):
        assert kwargs["env"] == evidence._ENV
        assert "API_KEY" not in str(kwargs["env"])
        raise subprocess.CalledProcessError(1, args, stderr=b"sensitive provider key")

    monkeypatch.setattr(subprocess, "run", failed)
    with pytest.raises(evidence.EvidenceError, match="local_media_tool_failed") as error:
        evidence._run(["fake"])
    assert "sensitive" not in str(error.value)
    assert evidence._volume(b"mean_volume: -inf dB", b"mean_volume") is None
    assert evidence._volume(b"mean_volume: -12.5 dB", b"mean_volume") == -12.5


def test_silent_video_and_missing_sample_are_not_misrepresented(video, tools, tmp_path):
    silent = tmp_path / "silent.mp4"
    subprocess.run(
        [tools["ffmpeg"], "-nostdin", "-v", "error", "-i", str(video), "-an", "-c:v", "copy", str(silent)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    root = tmp_path / "evidence"
    result = evidence.extract_evidence(silent, sha(silent), tools, root)
    assert result["technical"] == {
        "audio_present": False,
        "decode_ok": True,
        "audio_mean_db": None,
        "audio_peak_db": None,
    }
    changed = copy.deepcopy(result)
    changed["frames"].pop()
    with pytest.raises(evidence.EvidenceError, match="invalid_evidence"):
        evidence.verify_evidence(changed, root)


def test_changed_source_never_produces_committed_manifest(video, tools, tmp_path, monkeypatch):
    original_hash = evidence._hash
    calls = 0

    def altered_hash(path):
        nonlocal calls
        calls += 1
        return original_hash(path) if calls == 1 else "0" * 64

    monkeypatch.setattr(evidence, "_hash", altered_hash)
    output = tmp_path / "evidence"
    with pytest.raises(evidence.EvidenceError, match="video_changed_during_extraction"):
        evidence.extract_evidence(video, sha(video), tools, output)
    assert not (output / "evidence.json").exists()


def test_excess_samples_fail_before_output(video, tools, tmp_path):
    output = tmp_path / "evidence"
    with pytest.raises(evidence.EvidenceError, match="invalid_extra_times"):
        evidence.extract_evidence(video, sha(video), tools, output, extra_times_ms=list(range(131)))
    assert not output.exists()


def test_fractional_duration_does_not_invent_frame_at_eof(tools, tmp_path):
    source = tmp_path / "fractional-duration.mp4"
    subprocess.run(
        [
            tools["ffmpeg"],
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x96:rate=30",
            "-frames:v",
            "284",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    result = evidence.extract_evidence(source, sha(source), tools, tmp_path / "evidence")
    assert result["duration_ms"] == 9467
    assert result["frames"][-1]["timestamp_ms"] == 9433
    assert len(result["frames"]) == 20
