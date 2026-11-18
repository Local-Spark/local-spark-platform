"""Numeric energy admission, including crop-safe coordinated overlays and replay."""

from copy import deepcopy

import pytest

from app.schemas.motion_plan import MotionBeat
from app.services.auth import AuthError
from app.services.motion_photo_energy import energetic
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, PHOTO_INTENT_CONTRACT_V5
from app.tests.unit.test_motion_photo_quality import quality_case, validate


def beat(start="scale=1 x_pct=0 y_pct=0", end="scale=1.02 x_pct=0 y_pct=0", **updates):
    return MotionBeat.model_validate(
        dict(
            phase="transform",
            start_ms=0,
            end_ms=2000,
            start_state=start,
            end_state=end,
            trajectory="Linear motion with safe crop",
            curve={"kind": "linear", "parameters": []},
            **updates,
        )
    )


@pytest.mark.parametrize(
    "end,allowed",
    [
        ("scale=1.02 x_pct=0 y_pct=0", True),
        ("scale=1.019 x_pct=0 y_pct=0", False),
        ("scale=1 x_pct=1 y_pct=0", True),
        ("scale=1 x_pct=0 y_pct=-1", True),
        ("scale=1 x_pct=0 y_pct=0.99", False),
        ("scale=1 x_pct=0 y_pct=0", False),
        ("visually different prose", False),
        ("scale=0 x_pct=0 y_pct=4", False),
        ("scale=-1 x_pct=0 y_pct=4", False),
        ("scale=1 x_pct=" + "9" * 310 + " y_pct=0", False),
    ],
)
def test_numeric_rate_boundary_and_invalid_states(end, allowed):
    assert energetic(beat(end=end)) is allowed


def test_phase_curve_and_invalid_start_do_not_count():
    b = beat()
    assert not energetic(b.model_copy(update={"phase": "hold"}))
    assert not energetic(b.model_copy(update={"curve": b.curve.model_copy(update={"kind": "ease_in"})}))
    assert not energetic(beat(start="unknown"))


def current_case():
    data, _, assets = quality_case()
    return data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets


@pytest.mark.parametrize("fragment", [False, True])
def test_six_second_micro_transform_cannot_bypass_energy_with_labels_or_splits(fragment):
    data, context, assets = current_case()
    photo = data["motion_plan"]["scenes"][0]["elements"][0]
    b = photo["beats"][0]
    b.update(start_state="scale=1 x_pct=0 y_pct=0", end_state="scale=1.0001 x_pct=0 y_pct=0")
    if fragment:
        photo["beats"] = [dict(b, start_ms=t, end_ms=min(t + 1500, b["end_ms"])) for t in range(0, b["end_ms"], 1500)]
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, context, assets)
    validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT_V5}, assets)


@pytest.mark.parametrize("gap,allowed", [(2500, True), (2501, False)])
@pytest.mark.parametrize("position", ["start", "end", "middle"])
def test_energy_uncovered_windows(gap, allowed, position):
    data, context, assets = current_case()
    b = data["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]
    photo = data["motion_plan"]["scenes"][0]["elements"][0]
    if position == "start":
        b["start_ms"] += gap
    elif position == "end":
        b["end_ms"] = data["motion_plan"]["scenes"][1]["start_ms"] - gap
    else:
        photo["beats"] = [dict(b, end_ms=2000), dict(b, start_ms=2000 + gap)]
    if allowed:
        validate(data, context, assets)
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
            validate(data, context, assets)


def test_crop_limited_photo_can_coordinate_an_energetic_overlay_but_not_unlinked_or_logo():
    data, context, assets = current_case()
    scene = data["motion_plan"]["scenes"][0]
    photo = scene["elements"][0]
    overlay = deepcopy(photo)
    overlay.update(id="moving-copy", role="text", asset_id=None, related_element_ids=[])
    scene["elements"].append(overlay)
    photo["beats"][0]["end_state"] = photo["beats"][0]["start_state"]
    photo["related_element_ids"] = [overlay["id"]]
    validate(data, context, assets)
    photo["related_element_ids"] = []
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, context, assets)
    photo["related_element_ids"] = [overlay["id"]]
    overlay.update(role="image", asset_id="assets/logo.png")
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, context, assets)


def test_valid_plan_is_not_mutated_and_overlapping_energy_is_merged():
    data, context, assets = current_case()
    photo = data["motion_plan"]["scenes"][0]["elements"][0]
    other = deepcopy(photo)
    other.update(id="second-photo", related_element_ids=[])
    other["beats"][0].update(start_ms=1000, end_ms=4000)
    data["motion_plan"]["scenes"][0]["elements"].append(other)
    before = deepcopy(data)
    validate(data, context, assets)
    assert data == before


def test_scene_boundaries_do_not_reset_a_static_window():
    from app.schemas.motion_plan import MotionPlan
    from app.services.motion_photo_energy import validate_photo_energy

    data, _, _ = current_case()
    template = data["motion_plan"]["scenes"][0]
    scenes = []
    for i in range(4):
        scene = deepcopy(template)
        scene.update(id=f"scene{i}", start_ms=i * 2000, end_ms=(i + 1) * 2000)
        scene["elements"] = scene["elements"][:1]
        photo = scene["elements"][0]
        photo.update(id=f"photo{i}", related_element_ids=[])
        photo["beats"][0].update(
            start_ms=i * 2000,
            end_ms=(i + 1) * 2000,
            start_state="scale=1 x_pct=0 y_pct=0",
            end_state="scale=1.0001 x_pct=0 y_pct=0",
        )
        scenes.append(scene)
    plan = MotionPlan.model_validate({**data["motion_plan"], "scenes": scenes, "duration_ms": 8000})
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate_photo_energy(plan)
