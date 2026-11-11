"""Trusted motion direction to experimental compiler scenes, without effects."""

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from app.schemas.motion import MotionDirection
from app.services.auth import AuthError
from app.services.motion_composition import (
    EXPERIMENTAL_MOTION_CAPABILITIES,
    VerifiedMotionSnapshot,
    VerifiedMotionSource,
    compile_motion_composition,
)
from app.services.motion_skills import resolve_motion_skill
from app.tests.unit.test_motion_schema import carousel, direction, keys, time, transition, typography


def sample(fmt="reel"):
    document = carousel() if fmt == "carousel_motion" else direction()
    document["format"] = fmt
    skill_id, skill_sha, _ = resolve_motion_skill(fmt)
    document["skill"] = {"id": skill_id, "sha256": skill_sha}
    for page in document["pages"]:
        page["audio"] = {"mode": "silent", "speech": "not_present", "tracks": []}
    sources = tuple(
        VerifiedMotionSource(
            id=source["id"],
            kind=source["kind"],
            origin=source["origin"],
            duration_ms=source.get("duration_ms"),
            has_audio=source.get("has_audio"),
            has_speech=False if source["kind"] == "video" else None,
            derived_from_source_id=source.get("derived_from_source_id"),
            sha256="c" * 64,
        )
        for source in document["sources"]
    )
    snapshot = VerifiedMotionSnapshot(
        kit_id="cafe-pausas-v1",
        kit_sha256="d" * 64,
        style_id="style-v1",
        style_sha256="b" * 64,
        font_faces=frozenset({("dejavu-serif", 700)}),
        sources=sources,
    )
    return document, snapshot


@pytest.mark.parametrize("fmt", ["reel", "story_video", "carousel_motion"])
def test_supported_examples_compile_deterministically(fmt):
    document, snapshot = sample(fmt)
    first = compile_motion_composition(document, snapshot=snapshot)
    second = compile_motion_composition(document, snapshot=snapshot)
    assert first == second
    assert len(first.scenes) == (3 if fmt == "carousel_motion" else 1)
    assert first.kit_sha256 == snapshot.kit_sha256
    assert first.source_hashes == tuple((source.id, source.sha256) for source in snapshot.sources)
    scene = first.scenes[0]
    assert set(scene) == {"format", "duration_ms", "background", "layers"}
    assert scene["format"] == fmt
    layer = scene["layers"][0]
    assert layer["source_id"] == str(document["sources"][0]["id"])
    assert layer["frames"][0]["easing"] == "ease_out"
    assert layer["frames"][-1]["easing"] == "linear"
    assert layer["enter"] == {"kind": "cut", "duration_ms": 0}
    if fmt != "carousel_motion":
        assert scene["layers"][-1]["kind"] == "text"
        assert scene["layers"][-1]["text"] == "Uma pausa"
        assert scene["layers"][-1]["id"] != layer["id"]


def test_fades_and_motion_are_preserved_separately_with_no_approximation():
    document, snapshot = sample()
    visual = document["pages"][0]["visual"][0]
    visual["enter"] = transition("fade", 1000)
    visual["exit"] = transition("fade", 1200)
    visual["keyframes"][-1]["state"]["x"] = 1000
    visual["keyframes"][-1]["state"]["opacity"] = 5000
    result = compile_motion_composition(document, snapshot=snapshot).scenes[0]["layers"][0]
    assert result["enter"] == {"kind": "fade", "duration_ms": 1000}
    assert result["exit"] == {"kind": "fade", "duration_ms": 1200}
    assert result["frames"][-1]["x"] == 1000 and result["frames"][-1]["opacity"] == 5000


def test_invalid_model_and_snapshot_are_rejected():
    document, snapshot = sample()
    document["schema_version"] = "not-a-valid-version"
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_INVALID"):
        compile_motion_composition(document, snapshot=snapshot)
    document, snapshot = sample()
    for bad in (replace(snapshot, kit_id="  "), replace(snapshot, kit_sha256="z" * 64)):
        with pytest.raises(AuthError, match="MOTION_COMPOSITION_SNAPSHOT_INVALID"):
            compile_motion_composition(document, snapshot=bad)
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_STYLE_CHANGED"):
        compile_motion_composition(document, snapshot=replace(snapshot, style_sha256="a" * 64))


def test_skill_snapshot_must_match_registered_content_and_format():
    document, snapshot = sample()
    document["skill"]["sha256"] = "0" * 64
    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        compile_motion_composition(document, snapshot=snapshot)


@pytest.mark.parametrize("case", ["missing", "bad_hash", "kind", "origin", "duration", "has_audio", "derived"])
def test_each_source_must_match_authorized_snapshot(case):
    document, snapshot = sample()
    source = snapshot.sources[0]
    if case == "missing":
        changed = replace(snapshot, sources=())
    else:
        fields = {
            "bad_hash": {"sha256": "bad"},
            "kind": {"kind": "image"},
            "origin": {"origin": "asset"},
            "duration": {"duration_ms": 10},
            "has_audio": {"has_audio": False},
            "derived": {"derived_from_source_id": uuid4()},
        }
        changed = replace(snapshot, sources=(replace(source, **fields[case]),))
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SOURCE_CHANGED"):
        compile_motion_composition(document, snapshot=changed)


def test_duplicate_sources_and_untrusted_speech_metadata_are_rejected():
    document, snapshot = sample()
    source = snapshot.sources[0]
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SNAPSHOT_INVALID"):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=(source, source)))
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SNAPSHOT_INVALID"):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=(replace(source, has_speech=1),)))
    changed = replace(source, has_audio=False, has_speech=True)
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SNAPSHOT_INVALID"):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=(changed,)))


@pytest.mark.parametrize("speech", [None, True])
def test_declared_no_speech_requires_matching_trusted_evidence(speech):
    document, snapshot = sample()
    source = replace(snapshot.sources[0], has_speech=speech)
    code = "MOTION_COMPOSITION_SPEECH_UNVERIFIED" if speech is None else "MOTION_COMPOSITION_SPEECH_CHANGED"
    with pytest.raises(AuthError, match=code):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=(source,)))


def test_declared_speech_omission_requires_reason_and_is_not_silently_inferred():
    document, snapshot = sample()
    document["pages"][0]["audio"] = {
        "mode": "silent",
        "speech": "omit",
        "omission_reason": "O pedido solicita uma peça sem fala.",
        "tracks": [],
    }
    source = replace(snapshot.sources[0], has_speech=True)
    assert compile_motion_composition(document, snapshot=replace(snapshot, sources=(source,))).scenes
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SPEECH_CHANGED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_variable_video_speed_cannot_be_silently_discarded():
    document, snapshot = sample()
    visual = document["pages"][0]["visual"][0]
    visual["source_trim"]["end_ms"] = 5000
    visual["playback_rate"] = {"numerator": 1, "denominator": 2}
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_UNSUPPORTED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_compiler_source_duration_limit_is_not_ignored():
    document, snapshot = sample("carousel_motion")
    video = VerifiedMotionSource(
        id=uuid4(),
        kind="video",
        origin="asset",
        duration_ms=60001,
        has_audio=False,
        has_speech=False,
        derived_from_source_id=None,
        sha256="c" * 64,
    )
    document["sources"].append(
        {
            "id": video.id,
            "kind": video.kind,
            "origin": video.origin,
            "duration_ms": video.duration_ms,
            "has_audio": False,
        }
    )
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_UNSUPPORTED"):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=snapshot.sources + (video,)))


def test_text_font_face_must_belong_to_verified_kit():
    document, snapshot = sample()
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_FONT_UNAUTHORIZED"):
        compile_motion_composition(document, snapshot=replace(snapshot, font_faces=frozenset()))


@pytest.mark.parametrize(
    "bad,code", [("😀" * 251, "MOTION_COMPOSITION_UNSUPPORTED"), ("\ud800", "MOTION_COMPOSITION_INVALID")]
)
def test_text_must_fit_compiler_utf16_and_be_encodable(bad, code):
    document, snapshot = sample()
    document["pages"][0]["captions"][0]["text"] = bad
    with pytest.raises(AuthError, match=code):
        compile_motion_composition(document, snapshot=snapshot)


@pytest.mark.parametrize("field", ["caption", "timeline"])
def test_mutated_model_instances_are_revalidated_before_compilation(field):
    document, snapshot = sample()
    direction_model = MotionDirection.model_validate(document)
    if field == "caption":
        direction_model.pages[0].captions[0].text = "\ud800"
    else:
        direction_model.pages[0].visual[0].timeline.end_ms = 60001
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_INVALID"):
        compile_motion_composition(direction_model, snapshot=snapshot)


def test_more_than_64_total_visual_layers_and_captions_are_rejected():
    document, snapshot = sample()
    caption = document["pages"][0]["captions"][0]
    document["pages"][0]["captions"] = [caption] * 64
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_UNSUPPORTED"):
        compile_motion_composition(document, snapshot=snapshot)


@pytest.mark.parametrize("kind", ["rectangle", "circle", "text"])
def test_graphic_layers_translate_with_authorized_font(kind):
    document, snapshot = sample("carousel_motion")
    graphic = {
        "kind": kind,
        "text": "Pausa" if kind == "text" else None,
        "typography": typography() if kind == "text" else None,
        "fill": None if kind == "text" else "#FFFFFF",
    }
    document["pages"][0]["visual"].append(
        {
            "kind": "graphic",
            "timeline": time(0, 5000),
            "graphic": graphic,
            "keyframes": keys(5000),
            "enter": transition(),
            "exit": transition(),
            "direction": "Camada",
        }
    )
    result = compile_motion_composition(document, snapshot=snapshot).scenes[0]["layers"][1]
    assert result["kind"] == kind
    assert result["text"] == "Pausa" if kind == "text" else result["color"] == "#FFFFFF"


def test_unimplemented_rounded_corners_are_not_silently_ignored():
    document, snapshot = sample("carousel_motion")
    document["pages"][0]["visual"].append(
        {
            "kind": "graphic",
            "timeline": time(0, 5000),
            "graphic": {"kind": "rectangle", "fill": "#FFFFFF", "corner_radius": 500},
            "keyframes": keys(5000),
            "enter": transition(),
            "exit": transition(),
            "direction": "Camada",
        }
    )
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_UNSUPPORTED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_capabilities_are_explicit():
    assert EXPERIMENTAL_MOTION_CAPABILITIES.audio_plan
    assert not EXPERIMENTAL_MOTION_CAPABILITIES.audio
    assert not EXPERIMENTAL_MOTION_CAPABILITIES.variable_playback
    assert EXPERIMENTAL_MOTION_CAPABILITIES.independent_fade
    assert EXPERIMENTAL_MOTION_CAPABILITIES.captions_as_text


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is needed for the local compiler contract test")
@pytest.mark.parametrize("fmt", ["reel", "story_video", "carousel_motion"])
def test_scenes_compile_with_the_real_local_javascript_compiler(fmt):
    document, snapshot = sample(fmt)
    visual = document["pages"][0]["visual"][0]
    visual["enter"] = transition("fade", 200)
    visual["exit"] = transition("fade", 300)
    visual["keyframes"][-1]["state"]["x"] = 500
    visual["keyframes"][-1]["state"]["opacity"] = 5000
    scenes = compile_motion_composition(document, snapshot=snapshot).scenes
    profile = (
        {"width_px": 1080, "height_px": 1350, "fps": 30}
        if fmt == "carousel_motion"
        else {
            "width_px": 720,
            "height_px": 1280,
            "fps": 30,
        }
    )
    sources = [
        [str(source.id), {"kind": source.kind, "duration_ms": source.duration_ms}] for source in snapshot.sources
    ]
    request = {
        "scenes": scenes,
        "profile": profile,
        "sources": sources,
        "fonts": [face[0] for face in snapshot.font_faces],
    }
    compiler = Path(__file__).resolve().parents[2] / "assets" / "motion_renderer" / "compiler.cjs"
    script = (
        "const fs=require('node:fs'); const {compileScene}=require(process.argv[1]);"
        "const x=JSON.parse(fs.readFileSync(0,'utf8'));"
        "const reg={fonts:new Set(x.fonts),sources:new Map(x.sources)};"
        "const s=x.scenes.map(scene=>compileScene(scene,x.profile,reg));"
        "process.stdout.write(JSON.stringify(s.map(item=>({format:item.format,layers:item.layers.length}))));"
    )
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(compiler)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert json.loads(result.stdout) == [{"format": fmt, "layers": len(scene["layers"])} for scene in scenes]


def speech_mix():
    """Fictional original voice plus a separately authorized music asset."""
    document, snapshot = sample()
    video = snapshot.sources[0]
    video = replace(video, has_speech=True)
    music_id = uuid4()
    music = VerifiedMotionSource(
        id=music_id,
        kind="audio",
        origin="asset",
        duration_ms=10000,
        has_audio=None,
        has_speech=False,
        derived_from_source_id=None,
        sha256="e" * 64,
    )
    document["sources"].append({"id": music_id, "kind": "audio", "origin": "asset", "duration_ms": 10000})
    voice = {
        "source_id": video.id,
        "source_trim": time(1000, 4000),
        "timeline": time(2000, 5000),
        "playback_rate": {"numerator": 1, "denominator": 1},
        "role": "recorded_voice",
        "gain_mdb": 0,
        "fade_in_ms": 100,
        "fade_out_ms": 150,
        "direction": "fala original",
    }
    track = {
        "source_id": music_id,
        "source_trim": time(500, 8500),
        "timeline": time(1000, 9000),
        "playback_rate": {"numerator": 1, "denominator": 1},
        "role": "music",
        "gain_mdb": -6000,
        "fade_in_ms": 500,
        "fade_out_ms": 500,
        "direction": "trilha",
    }
    document["pages"][0]["audio"] = {"mode": "mix", "speech": "preserve", "tracks": [voice, track]}
    return document, replace(snapshot, sources=(video, music))


def test_audio_plan_preserves_voice_music_hashes_offsets_cuts_and_fades():
    from dataclasses import asdict

    document, snapshot = speech_mix()
    result = compile_motion_composition(document, snapshot=snapshot)
    audio = result.audio_plans[0]
    assert audio.mode == "mix" and audio.speech == "preserve"
    assert audio.omission_reason is None and audio.speech_semantics_verified is False
    voice, music = audio.tracks
    assert voice.source_id == str(snapshot.sources[0].id) and voice.sha256 == "c" * 64
    assert voice.source_kind == "video" and voice.role == "recorded_voice" and voice.source_has_speech is True
    assert (voice.trim_start_ms, voice.trim_end_ms, voice.timeline_start_ms, voice.timeline_end_ms) == (
        1000,
        4000,
        2000,
        5000,
    )
    assert (voice.fade_in_ms, voice.fade_out_ms, voice.gain_mdb) == (100, 150, 0)
    assert (music.source_kind, music.role, music.sha256, music.gain_mdb) == ("audio", "music", "e" * 64, -6000)
    assert (music.trim_start_ms, music.timeline_start_ms, music.fade_in_ms, music.fade_out_ms) == (500, 1000, 500, 500)
    assert voice.rate_numerator == voice.rate_denominator == 1
    assert len({voice.id, music.id}) == 2
    assert json.loads(json.dumps(asdict(audio)))["tracks"][0]["timeline_start_ms"] == 2000
    assert compile_motion_composition(document, snapshot=snapshot) == result


def test_explicit_silent_plan_has_no_implicit_audio_track():
    document, snapshot = sample()
    plan = compile_motion_composition(document, snapshot=snapshot).audio_plans[0]
    assert plan.mode == "silent" and plan.speech == "not_present" and plan.tracks == ()
    assert plan.speech_semantics_verified is False


def test_mixed_music_can_explicitly_omit_recording_speech_without_fake_confirmation():
    document, snapshot = speech_mix()
    audio = document["pages"][0]["audio"]
    audio.update(speech="omit", omission_reason="O pedido descreve uma versão sem fala.", tracks=[audio["tracks"][1]])
    result = compile_motion_composition(document, snapshot=snapshot).audio_plans[0]
    assert result.speech == "omit" and result.omission_reason == "O pedido descreve uma versão sem fala."
    assert len(result.tracks) == 1 and result.tracks[0].role == "music"


def test_undeclared_speech_omission_fails_closed():
    document, snapshot = speech_mix()
    audio = document["pages"][0]["audio"]
    audio.update(speech="not_present", tracks=[audio["tracks"][1]])
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SPEECH_CHANGED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_omit_speech_cannot_include_original_voice_audio():
    document, snapshot = speech_mix()
    audio = document["pages"][0]["audio"]
    audio.update(speech="omit", omission_reason="Versão sem fala.")
    audio["tracks"][0]["role"] = "original_sound"
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_SPEECH_CHANGED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_missing_original_audio_never_becomes_silent_or_new_track():
    document, snapshot = speech_mix()
    document["sources"][0]["has_audio"] = False
    source = replace(snapshot.sources[0], has_audio=False, has_speech=False)
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_INVALID"):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=(source, snapshot.sources[1])))


@pytest.mark.parametrize("change", ["missing", "false"])
def test_recorded_voice_needs_trusted_speech_evidence(change):
    document, snapshot = speech_mix()
    video = snapshot.sources[0]
    audio_id = uuid4()
    derived = VerifiedMotionSource(
        id=audio_id,
        kind="audio",
        origin="asset",
        duration_ms=10000,
        has_audio=None,
        has_speech=None if change == "missing" else False,
        derived_from_source_id=video.id,
        sha256="f" * 64,
    )
    document["sources"].append(
        {"id": audio_id, "kind": "audio", "origin": "asset", "duration_ms": 10000, "derived_from_source_id": video.id}
    )
    document["pages"][0]["audio"]["tracks"][0]["source_id"] = audio_id
    code = "MOTION_COMPOSITION_SPEECH_UNVERIFIED" if change == "missing" else "MOTION_COMPOSITION_SPEECH_CHANGED"
    with pytest.raises(AuthError, match=code):
        compile_motion_composition(document, snapshot=replace(snapshot, sources=snapshot.sources + (derived,)))


def test_verified_extracted_voice_records_derivation():
    document, snapshot = speech_mix()
    video = snapshot.sources[0]
    audio_id = uuid4()
    derived = VerifiedMotionSource(
        id=audio_id,
        kind="audio",
        origin="asset",
        duration_ms=10000,
        has_audio=None,
        has_speech=True,
        derived_from_source_id=video.id,
        sha256="f" * 64,
    )
    document["sources"].append(
        {"id": audio_id, "kind": "audio", "origin": "asset", "duration_ms": 10000, "derived_from_source_id": video.id}
    )
    document["pages"][0]["audio"]["tracks"][0]["source_id"] = audio_id
    plan = compile_motion_composition(
        document, snapshot=replace(snapshot, sources=snapshot.sources + (derived,))
    ).audio_plans[0]
    voice = plan.tracks[0]
    assert voice.source_id == str(audio_id) and voice.source_derived_from_id == str(video.id)
    assert voice.sha256 == "f" * 64 and voice.source_has_speech is True


@pytest.mark.parametrize("change", ["unknown_parent", "silent_parent"])
def test_derived_voice_needs_parent_speech_evidence(change):
    document, snapshot = speech_mix()
    parent = replace(snapshot.sources[0], has_speech=None if change == "unknown_parent" else False)
    # Use an unrelated image for the visual page so the derived audio parent
    # evidence, not the visible video guard, is what is being exercised.
    document["format"] = "carousel_motion"
    image_id, audio_id = uuid4(), uuid4()
    document["sources"].extend(
        [
            {"id": image_id, "kind": "image", "origin": "asset"},
            {
                "id": audio_id,
                "kind": "audio",
                "origin": "asset",
                "duration_ms": 10000,
                "derived_from_source_id": parent.id,
            },
        ]
    )
    image = VerifiedMotionSource(
        id=image_id,
        kind="image",
        origin="asset",
        duration_ms=None,
        has_audio=None,
        has_speech=None,
        derived_from_source_id=None,
        sha256="a" * 64,
    )
    derived = VerifiedMotionSource(
        id=audio_id,
        kind="audio",
        origin="asset",
        duration_ms=10000,
        has_audio=None,
        has_speech=True,
        derived_from_source_id=parent.id,
        sha256="f" * 64,
    )
    # Rebuild 3 valid five-second image pages; only one page contains voice.
    pages = carousel()["pages"]
    for page in pages:
        page["visual"][0]["source_id"] = image_id
    voice = document["pages"][0]["audio"]["tracks"][0]
    voice.update(source_id=audio_id, source_trim=time(1000, 4000), timeline=time(1000, 4000))
    pages[0]["audio"] = {"mode": "mix", "speech": "preserve", "tracks": [voice]}
    document["pages"] = pages
    skill_id, skill_hash, _ = resolve_motion_skill("carousel_motion")
    document["skill"] = {"id": skill_id, "sha256": skill_hash}
    updated = replace(snapshot, sources=(parent, snapshot.sources[1], image, derived))
    code = "MOTION_COMPOSITION_SPEECH_UNVERIFIED" if change == "unknown_parent" else "MOTION_COMPOSITION_SPEECH_CHANGED"
    with pytest.raises(AuthError, match=code):
        compile_motion_composition(document, snapshot=updated)


@pytest.mark.parametrize("kind", ["variable_rate", "positive_gain"])
def test_unsupported_audio_plan_fails_closed(kind):
    document, snapshot = speech_mix()
    voice = document["pages"][0]["audio"]["tracks"][0]
    if kind == "variable_rate":
        voice["source_trim"] = time(1000, 2500)
        voice["playback_rate"] = {"numerator": 1, "denominator": 2}
    else:
        voice["gain_mdb"] = 1
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_AUDIO_UNSUPPORTED"):
        compile_motion_composition(document, snapshot=snapshot)


def test_cuts_and_fades_cannot_exceed_track_or_page():
    document, snapshot = speech_mix()
    document["pages"][0]["audio"]["tracks"][0]["fade_in_ms"] = 3001
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_INVALID"):
        compile_motion_composition(document, snapshot=snapshot)
    document, snapshot = speech_mix()
    voice = document["pages"][0]["audio"]["tracks"][0]
    voice["timeline"] = time(8000, 11000)
    with pytest.raises(AuthError, match="MOTION_COMPOSITION_INVALID"):
        compile_motion_composition(document, snapshot=snapshot)


@pytest.mark.parametrize("speech", [None, False])
def test_omission_requires_evidence_for_audio_derived_from_recording(speech):
    document, snapshot = speech_mix()
    parent = snapshot.sources[0]
    audio_id = uuid4()
    audio_source = VerifiedMotionSource(
        id=audio_id,
        kind="audio",
        origin="asset",
        duration_ms=10000,
        has_audio=None,
        has_speech=speech,
        derived_from_source_id=parent.id,
        sha256="f" * 64,
    )
    document["sources"].append(
        {"id": audio_id, "kind": "audio", "origin": "asset", "duration_ms": 10000, "derived_from_source_id": parent.id}
    )
    track = document["pages"][0]["audio"]["tracks"][0]
    track.update(source_id=audio_id, role="original_sound")
    document["pages"][0]["audio"].update(speech="omit", omission_reason="Peça sem fala.", tracks=[track])
    updated = replace(snapshot, sources=snapshot.sources + (audio_source,))
    if speech is None:
        with pytest.raises(AuthError, match="MOTION_COMPOSITION_SPEECH_UNVERIFIED"):
            compile_motion_composition(document, snapshot=updated)
    else:
        plan = compile_motion_composition(document, snapshot=updated).audio_plans[0]
        assert plan.tracks[0].source_has_speech is False


@pytest.mark.parametrize("speech", [None, True, False])
def test_music_track_cannot_hide_speech_in_a_no_speech_plan(speech):
    document, snapshot = sample("carousel_motion")
    sound = VerifiedMotionSource(
        id=uuid4(),
        kind="audio",
        origin="asset",
        duration_ms=5000,
        has_audio=None,
        has_speech=speech,
        derived_from_source_id=None,
        sha256="e" * 64,
    )
    document["sources"].append({"id": sound.id, "kind": "audio", "origin": "asset", "duration_ms": 5000})
    document["pages"][0]["audio"] = {
        "mode": "mix",
        "speech": "not_present",
        "tracks": [
            {
                "source_id": sound.id,
                "source_trim": time(0, 5000),
                "timeline": time(0, 5000),
                "playback_rate": {"numerator": 1, "denominator": 1},
                "role": "music",
                "gain_mdb": -6000,
                "fade_in_ms": 0,
                "fade_out_ms": 0,
                "direction": "trilha autorizada",
            }
        ],
    }
    changed = replace(snapshot, sources=snapshot.sources + (sound,))
    if speech is False:
        assert (
            compile_motion_composition(document, snapshot=changed).audio_plans[0].tracks[0].source_has_speech is False
        )
    else:
        code = "MOTION_COMPOSITION_SPEECH_UNVERIFIED" if speech is None else "MOTION_COMPOSITION_SPEECH_CHANGED"
        with pytest.raises(AuthError, match=code):
            compile_motion_composition(document, snapshot=changed)
