"""Owner-authorized, bounded additions cannot alter the original recording branch."""

import hashlib
from copy import deepcopy
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters import motion_html_renderer, motion_inputs, motion_media
from app.adapters.material_media import FetchedMedia, MaterialError
from app.adapters.motion_html_renderer import RenderAsset
from app.schemas.motion_production import MotionDucking, MotionRequest, MotionSoundEvent
from app.services.auth import AuthError
from app.services.motion_audio import compile_soundtrack, validate_original_branch
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_context_requests import context_case, result  # noqa: F401
from app.tests.unit.test_motion_html_renderer import bundle, output, packed
from app.tests.unit.test_motion_inputs import source_snapshot, video_info
from app.tests.unit.test_motion_orchestrator import unit_case  # noqa: F401


def event_data(identifier=None, **changes):
    return {
        "asset_id": identifier or uuid4(),
        "role": "music",
        "rights_confirmed": True,
        "not_duplicate_of_source": True,
        "trim_start_ms": 0,
        "trim_end_ms": 700,
        "offset_ms": 100,
        "volume": 0.2,
        "fade_in_ms": 100,
        "fade_out_ms": 100,
        **changes,
    }


def original():
    return {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1.0}
        ],
    }


def test_old_request_has_no_new_audio_fields_and_additions_require_explicit_attestations():
    data = {"operation_id": uuid4(), "source_asset_id": uuid4(), "instruction": "Synthetic"}
    assert "sound_events" not in MotionRequest.model_validate(data).model_dump(mode="json")
    for change in (
        {"rights_confirmed": False},
        {"not_duplicate_of_source": False},
        {"rights_confirmed": 1},
        {"fade_in_ms": 701},
        {"trim_end_ms": 0},
        {"volume": True},
        {"volume": 0.1234567},
    ):
        with pytest.raises(ValidationError):
            MotionSoundEvent.model_validate(event_data(**change))
    with pytest.raises(ValidationError):
        MotionRequest.model_validate(
            {**data, "music_ducking": {"threshold": 0.1, "ratio": 4, "attack_ms": 10, "release_ms": 100}}
        )


def test_compile_keeps_the_original_branch_and_rejects_unbound_or_changed_source():
    event = MotionSoundEvent.model_validate(event_data())
    duck = MotionDucking(threshold=0.02, ratio=4, attack_ms=10, release_ms=100)
    materials = {str(event.asset_id): {"asset_id": "assets/music.wav", "sha256": "a" * 64}}
    source = original()
    mixed = compile_soundtrack(source, (event,), duck, materials, 1000)
    assert source == original() and mixed["tracks"][0] == {
        **source["tracks"][0],
        "role": "original",
        "fade_in_ms": 0,
        "fade_out_ms": 0,
    }
    assert mixed["tracks"][1]["role"] == "music" and mixed["ducking"] == duck.model_dump()
    assert compile_soundtrack(source, (), None, {}, 1000) is None
    for changed in (
        {**mixed, "tracks": [{**mixed["tracks"][0], "volume": 0.5}, mixed["tracks"][1]]},
        {**mixed, "tracks": mixed["tracks"] + [mixed["tracks"][0]]},
        {**mixed, "tracks": mixed["tracks"] + [{**mixed["tracks"][0], "role": "effect"}]},
    ):
        with pytest.raises(AuthError, match="ORIGINAL_AUDIO_CHANGED"):
            validate_original_branch(changed, source)
    with pytest.raises(AuthError, match="MATERIAL_UNAVAILABLE"):
        compile_soundtrack(source, (event,), duck, {}, 1000)
    with pytest.raises(AuthError, match="MATERIAL_UNAVAILABLE"):
        compile_soundtrack(source, (event,), duck, materials, 799)
    with pytest.raises(AuthError, match="DUCKING_INVALID"):
        compile_soundtrack({"mode": "silent", "tracks": []}, (event,), duck, materials, 1000)


async def test_preparation_binds_selected_audio_bytes_and_keeps_original_audio(monkeypatch):
    recording, sound = b"synthetic recording", b"synthetic sound"
    audio_id = uuid4()
    event = MotionSoundEvent.model_validate(event_data(audio_id))
    duck = MotionDucking(threshold=0.02, ratio=4, attack_ms=10, release_ms=100)
    snapshot = source_snapshot(recording)
    snapshot["request"] = {"sound_events": [event.model_dump(mode="json")], "music_ducking": duck.model_dump()}
    snapshot["audio_materials"] = [
        {
            "id": str(audio_id),
            "object_key": "private/sound",
            "mime_type": "audio/ogg",
            "size_bytes": len(sound),
            "sha256": hashlib.sha256(sound).hexdigest(),
        }
    ]
    store = AsyncMock()
    store.get_video.return_value = recording
    store.get_audio.return_value = sound
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "inspect_supplemental_audio", AsyncMock(return_value=1.0))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(),)))
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert prepared.audio == original() | {"tracks": [{**original()["tracks"][0], "trim_end_ms": 1000}]}
    assert prepared.soundtrack["tracks"][0]["role"] == "original"
    assert prepared.soundtrack["tracks"][1]["asset_id"] == f"assets/audio-{audio_id}.ogg"
    assert prepared.context["authorized_soundtrack"] == prepared.soundtrack
    assert "private/sound" not in str(prepared.context)
    payload = provider().build_request(replace(request(), context=prepared.context, assets=prepared.assets))
    assert "trilha complementar foi escolhida" in payload["instructions"]
    monkeypatch.setattr(motion_inputs, "inspect_supplemental_audio", AsyncMock(return_value=0.1))
    with pytest.raises(AuthError, match="MATERIAL_TOO_SHORT"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    store.get_audio.return_value = b"changed"
    with pytest.raises(AuthError, match="MATERIAL_CHANGED"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    snapshot["audio_materials"] = []
    with pytest.raises(AuthError, match="MATERIAL_CHANGED"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)


async def test_supplemental_audio_probe_rejects_invalid_media_before_use(monkeypatch):
    raw = b"synthetic audio"
    media = FetchedMedia(raw, "audio/wav", hashlib.sha256(raw).hexdigest())
    command = AsyncMock(
        return_value=b'{"streams":[{"codec_type":"audio","codec_name":"pcm"}],"format":{"duration":"1.25"}}'
    )
    monkeypatch.setattr(motion_media, "_command", command)
    assert await motion_media.inspect_supplemental_audio(media) == 1.25
    assert "file,pipe" in command.await_args.args
    command.return_value = b'{"streams":[{"codec_type":"video","codec_name":"h264"}],"format":{"duration":"1"}}'
    with pytest.raises(MaterialError, match="MOTION_MEDIA_INVALID"):
        await motion_media.inspect_supplemental_audio(media)
    with pytest.raises(MaterialError, match="MOTION_MEDIA_INVALID"):
        await motion_media.inspect_supplemental_audio(FetchedMedia(raw, "audio/wav", "0" * 64))


async def test_audio_context_lookup_is_scoped_and_records_selection(context_case):  # noqa: F811
    c = context_case
    audio_id = uuid4()
    event = MotionSoundEvent.model_validate(event_data(audio_id))
    body = c.body.model_copy(update={"sound_events": (event,)})
    material = {
        "id": audio_id,
        "object_key": "private/audio",
        "mime_type": "audio/ogg",
        "size_bytes": 20,
        "sha256": "e" * 64,
    }
    c.session.execute.side_effect = [result(c.source), result(material), result(c.logo)]
    captured = await c.service.capture(c.session, c.tenant, c.business, body)
    assert captured["audio_materials"][0]["id"] == str(audio_id)
    query, params = c.session.execute.await_args_list[1].args
    assert params == {"tenant": c.tenant, "business": c.business, "audio": audio_id}
    assert "tenant_id=:tenant" in str(query) and "business_id=:business" in str(query)
    assert "kind='audio'" in str(query) and "delete_requested_at IS NULL" in str(query)


def test_renderer_accepts_only_valid_v2_roles_and_protected_source():
    source_data, music_data = b"source", b"music"
    source = RenderAsset("assets/source.mp4", "video/mp4", source_data, hashlib.sha256(source_data).hexdigest())
    music = RenderAsset("assets/music.wav", "audio/wav", music_data, hashlib.sha256(music_data).hexdigest())
    event = MotionSoundEvent.model_validate(event_data())
    plan = compile_soundtrack(original(), (event,), None, {str(event.asset_id): {"asset_id": music.id}}, 1000)
    assets = {source.id: source, music.id: music}
    assert motion_html_renderer._audio(plan, assets, 1000) == plan
    for change in ("source_gain", "source_fade", "duplicate", "missing", "too_long"):
        bad = deepcopy(plan)
        if change == "source_gain":
            bad["tracks"][0]["volume"] = 0.5
        elif change == "source_fade":
            bad["tracks"][0]["fade_in_ms"] = 10
        elif change == "duplicate":
            bad["tracks"].append(bad["tracks"][0])
        elif change == "missing":
            bad["tracks"][1]["asset_id"] = "assets/missing.wav"
        else:
            bad["tracks"][1]["fade_in_ms"] = 701
        with pytest.raises(motion_html_renderer.MotionRenderError):
            motion_html_renderer._audio(bad, assets, 1000)


async def test_compiled_soundtrack_reaches_renderer_with_immutable_original(unit_case):  # noqa: F811
    from app.schemas.motion_production import MotionAudio
    from app.tests.unit.test_motion_ai import composition

    c = unit_case
    event = MotionSoundEvent.model_validate(event_data())
    sound = b"synthetic music"
    music = RenderAsset("assets/music.wav", "audio/wav", sound, hashlib.sha256(sound).hexdigest())
    source_data = b"synthetic video"
    source = RenderAsset("assets/source.mp4", "video/mp4", source_data, hashlib.sha256(source_data).hexdigest())
    mixed = compile_soundtrack(original(), (event,), None, {str(event.asset_id): {"asset_id": music.id}}, 1000)
    prepared = replace(
        c.prepared, assets=(source, music), audio=original(), soundtrack=mixed, context={"authorized_soundtrack": mixed}
    )
    value = composition().model_copy(update={"audio": MotionAudio.model_validate(original())})
    await c.runner.render(c.row, c.token, prepared, 0, value)
    assert c.runner.renderer.render.await_args.args[0].audio == mixed
    assert c.runner.effects.claim.await_args_list[0].args[-1]["soundtrack"] == mixed
    assert prepared.audio == original() and mixed["tracks"][0]["volume"] == 1
    changed = deepcopy(mixed)
    changed["tracks"][0]["volume"] = 0.5
    with pytest.raises(AuthError, match="AUDIO_CONTEXT_CHANGED"):
        await c.runner.render(c.row, c.token, replace(prepared, soundtrack=changed), 0, value)


def test_decoded_v2_result_requires_bounded_loudness_evidence(tmp_path):
    raw = b"synthetic audio"
    source = RenderAsset("assets/source.mp4", "video/mp4", raw, hashlib.sha256(raw).hexdigest())
    sound = RenderAsset("assets/music.wav", "audio/wav", raw, hashlib.sha256(raw).hexdigest())
    event = MotionSoundEvent.model_validate(event_data())
    plan = compile_soundtrack(original(), (event,), None, {str(event.asset_id): {"asset_id": sound.id}}, 1000)
    config = motion_html_renderer._prepare(bundle(assets=(source, sound), audio=plan), tmp_path / "audio")
    header, data = output(config)
    with pytest.raises(motion_html_renderer.MotionRenderError):
        motion_html_renderer._decode(packed(header, data), config)
    header["diagnostics"]["audio_measurements"] = {
        "integrated_lufs": -18.4,
        "sample_peak_dbfs": -3.1,
        "peak_kind": "sample",
        "source": "decoded_output",
    }
    assert (
        motion_html_renderer._decode(packed(header, data), config).diagnostics["audio_measurements"]
        == (header["diagnostics"]["audio_measurements"])
    )
    header["diagnostics"]["audio_measurements"]["sample_peak_dbfs"] = float("nan")
    with pytest.raises(motion_html_renderer.MotionRenderError):
        motion_html_renderer._decode(packed(header, data), config)


def test_renderer_v2_ducking_requires_original_voice_music_and_bounded_controls():
    source = RenderAsset("assets/source.mp4", "video/mp4", b"source", hashlib.sha256(b"source").hexdigest())
    music = RenderAsset("assets/music.wav", "audio/wav", b"music", hashlib.sha256(b"music").hexdigest())
    event = MotionSoundEvent.model_validate(event_data())
    plan = compile_soundtrack(original(), (event,), None, {str(event.asset_id): {"asset_id": music.id}}, 1000)
    plan["ducking"] = {"threshold": 0.1, "ratio": 4, "attack_ms": 10, "release_ms": 100}
    assets = {source.id: source, music.id: music}
    assert motion_html_renderer._audio(plan, assets, 1000) == plan
    for change in (
        "mode",
        "tracks",
        "track_fields",
        "role",
        "source_as_effect",
        "duck_type",
        "duck_fields",
        "without_original",
        "without_music",
        "threshold",
        "ratio",
        "attack",
        "release",
    ):
        bad = deepcopy(plan)
        if change == "mode":
            bad["mode"] = "silent"
        elif change == "tracks":
            bad["tracks"] = []
        elif change == "track_fields":
            bad["tracks"][1]["unknown"] = True
        elif change == "role":
            bad["tracks"][1]["role"] = "unknown"
        elif change == "source_as_effect":
            bad["tracks"][0]["role"] = "effect"
        elif change == "duck_type":
            bad["ducking"] = []
        elif change == "duck_fields":
            bad["ducking"]["unknown"] = 0
        elif change == "without_original":
            bad["tracks"] = bad["tracks"][1:]
        elif change == "without_music":
            bad["tracks"][1]["role"] = "effect"
        elif change == "threshold":
            bad["ducking"]["threshold"] = float("nan")
        elif change == "ratio":
            bad["ducking"]["ratio"] = 21
        elif change == "attack":
            bad["ducking"]["attack_ms"] = 0
        else:
            bad["ducking"]["release_ms"] = 0
        with pytest.raises(motion_html_renderer.MotionRenderError):
            motion_html_renderer._audio(bad, assets, 1000)


def test_sound_compiler_rejects_invalid_original_and_ducking_without_events():
    event = MotionSoundEvent.model_validate(event_data())
    duck = MotionDucking(threshold=0.1, ratio=4, attack_ms=10, release_ms=100)
    with pytest.raises(AuthError, match="DUCKING_INVALID"):
        compile_soundtrack(original(), (), duck, {}, 1000)
    for value in (
        {"mode": "mix", "tracks": []},
        {"mode": "mix", "tracks": [{**original()["tracks"][0], "volume": 0.5}]},
    ):
        with pytest.raises(AuthError, match="ORIGINAL_AUDIO_CHANGED"):
            compile_soundtrack(value, (event,), None, {}, 1000)
    soundtrack = compile_soundtrack(
        original(), (event,), None, {str(event.asset_id): {"asset_id": "assets/music.wav"}}, 1000
    )
    for track, source in (
        ({}, original()),
        (soundtrack, {"mode": "silent", "tracks": []}),
        (soundtrack, {"mode": "mix", "tracks": []}),
    ):
        with pytest.raises(AuthError, match="ORIGINAL_AUDIO_CHANGED"):
            validate_original_branch(track, source)


async def test_missing_authorized_sound_material_stops_context_capture(context_case):  # noqa: F811
    c = context_case
    event = MotionSoundEvent.model_validate(event_data())
    c.session.execute.side_effect = [result(c.source), result(None)]
    with pytest.raises(AuthError, match="AUDIO_MATERIAL_UNAVAILABLE"):
        await c.service.capture(c.session, c.tenant, c.business, c.body.model_copy(update={"sound_events": (event,)}))
