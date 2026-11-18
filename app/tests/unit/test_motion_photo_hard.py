"""R1–R3 hard admission, immutable versions and executable guard wiring."""

import hashlib
import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.motion_generation import MotionStagedPlanningOutput
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_generation import expand_compact_output
from app.services.motion_photo_hard import (
    GUARD_PATH,
    GUARD_SHA256,
    GUARD_V2_PATH,
    guarded_photo_scene_init,
    validate_photo_layout,
)
from app.services.motion_photo_intent import (
    PHOTO_INTENT_CONTRACT,
    PHOTO_INTENT_CONTRACT_V8,
    PHOTO_INTENT_CONTRACT_V9,
    implementation_intent,
)
from app.services.motion_plan import validate_motion_plan
from app.tests.unit.test_motion_photo_planning import ASSET_ID, photo_case


def hard_case():
    _, _, base = photo_case()
    data = base.model_dump(mode="json")
    data.update(staging=None, audiovisual=None, scene_direction=None)
    template = data["motion_plan"]["scenes"][0]
    scenes = []
    for index in range(3):
        scene = deepcopy(template)
        photo = deepcopy(scene["elements"][0])
        start, end = index * 5000, (index + 1) * 5000
        photo.update(id=f"photo{index}", related_element_ids=[])
        photo["beats"][0].update(start_ms=start, end_ms=end)
        scene.update(
            id=f"scene{index}",
            start_ms=start,
            end_ms=end,
            keyframe_ms=start + 2500,
            elements=[photo],
            photo_layout={"mode": "cover", "primary_element_id": photo["id"], "crop_exception": None},
        )
        scenes.append(scene)
    final = scenes[-1]
    brand = deepcopy(final["elements"][0])
    brand.update(id="brand", asset_id="assets/logo.png")
    brand["beats"][0].update(end_state="scale=1.065 x_pct=0 y_pct=0")
    cta = deepcopy(brand)
    cta.update(id="cta", role="text", asset_id=None)
    final["elements"] += [brand, cta]
    final["photo_closing"] = {"brand_element_id": "brand", "surface": "transparent_overlay", "cta_element_id": "cta"}
    data["motion_plan"]["scenes"] = scenes
    return data


def artifact(data):
    return HTMLMotionComposition.model_validate(dict(data, html="<main></main>", scene_init="window.seek=()=>{}"))


def validate(data):
    validate_motion_plan(
        artifact(data),
        {"photo_intent_contract": PHOTO_INTENT_CONTRACT},
        duration_ms=15000,
        asset_ids={ASSET_ID, "assets/logo.png"},
    )


def exception(scene):
    scene["photo_layout"].update(
        mode="contain_blur",
        crop_exception={
            "asset_id": ASSET_ID,
            "essential_region": "Cup and saucer at opposite edges",
            "alternatives_rejected": "Other authorized frame loses the product",
            "safe_motion": "Use related text pan",
        },
    )


def test_cover_and_one_structured_exception_accept_without_mutation():
    data = hard_case()
    validate(data)
    exception(data["motion_plan"]["scenes"][1])
    before = deepcopy(data)
    validate(data)
    assert data == before


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "LAYOUT_REQUIRED"),
        ("foreign", "LAYOUT_REQUIRED"),
        ("no_reason", "CROP_EXCEPTION_REQUIRED"),
        ("wrong_asset", "CROP_EXCEPTION_REQUIRED"),
        ("blank", "CROP_EXCEPTION_REQUIRED"),
        ("cover_exception", "LAYOUT_INVALID"),
        ("two", "COVER_DOMINANCE_REQUIRED"),
        ("all", "COVER_DOMINANCE_REQUIRED"),
        ("long", "COVER_DOMINANCE_REQUIRED"),
        ("no_photo", "LAYOUT_INVALID"),
    ],
)
def test_layout_rejects_stories_and_exception_laundering(change, code):
    data = hard_case()
    scenes = data["motion_plan"]["scenes"]
    layout = scenes[1]["photo_layout"]
    if change == "missing":
        scenes[1].pop("photo_layout")
    elif change == "foreign":
        layout["primary_element_id"] = "photo0"
    elif change == "no_photo":
        scenes[1]["elements"][0].update(role="text", asset_id=None)
    else:
        exception(scenes[1])
        if change == "no_reason":
            layout["crop_exception"] = None
        elif change == "wrong_asset":
            layout["crop_exception"]["asset_id"] = "assets/photo-other.png"
        elif change == "blank":
            layout["crop_exception"]["safe_motion"] = "  "
        elif change == "cover_exception":
            layout["mode"] = "cover"
        elif change in ("two", "all"):
            exception(scenes[0])
            if change == "all":
                exception(scenes[2])
        else:
            # An overlapping exception cannot count simultaneous cover time twice.
            scenes[1]["start_ms"] = 0
            scenes[1]["elements"][0]["beats"][0]["start_ms"] = 0
    with pytest.raises(AuthError, match="MOTION_PHOTO_" + code):
        validate_photo_layout(artifact(data), handoff_end=10000)


@pytest.mark.parametrize("change", ["missing", "wrong_cta", "image_cta", "wrong_brand", "missing_brand", "early"])
def test_closing_overlay_binds_real_final_elements(change):
    data = hard_case()
    final = data["motion_plan"]["scenes"][-1]
    closing = final["photo_closing"]
    if change == "missing":
        final.pop("photo_closing")
    elif change == "wrong_cta":
        closing["cta_element_id"] = "photo0"
    elif change == "image_cta":
        closing["cta_element_id"] = "brand"
    elif change == "wrong_brand":
        closing["brand_element_id"] = "photo2"
    elif change == "missing_brand":
        closing["brand_element_id"] = None
    else:
        data["motion_plan"]["scenes"][0]["photo_closing"] = closing
    with pytest.raises(AuthError, match="MOTION_PHOTO_CLOSING_OVERLAY_REQUIRED"):
        validate(data)


@pytest.mark.parametrize(
    "field,value",
    [("curve", {"kind": "ease_out", "parameters": []}), ("start_state", "scale=1"), ("end_state", "static")],
)
def test_closing_requires_executable_numeric_beats(field, value):
    data = hard_case()
    data["motion_plan"]["scenes"][-1]["elements"][1]["beats"][0][field] = value
    with pytest.raises(AuthError, match="MOTION_PHOTO_EXECUTABLE_MOTION_REQUIRED"):
        validate(data)


def test_plate_is_not_a_valid_declared_surface():
    data = hard_case()
    data["motion_plan"]["scenes"][-1]["photo_closing"]["surface"] = "cream_card"
    with pytest.raises(ValidationError):
        artifact(data)


def test_v8_replay_without_fields_keeps_original_gates_and_executor():
    data = hard_case()
    for scene in data["motion_plan"]["scenes"]:
        scene.pop("photo_layout")
        scene.pop("photo_closing", None)
    old = artifact(data)
    context = {"photo_intent_contract": PHOTO_INTENT_CONTRACT_V8}
    validate_motion_plan(old, context, duration_ms=15000, asset_ids={ASSET_ID, "assets/logo.png"})
    assert guarded_photo_scene_init(old, context) == old.scene_init
    assert "photo_layout" not in json.dumps(old.model_dump(mode="json"))
    with pytest.raises(AuthError, match="MOTION_PHOTO_LAYOUT_REQUIRED"):
        validate(data)


def test_guard_pin_exact_plan_and_no_audio_or_html_mutation(monkeypatch, tmp_path):
    comp = artifact(hard_case())
    before = comp.model_dump(mode="json")
    code = guarded_photo_scene_init(comp, {"photo_intent_contract": PHOTO_INTENT_CONTRACT})
    assert code.startswith(comp.scene_init)
    assert hashlib.sha256(GUARD_V2_PATH.read_bytes()).hexdigest() == PHOTO_INTENT_CONTRACT["dom_guard_sha256"]
    assert '"handoff_end": 10000' in code and '"id": "photo1"' in code
    assert comp.model_dump(mode="json") == before
    fake = tmp_path / "guard.js"
    fake.write_text("changed")
    monkeypatch.setattr("app.services.motion_photo_hard.GUARD_V2_PATH", fake)
    with pytest.raises(AuthError, match="MOTION_PHOTO_GUARD_CHANGED"):
        guarded_photo_scene_init(comp, {"photo_intent_contract": PHOTO_INTENT_CONTRACT})


def test_staged_plan_projection_and_compact_wire_keep_layout_and_closing():
    _, prepared, plan = photo_case()
    projection = implementation_intent(plan)
    assert projection["scenes"][0]["photo_layout"] == plan.motion_plan.scenes[0].photo_layout.model_dump(mode="json")
    assert projection["scenes"][-1]["photo_closing"] == plan.motion_plan.scenes[-1].photo_closing.model_dump(
        mode="json"
    )
    schema = MotionStagedPlanningOutput.model_json_schema()
    assert "photo_layout" in schema["$defs"]["CompactMotionScene"]["properties"]
    # Expansion only rewrites beats; optional fields are retained unchanged.
    data = {"motion_plan": {"scenes": [{"photo_layout": {"mode": "cover"}, "elements": []}]}}
    assert expand_compact_output(deepcopy(data)) == data
    comp = artifact(plan.model_dump(mode="json"))
    assert '"handoff_end": 13000' in guarded_photo_scene_init(comp, prepared.context)


def test_nonphotographic_scene_without_layout_and_no_logo_are_supported():
    data = hard_case()
    first = data["motion_plan"]["scenes"][0]
    first.pop("photo_layout")
    first["elements"][0].update(role="text", asset_id=None)
    final = data["motion_plan"]["scenes"][-1]
    final["elements"] = [e for e in final["elements"] if e["id"] != "brand"]
    final["photo_closing"]["brand_element_id"] = None
    validate_photo_layout(artifact(data), handoff_end=10000)


def test_guard_keeps_related_overlay_and_skips_pre_handoff_logo_entry():
    data = hard_case()
    final = data["motion_plan"]["scenes"][-1]
    photo, brand, cta = final["elements"]
    photo["related_element_ids"] = ["cta"]
    brand["beats"].insert(0, dict(brand["beats"][0], phase="enter", end_ms=11000))
    brand["beats"][1]["start_ms"] = 11000
    code = guarded_photo_scene_init(artifact(data), {"photo_intent_contract": PHOTO_INTENT_CONTRACT})
    assert '"handoff_end": 11000' in code


def test_numeric_equivalent_states_cannot_fake_closing_motion():
    data = hard_case()
    data["motion_plan"]["scenes"][-1]["elements"][1]["beats"][0]["end_state"] = "scale=1.040 x_pct=0 y_pct=0"
    with pytest.raises(AuthError, match="MOTION_PHOTO_EXECUTABLE_MOTION_REQUIRED"):
        validate(data)


def test_v8_capture_preserves_contract_skill_repertoire_and_rules():
    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_photos import PHOTO_MOTION_RULES_V8
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import _SKILLS, load_motion_skill

    request, prepared, _ = photo_case()
    old = deepcopy(prepared.context)
    identifier = "instagram-reel-photo-v19"
    digest = _SKILLS[identifier][1]
    old.update(
        photo_intent_contract=PHOTO_INTENT_CONTRACT_V8,
        repertoire=capture_repertoire("business-reel-v11"),
        skill={"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")},
    )
    old["photo_motion"]["rules"] = PHOTO_MOTION_RULES_V8
    replay = capture_motion_guidance(request, previous=old)
    for key in ("photo_intent_contract", "skill", "repertoire", "photo_motion"):
        assert replay[key] == old[key]


def test_v9_guard_bytes_and_execution_remain_pinned():
    comp = artifact(hard_case())
    code = guarded_photo_scene_init(comp, {"photo_intent_contract": PHOTO_INTENT_CONTRACT_V9})
    assert (
        GUARD_SHA256
        == hashlib.sha256(GUARD_PATH.read_bytes()).hexdigest()
        == PHOTO_INTENT_CONTRACT_V9["dom_guard_sha256"]
    )
    assert "exit_handoff" not in code
    assert "minimumOpacity" not in code


@pytest.mark.parametrize(
    "duration,overlap,allowed", [(400, True, True), (500, True, True), (501, True, False), (400, False, False)]
)
def test_only_bounded_approved_overlaps_receive_exit_handoff(duration, overlap, allowed):
    from app.services.motion_photo_hard import _exit_handoff

    _, _, plan = photo_case()
    data = plan.model_dump(mode="json")
    scenes = data["motion_plan"]["scenes"]
    h = data["staging"]["moments"][0]["transition"]
    start = scenes[1]["start_ms"] if overlap else scenes[1]["start_ms"] - 1
    h.update(start_ms=start, end_ms=start + duration)
    comp = artifact(data)
    assert bool(_exit_handoff(comp, scenes[0]["id"], PHOTO_INTENT_CONTRACT)) == allowed
    assert _exit_handoff(comp, scenes[0]["id"], PHOTO_INTENT_CONTRACT_V9) == {}
    assert _exit_handoff(comp, scenes[-1]["id"], PHOTO_INTENT_CONTRACT) == {}


@pytest.mark.parametrize("end,allowed", [(13500, True), (13501, False), (15000, False)])
def test_cta_reading_window_has_hard_minimum_without_extending_handoff(end, allowed):
    from app.services.motion_photo_hard import photo_cta_read_start

    data = hard_case()
    final = data["motion_plan"]["scenes"][-1]
    cta = final["elements"][-1]
    cta["beats"][0].update(phase="enter", end_ms=end)
    comp = artifact(data)
    if allowed:
        assert photo_cta_read_start(comp, 11000) == end
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTO_CTA_WINDOW_INVALID"):
            photo_cta_read_start(comp, 11000)
