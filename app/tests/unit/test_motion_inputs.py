"""Input provenance, bounded sampling and whole-source audio preservation."""

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.adapters import motion_inputs, motion_media
from app.adapters.material_media import MaterialError
from app.adapters.motion_media import MotionVideoInfo
from app.services.auth import AuthError
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_media import encode, media, probe


def source_snapshot(data=b"original recording", *, logo=None):
    return {
        "tenant_id": "private tenant",
        "business_id": "private business",
        "source": {
            "object_key": "private/source.mp4",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        },
        "logo": logo,
        "references": ["private references"],
        "kit": {"overrides": {"brand_name": "Café de teste"}},
        "brief": "Prepare um convite para conhecer a cafeteria.",
    }


def video_info(*, seconds=1.001, audio="aac"):
    return MotionVideoInfo(seconds, 1080, 1920, 30, 90, "h264", audio)


async def test_inspection_can_retain_original_audio_without_transcription_wav(monkeypatch):
    command = AsyncMock(return_value=encode(probe(audio=True)))
    monkeypatch.setattr(motion_media, "_command", command)
    info, audio = await motion_media.inspect_and_extract_motion_audio(media(), extract_audio=False)
    assert info.audio_codec == "aac" and audio is None
    command.assert_awaited_once()
    assert command.await_args.args[0] == "ffprobe"
    assert not Path(command.await_args.args[-1]).exists()


@pytest.mark.parametrize("duration,expected", [(11200, (0, 2240, 4480, 6720, 8960, 11100)), (1, (0,))])
async def test_source_sampling_is_bounded_deduplicated_and_cleans_private_tempfile(monkeypatch, duration, expected):
    png = frame().png
    paths = []
    times = []

    async def command(*args, output_limit):
        assert args[0] == "ffmpeg" and output_limit == 4 * 1024 * 1024
        assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
        assert args[args.index("-enable_drefs") + 1] == "0"
        assert args[args.index("-frames:v") + 1] == "1"
        assert args[args.index("-vf") + 1] == "scale=360:640:force_original_aspect_ratio=decrease"
        path = Path(args[args.index("-i") + 1])
        assert path.read_bytes() == b"private recording"
        paths.append(path)
        times.append(round(float(args[args.index("-ss") + 1]) * 1000))
        return png

    monkeypatch.setattr(motion_inputs, "_command", command)
    result = await motion_inputs.source_frames(b"private recording", duration)
    assert tuple(times) == expected == tuple(item.ms for item in result)
    assert all(item.png == png and item.sha256 == hashlib.sha256(png).hexdigest() for item in result)
    assert all(not path.exists() for path in paths)


@pytest.mark.parametrize("failure", ["invalid", "tool"])
async def test_bad_source_evidence_fails_and_removes_private_temporary_file(monkeypatch, failure):
    paths = []

    async def command(*args, **kwargs):
        paths.append(Path(args[args.index("-i") + 1]))
        if failure == "tool":
            raise MaterialError("MOTION_MEDIA_TIMEOUT", retryable=True)
        return b"not a PNG"

    monkeypatch.setattr(motion_inputs, "_command", command)
    with pytest.raises((AuthError, MaterialError), match="MOTION_SOURCE_FRAME_INVALID|MOTION_MEDIA_TIMEOUT"):
        await motion_inputs.source_frames(b"private recording", 11200)
    assert len(paths) == 1 and not paths[0].exists()


@pytest.mark.parametrize("audio,with_logo", [(None, False), ("aac", True)])
async def test_preparation_preserves_source_audio_and_exposes_no_private_storage_keys(monkeypatch, audio, with_logo):
    data, png = b"original recording", frame().png
    logo = {"object_key": "private/logo.png", "sha256": hashlib.sha256(png).hexdigest(), "size_bytes": len(png)}
    snapshot = source_snapshot(data, logo=logo if with_logo else None)
    store = AsyncMock()
    store.get_video.return_value, store.get_image.return_value = data, png
    inspect = AsyncMock(return_value=(video_info(audio=audio), None))
    samples = (frame(ms=0), frame(ms=900))
    sampling = AsyncMock(return_value=samples)
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", inspect)
    monkeypatch.setattr(motion_inputs, "source_frames", sampling)
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    inspect.assert_awaited_once()
    assert inspect.await_args.kwargs == {"extract_audio": False}
    assert inspect.await_args.args[0].data == data
    sampling.assert_awaited_once_with(data, 1000)
    assert prepared.duration_ms == 1034 and prepared.source_frames == samples
    source = prepared.assets[0]
    assert source.id == "assets/source.mp4" and source.data == data
    assert source.sha256 == hashlib.sha256(data).hexdigest()
    assert [asset.id for asset in prepared.assets[1:3]] == ["assets/DejaVuSans.ttf", "assets/DejaVuSerif.ttf"]
    assert all(asset.sha256 == hashlib.sha256(asset.data).hexdigest() for asset in prepared.assets)
    assert prepared.context["kit"] == snapshot["kit"]
    assert not {"tenant_id", "business_id", "references", "logo"} & prepared.context.keys()
    assert "private/" not in str(prepared.context) and "object_key" not in str(prepared.context)
    assert prepared.context["source"]["rotation"] == 90
    assert prepared.context["source"]["duration_ms"] == 1000
    assert prepared.context["source"]["has_audio"] == (audio is not None)
    assert prepared.context["transcript"] is None and len(prepared.context["limitations"]) == 2
    assert prepared.context["authorized_audio"] == prepared.audio
    assert prepared.context["output"] == {"width": 720, "height": 1280, "fps": 30, "duration_ms": 1034}
    if audio:
        assert prepared.audio == {
            "mode": "mix",
            "tracks": [
                {
                    "asset_id": "assets/source.mp4",
                    "offset_ms": 0,
                    "trim_start_ms": 0,
                    "trim_end_ms": 1000,
                    "volume": 1.0,
                }
            ],
        }
        assert prepared.assets[-1].id == "assets/logo.png" and prepared.assets[-1].data == png
        store.get_image.assert_awaited_once_with("private/logo.png")
    else:
        assert prepared.audio == {"mode": "silent", "tracks": []}
        store.get_image.assert_not_awaited()


@pytest.mark.parametrize("field,value", [("size_bytes", 1), ("sha256", "0" * 64)])
async def test_changed_source_bytes_are_rejected_before_media_inspection(monkeypatch, field, value):
    snapshot = source_snapshot()
    snapshot["source"][field] = value
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    inspect = AsyncMock()
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", inspect)
    with pytest.raises(AuthError, match="MOTION_SOURCE_BYTES_CHANGED"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    inspect.assert_not_awaited()


@pytest.mark.parametrize("field,value", [("size_bytes", 1), ("sha256", "0" * 64)])
async def test_changed_logo_bytes_are_rejected_before_sampling(monkeypatch, field, value):
    png = frame().png
    logo = {"object_key": "private/logo.png", "sha256": hashlib.sha256(png).hexdigest(), "size_bytes": len(png)}
    logo[field] = value
    store = AsyncMock()
    store.get_video.return_value, store.get_image.return_value = b"original recording", png
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    samples = AsyncMock()
    monkeypatch.setattr(motion_inputs, "source_frames", samples)
    with pytest.raises(AuthError, match="MOTION_LOGO_BYTES_CHANGED"):
        await motion_inputs.MotionInputLoader(store).prepare(source_snapshot(logo=logo))
    samples.assert_not_awaited()


@pytest.mark.parametrize("seconds,valid", [(59.999, True), (60.001, False)])
async def test_rounding_up_cannot_truncate_or_silently_exceed_duration_cap(monkeypatch, seconds, valid):
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    monkeypatch.setattr(
        motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(seconds=seconds), None))
    )
    samples = AsyncMock(return_value=(frame(),))
    monkeypatch.setattr(motion_inputs, "source_frames", samples)
    if valid:
        result = await motion_inputs.MotionInputLoader(store).prepare(source_snapshot())
        assert result.duration_ms == 60000
    else:
        with pytest.raises(AuthError, match="MOTION_SOURCE_TOO_LONG"):
            await motion_inputs.MotionInputLoader(store).prepare(source_snapshot())
        samples.assert_not_awaited()


@pytest.mark.parametrize("failure", [None, "changed", "invalid", "wrong_format", "limit"])
async def test_collection_materials_are_verified_and_get_private_key_free_previews(monkeypatch, failure):
    png = frame().png if failure != "invalid" else b"not an image"
    if failure == "wrong_format":
        import io

        from PIL import Image

        output = io.BytesIO()
        Image.open(io.BytesIO(png)).convert("RGB").save(output, "JPEG")
        png = output.getvalue()
    snapshot = source_snapshot()
    snapshot["collection_photos"] = [
        {
            "id": "synthetic",
            "object_key": "private/collection.png",
            "sha256": hashlib.sha256(png).hexdigest(),
            "size_bytes": len(png),
            "title": "Produto real",
            "version": 2,
            "item_id": "item",
        }
    ]
    if failure == "changed":
        snapshot["collection_photos"][0]["sha256"] = "0" * 64
    elif failure == "limit":
        snapshot["collection_photos"] *= 5
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    store.get_image.return_value = png
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(),)))
    if failure:
        with pytest.raises(AuthError, match="MOTION_COLLECTION_PHOTO_"):
            await motion_inputs.MotionInputLoader(store).prepare(snapshot)
        return
    value = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    asset_id, preview = value.asset_previews[0]
    assert asset_id == "assets/photo-synthetic.png"
    assert next(asset.data for asset in value.assets if asset.id == asset_id) == png
    assert preview.sha256 == hashlib.sha256(preview.png).hexdigest()
    assert value.context["available_materials"][0]["role"] == "product"
    assert "private/" not in str(value.context) and "object_key" not in str(value.context)


@pytest.mark.parametrize("invalid", [False, True])
async def test_reviewed_speech_survives_preparation_without_transcribing_or_changing_audio(monkeypatch, invalid):
    from app.tests.unit.test_motion_speech import timing_data

    snapshot = source_snapshot()
    timing = timing_data()
    timing["source_sha256"] = snapshot["source"]["sha256"]
    if invalid:
        timing["cues"][-1]["end_ms"] = 1001
    snapshot["request"] = {"speech_timing": timing}
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(),)))
    if invalid:
        with pytest.raises(AuthError, match="MOTION_SPEECH_SOURCE_INVALID"):
            await motion_inputs.MotionInputLoader(store).prepare(snapshot)
        return
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert prepared.context["transcript"]["cues"] == timing["cues"]
    assert prepared.context["transcript"]["provenance"] == "owner_reviewed"
    assert prepared.audio["tracks"][0]["volume"] == 1
    assert prepared.audio["tracks"][0]["offset_ms"] == 0
    assert "No transcript" not in prepared.context["limitations"][0]


async def test_explicit_evolution_needs_scoped_resolver_and_uses_it_only_when_requested(monkeypatch):
    from app.services import motion_evolution_inputs

    snapshot = source_snapshot()
    snapshot["evolution"] = {"synthetic_selection": True}
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(),)))
    resolve = AsyncMock(return_value="scoped evolution result")
    monkeypatch.setattr(motion_evolution_inputs, "load_evolution", resolve)
    with pytest.raises(AuthError, match="EVOLUTION_RESOLVER_REQUIRED"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    resolve.assert_not_awaited()
    scoped = object()
    assert await motion_inputs.MotionInputLoader(store, scoped).prepare(snapshot) == "scoped evolution result"
    assert resolve.await_args.args[1:] == (snapshot["evolution"], scoped, store)
