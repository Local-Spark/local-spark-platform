"""Pure v2 direction tests: bounded data, timelines, sources and explicit audio."""

from copy import deepcopy
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.motion import (
    AudioPlan,
    AudioSegment,
    Caption,
    ClipInsets,
    GraphicSpec,
    MediaSource,
    MotionDirection,
    MotionRenderProfile,
    PlaybackRate,
    TimeRange,
    Transition,
    VisualSegment,
    _source_trim,
)


def state():
    return {
        "x": 0,
        "y": 0,
        "width": 10000,
        "height": 10000,
        "scale": 10000,
        "opacity": 10000,
        "rotation": 0,
        "clip": {"top": 0, "right": 0, "bottom": 0, "left": 0},
    }


def keys(duration=10000):
    return [
        {"at_ms": 0, "state": state(), "easing_to_next": "ease_out"},
        {"at_ms": duration, "state": state(), "easing_to_next": None},
    ]


def time(start=0, end=10000):
    return {"start_ms": start, "end_ms": end}


def transition(kind="cut", duration=0):
    return {"kind": kind, "duration_ms": duration}


def typography():
    return {
        "font_id": "dejavu-serif",
        "font_size": 600,
        "weight": 700,
        "align": "center",
        "vertical_align": "center",
        "color": "#FFFFFF",
        "line_height": 12000,
        "letter_spacing": 0,
    }


def direction():
    video = uuid4()
    return {
        "schema_version": "motion-direction-v2",
        "format": "reel",
        "skill": {"id": "reel-v1", "sha256": "a" * 64},
        "style": {"id": "style-v1", "sha256": "b" * 64},
        "sources": [
            {
                "id": video,
                "kind": "video",
                "origin": "customer_recording",
                "duration_ms": 60000,
                "has_audio": True,
            }
        ],
        "pages": [
            {
                "id": uuid4(),
                "duration_ms": 10000,
                "background": "#244739",
                "visual": [
                    {
                        "kind": "video",
                        "timeline": time(),
                        "source_id": video,
                        "source_trim": time(),
                        "playback_rate": {"numerator": 1, "denominator": 1},
                        "placement": {"fit": "cover", "focus_x": 5000, "focus_y": 6600},
                        "keyframes": keys(),
                        "enter": transition(),
                        "exit": transition(),
                        "direction": "café",
                    }
                ],
                "audio": {
                    "mode": "mix",
                    "speech": "preserve",
                    "tracks": [
                        {
                            "source_id": video,
                            "source_trim": time(),
                            "timeline": time(),
                            "playback_rate": {"numerator": 1, "denominator": 1},
                            "role": "recorded_voice",
                            "gain_mdb": 0,
                            "fade_in_ms": 0,
                            "fade_out_ms": 0,
                            "direction": "fala original",
                        }
                    ],
                },
                "captions": [
                    {
                        "timeline": time(),
                        "text": "Uma pausa",
                        "typography": typography(),
                        "keyframes": keys(),
                        "enter": transition(),
                        "exit": transition(),
                    }
                ],
            }
        ],
    }


def carousel(count=3, duration=5000):
    p = direction()
    image = uuid4()
    p["format"] = "carousel_motion"
    p["sources"] = [{"id": image, "kind": "image", "origin": "asset"}]
    p["pages"] = [
        {
            "id": uuid4(),
            "duration_ms": duration,
            "background": "#244739",
            "visual": [
                {
                    "kind": "image",
                    "timeline": time(0, duration),
                    "source_id": image,
                    "placement": {"fit": "contain", "focus_x": 5000, "focus_y": 5000},
                    "keyframes": keys(duration),
                    "enter": transition(),
                    "exit": transition(),
                    "direction": "foto",
                }
            ],
            "audio": {"mode": "silent", "speech": "not_present", "tracks": []},
            "captions": [],
        }
        for _ in range(count)
    ]
    return p


@pytest.mark.parametrize("fmt", ["reel", "story_video"])
def test_video_direction_with_original_audio_and_caption(fmt):
    p = direction()
    p["format"] = fmt
    assert MotionDirection.model_validate(p).pages[0].audio.speech == "preserve"


@pytest.mark.parametrize("duration,valid", [(60000, True), (60001, False)])
def test_video_final_duration_limit(duration, valid):
    p = direction()
    p["pages"][0]["duration_ms"] = duration
    if valid:
        assert MotionDirection.model_validate(p).pages[0].duration_ms == 60000
    else:
        with pytest.raises(ValidationError):
            MotionDirection.model_validate(p)


@pytest.mark.parametrize("count,duration", [(3, 5000), (4, 6500), (5, 8000)])
def test_carousel_bounds_and_order(count, duration):
    p = carousel(count, duration)
    assert [v.id for v in MotionDirection.model_validate(p).pages] == [v["id"] for v in p["pages"]]


def test_derivative_audio_is_attributed_to_recording():
    p = direction()
    vid = p["sources"][0]["id"]
    aid = uuid4()
    p["sources"].append(
        {
            "id": aid,
            "kind": "audio",
            "origin": "asset",
            "duration_ms": 10000,
            "derived_from_source_id": vid,
        }
    )
    p["pages"][0]["audio"]["tracks"][0]["source_id"] = aid
    assert MotionDirection.model_validate(p).pages[0].audio.tracks[0].source_id == aid


@pytest.mark.parametrize("kind", ["rectangle", "circle", "text"])
def test_graphic_types_are_explicit(kind):
    p = carousel()
    visual = p["pages"][0]["visual"][0]
    visual.update(kind="graphic", source_id=None, placement=None)
    visual["graphic"] = {
        "kind": kind,
        "text": "Um café" if kind == "text" else None,
        "typography": typography() if kind == "text" else None,
        "fill": None if kind == "text" else "#FFFFFF",
        "corner_radius": 200 if kind == "rectangle" else None,
    }
    assert MotionDirection.model_validate(p).pages[0].visual[0].graphic.kind == kind


@pytest.mark.parametrize("value", [-1, 1.5, True, "100"])
def test_strict_integer_time(value):
    with pytest.raises(ValidationError):
        TimeRange(start_ms=value, end_ms=1000)


@pytest.mark.parametrize("start,end", [(0, 0), (1000, 1000), (1000, 999)])
def test_positive_interval(start, end):
    with pytest.raises(ValidationError):
        TimeRange(start_ms=start, end_ms=end)


@pytest.mark.parametrize(
    "kw",
    [
        {"kind": "image", "origin": "asset", "duration_ms": 1},
        {"kind": "image", "origin": "asset", "has_audio": False},
        {"kind": "video", "origin": "asset"},
        {"kind": "audio", "origin": "asset"},
        {"kind": "audio", "origin": "asset", "duration_ms": 1, "has_audio": True},
        {"kind": "image", "origin": "customer_recording"},
        {"kind": "audio", "origin": "customer_recording", "duration_ms": 1},
        {"kind": "video", "origin": "customer_recording", "duration_ms": 60001},
        {
            "kind": "video",
            "origin": "asset",
            "duration_ms": 1,
            "derived_from_source_id": uuid4(),
        },
    ],
)
def test_invalid_source(kw):
    with pytest.raises(ValidationError):
        MediaSource(id=uuid4(), **kw)


@pytest.mark.parametrize(
    "v",
    [
        {"numerator": 0, "denominator": 1},
        {"numerator": 17, "denominator": 1},
        {"numerator": 1, "denominator": 17},
    ],
)
def test_playback_bounds(v):
    with pytest.raises(ValidationError):
        PlaybackRate.model_validate(v)


def test_exact_rational_rate_and_no_rounding_tolerance():
    a = direction()["pages"][0]["audio"]["tracks"][0]
    a["source_trim"] = time(0, 5000)
    a["playback_rate"] = {"numerator": 1, "denominator": 2}
    assert AudioSegment.model_validate(a).playback_rate.denominator == 2
    a["source_trim"]["end_ms"] = 5001
    with pytest.raises(ValidationError, match="disagree"):
        AudioSegment.model_validate(a)


@pytest.mark.parametrize("kw", [{"top": 5000, "bottom": 5000}, {"left": 6000, "right": 4000}, {"top": 10000}])
def test_clip_requires_visible_area(kw):
    d = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    d.update(kw)
    with pytest.raises(ValidationError):
        ClipInsets.model_validate(d)


@pytest.mark.parametrize("kind,duration", [("cut", 1), ("fade", 0)])
def test_transition_kind_and_duration(kind, duration):
    with pytest.raises(ValidationError):
        Transition(kind=kind, duration_ms=duration)


@pytest.mark.parametrize(
    "case",
    [
        "text_missing",
        "font_missing",
        "text_has_fill",
        "text_has_radius",
        "shape_text",
        "shape_font",
        "shape_no_fill",
        "circle_radius",
    ],
)
def test_graphic_requires_its_own_fields(case):
    text = {"kind": "text", "text": "Olá", "typography": typography()}
    shape = {"kind": "rectangle", "fill": "#FFFFFF"}
    if case == "text_missing":
        text["text"] = None
    elif case == "font_missing":
        text["typography"] = None
    elif case == "text_has_fill":
        text["fill"] = "#FFFFFF"
    elif case == "text_has_radius":
        text["corner_radius"] = 1
    elif case == "shape_text":
        shape["text"] = "Olá"
    elif case == "shape_font":
        shape["typography"] = typography()
    elif case == "shape_no_fill":
        shape["fill"] = None
    else:
        shape.update(kind="circle", corner_radius=1)
    with pytest.raises(ValidationError):
        GraphicSpec.model_validate(text if case.startswith(("text_", "font_")) else shape)


@pytest.mark.parametrize(
    "case",
    [
        "start",
        "end",
        "unordered",
        "missing_easing",
        "last_easing",
        "overlapping_transitions",
    ],
)
def test_keyframe_sequence_and_transitions(case):
    layer = direction()["pages"][0]["visual"][0]
    if case == "start":
        layer["keyframes"][0]["at_ms"] = 1
    elif case == "end":
        layer["keyframes"][-1]["at_ms"] = 9999
    elif case == "unordered":
        layer["keyframes"].insert(1, deepcopy(layer["keyframes"][0]))
    elif case == "missing_easing":
        layer["keyframes"][0]["easing_to_next"] = None
    elif case == "last_easing":
        layer["keyframes"][-1]["easing_to_next"] = "linear"
    else:
        layer.update(enter=transition("fade", 6000), exit=transition("fade", 5000))
    with pytest.raises(ValidationError):
        VisualSegment.model_validate(layer)


def test_render_limits_number_of_keyframes_and_layers():
    p = direction()
    layer = p["pages"][0]["visual"][0]
    layer["keyframes"] = layer["keyframes"] * 17
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(p)
    p = direction()
    p["pages"][0]["visual"] = p["pages"][0]["visual"] * 65
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(p)


@pytest.mark.parametrize(
    "case",
    [
        "graphic_source",
        "graphic_missing",
        "media_no_source",
        "media_no_placement",
        "media_graphic",
        "video_no_trim",
        "video_no_rate",
        "image_trim",
        "image_rate",
    ],
)
def test_layer_source_shape(case):
    layer = direction()["pages"][0]["visual"][0]
    if case.startswith("graphic"):
        layer.update(
            kind="graphic",
            source_id=None,
            source_trim=None,
            playback_rate=None,
            placement=None,
            graphic={"kind": "rectangle", "fill": "#000000"},
        )
        if case == "graphic_source":
            layer["source_id"] = uuid4()
        else:
            layer["graphic"] = None
    elif case == "media_no_source":
        layer["source_id"] = None
    elif case == "media_no_placement":
        layer["placement"] = None
    elif case == "media_graphic":
        layer["graphic"] = {"kind": "rectangle", "fill": "#000000"}
    elif case == "video_no_trim":
        layer["source_trim"] = None
    elif case == "video_no_rate":
        layer["playback_rate"] = None
    elif case == "image_trim":
        layer.update(kind="image", playback_rate=None)
    else:
        layer.update(kind="image", source_trim=None)
    with pytest.raises(ValidationError):
        VisualSegment.model_validate(layer)


def test_audio_fades_must_fit_and_silent_mode_explicit():
    a = direction()["pages"][0]["audio"]["tracks"][0]
    a.update(fade_in_ms=6000, fade_out_ms=4001)
    with pytest.raises(ValidationError, match="fades"):
        AudioSegment.model_validate(a)
    assert AudioPlan(mode="silent", speech="not_present", tracks=[]).mode == "silent"


@pytest.mark.parametrize(
    "case",
    [
        "silent_with_tracks",
        "mix_no_tracks",
        "omit_without_reason",
        "reason_without_omit",
        "preserve_without_voice",
        "voice_when_no_speech",
    ],
)
def test_audio_policy_does_not_silently_omit_voice(case):
    a = deepcopy(direction()["pages"][0]["audio"])
    if case == "silent_with_tracks":
        a["mode"] = "silent"
    elif case == "mix_no_tracks":
        a["tracks"] = []
        a["speech"] = "not_present"
    elif case == "omit_without_reason":
        a["speech"] = "omit"
        a["tracks"][0]["role"] = "music"
    elif case == "reason_without_omit":
        a["omission_reason"] = "sem autorização"
    elif case == "preserve_without_voice":
        a["tracks"][0]["role"] = "music"
    else:
        a["speech"] = "not_present"
    with pytest.raises(ValidationError):
        AudioPlan.model_validate(a)


def test_explicit_speech_omission_is_recorded():
    result = AudioPlan(
        mode="silent",
        speech="omit",
        omission_reason="Solicitado pelo titular",
        tracks=[],
    )
    assert result.omission_reason == "Solicitado pelo titular"


@pytest.mark.parametrize("count,duration", [(0, 5000), (2, 5000), (6, 5000), (3, 4999), (3, 8001)])
def test_invalid_carousel_bounds(count, duration):
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(carousel(count, duration))


@pytest.mark.parametrize(
    "case",
    [
        "no_recording",
        "two_recordings",
        "extra_page",
        "unused_recording",
        "duplicate_source",
        "duplicate_page",
        "missing_derived",
        "wrong_derived",
        "missing_visual",
        "wrong_visual",
        "trim_outside",
        "audio_unknown",
        "audio_image",
        "video_audio_absent",
        "voice_wrong_recording",
        "voice_unverified",
    ],
)
def test_cross_references_and_media_are_validated(case):
    p = direction()
    page = p["pages"][0]
    source = p["sources"][0]
    clip = page["visual"][0]
    audio = page["audio"]["tracks"][0]
    if case == "no_recording":
        source["origin"] = "asset"
    elif case == "two_recordings":
        d = deepcopy(source)
        d["id"] = uuid4()
        p["sources"].append(d)
    elif case == "extra_page":
        page2 = deepcopy(page)
        page2["id"] = uuid4()
        p["pages"].append(page2)
    elif case == "unused_recording":
        clip.update(
            kind="graphic",
            source_id=None,
            source_trim=None,
            playback_rate=None,
            placement=None,
            graphic={"kind": "rectangle", "fill": "#000000"},
        )
    elif case == "duplicate_source":
        p["sources"].append(deepcopy(source))
    elif case == "duplicate_page":
        p = carousel()
        p["pages"][1]["id"] = p["pages"][0]["id"]
    elif case == "missing_derived":
        p["sources"].append(
            {
                "id": uuid4(),
                "kind": "audio",
                "origin": "asset",
                "duration_ms": 10000,
                "derived_from_source_id": uuid4(),
            }
        )
    elif case == "wrong_derived":
        x = uuid4()
        p["sources"].append({"id": x, "kind": "image", "origin": "asset"})
        p["sources"].append(
            {
                "id": uuid4(),
                "kind": "audio",
                "origin": "asset",
                "duration_ms": 10000,
                "derived_from_source_id": x,
            }
        )
    elif case == "missing_visual":
        clip["source_id"] = uuid4()
    elif case == "wrong_visual":
        source.update(origin="asset", kind="image", duration_ms=None, has_audio=None)
        p["sources"].append(
            {
                "id": uuid4(),
                "kind": "video",
                "origin": "customer_recording",
                "duration_ms": 10000,
            }
        )
    elif case == "trim_outside":
        source["duration_ms"] = 9999
    elif case == "audio_unknown":
        audio["source_id"] = uuid4()
    elif case == "audio_image":
        x = uuid4()
        p["sources"].append({"id": x, "kind": "image", "origin": "asset"})
        audio["source_id"] = x
    elif case == "video_audio_absent":
        source["has_audio"] = False
    elif case == "voice_wrong_recording":
        x = uuid4()
        p["sources"].append({"id": x, "kind": "audio", "origin": "asset", "duration_ms": 10000})
        audio["source_id"] = x
    else:
        source["has_audio"] = False
        x = uuid4()
        p["sources"].append(
            {
                "id": x,
                "kind": "audio",
                "origin": "asset",
                "duration_ms": 10000,
                "derived_from_source_id": source["id"],
            }
        )
        audio["source_id"] = x
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(p)


@pytest.mark.parametrize("track", ["visual", "audio", "captions"])
def test_each_timeline_fits_page(track):
    p = direction()
    page = p["pages"][0]
    if track == "audio":
        t = page["audio"]["tracks"][0]
        t["timeline"]["end_ms"] = 10001
        t["source_trim"]["end_ms"] = 10001
    elif track == "visual":
        t = page["visual"][0]
        t["timeline"]["end_ms"] = 10001
        t["source_trim"]["end_ms"] = 10001
        t["keyframes"][-1]["at_ms"] = 10001
    else:
        t = page["captions"][0]
        t["timeline"]["end_ms"] = 10001
        t["keyframes"][-1]["at_ms"] = 10001
    with pytest.raises(ValidationError, match="output duration"):
        MotionDirection.model_validate(p)


@pytest.mark.parametrize("field", ["html", "javascript", "path", "url"])
def test_extra_code_or_path_fields_forbidden(field):
    p = direction()
    p["sources"][0][field] = "untrusted"
    with pytest.raises(ValidationError, match="Extra inputs"):
        MotionDirection.model_validate(p)


@pytest.mark.parametrize("bad", ["", "   ", "a" * 501])
def test_caption_text_bounded(bad):
    c = direction()["pages"][0]["captions"][0]
    c["text"] = bad
    with pytest.raises(ValidationError):
        Caption.model_validate(c)


def test_hash_format_and_static_story_not_motion():
    p = direction()
    p["format"] = "story"
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(p)
    p = direction()
    p["style"]["sha256"] = "z" * 64
    with pytest.raises(ValidationError):
        MotionDirection.model_validate(p)


def test_bad_source_even_if_construct_bypasses_validation():
    source = MediaSource.model_construct(id=uuid4(), kind="video", origin="asset", duration_ms=None)
    with pytest.raises(ValueError):
        _source_trim(TimeRange(start_ms=0, end_ms=1), source)
    with pytest.raises(ValueError):
        _source_trim(None, source)


def test_render_profile_is_separate_bounded_executor_configuration():
    assert MotionRenderProfile(width_px=1080, height_px=1350, fps=30).width_px == 1080
    with pytest.raises(ValidationError, match="pixel budget"):
        MotionRenderProfile(width_px=4096, height_px=4096, fps=30)
