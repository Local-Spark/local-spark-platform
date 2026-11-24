"""Synthetic EDL, fail-closed gates and replay of Fatia A/photo without new pins."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from app.adapters.motion_ai import _format
from app.schemas.motion_plan import MotionPlan
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_repertoire import capture_repertoire, validate_repertoire_images
from app.services.motion_video_edit import (
    CONTRACT,
    CONTRACT_V2,
    SOURCE,
    capture_video_edit,
    edit_rules,
    guarded_video_edit_init,
    validate_video_edit,
)
from app.services.motion_video_reel import VIDEO_REEL_CONTRACT, guarded_video_scene_init, validate_video_reel
from app.services.motion_video_scene_visibility import CONTRACT as VISIBILITY
from app.services.motion_video_scene_visibility import scoped_video_scene_init
from app.tests.unit.test_motion_audiovisual import natural_body

CTX = {"video_reel_contract": VIDEO_REEL_CONTRACT, "video_edit_contract": CONTRACT}
ASSETS = {"assets/source.mp4", "assets/logo.png"}


def case():
    return json.loads(Path("app/tests/fixtures/motion_video_edit.json").read_text())


def artifact(data=None):
    return HTMLMotionComposition.model_validate(case() if data is None else data)


def test_canonical_plan_admission_and_execution_identity():
    a = artifact()
    validate_video_reel(a, CTX, asset_ids=ASSETS)
    context = {**CTX, "video_scene_visibility_contract": VISIBILITY}
    js = guarded_video_scene_init(a, context, scoped_video_scene_init(a, context, a.scene_init))
    assert js.index("installVideoSceneVisibilityV1") < js.index("installVideoReelV1") < js.index("installVideoEditV1")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == CONTRACT["sha256"]
    assert '"source_in_ms": 3000' in js
    pack = capture_repertoire("business-video-reel-v3")
    assert validate_repertoire_images({"repertoire": pack}, ()) == []
    example = next(e for e in pack["examples"] if e["id"] == "edl-plan")
    assert MotionPlan.model_validate_json(example["content"]) == a.motion_plan


def test_new_capture_and_old_replay_are_separate():
    new = capture_motion_guidance(natural_body(repertoire_id=None))
    assert new["video_edit_contract"] == CONTRACT_V2
    assert new["skill"]["id"] == "instagram-reel-video-v21"
    assert new["repertoire"]["id"] == "business-video-reel-v4"
    assert "Sem EDL" not in new["executor_contract"]["integration_policy"]
    assert new["video_edit_contract"]["music"]["status"] == "unavailable"
    assert capture_video_edit(video=True, previous=new) == {"video_edit_contract": CONTRACT_V2}
    assert capture_video_edit(video=True, previous={}) == {}
    assert capture_video_edit(video=False, previous=None) == {}
    old = deepcopy(new)
    old.pop("video_edit_contract")
    replay = capture_motion_guidance(natural_body(repertoire_id=None), previous=old)
    assert "video_edit_contract" not in replay
    assert replay["video_reel_contract"] == old["video_reel_contract"]


def test_contract_absence_and_tamper():
    assert edit_rules({}) == ""
    validate_video_edit(artifact(), {})
    assert guarded_video_edit_init(artifact(), {}, "bytes") == "bytes"
    with pytest.raises(AuthError, match="CONTRACT_CHANGED"):
        edit_rules({"video_edit_contract": {**CONTRACT, "version": "other"}})


@pytest.mark.parametrize("missing", [True, False])
def test_missing_or_single_segment(missing):
    data = case()
    if missing:
        data.pop("motion_plan")
    else:
        data["motion_plan"]["scenes"] = data["motion_plan"]["scenes"][:1]
        data["motion_plan"]["duration_ms"] = 3000
    with pytest.raises(AuthError, match="EDL_REQUIRED"):
        validate_video_edit(artifact(data), CTX)


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda d: d["motion_plan"]["scenes"][0].pop("video_layout"), "EDL_INVALID"),
        (lambda d: d["motion_plan"]["scenes"][0]["video_layout"].pop("edit"), "EDL_INVALID"),
        (lambda d: d["motion_plan"]["scenes"][1].update(start_ms=2999), "EDL_INVALID"),
        (lambda d: d["motion_plan"]["scenes"][0]["video_layout"]["edit"].update(source_out_ms=2000), "EDL_INVALID"),
        (
            lambda d: d["motion_plan"]["scenes"][1]["video_layout"]["edit"].update(
                source_in_ms=4000, source_out_ms=7000
            ),
            "EDL_INVALID",
        ),
        (lambda d: d["motion_plan"]["scenes"][0]["video_layout"]["edit"]["crop_from"].update(x=0.1), "CROP_UNSAFE"),
        (lambda d: d["motion_plan"]["scenes"][0]["video_layout"]["edit"]["crop_to"].update(scale=1), "MOTION_REQUIRED"),
        (
            lambda d: d["motion_plan"]["scenes"][1]["video_layout"]["edit"]["crop_from"].update(scale=1.06),
            "CUT_REQUIRED",
        ),
        (
            lambda d: d["motion_plan"]["scenes"][1]["video_layout"]["edit"].update(purpose="hook"),
            "EDITORIAL_FUNCTION_REQUIRED",
        ),
    ],
)
def test_bad_edl(change, code):
    data = case()
    change(data)
    with pytest.raises(AuthError, match=code):
        validate_video_edit(artifact(data), CTX)


def test_playthrough_with_only_text_changes_is_rejected():
    data = case()
    for scene in data["motion_plan"]["scenes"]:
        scene["video_layout"]["edit"].update(crop_from=dict(scale=1, x=0, y=0), crop_to=dict(scale=1, x=0, y=0))
    with pytest.raises(AuthError, match="MOTION_REQUIRED"):
        validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


def test_audio_continuity_and_silent_remontage():
    data = case()
    data["audio"] = dict(
        mode="mix",
        tracks=[dict(asset_id="assets/source.mp4", offset_ms=0, trim_start_ms=0, trim_end_ms=6000, volume=1)],
    )
    validate_video_edit(artifact(data), CTX)
    for scene in data["motion_plan"]["scenes"]:
        edit = scene["video_layout"]["edit"]
        edit.update(source_in_ms=3000 - scene["start_ms"], source_out_ms=6000 - scene["start_ms"])
    with pytest.raises(AuthError, match="EDL_INVALID"):
        validate_video_edit(artifact(data), CTX)
    data["audio"] = dict(mode="silent", tracks=[])
    validate_video_edit(artifact(data), CTX)
    with pytest.raises(AuthError, match="MUSIC_UNAVAILABLE"):
        validate_video_edit(artifact(data), {**CTX, "authorized_soundtrack": {}})


@pytest.mark.parametrize("missing", [True, False])
def test_guard_integrity(tmp_path, monkeypatch, missing):
    path = tmp_path / "guard.js"
    if not missing:
        path.write_text("tampered")
    monkeypatch.setattr("app.services.motion_video_edit.SOURCE", path)
    with pytest.raises(AuthError, match="EDIT_GUARD_CHANGED"):
        guarded_video_edit_init(artifact(), CTX, "original")


@pytest.mark.parametrize("model", [HTMLMotionComposition, MotionConstructionPlan])
def test_schema_preserves_a_and_photo(model):
    historical = _format(model, allow_staging=False, allow_video_layout=True)
    new = _format(model, allow_staging=False, allow_video_layout=True, allow_video_edit=True)
    # Search serialized schema: provider output must not solicit B fields for A/photo.
    assert "source_in_ms" not in json.dumps(historical)
    assert "source_in_ms" in json.dumps(new)
    assert "VideoEdit" not in json.dumps(_format(model, allow_staging=False))


@pytest.mark.parametrize("field,value", [("scale", 0.9), ("scale", 1.36), ("x", float("nan")), ("y", float("inf"))])
def test_crop_schema_bounds(field, value):
    from pydantic import ValidationError

    data = case()
    data["motion_plan"]["scenes"][0]["video_layout"]["edit"]["crop_from"][field] = value
    with pytest.raises(ValidationError):
        artifact(data)


def test_b_still_rejects_a_kinetic_text_violation():
    data = case()
    data["motion_plan"]["scenes"][1]["elements"][2]["beats"][1]["phase"] = "hold"
    with pytest.raises(AuthError, match="KINETIC_TEXT_REQUIRED"):
        validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


def test_generation_contract_is_versioned_without_promoting_a():
    from app.services.motion_generation import VIDEO_EDIT_GENERATION_CONTRACT, VIDEO_GENERATION_CONTRACT
    from app.services.motion_video_requests import planned_video_request

    request = planned_video_request(
        natural_body(repertoire_id=None, review_checkpoints=False, storyboard=False, automatic_plan=True)
    )
    current = capture_motion_guidance(request)
    assert current["generation_contract"] == VIDEO_EDIT_GENERATION_CONTRACT
    assert "sem EDL" not in current["generation_contract"]["response_rules"]
    assert "sem EDL" in VIDEO_GENERATION_CONTRACT["response_rules"]
    previous = {**current, "generation_contract": VIDEO_GENERATION_CONTRACT}
    previous.pop("video_edit_contract")
    assert capture_motion_guidance(request, previous=previous) == previous


def test_a_executed_bytes_match_pre_b_checkout():
    from app.tests.unit.test_motion_video_reel import artifact as a_artifact

    old = a_artifact()
    context = {"video_reel_contract": VIDEO_REEL_CONTRACT, "video_scene_visibility_contract": VISIBILITY}
    executed = guarded_video_scene_init(old, context, scoped_video_scene_init(old, context, old.scene_init))
    # Measured independently in an archived HEAD checkout, before B edits.
    assert (
        hashlib.sha256(executed.encode()).hexdigest()
        == "974bf6592d40af8b84e91c08f5cd8d5455306fb513596e018354c14fa5ce9f11"
    )


def test_safe_pan_is_an_intentional_alternative_to_zoom():
    data = case()
    a, b = [s["video_layout"]["edit"] for s in data["motion_plan"]["scenes"]]
    a.update(crop_from=dict(scale=1.2, x=-0.05, y=0), crop_to=dict(scale=1.2, x=0, y=0.04))
    b.update(crop_from=dict(scale=1.2, x=0.06, y=0), crop_to=dict(scale=1.2, x=0.03, y=0))
    validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


@pytest.mark.parametrize("mode", ["silent", "mix"])
@pytest.mark.parametrize("padding", [1, 24, 34])
def test_verified_terminal_frame_padding(mode, padding):
    data = case()
    source_duration = 6000 - padding
    data["motion_plan"]["scenes"][-1]["video_layout"]["edit"]["source_out_ms"] = source_duration
    if mode == "mix":
        data["audio"] = dict(
            mode="mix",
            tracks=[
                dict(asset_id="assets/source.mp4", offset_ms=0, trim_start_ms=0, trim_end_ms=source_duration, volume=1)
            ],
        )
    ctx = {**CTX, "video_edit_contract": CONTRACT_V2, "source": {"duration_ms": source_duration}}
    validate_video_reel(artifact(data), ctx, asset_ids=ASSETS)
    assert "installVideoEditV1" in guarded_video_scene_init(artifact(data), ctx, "original")
    with pytest.raises(AuthError, match="EDL_INVALID"):
        validate_video_edit(artifact(data), {**ctx, "video_edit_contract": CONTRACT})


@pytest.mark.parametrize("change", ["internal", "unknown", "wrong_end", "too_long", "stretched", "bool_duration"])
def test_padding_cannot_authorize_internal_gaps_unverified_ends_or_stretch(change):
    data = case()
    ctx = {**CTX, "video_edit_contract": CONTRACT_V2, "source": {"duration_ms": 5976}}
    edit = data["motion_plan"]["scenes"][-1]["video_layout"]["edit"]
    edit["source_out_ms"] = 5976
    if change == "internal":
        edit["source_out_ms"] = 6000
        data["motion_plan"]["scenes"][0]["video_layout"]["edit"]["source_out_ms"] = 2976
        ctx["source"]["duration_ms"] = 2976
    elif change == "unknown":
        ctx.pop("source")
    elif change == "wrong_end":
        ctx["source"]["duration_ms"] = 5975
    elif change == "too_long":
        edit["source_out_ms"] = ctx["source"]["duration_ms"] = 5965
    elif change == "bool_duration":
        ctx["source"]["duration_ms"] = True
    else:
        edit["source_in_ms"] = 0
    with pytest.raises(AuthError, match="EDL_INVALID"):
        validate_video_edit(artifact(data), ctx)


def test_v1_snapshot_replay_and_new_v2_pins():
    previous = {"video_edit_contract": CONTRACT}
    assert capture_video_edit(video=True, previous=previous) == previous
    assert capture_video_edit(video=True, previous=None)["video_edit_contract"] == CONTRACT_V2
    package = capture_repertoire("business-video-reel-v4")
    assert validate_repertoire_images({"repertoire": package}, ()) == []
    assert "source.duration_ms" in package["rules"]
