"""Audio energy, binding and local decoding; never infer listening or render a mix."""

import hashlib
import struct
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.adapters import motion_media
from app.adapters.material_media import FetchedMedia, MaterialError
from app.adapters.motion_html_renderer import RenderAsset
from app.services import motion_sound_analysis as analysis
from app.services.auth import AuthError
from app.tests.unit.test_motion_audiovisual import natural_prepared


def pcm(value, count):
    return struct.pack("<" + "h" * count, *([value] * count))


def test_silence_activity_and_peak_measurements_are_not_semantic_or_perceptual_claims():
    silence = analysis.pcm_measurements(pcm(0, 1600))
    assert silence["decoded_duration_ms"] == 100 and silence["active_intervals_ms"] == []
    assert silence["rms_dbfs"] is None and silence["sample_peak_dbfs"] is None
    signal = pcm(0, 1600) + pcm(16384, 160) + pcm(0, 1600) + pcm(32767, 160)
    actual = analysis.pcm_measurements(signal)
    assert actual["active_intervals_ms"] == [[100, 220]]
    assert actual["peak_at_ms"] == 210 and actual["samples_at_full_scale"] == 160
    assert actual["sample_peak_dbfs"] <= 0 and actual["rms_dbfs"] < -10
    assert (
        actual["suitability"] == actual["source_duplication"] == actual["voice_intelligibility"] == "requires_listening"
    )
    assert actual["listening_status"] == "not_listened"
    assert analysis.pcm_measurements(pcm(1000, 1))["decoded_duration_ms"] == 1


@pytest.mark.parametrize("raw", [b"", b"x", b"\0" * (60 * 16000 * 2 + 2)])
def test_invalid_or_overlong_pcm_is_rejected(raw):
    with pytest.raises(AuthError, match="PCM_INVALID"):
        analysis.pcm_measurements(raw)


def test_measurements_handle_byte_order_and_declare_omitted_activity_windows(monkeypatch):
    expected = analysis.pcm_measurements(pcm(1200, 160))
    monkeypatch.setattr(analysis, "sys", SimpleNamespace(byteorder="big"))
    actual = analysis.pcm_measurements(struct.pack(">" + "h" * 160, *([1200] * 160)))
    assert actual["rms_dbfs"] == expected["rms_dbfs"]
    monkeypatch.setattr(analysis, "sys", SimpleNamespace(byteorder="little"))
    signal = (pcm(16000, 160) + pcm(0, 3200)) * 20
    measured = analysis.pcm_measurements(signal)
    assert len(measured["active_intervals_ms"]) == 16 and measured["omitted_active_intervals"] == 4


async def test_real_prepared_assets_are_measured_without_changing_source_or_audio(monkeypatch):
    p = natural_prepared()
    p.context["source"]["has_audio"] = True
    data = b"synthetic video"
    digest = hashlib.sha256(data).hexdigest()
    p.context["source"]["sha256"] = digest
    p = replace(p, assets=(*p.assets, RenderAsset("assets/source.mp4", "video/mp4", data, digest)))
    decode = AsyncMock(return_value=pcm(5000, 1600))
    monkeypatch.setattr(analysis, "decode_analysis_pcm", decode)
    out = await analysis.prepare_sound_assessment(p)
    assert out.assets is p.assets and out.audio is p.audio and out.soundtrack is p.soundtrack
    assert len(out.context["audio_assessment"]["measurements"]) == 3
    assert decode.await_count == 3
    assert {m["sha256"] for m in out.context["audio_assessment"]["measurements"]} == {a.sha256 for a in p.assets}


async def test_legacy_absent_audio_changed_policy_and_missing_bytes(monkeypatch):
    p = natural_prepared()
    p.context["source"]["has_audio"] = False
    legacy = replace(p, context={})
    assert await analysis.prepare_sound_assessment(legacy) is legacy
    bad = replace(p, context={**p.context, "audio_analysis_contract": {}})
    with pytest.raises(AuthError, match="CONTRACT_CHANGED"):
        await analysis.prepare_sound_assessment(bad)
    with pytest.raises(AuthError, match="ASSET_MISSING"):
        await analysis.prepare_sound_assessment(replace(p, assets=()))
    with pytest.raises(AuthError, match="ASSET_CHANGED"):
        await analysis.prepare_sound_assessment(replace(p, assets=(*p.assets, p.assets[0])))
    with pytest.raises(AuthError, match="ASSET_CHANGED"):
        await analysis.prepare_sound_assessment(
            replace(p, assets=(replace(p.assets[0], sha256="0" * 64), *p.assets[1:]))
        )
    monkeypatch.setattr(analysis, "decode_analysis_pcm", AsyncMock(return_value=pcm(0, 160)))
    assert len((await analysis.prepare_sound_assessment(p)).context["audio_assessment"]["measurements"]) == 2
    p.context.pop("sound_library")
    p = replace(p, assets=())
    assert (await analysis.prepare_sound_assessment(p)).context["audio_assessment"]["measurements"] == []


@pytest.mark.parametrize("mime", ["video/mp4", "audio/mpeg", "audio/ogg", "audio/wav"])
async def test_decoder_is_local_bounded_and_cleans_temporary_input(monkeypatch, mime):
    paths = []

    async def command(*args, output_limit):
        path = Path(args[args.index("-i") + 1])
        paths.append(path)
        assert path.read_bytes() == b"synthetic" and output_limit == 60 * 16000 * 2
        assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
        assert "-t" not in args
        return pcm(100, 160)

    monkeypatch.setattr(motion_media, "_command", command)
    media = FetchedMedia(b"synthetic", mime, hashlib.sha256(b"synthetic").hexdigest())
    assert await motion_media.decode_analysis_pcm(media) == pcm(100, 160)
    assert all(not p.exists() for p in paths)


@pytest.mark.parametrize("change", ["type", "hash", "empty", "too_large", "odd_pcm", "empty_pcm"])
async def test_bad_audio_never_enters_measurements(monkeypatch, change):
    data = b"synthetic"
    if change == "empty":
        data = b""
    elif change == "too_large":
        monkeypatch.setattr(motion_media, "MAX_INPUT_BYTES", 1)
    media = FetchedMedia(
        data,
        "image/png" if change == "type" else "audio/mpeg",
        "0" * 64 if change == "hash" else hashlib.sha256(data).hexdigest(),
    )
    monkeypatch.setattr(motion_media, "_command", AsyncMock(return_value=b"x" if change == "odd_pcm" else b""))
    with pytest.raises(MaterialError, match="MOTION_AUDIO_ANALYSIS_"):
        await motion_media.decode_analysis_pcm(media)
