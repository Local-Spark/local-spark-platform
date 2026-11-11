"""Bounded, local-only motion media inspection."""

import asyncio
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.adapters import motion_media as motion
from app.adapters.material_media import FetchedMedia, MaterialError


def media(data=b"video", mime="video/mp4", digest=None):
    return FetchedMedia(data, mime, digest if digest is not None else hashlib.sha256(data).hexdigest())


def probe(audio=True):
    streams = [{"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920, "avg_frame_rate": "30/1"}]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": "aac"})
    return {"streams": streams, "format": {"duration": "59.5"}}


def encode(obj):
    return json.dumps(obj).encode()


@pytest.mark.parametrize(
    "candidate,code",
    [
        (media(b""), "MOTION_MEDIA_INVALID"),
        (media(b"x" * 11), "MOTION_MEDIA_SIZE_EXCEEDED"),
        (media(mime="audio/mp4"), "MOTION_MEDIA_TYPE_UNSUPPORTED"),
        (media(digest="0" * 64), "MOTION_MEDIA_HASH_MISMATCH"),
    ],
)
async def test_rejects_input_before_subprocess(monkeypatch, candidate, code):
    monkeypatch.setattr(motion, "MAX_INPUT_BYTES", 10)
    runner = AsyncMock()
    monkeypatch.setattr(motion, "_command", runner)
    with pytest.raises(MaterialError, match=code):
        await motion.inspect_and_extract_motion_audio(candidate)
    runner.assert_not_called()


@pytest.mark.parametrize("with_audio", [True, False])
async def test_probe_and_extract_cleanup_workspace(monkeypatch, with_audio):
    calls = []

    async def command(*args, output_limit):
        calls.append((args, output_limit))
        if args[0] == "ffprobe":
            assert "-protocol_whitelist" in args and "file,pipe" in args
            assert "-enable_drefs" in args
            assert Path(args[-1]).read_bytes() == b"video"
            return encode(probe(with_audio))
        assert args[0] == "ffmpeg" and "pipe:1" in args
        return b"RIFF-synthetic"

    monkeypatch.setattr(motion, "_command", command)
    info, audio = await motion.inspect_and_extract_motion_audio(media(mime="video/3gpp"))
    assert info.duration_seconds == 59.5 and info.fps == 30
    assert info.audio_codec == ("aac" if with_audio else None)
    assert audio == (b"RIFF-synthetic" if with_audio else None)
    assert len(calls) == (2 if with_audio else 1)
    assert not Path(calls[0][0][-1]).exists()


async def test_cancelled_inspection_cleans_workspace(monkeypatch):
    paths = []

    async def command(*args, output_limit):
        paths.append(Path(args[-1]))
        raise asyncio.CancelledError

    monkeypatch.setattr(motion, "_command", command)
    with pytest.raises(asyncio.CancelledError):
        await motion.inspect_and_extract_motion_audio(media())
    assert len(paths) == 1 and not paths[0].exists()


async def test_extraction_failure_does_not_return_fake_audio(monkeypatch):
    runner = AsyncMock(side_effect=[encode(probe()), b""])
    monkeypatch.setattr(motion, "_command", runner)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_INVALID"):
        await motion.inspect_and_extract_motion_audio(media())


@pytest.mark.parametrize("rotation,expected", [(90, 90), (-90, 270), (360, 0)])
def test_valid_rotation(rotation, expected):
    item = probe()
    item["streams"][0]["side_data_list"] = [{"rotation": rotation}]
    info = motion._parse_probe(encode(item))
    assert info.rotation == expected
    assert info.video_codec == "h264" and info.audio_codec == "aac"


def test_tag_rotation_without_audio():
    item = probe(False)
    item["streams"][0]["tags"] = {"rotate": "180"}
    assert motion._parse_probe(encode(item)).rotation == 180


@pytest.mark.parametrize(
    "mutate,code",
    [
        (lambda p: p.update(streams=[]), "MOTION_MEDIA_INVALID"),
        (lambda p: p.update(streams="bad"), "MOTION_MEDIA_INVALID"),
        (lambda p: p.update(format="bad"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"].append(copy.deepcopy(p["streams"][0])), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"].append(copy.deepcopy(p["streams"][1])), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(codec_name=""), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][1].update(codec_name=""), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(width=True), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(height=0), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(width=10000), "MOTION_MEDIA_DIMENSIONS_EXCEEDED"),
        (lambda p: p["format"].update(duration="60.01"), "MOTION_MEDIA_DURATION_EXCEEDED"),
        (lambda p: p["format"].update(duration="NaN"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["format"].update(duration="Inf"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["format"].update(duration="0"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["format"].update(duration=True), "MOTION_MEDIA_INVALID"),
        (lambda p: p["format"].update(duration="bad"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(avg_frame_rate="0/0"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(avg_frame_rate=True), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(avg_frame_rate="0/1"), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(side_data_list=[{"rotation": "NaN"}]), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(side_data_list=[{"rotation": 45}]), "MOTION_MEDIA_INVALID"),
        (
            lambda p: p["streams"][0].update(side_data_list=[{"rotation": 90}, {"rotation": 180}]),
            "MOTION_MEDIA_INVALID",
        ),
        (lambda p: p["streams"][0].update(side_data_list=["bad"]), "MOTION_MEDIA_INVALID"),
        (lambda p: p["streams"][0].update(tags="bad"), "MOTION_MEDIA_INVALID"),
    ],
)
def test_rejects_invalid_probe(mutate, code):
    item = probe()
    mutate(item)
    with pytest.raises(MaterialError, match=code):
        motion._parse_probe(encode(item))


@pytest.mark.parametrize("raw", [b"{", b"\xff", b"[]", b"{}"])
def test_rejects_malformed_json(raw):
    with pytest.raises(MaterialError, match="MOTION_MEDIA_INVALID"):
        motion._parse_probe(raw)


async def test_command_bounds_output_and_exit_status():
    assert await motion._command(sys.executable, "-c", "print('ok')", output_limit=20) == b"ok\n"
    with pytest.raises(MaterialError, match="MOTION_MEDIA_OUTPUT_TOO_LARGE"):
        await motion._command(sys.executable, "-c", "print('x'*1000)", output_limit=10)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_INVALID"):
        await motion._command(sys.executable, "-c", "exit(1)", output_limit=10)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_TOOL_UNAVAILABLE"):
        await motion._command("/no/such/command", output_limit=10)


async def test_timeout_and_cancellation_kill_child(monkeypatch):
    child = Mock(returncode=None)

    async def slow_read(_size):
        if child.kill.called:
            return b""
        await asyncio.sleep(30)
        return b""

    child.stdout.read = AsyncMock(side_effect=slow_read)
    child.wait = AsyncMock()
    child.kill = Mock()
    monkeypatch.setattr(motion.asyncio, "create_subprocess_exec", AsyncMock(return_value=child))
    monkeypatch.setattr(motion, "COMMAND_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_TIMEOUT"):
        await motion._command("slow", output_limit=10)
    child.kill.assert_called_once()
    child.kill.reset_mock()
    task = asyncio.create_task(motion._command("slow", output_limit=10))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    child.kill.assert_called_once()


async def test_command_tolerates_child_exit_during_termination(monkeypatch):
    child = Mock(returncode=None)

    async def slow_read(_size):
        if child.kill.called:
            return b""
        await asyncio.sleep(30)
        return b""

    child.stdout.read = AsyncMock(side_effect=slow_read)
    child.wait = AsyncMock()
    child.kill = Mock(side_effect=ProcessLookupError)
    monkeypatch.setattr(motion.asyncio, "create_subprocess_exec", AsyncMock(return_value=child))
    monkeypatch.setattr(motion, "COMMAND_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_TIMEOUT"):
        await motion._command("slow", output_limit=10)
    child.kill.assert_called_once()


async def test_cleanup_timeout_closes_pipe_transport(monkeypatch):
    child = Mock(returncode=None)

    async def slow_read(_size):
        await asyncio.sleep(30)
        return b""

    child.stdout.read = AsyncMock(side_effect=slow_read)
    child.wait = AsyncMock()
    child.kill = Mock()
    child._transport = Mock()
    monkeypatch.setattr(motion.asyncio, "create_subprocess_exec", AsyncMock(return_value=child))
    monkeypatch.setattr(motion, "COMMAND_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(motion, "CLEANUP_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_TIMEOUT"):
        await motion._command("slow", output_limit=10)
    child.kill.assert_called_once()
    child._transport.close.assert_called_once()


async def test_large_output_kills_child_without_deadlock():
    with pytest.raises(MaterialError, match="MOTION_MEDIA_OUTPUT_TOO_LARGE"):
        await asyncio.wait_for(
            motion._command(
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'x' * 10000000); sys.stdout.flush()",
                output_limit=10,
            ),
            timeout=2,
        )


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="local FFmpeg tools unavailable")
@pytest.mark.parametrize("audio", [True, False])
async def test_real_synthetic_mp4(tmp_path, audio):
    path = tmp_path / "synthetic.mp4"
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=5"]
    if audio:
        args += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000"]
    args += ["-t", "1", "-c:v", "mpeg4"]
    if audio:
        args += ["-c:a", "aac"]
    subprocess.run([*args, str(path)], check=True, timeout=20, capture_output=True)
    info, wav = await motion.inspect_and_extract_motion_audio(media(path.read_bytes()))
    assert info.width == 64 and info.height == 64 and info.fps == 5
    assert info.duration_seconds <= 1.1
    assert (wav is not None) == audio
    if wav:
        assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
        assert len(wav) < motion.MAX_WAV_BYTES
