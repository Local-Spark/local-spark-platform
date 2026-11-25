"""Synthetic C capability admission, safe audio edits, replay and review regression."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import _format
from app.adapters.motion_html_renderer import RenderAsset, _audio
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_plan import VideoViewport
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_audio import validate_original_branch
from app.services.motion_review import MotionReviewError, validate_review
from app.services.motion_video_audio import apply_video_audio, compile_video_audio
from app.services.motion_video_capabilities import (
    EDIT_CONTRACT_V3,
    safe_boundary,
    state,
    validate_development,
    validate_edl,
    validate_frame_occupancy,
)
from app.services.motion_video_reel import VIDEO_REEL_CONTRACT_V2, guarded_video_scene_init, validate_video_reel
from app.services.motion_video_scene_visibility import CONTRACT as VISIBILITY
from app.services.motion_video_scene_visibility import scoped_video_scene_init

CTX = {
    "video_reel_contract": VIDEO_REEL_CONTRACT_V2,
    "video_edit_contract": EDIT_CONTRACT_V3,
    "source": {"duration_ms": 6000, "sha256": "a" * 64, "has_audio": False},
}


def case():
    return json.loads(Path("app/tests/fixtures/motion_video_capabilities.json").read_text())


def artifact(data=None):
    return HTMLMotionComposition.model_validate(data or case())


def prepared(context=None):
    return PreparedMotionInput(deepcopy(context or CTX), (), (), 6000, {"mode": "silent", "tracks": []})


def test_canonical_layers_and_shared_storyboard_render_bundle():
    comp = artifact()
    validate_video_reel(comp, CTX, asset_ids={"assets/source.mp4", "assets/logo.png"})
    ctx = {**CTX, "video_scene_visibility_contract": VISIBILITY}
    code = guarded_video_scene_init(comp, ctx, scoped_video_scene_init(comp, ctx, comp.scene_init))
    assert (
        code.index("installVideoSceneVisibilityV1")
        < code.index("installVideoCapabilitiesV1")
        < code.index("installVideoReelV2")
    )
    assert "installVideoEditV1" not in code
    old = _format(HTMLMotionComposition, allow_staging=False, allow_video_layout=True, allow_video_edit=True)
    new = _format(
        HTMLMotionComposition,
        allow_staging=False,
        allow_video_layout=True,
        allow_video_edit=True,
        allow_video_design=True,
    )
    assert "VideoDesign" not in json.dumps(old)
    assert "VideoDesign" in json.dumps(new)
    assert old["schema"]["$defs"]["VideoLayout"]["properties"]["mode"]["const"] == "cover"


@pytest.mark.parametrize(
    "reel,version",
    [
        ("motion-video-reel-v2", "video-design-v1"),
        ("motion-video-reel-v3", "video-design-v2"),
        ("motion-video-reel-v4", "video-design-v2"),
    ],
)
def test_structured_output_requires_design_for_all_design_reels(reel, version):
    from app.services.motion_video_capabilities import design_schema_enabled, pinned_design_version

    context = {"video_reel_contract": {"version": reel}}
    assert design_schema_enabled(context)
    assert pinned_design_version(context) == version
    fmt = _format(
        HTMLMotionComposition,
        allow_staging=False,
        allow_video_layout=True,
        allow_video_edit=True,
        allow_video_design=True,
        video_design_version=version,
    )
    layout = fmt["schema"]["$defs"]["VideoLayout"]
    design = fmt["schema"]["$defs"]["VideoDesign"]
    assert "design" in layout["properties"]
    assert "design" in layout["required"]
    assert design["properties"]["version"]["const"] == version
    assert layout["properties"]["mode"].get("const") != "cover"


@pytest.mark.parametrize(
    "raw",
    [
        "bad",
        "null",
        "[]",
        '{"x":0}',
        '{"x":true,"y":0,"opacity":1}',
        '{"x":NaN,"y":0,"opacity":1}',
        '{"x":0,"y":0,"opacity":2}',
    ],
)
def test_layer_state_is_bounded_json(raw):
    with pytest.raises(AuthError, match="LAYER_STATE_INVALID"):
        state(raw)


@pytest.mark.parametrize(
    "change,code",
    [
        ("no_plan", "EDITORIAL_DEVELOPMENT_REQUIRED"),
        ("single", "EDITORIAL_DEVELOPMENT_REQUIRED"),
        ("no_layout", "DESIGN_REQUIRED"),
        ("no_design", "DESIGN_REQUIRED"),
        ("extra", "LAYER_ALLOWLIST_INVALID"),
        ("duplicate", "LAYER_ALLOWLIST_INVALID"),
        ("viewport", "VIEWPORT_INVALID"),
        ("background", "BACKGROUND_REQUIRED"),
        ("hidden_background", "BACKGROUND_REQUIRED"),
        ("role", "LAYER_ALLOWLIST_INVALID"),
        ("curve", "LAYER_STATE_INVALID"),
        ("gap", "LAYER_STATE_INVALID"),
        ("end", "LAYER_STATE_INVALID"),
        ("tiny", "EDITORIAL_DEVELOPMENT_REQUIRED"),
        ("hidden", "EDITORIAL_DEVELOPMENT_REQUIRED"),
        ("covered", "EDITORIAL_DEVELOPMENT_REQUIRED"),
        ("cut", "EDL_INVALID"),
        ("no_edit", "EDL_REQUIRED"),
        ("purpose", "EDITORIAL_FUNCTION_REQUIRED"),
        ("crop", "CROP_UNSAFE"),
        ("unknown_source", "EDL_SOURCE_REQUIRED"),
    ],
)
def test_capability_failures_are_specific(change, code):
    data, ctx = case(), deepcopy(CTX)
    scene = data["motion_plan"]["scenes"][1]
    layout = scene["video_layout"]
    layer = layout["design"]["layers"][-1]
    element = scene["elements"][-1]
    if change == "no_plan":
        data.pop("motion_plan")
    elif change == "single":
        data["motion_plan"]["scenes"] = [data["motion_plan"]["scenes"][0]]
        data["motion_plan"]["duration_ms"] = 3000
    elif change == "no_layout":
        scene.pop("video_layout")
    elif change == "no_design":
        layout.pop("design")
    elif change == "extra":
        layout["design"]["layers"].pop()
    elif change == "duplicate":
        layout["design"]["layers"].append(layer)
    elif change == "viewport":
        layout["mode"] = "cover"
    elif change == "background":
        layout["design"]["layers"][0]["box"]["height"] = 0.9
    elif change == "hidden_background":
        scene["elements"][-2]["beats"][0]["end_state"] = '{"x":0,"y":0,"opacity":0}'
    elif change == "role":
        element["role"] = "text"
    elif change == "curve":
        element["beats"][0]["curve"]["kind"] = "ease_out"
    elif change == "gap":
        element["beats"][0]["start_ms"] += 1
    elif change == "end":
        element["beats"][0]["end_ms"] -= 1
    elif change == "tiny":
        element["beats"][0]["end_state"] = '{"x":4,"y":0,"opacity":1}'
    elif change == "hidden":
        element["beats"][0]["start_state"] = '{"x":0,"y":0,"opacity":0}'
    elif change == "covered":
        layer["box"]["y"] = 0.3
    elif change == "cut":
        layout["edit"]["source_out_ms"] = 5990
    elif change == "no_edit":
        layout.pop("edit")
    elif change == "purpose":
        layout["edit"]["purpose"] = "hook"
    elif change == "crop":
        layout["edit"]["crop_to"]["x"] = 0.175
    elif change == "unknown_source":
        ctx["source"].pop("duration_ms")
    with pytest.raises(AuthError, match=code):
        validate_edl(artifact(data), ctx)


def test_partial_beats_cannot_teleport_and_viewport_must_fit():
    data = case()
    beats = data["motion_plan"]["scenes"][1]["elements"][-1]["beats"]
    b = deepcopy(beats[0])
    beats[0]["end_ms"] = 4500
    b["start_ms"] = 4500
    beats.append(b)
    with pytest.raises(AuthError, match="LAYER_STATE_INVALID"):
        validate_edl(artifact(data), CTX)
    with pytest.raises(ValidationError):
        VideoViewport(x=0.8, y=0, width=0.3, height=1)


def measurement(**updates):
    return {
        "asset_id": "assets/source.mp4",
        "sha256": "a" * 64,
        "omitted_active_intervals": 0,
        "decoded_duration_ms": 6000,
        "activity_threshold_dbfs": -50,
        "active_intervals_ms": [[0, 2700], [3300, 6000]],
        **updates,
    }


def audio_context(**updates):
    return {
        **deepcopy(CTX),
        "source": {**CTX["source"], "has_audio": True},
        "audio_assessment": {"measurements": [measurement()]},
        **updates,
    }


def timing(provenance="local_asr_unreviewed", confidence=0.9):
    return dict(
        version="motion-speech-v1",
        source_sha256="a" * 64,
        provenance=provenance,
        alignment="word",
        focus_cue_ids=["first"] if provenance == "owner_reviewed" else [],
        cues=[
            dict(id="first", text="Pausa.", start_ms=0, end_ms=2700, confidence=confidence),
            dict(id="second", text="Venha.", start_ms=3300, end_ms=5900, confidence=confidence),
        ],
    )


@pytest.mark.parametrize(
    "at,valid", [(0, True), (6000, True), (3000, True), (2820, True), (2819, False), (3180, True), (3181, False)]
)
def test_silence_margin_boundaries(at, valid):
    assert safe_boundary(at, audio_context()) is valid


@pytest.mark.parametrize(
    "update",
    [
        {"sha256": "b" * 64},
        {"omitted_active_intervals": 1},
        {"activity_threshold_dbfs": -30},
        {"decoded_duration_ms": 3001},
        {"asset_id": "assets/other.mp4"},
    ],
)
def test_missing_unbound_or_truncated_energy_never_authorizes_cut(update):
    ctx = audio_context()
    ctx["audio_assessment"]["measurements"] = [measurement(**update)]
    assert not safe_boundary(3000, ctx)


def test_asr_full_utterance_gap_and_partial_low_confidence_conflicts():
    assert safe_boundary(3000, audio_context(audio_assessment={}, speech_result=timing()))
    assert not safe_boundary(3000, audio_context(audio_assessment={}, speech_result=timing(confidence=0.5)))
    assert not safe_boundary(3000, audio_context(audio_assessment={}, speech_result=timing("owner_reviewed")))
    assert not safe_boundary(5990, audio_context(audio_assessment={}, speech_result=timing()))
    t = timing()
    t["cues"][0]["end_ms"] = 3000
    assert not safe_boundary(3000, audio_context(speech_result=t))


def audio_case():
    d = case()
    d["audio"] = {
        "mode": "mix",
        "tracks": [dict(asset_id="assets/source.mp4", offset_ms=0, trim_start_ms=0, trim_end_ms=6000, volume=1)],
    }
    return d


def test_remontage_speech_safe_and_actual_audio_clock():
    d = audio_case()
    for s in d["motion_plan"]["scenes"]:
        s["video_layout"]["edit"].update(source_in_ms=3000 - s["start_ms"], source_out_ms=6000 - s["start_ms"])
    a = artifact(d)
    ctx = audio_context()
    validate_edl(a, ctx)
    with pytest.raises(AuthError, match="SPEECH_CUT_UNSAFE"):
        validate_edl(a, {**ctx, "audio_assessment": {}})
    p = replace(prepared(ctx), audio=d["audio"])
    out = apply_video_audio(p, a)
    assert [t["trim_start_ms"] for t in out.soundtrack["tracks"]] == [3000, 0]
    assert [t["offset_ms"] for t in out.soundtrack["tracks"]] == [0, 3000]
    validate_original_branch(out.soundtrack, p.audio, edl=out.context["video_audio_edl"])
    with pytest.raises(AuthError, match="ORIGINAL_AUDIO_CHANGED"):
        validate_original_branch(out.soundtrack, p.audio)
    altered = deepcopy(out.soundtrack)
    altered["tracks"][0]["role"] = "music"
    with pytest.raises(AuthError, match="ORIGINAL_AUDIO_CHANGED"):
        validate_original_branch(altered, p.audio, edl=[])
    assets = {"assets/source.mp4": RenderAsset("assets/source.mp4", "video/mp4", b"synthetic", "a" * 64)}
    assert _audio(out.soundtrack, assets, 6000) == out.soundtrack
    assert apply_video_audio(out, a) == out


def test_vr6_mixes_authorized_music_with_duck_and_preserves_silence():
    from app.services.motion_photos import music_soundtrack

    d = audio_case()
    a = artifact(d)
    music = music_soundtrack("assets/video-music.mp3", 6000)
    p = replace(prepared(audio_context()), audio=d["audio"], soundtrack=music)
    p = replace(p, context={**p.context, "authorized_soundtrack": music})
    out = apply_video_audio(p, a)
    assert out.soundtrack["ducking"] and out.context["video_mix_status"] == "music_duck_ready"
    assert len(out.soundtrack["tracks"]) == 3
    silent = apply_video_audio(prepared(), artifact())
    assert silent.soundtrack is None and silent.context["video_mix_status"] == "no_eligible_music"
    no_voice = apply_video_audio(replace(prepared(), context={**CTX, "authorized_soundtrack": music}), artifact())
    assert no_voice.context["video_mix_status"] == "music_ready"
    too_many = {**music, "tracks": music["tracks"] * 17}
    with pytest.raises(AuthError, match="TRACK_LIMIT"):
        compile_video_audio(replace(p, context={**p.context, "video_audio_base": too_many}), a)


def test_review_cannot_call_take_text_crop_adequate():
    from app.tests.unit.test_motion_video_edit import artifact as old_artifact

    job = SimpleNamespace(context=CTX, composition=old_artifact())
    with pytest.raises(MotionReviewError, match="DESIGN_REQUIRED"):
        validate_review(job, SimpleNamespace(verdict="adequate"))
    with pytest.raises(MotionReviewError, match="EDITORIAL_DEVELOPMENT_REQUIRED"):
        validate_review(SimpleNamespace(context=CTX, composition=None), SimpleNamespace(verdict="adequate"))


def test_final_padding_and_speech_continuity_do_not_require_silence():
    d = audio_case()
    d["motion_plan"]["scenes"][-1]["video_layout"]["edit"]["source_out_ms"] = 5976
    ctx = audio_context(audio_assessment={})
    ctx["source"]["duration_ms"] = 5976
    validate_edl(artifact(d), ctx)


def test_short_scene_is_not_counted_as_development():
    d = case()
    # Model-copy isolates this gate from the general timeline schema.
    a = artifact(d)
    scene = a.motion_plan.scenes[0].model_copy(update={"end_ms": 799})
    plan = a.motion_plan.model_copy(update={"scenes": (scene, a.motion_plan.scenes[1])})
    with pytest.raises(AuthError, match="EDITORIAL_DEVELOPMENT_REQUIRED"):
        validate_development(plan)


def test_c_requires_matching_contract_and_runtime_pin(tmp_path, monkeypatch):
    from app.services.motion_video_reel import video_reel_rules

    with pytest.raises(AuthError, match="CONTRACT_CHANGED"):
        video_reel_rules({"video_reel_contract": VIDEO_REEL_CONTRACT_V2})
    from app.services import motion_video_reel

    guard = tmp_path / "video-reel-v1.js"
    (tmp_path / "video-reel-v2.js").write_bytes(motion_video_reel.GUARD_PATH.with_name("video-reel-v2.js").read_bytes())
    (tmp_path / "capabilities-v1.js").write_text("tampered")
    monkeypatch.setattr(motion_video_reel, "GUARD_PATH", guard)
    with pytest.raises(AuthError, match="GUARD_CHANGED"):
        guarded_video_scene_init(artifact(), CTX, "original")


def test_only_licensed_planned_sfx_enter_the_mix():
    from app.schemas.motion_audiovisual import MotionPlannedSound
    from app.tests.unit.test_motion_audiovisual import sound_data

    sound = MotionPlannedSound.model_validate(sound_data())
    a = artifact().model_copy(update={"audiovisual": SimpleNamespace(sounds=(sound,))})
    ctx = {**CTX, "sound_library": {"items": [{"id": sound.candidate_id, "license": "CC0-1.0"}]}}
    out = apply_video_audio(prepared(ctx), a)
    assert out.soundtrack["tracks"][0]["role"] == "effect"
    ctx["sound_library"]["items"][0]["license"] = "unknown"
    with pytest.raises(AuthError, match="SOUND_LICENSE_REQUIRED"):
        compile_video_audio(prepared(ctx), a)


def test_short_edl_reduces_output_and_clamps_music_without_repeating_material():
    from app.services.motion_photos import music_soundtrack
    from app.services.motion_plan import validate_motion_plan

    d = audio_case()
    d["audio"]["tracks"][0]["trim_end_ms"] = 9000
    d["motion_plan"]["scenes"][1]["video_layout"]["edit"].update(source_in_ms=6000, source_out_ms=9000)
    ctx = audio_context()
    ctx["source"]["duration_ms"] = 9000
    ctx["audio_assessment"]["measurements"] = [
        measurement(decoded_duration_ms=9000, active_intervals_ms=[[0, 2700], [6300, 9000]])
    ]
    a = artifact(d)
    validate_motion_plan(a, ctx, duration_ms=9000, asset_ids={"assets/source.mp4", "assets/logo.png"})
    music = music_soundtrack("assets/music.mp3", 9000)
    original = dict(
        asset_id="assets/source.mp4",
        role="original",
        offset_ms=0,
        trim_start_ms=0,
        trim_end_ms=9000,
        volume=1,
        fade_in_ms=0,
        fade_out_ms=0,
    )
    late = {**music["tracks"][0], "offset_ms": 7000, "trim_end_ms": 1000}
    music["tracks"] = [original, *music["tracks"], late]
    p = replace(prepared(ctx), audio=d["audio"], duration_ms=9000, context={**ctx, "authorized_soundtrack": music})
    out = apply_video_audio(p, a)
    assert out.duration_ms == 6000 and out.context["output"]["duration_ms"] == 6000
    assert out.soundtrack["tracks"][-1]["trim_end_ms"] == 6000
    assert len(out.soundtrack["tracks"]) == 3


def test_authorized_foreground_image_is_an_alternative_to_pip():
    d = case()
    scene = d["motion_plan"]["scenes"][1]
    layout = scene["video_layout"]
    layout["mode"] = "cover"
    layout["design"]["viewport"] = dict(x=0, y=0, width=1, height=1)
    layout["design"]["layers"][0]["z_index"] = 11
    layout["design"]["layers"][1]["z_index"] = 12
    scene["elements"][-2].update(role="image", asset_id="assets/support.png")
    validate_development(artifact(d).motion_plan)
    from app.services.motion_plan import validate_motion_plan

    with pytest.raises(AuthError, match="ASSET_UNAVAILABLE"):
        validate_motion_plan(artifact(d), CTX, duration_ms=6000, asset_ids={"assets/source.mp4", "assets/logo.png"})
    validate_motion_plan(
        artifact(d), CTX, duration_ms=6000, asset_ids={"assets/source.mp4", "assets/logo.png", "assets/support.png"}
    )
    # A second layer concealing the moving graphic cannot earn development.
    layout["design"]["layers"][0]["z_index"] = 13
    with pytest.raises(AuthError, match="EDITORIAL_DEVELOPMENT_REQUIRED"):
        validate_development(artifact(d).motion_plan)


def test_shortened_edl_checkpoint_restores_exact_output_duration():
    import hashlib

    from app.schemas.motion_production import MotionConstructionPlan
    from app.services.motion_checkpoint_execution import restore_input
    from app.services.motion_checkpoints import input_manifest
    from app.services.motion_materials import prepare_implementation_materials
    from app.tests.unit.test_motion_ai import frame
    from app.tests.unit.test_motion_illustrations import composition_with_art

    a = artifact().model_copy(update={"scene_direction": composition_with_art().scene_direction})
    png = frame(0).png
    p = replace(
        prepared(),
        duration_ms=9000,
        context={**CTX, "output": {"width": 720, "height": 1280, "fps": 30, "duration_ms": 9000}},
        assets=(RenderAsset("assets/logo.png", "image/png", png, hashlib.sha256(png).hexdigest()),),
    )
    planned = MotionConstructionPlan.model_validate(
        {**a.model_dump(exclude={"html", "scene_init"}), "illustrations": []}
    )
    out = prepare_implementation_materials(planned, apply_video_audio(p, a))
    packet = dict(
        stage="render",
        context=out.context,
        artifact=a.model_dump(mode="json"),
        inputs=input_manifest(out),
        resolved_images=[],
    )
    assert restore_input(p, packet).duration_ms == 6000
    packet["artifact"].pop("motion_plan")
    with pytest.raises(AuthError, match="CHECKPOINT_INPUT_CHANGED"):
        restore_input(p, packet)


@pytest.mark.parametrize("pin", ["video_reel_contract", "video_edit_contract", "video_scene_visibility_contract"])
def test_checkpoint_cannot_downgrade_pins(pin):
    from app.services.motion_checkpoint_execution import restore_input
    from app.services.motion_checkpoints import input_manifest

    p = prepared()
    ctx = {**p.context, pin: {"version": "tampered"}}
    with pytest.raises(AuthError, match="CHECKPOINT_INPUT_CHANGED"):
        restore_input(p, dict(stage="plan", context=ctx, inputs=input_manifest(p)))


def test_renderer_validates_segmented_original_and_duck_separately_from_v2():
    from app.adapters.motion_html_renderer import MotionRenderError
    from app.services.motion_photos import music_soundtrack

    d = audio_case()
    a = artifact(d)
    music = music_soundtrack("assets/music.mp3", 6000)
    p = replace(
        prepared(audio_context()), audio=d["audio"], context={**audio_context(), "authorized_soundtrack": music}
    )
    mix = apply_video_audio(p, a).soundtrack
    assets = {
        id: RenderAsset(id, mime, b"test", "a" * 64)
        for id, mime in [("assets/source.mp4", "video/mp4"), ("assets/music.mp3", "audio/mpeg")]
    }
    assert _audio(mix, assets, 6000) == mix
    for change in ("legacy", "order", "gap"):
        bad = deepcopy(mix)
        if change == "legacy":
            bad["version"] = "motion-audio-v2"
        elif change == "order":
            bad["tracks"] = [bad["tracks"][-1], *bad["tracks"][:-1]]
        else:
            bad["tracks"][1]["offset_ms"] = 2999
        with pytest.raises(MotionRenderError):
            _audio(bad, assets, 6000)


def test_speech_cue_onset_is_projected_from_source_into_edited_scene():
    from app.services.motion_speech import speech_context, validate_speech_plan

    d = audio_case()
    scene = d["motion_plan"]["scenes"][1]
    scene["video_layout"]["edit"].update(source_in_ms=0, source_out_ms=3000)
    scene["elements"][-1]["beats"][0]["speech_cue_id"] = "first"
    t = timing()
    t["cues"] = t["cues"][:1]
    ctx = audio_context(speech_result=t)
    ctx["transcript"] = speech_context(ctx, ctx["source"])
    validate_speech_plan(artifact(d), ctx)
    old = {**ctx}
    old.pop("video_edit_contract")
    with pytest.raises(AuthError, match="SPEECH_BEAT_INVALID"):
        validate_speech_plan(artifact(d), old)


def test_dissolve_requires_full_bleed_cover_on_handoff_pins():
    from copy import deepcopy

    from app.services.motion_video_capabilities import (
        EDIT_CONTRACT_V5,
        _cover_opacity,
        state,
        validate_edl,
        validate_handoff_cover,
    )
    from app.services.motion_video_reel import VIDEO_REEL_CONTRACT_V4

    with pytest.raises(AuthError, match="LAYER_STATE_INVALID"):
        state('{"x":0,"y":0,"opacity":1,"scale":0}')
    with pytest.raises(AuthError, match="HANDOFF_COVER_REQUIRED"):
        validate_handoff_cover(None)

    d = case()
    for scene in d["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
    d["motion_plan"]["scenes"][0]["video_layout"]["edit"]["transition"] = "dissolve"
    with pytest.raises(AuthError, match="HANDOFF_COVER_REQUIRED"):
        validate_handoff_cover(artifact(d).motion_plan)
    d["motion_plan"]["scenes"][0]["video_layout"]["edit"]["transition"] = "cut"
    pip = d["motion_plan"]["scenes"][1]
    pip["video_layout"]["edit"]["transition"] = "fade"
    plan = artifact(d).motion_plan
    assert _cover_opacity(plan.scenes[1], plan.scenes[1].start_ms)
    # Partial opacity and non-cover layer keep sampling honest.
    bg = pip["video_layout"]["design"]["layers"][0]
    element = next(e for e in pip["elements"] if e["id"] == bg["element_id"])
    for beat in element["beats"]:
        beat["start_state"] = '{"x":0,"y":0,"opacity":0.5}'
        beat["end_state"] = '{"x":0,"y":0,"opacity":0.5}'
    assert not _cover_opacity(artifact(d).motion_plan.scenes[1], plan.scenes[1].start_ms)
    for beat in element["beats"]:
        beat["start_state"] = '{"x":0,"y":0,"opacity":1}'
        beat["end_state"] = '{"x":0,"y":0,"opacity":1}'
    bg["z_index"] = 11
    assert not _cover_opacity(artifact(d).motion_plan.scenes[1], plan.scenes[1].start_ms)
    bg["z_index"] = 0
    validate_handoff_cover(artifact(d).motion_plan)
    ctx = {
        "video_reel_contract": VIDEO_REEL_CONTRACT_V4,
        "video_edit_contract": EDIT_CONTRACT_V5,
        "source": deepcopy(CTX["source"]),
    }
    validate_edl(artifact(d), ctx)


def test_unlocked_accepts_pip_or_image_without_forcing_moving_graphic():
    from copy import deepcopy

    from app.services.motion_video_capabilities import validate_development

    d = deepcopy(case())
    for scene in d["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
    # Cover scene keeps distinct signature; PIP scene develops without a moving bar.
    pip = d["motion_plan"]["scenes"][1]
    for beat in pip["elements"][-1]["beats"]:
        beat["start_state"] = '{"x":0,"y":0,"opacity":1}'
        beat["end_state"] = '{"x":0,"y":0,"opacity":1}'
    validate_development(artifact(d).motion_plan, unlocked=True)


def test_unlocked_design_version_and_cover_beat_gap():
    from app.services.motion_video_capabilities import _cover_opacity, validate_development, validate_handoff_cover

    d = case()
    d["motion_plan"]["scenes"][0]["video_layout"]["design"]["version"] = "video-design-v1"
    d["motion_plan"]["scenes"][1]["video_layout"]["design"]["version"] = "video-design-v2"
    with pytest.raises(AuthError, match="DESIGN_REQUIRED"):
        validate_development(artifact(d).motion_plan, unlocked=True)
    d = case()
    for scene in d["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
    pip = d["motion_plan"]["scenes"][1]
    pip["video_layout"]["edit"]["transition"] = "dissolve"
    bg = pip["video_layout"]["design"]["layers"][0]
    element = next(e for e in pip["elements"] if e["id"] == bg["element_id"])
    # Leave a gap at scene end so the edge sample misses every beat.
    for beat in element["beats"]:
        beat["end_ms"] = min(beat["end_ms"], pip["end_ms"] - 50)
    assert not _cover_opacity(artifact(d).motion_plan.scenes[1], pip["end_ms"])
    with pytest.raises(AuthError, match="HANDOFF_COVER_REQUIRED"):
        validate_handoff_cover(artifact(d).motion_plan)


def test_frame_occupancy_rejects_weak_opening_and_wash_pip_canvas():
    from copy import deepcopy

    base = artifact()
    short = base.motion_plan.scenes[0].model_copy(update={"end_ms": 500})
    with pytest.raises(AuthError, match="FRAME_OCCUPANCY_REQUIRED"):
        validate_frame_occupancy(base.motion_plan.model_copy(update={"scenes": (short, *base.motion_plan.scenes[1:])}))

    pip_open = base.motion_plan.scenes[0].model_copy(
        update={
            "video_layout": base.motion_plan.scenes[0].video_layout.model_copy(
                update={
                    "mode": "pip",
                    "design": base.motion_plan.scenes[0].video_layout.design.model_copy(
                        update={"viewport": VideoViewport(x=0.2, y=0.2, width=0.5, height=0.5)}
                    ),
                }
            )
        }
    )
    with pytest.raises(AuthError, match="FRAME_OCCUPANCY_REQUIRED"):
        validate_frame_occupancy(
            base.motion_plan.model_copy(update={"scenes": (pip_open, *base.motion_plan.scenes[1:])})
        )

    d = deepcopy(case())
    for scene in d["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
    pip = d["motion_plan"]["scenes"][1]
    pip["video_layout"]["design"]["viewport"] = {"x": 0.27, "y": 0.27, "width": 0.46, "height": 0.46}
    pip["video_layout"]["design"]["layers"][0]["color"] = "#FFF8EC"
    with pytest.raises(AuthError, match="COLLAGE_BACKGROUND_INVALID"):
        validate_development(artifact(d).motion_plan, unlocked=True)

    ok = deepcopy(case())
    for scene in ok["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
    validate_development(artifact(ok).motion_plan, unlocked=True)


def test_edl_rejects_cosmetic_crop_without_perceptible_change():
    from copy import deepcopy

    from app.services.motion_video_capabilities import EDIT_CONTRACT_V5
    from app.services.motion_video_reel import VIDEO_REEL_CONTRACT_V4

    d = deepcopy(case())
    for scene in d["motion_plan"]["scenes"]:
        scene["video_layout"]["design"]["version"] = "video-design-v2"
        edit = scene["video_layout"]["edit"]
        edit["crop_from"] = {"scale": 1, "x": 0, "y": 0}
        edit["crop_to"] = {"scale": 1, "x": 0, "y": 0}
    ctx = {
        "video_reel_contract": VIDEO_REEL_CONTRACT_V4,
        "video_edit_contract": EDIT_CONTRACT_V5,
        "source": deepcopy(CTX["source"]),
    }
    with pytest.raises(AuthError, match="EDL_COSMETIC"):
        validate_edl(artifact(d), ctx)


def test_dense_sample_times_stay_within_renderer_cap_for_unlocked_video():
    from copy import deepcopy

    from app.services.motion_temporal import POLICY_V2, sample_times
    from app.services.motion_video_capabilities import EDIT_CONTRACT_V5
    from app.services.motion_video_reel import VIDEO_REEL_CONTRACT_V4

    comp = artifact()
    ctx = {
        "video_reel_contract": VIDEO_REEL_CONTRACT_V4,
        "video_edit_contract": EDIT_CONTRACT_V5,
        "creative_contract": {"temporal_review": POLICY_V2},
        "source": deepcopy(CTX["source"]),
    }
    times = sample_times(comp, ctx)
    assert times and len(times) <= 64 and times == tuple(sorted(set(times)))
    mid = (comp.motion_plan.scenes[0].start_ms + comp.motion_plan.scenes[0].end_ms) // 2
    assert any(abs(t - mid) <= 40 for t in times)
