"""A4 observations cannot reject static pieces; authorized music must survive rendering."""

from dataclasses import replace

import pytest

from app.adapters.motion_html_renderer import RenderedMotion
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_diagnostics import diagnose_render
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_orchestrator import unit_case  # noqa: F401
from app.tests.unit.test_motion_photo_planning import photo_case


def case():
    _, prepared, plan = photo_case()
    composition = HTMLMotionComposition(
        **plan.model_dump(mode="json"), html="<div></div>", scene_init="window.seek=()=>{}"
    )
    rendered = RenderedMotion(b"synthetic", "hash", (frame(0), frame(1000)), {})
    return prepared, composition, rendered


@pytest.mark.parametrize("color,expected", [("red", 100), ("blue", 0)])
def test_static_and_changing_samples_are_informative_only(color, expected):
    prepared, composition, rendered = case()
    rendered = replace(rendered, evidence=(frame(0), frame(1000, color)))
    result = diagnose_render(rendered, prepared, composition)
    metrics = result.diagnostics["photo_metrics"]
    assert metrics["mode"] == "informative_only"
    assert metrics["near_static"]["sample_pair_percent"] == expected
    assert metrics["narrative_strength"]["score"] is None
    assert metrics["transitions"]["count"] == 1
    assert result.mp4 == rendered.mp4 and rendered.diagnostics == {}


def test_insufficient_samples_and_missing_plan_do_not_invent_measurements():
    prepared, composition, rendered = case()
    composition = composition.model_copy(update={"motion_plan": None})
    result = diagnose_render(replace(rendered, evidence=(frame(),)), prepared, composition)
    metrics = result.diagnostics["photo_metrics"]
    assert metrics["movement"]["mean_normalized_pixel_difference"] is None
    assert metrics["near_static"]["sample_pair_percent"] is None
    assert metrics["transitions"]["count"] == 0
    assert diagnose_render(rendered, replace(prepared, context={}), composition) is rendered


def music_case():
    from app.services.motion_photos import music_soundtrack

    prepared, composition, rendered = case()
    prepared = replace(
        prepared, context={**prepared.context, "authorized_soundtrack": music_soundtrack("assets/music.mp3", 15000)}
    )
    rendered = replace(
        rendered,
        diagnostics={
            "music_integrity": {"source": "decoded_output", "audio_duration_ms": 15000, "required_end_ms": 15000},
            "audio_measurements": {"source": "decoded_output", "sample_peak_dbfs": -40},
        },
    )
    return prepared, composition, rendered


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "metadata"),
        ("audio_duration_ms", None),
        ("audio_duration_ms", float("nan")),
        ("audio_duration_ms", 0),
        ("audio_duration_ms", 1000),
        ("required_end_ms", 1),
    ],
)
def test_missing_or_short_music_is_integrity_failure(field, value):
    prepared, composition, rendered = music_case()
    rendered.diagnostics["music_integrity"][field] = value
    with pytest.raises(AuthError, match="MOTION_RENDER_MUSIC_INVALID"):
        diagnose_render(rendered, prepared, composition)


@pytest.mark.parametrize(
    "measurements",
    [
        {},
        {"source": "wrong"},
        {"source": "decoded_output", "sample_peak_dbfs": None},
        {"source": "decoded_output", "sample_peak_dbfs": float("inf")},
    ],
)
def test_absent_or_empty_audio_never_passes(measurements):
    prepared, composition, rendered = music_case()
    rendered.diagnostics["audio_measurements"] = measurements
    with pytest.raises(AuthError, match="MOTION_RENDER_MUSIC_INVALID"):
        diagnose_render(rendered, prepared, composition)


def test_quiet_music_is_not_rejected_by_loudness_threshold():
    prepared, composition, rendered = music_case()
    rendered.diagnostics["audio_measurements"]["sample_peak_dbfs"] = -100
    assert diagnose_render(rendered, prepared, composition).diagnostics["photo_metrics"]["mode"] == "informative_only"


def test_informative_metrics_stay_out_of_model_review_input():
    from app.services.motion_corrections import review_diagnostics

    assert review_diagnostics({"photo_metrics": {"near_static": 100}, "width": 720}) == {"width": 720}


@pytest.mark.parametrize("valid", [False, True])
async def test_integrity_runs_before_upload_and_diagnostics_are_durable(unit_case, valid):  # noqa: F811
    from unittest.mock import Mock

    from app.tests.unit.test_motion_ai import composition as simple_composition

    c = unit_case
    prepared, _, rendered = music_case()
    context = {"source": {"kind": "photos"}, "authorized_soundtrack": prepared.context["authorized_soundtrack"]}
    prepared = replace(c.prepared, context=context, duration_ms=15000, soundtrack=context["authorized_soundtrack"])
    rendered = replace(rendered, mp4=c.rendered.mp4, sha256=c.rendered.sha256)
    if not valid:
        rendered = replace(rendered, diagnostics={})
    c.runner.renderer.render.return_value = rendered
    c.runner.requests.context.seal = Mock(return_value="ciphertext")
    if not valid:
        with pytest.raises(AuthError, match="MOTION_RENDER_MUSIC_INVALID"):
            await c.runner.render(c.row, c.token, prepared, 0, simple_composition())
        c.runner.store.put.assert_not_awaited()
        c.runner.effects.received.assert_not_awaited()
    else:
        candidate = await c.runner.render(c.row, c.token, prepared, 0, simple_composition())
        assert candidate.rendered.diagnostics["photo_metrics"]["mode"] == "informative_only"
        result = c.runner.effects.received.call_args_list[0].args[3]
        assert result["diagnostics"]["photo_metrics"]["near_static"]["sample_pair_percent"] == 100
        assert any("photo_metrics" in call.args[0] for call in c.runner.requests.context.seal.call_args_list)


@pytest.mark.parametrize("field", ["music_integrity", "audio_measurements"])
def test_malformed_integrity_is_a_stable_failure(field):
    prepared, composition, rendered = music_case()
    rendered.diagnostics[field] = "invalid"
    with pytest.raises(AuthError, match="MOTION_RENDER_MUSIC_INVALID"):
        diagnose_render(rendered, prepared, composition)


@pytest.mark.parametrize("field", ["duration", "peak"])
def test_boolean_is_not_a_numeric_measurement(field):
    prepared, composition, rendered = music_case()
    if field == "duration":
        rendered.diagnostics["music_integrity"]["audio_duration_ms"] = True
    else:
        rendered.diagnostics["audio_measurements"]["sample_peak_dbfs"] = True
    with pytest.raises(AuthError, match="MOTION_RENDER_MUSIC_INVALID"):
        diagnose_render(rendered, prepared, composition)
