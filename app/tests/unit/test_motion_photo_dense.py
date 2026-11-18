"""Q2 density, interval union, global edges and historical replay."""

from copy import deepcopy

import pytest

from app.schemas.motion_plan import MotionPlan
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_energy import validate_photo_energy
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, PHOTO_INTENT_CONTRACT_V7
from app.services.motion_photos import PHOTO_MOTION_RULES_V7
from app.services.motion_repertoire import capture_repertoire
from app.services.motion_skills import _SKILLS, load_motion_skill
from app.tests.unit.test_motion_photo_planning import photo_case
from app.tests.unit.test_motion_photo_quality import quality_case, validate


def dense_plan(intervals):
    data, _, _ = quality_case(logo=False)
    plan = data["motion_plan"]
    scene = plan["scenes"][0]
    scene.update(start_ms=0, end_ms=5000)
    photo = scene["elements"][0]
    photo["related_element_ids"] = []
    base = photo["beats"][0]
    photo["beats"] = [
        dict(
            base,
            start_ms=start,
            end_ms=end,
            phase="transform",
            start_state="scale=1 x_pct=0 y_pct=0",
            end_state="scale=1 x_pct=10 y_pct=0",
            curve={"kind": "linear", "parameters": []},
        )
        for start, end in intervals
    ]
    scene["elements"] = [photo]
    plan.update(duration_ms=5000, scenes=[scene])
    return MotionPlan.model_validate(plan)


@pytest.mark.parametrize(
    "intervals,allowed",
    [
        ([(500, 4500)], True),
        ([(501, 5000)], False),
        ([(0, 4499)], False),
        ([(0, 2000), (2501, 5000)], False),
        ([(0, 2000), (2500, 4500)], True),
        ([(0, 1000), (1500, 2500), (3000, 4000), (4500, 5000)], False),
    ],
)
def test_density_and_global_gap_boundaries(intervals, allowed):
    plan = dense_plan(intervals)
    validate_photo_energy(plan, stronger=True)  # v7 keeps its semantics
    if allowed:
        validate_photo_energy(plan, stronger=True, dense=True)
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
            validate_photo_energy(plan, stronger=True, dense=True)


def test_overlapping_related_overlay_does_not_double_count_density():
    plan = dense_plan([(0, 1000), (1500, 2500), (3000, 4000), (4500, 5000)])
    photo = plan.scenes[0].elements[0]
    overlay = photo.model_copy(update={"id": "overlay", "role": "text", "asset_id": None})
    photo = photo.model_copy(update={"related_element_ids": ("overlay",)})
    scene = plan.scenes[0].model_copy(update={"elements": (photo, overlay)})
    plan = plan.model_copy(update={"scenes": (scene,)})
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate_photo_energy(plan, stronger=True, dense=True)


def test_current_contract_routes_to_density_gate_but_v7_replays():
    data, _, assets = quality_case()
    photo = data["motion_plan"]["scenes"][0]["elements"][0]
    for scene in data["motion_plan"]["scenes"]:
        for element in scene["elements"]:
            for b in element["beats"]:
                b.update(
                    start_state="scale=1 x_pct=0 y_pct=0",
                    end_state="scale=1 x_pct=20 y_pct=0",
                    curve={"kind": "linear", "parameters": []},
                )
    photo["beats"][0]["start_ms"] = 501
    validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT_V7}, assets)
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets)
    photo["beats"][0]["start_ms"] = 0
    validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets)


def test_v7_capture_preserves_all_pinned_guidance():
    request, prepared, _ = photo_case()
    old = deepcopy(prepared.context)
    identifier = "instagram-reel-photo-v18"
    digest = _SKILLS[identifier][1]
    old.update(
        photo_intent_contract=PHOTO_INTENT_CONTRACT_V7,
        repertoire=capture_repertoire("business-reel-v10"),
        skill={"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")},
    )
    old["photo_motion"]["rules"] = PHOTO_MOTION_RULES_V7
    result = capture_motion_guidance(request, previous=old)
    for key in ("photo_intent_contract", "repertoire", "skill", "photo_motion"):
        assert result[key] == old[key]


def test_other_scene_cannot_supply_missing_density():
    plan = dense_plan([(0, 5000)])
    first = plan.scenes[0]
    # A fully energetic overlapping scene must not hide an idle photographic scene.
    second = first.model_copy(deep=True, update={"id": "idle"})
    idle = second.elements[0].model_copy(update={"beats": ()})
    second = second.model_copy(update={"elements": (idle,)})
    plan = plan.model_copy(update={"scenes": (first, second)})
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate_photo_energy(plan, stronger=True, dense=True)


def test_related_overlay_can_fill_safe_photo_gaps():
    plan = dense_plan([(500, 4500)])
    photo = plan.scenes[0].elements[0]
    overlay = photo.model_copy(deep=True, update={"id": "overlay", "role": "graphic", "asset_id": None})
    photo = photo.model_copy(update={"related_element_ids": ("overlay",), "beats": ()})
    scene = plan.scenes[0].model_copy(update={"elements": (photo, overlay)})
    plan = plan.model_copy(update={"scenes": (scene,)})
    validate_photo_energy(plan, stronger=True, dense=True)
    photo = photo.model_copy(update={"related_element_ids": ()})
    scene = scene.model_copy(update={"elements": (photo, overlay)})
    plan = plan.model_copy(update={"scenes": (scene,)})
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate_photo_energy(plan, stronger=True, dense=True)
