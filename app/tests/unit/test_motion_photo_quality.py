"""M1–M3 admission uses the captured contract and actual plan times, never pixels."""

from copy import deepcopy

import pytest

from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_photo_intent import (
    PHOTO_INTENT_CONTRACT_V1,
    PHOTO_INTENT_CONTRACT_V2,
    PHOTO_INTENT_CONTRACT_V3,
)
from app.services.motion_photo_intent import (
    PHOTO_INTENT_CONTRACT_V5 as PHOTO_INTENT_CONTRACT,
)
from app.services.motion_plan import validate_motion_plan
from app.tests.unit.test_motion_photo_planning import ASSET_ID, photo_case


def quality_case(*, logo=True):
    _, prepared, plan = photo_case()
    data = plan.model_dump(mode="json")
    data.update(staging=None, scene_direction=None, audiovisual=None)
    final = data["motion_plan"]["scenes"][-1]
    final["elements"][0]["beats"][0]["end_ms"] = 13000
    if logo:
        brand = deepcopy(final["elements"][-1])
        brand.update(id="brand", asset_id="assets/logo.png")
        brand["beats"][0].update(start_ms=13000, start_state="scale=1", end_state="scale=1.025")
        final["elements"].append(brand)
    return data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, {ASSET_ID, "assets/logo.png"} if logo else {ASSET_ID}


def validate(data, context, assets):
    plan = HTMLMotionComposition.model_validate({**data, "html": "<main></main>", "scene_init": "window.seek=()=>{}"})
    validate_motion_plan(plan, context, duration_ms=plan.motion_plan.duration_ms, asset_ids=assets)


@pytest.mark.parametrize(
    "version", [None, PHOTO_INTENT_CONTRACT_V1, PHOTO_INTENT_CONTRACT_V2, PHOTO_INTENT_CONTRACT_V3]
)
def test_historical_contracts_keep_long_holds_and_no_closing_motion(version):
    data, _, assets = quality_case()
    for scene in data["motion_plan"]["scenes"]:
        for element in scene["elements"]:
            for beat in element["beats"]:
                beat["phase"] = "hold"
    validate(data, {"photo_intent_contract": version}, assets)


@pytest.mark.parametrize("logo", [False, True])
def test_valid_closing_motion_and_plan_identity(logo):
    data, context, assets = quality_case(logo=logo)
    before = deepcopy(data)
    validate(data, context, assets)
    assert data == before


@pytest.mark.parametrize("duration,allowed", [(2000, True), (2500, True), (2501, False)])
@pytest.mark.parametrize("split", [False, True])
def test_hold_limit_including_consecutive_beats(duration, allowed, split):
    data, context, assets = quality_case()
    element = data["motion_plan"]["scenes"][0]["elements"][0]
    beat = element["beats"][0]
    beat.update(phase="hold", start_ms=100, end_ms=100 + duration)
    if split:
        other = deepcopy(beat)
        beat["end_ms"] = other["start_ms"] = 1100
        element["beats"].append(other)
    if allowed:
        validate(data, context, assets)
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTO_HOLD_TOO_LONG"):
            validate(data, context, assets)


def test_separate_holds_reset_after_movement_or_gap():
    data, context, assets = quality_case()
    element = data["motion_plan"]["scenes"][0]["elements"][0]
    base = element["beats"][0]
    element["beats"] = [
        dict(base, phase="hold", start_ms=0, end_ms=2500),
        dict(base, phase="transform", start_ms=2500, end_ms=3000),
        dict(base, phase="hold", start_ms=3000, end_ms=5500),
        dict(base, phase="hold", start_ms=6000, end_ms=8500),
    ]
    validate(data, context, assets)


@pytest.mark.parametrize("closing_start,allowed", [(12500, True), (12499, True), (15000, False)])
def test_closing_window_uses_plan_times(closing_start, allowed):
    data, context, assets = quality_case(logo=False)
    data["motion_plan"]["scenes"][-1]["elements"][0]["beats"][0]["end_ms"] = closing_start
    if allowed:
        validate(data, context, assets)
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTO_CLOSING_WINDOW_INVALID"):
            validate(data, context, assets)


@pytest.mark.parametrize("change", ["gap", "hold", "same_state", "early_end", "early_only"])
@pytest.mark.parametrize("target", ["photo", "logo"])
def test_closing_requires_continuous_declared_motion(change, target):
    data, context, assets = quality_case()
    element = data["motion_plan"]["scenes"][-1]["elements"][-2 if target == "photo" else -1]
    beat = element["beats"][0]
    if change == "gap":
        beat["start_ms"] = 13001
    elif change == "hold":
        beat.update(phase="hold", start_ms=13000)
    elif change == "same_state":
        beat["end_state"] = beat["start_state"]
    elif change == "early_only":
        beat.update(start_ms=7500, end_ms=12500)
    else:
        beat["end_ms"] = 14999
    with pytest.raises(AuthError, match="MOTION_PHOTO_CLOSING_MOTION_REQUIRED"):
        validate(data, context, assets)


@pytest.mark.parametrize("missing", ["photo", "logo"])
def test_closing_materials_cannot_be_replaced_by_a_logo_in_an_earlier_scene(missing):
    data, context, assets = quality_case()
    final = data["motion_plan"]["scenes"][-1]
    removed = final["elements"].pop(-2 if missing == "photo" else -1)
    # Preserve logo declaration elsewhere: the old L1 gate alone would accept this.
    if missing == "logo":
        removed["beats"][0].update(start_ms=0, end_ms=1000)
        data["motion_plan"]["scenes"][0]["elements"].append(removed)
    with pytest.raises(AuthError, match="MOTION_PHOTO_CLOSING_MATERIAL_REQUIRED"):
        validate(data, context, assets)


def test_staging_handoff_overrides_enter_times_and_missing_plan_is_rejected():
    _, prepared, plan = photo_case()
    validate_motion_plan(plan, prepared.context, duration_ms=15000, asset_ids={ASSET_ID})
    with pytest.raises(AuthError, match="MOTION_PLAN_REQUIRED"):
        validate_motion_plan(
            plan.model_copy(
                update={"motion_plan": None, "staging": None, "scene_direction": None, "audiovisual": None}
            ),
            {"photo_intent_contract": PHOTO_INTENT_CONTRACT},
            duration_ms=15000,
            asset_ids=set(),
        )


def test_single_scene_without_enter_uses_scene_start_and_multiple_transforms_are_continuous():
    data, context, assets = quality_case(logo=False)
    final = data["motion_plan"]["scenes"][-1]
    final.update(start_ms=0, end_ms=2500)
    final["elements"] = final["elements"][-1:]
    image = final["elements"][0]
    beat = image["beats"][0]
    image["beats"] = [dict(beat, start_ms=0, end_ms=1000), dict(beat, start_ms=1000, end_ms=2500)]
    data["motion_plan"].update(scenes=[final], duration_ms=2500)
    validate(data, context, assets)
