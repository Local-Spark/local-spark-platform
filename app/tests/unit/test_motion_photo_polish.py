"""Inventory-aware variety, snapshot isolation and supplement assembly."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_hard import guarded_photo_scene_init
from app.services.motion_photo_intent import photo_intent_rules
from app.services.motion_photo_polish import (
    PHOTO_POLISH_CONTRACT,
    polish_enabled,
    polish_scene_init,
    validate_photo_polish,
)
from app.tests.unit.test_motion_photo_finish import CTX, finish_case
from app.tests.unit.test_motion_photo_hard import artifact
from app.tests.unit.test_motion_photo_planning import photo_case

CONTEXT = {**CTX, "photo_polish_contract": PHOTO_POLISH_CONTRACT}


def case(count=3):
    data = finish_case()
    ids = [f"assets/photo-{i}.png" for i in range(count)]
    data["staging"]["photo_material_reviews"] = [
        dict(
            asset_id=a,
            subject="environment" if i == 0 else "detail",
            identity="clean",
            crop_safe=True,
            evidence="Synthetic clean wide shot; safe crop",
        )
        for i, a in enumerate(ids)
    ]
    for i, scene in enumerate(data["motion_plan"]["scenes"]):
        scene["elements"][0]["asset_id"] = ids[i % count]
    return data, set(ids)


def check(data, ids):
    validate_photo_polish(artifact(data), CONTEXT, asset_ids=ids)


def test_pin_replay_rules_and_missing_contract():
    body, prepared, _ = photo_case()
    new = capture_motion_guidance(body)
    assert new["photo_polish_contract"] == PHOTO_POLISH_CONTRACT
    assert capture_motion_guidance(body, previous=new)["photo_polish_contract"] == PHOTO_POLISH_CONTRACT
    old = deepcopy(prepared.context)
    old.pop("photo_polish_contract")
    replay = capture_motion_guidance(body, previous=old)
    assert "photo_polish_contract" not in replay
    for key in ("photo_motion", "photo_intent_contract", "photo_finish_contract", "photo_readability_contract"):
        assert replay[key] == new[key]
    assert photo_intent_rules(CONTEXT).endswith(PHOTO_POLISH_CONTRACT["rules"])
    assert not polish_enabled({})
    with pytest.raises(AuthError, match="POLISH_CONTRACT_CHANGED"):
        polish_enabled({"photo_polish_contract": {}})
    comp = artifact(finish_case())
    validate_photo_polish(comp, {}, asset_ids=set())
    assert polish_scene_init(comp, {}, "historical bytes") == "historical bytes"
    assert "photo_material_reviews" not in comp.staging.model_copy(update={"photo_material_reviews": None}).model_dump()


@pytest.mark.parametrize("count", [1, 2, 3])
def test_use_available_clean_material_without_inventing_more(count):
    data, ids = case(count)
    check(data, ids)
    before = deepcopy(data)
    check(data, ids)
    assert data == before


@pytest.mark.parametrize("change", ["absent", "no_staging", "duplicate", "foreign", "blank"])
def test_complete_inventory_evidence_required(change):
    data, ids = case()
    reviews = data["staging"]["photo_material_reviews"]
    if change == "absent":
        data["staging"].pop("photo_material_reviews")
    elif change == "no_staging":
        data["staging"] = None
    elif change == "duplicate":
        reviews[1] = deepcopy(reviews[0])
    elif change == "foreign":
        reviews[0]["asset_id"] = "assets/photo-foreign.png"
    else:
        reviews[0]["evidence"] = " "
    with pytest.raises(AuthError, match="INVENTORY_REVIEW_REQUIRED"):
        check(data, ids)


@pytest.mark.parametrize("change", ["third_party", "uncertain", "crop"])
def test_variety_never_overrides_identity_or_crop(change):
    data, ids = case()
    review = data["staging"]["photo_material_reviews"][0]
    review.update({"crop_safe": False} if change == "crop" else {"identity": change})
    with pytest.raises(AuthError, match="MATERIAL_INELIGIBLE"):
        check(data, ids)
    for scene in data["motion_plan"]["scenes"]:
        if scene["elements"][0]["asset_id"] == review["asset_id"]:
            scene["elements"][0]["asset_id"] = "assets/photo-1.png"
    check(data, ids)


@pytest.mark.parametrize("change", ["loop", "short", "overlap", "no_layout", "foreign_primary", "empty"])
def test_short_or_repeated_photos_do_not_meet_diversity(change):
    data, ids = case()
    scene = data["motion_plan"]["scenes"][0]
    if change == "loop":
        scene["elements"][0]["asset_id"] = "assets/photo-1.png"
    elif change == "short":
        scene.update(end_ms=1499, keyframe_ms=1000)
        scene["elements"][0]["beats"][0]["end_ms"] = 1499
        data["motion_plan"]["scenes"][1]["start_ms"] = 1499
    elif change == "overlap":
        data["motion_plan"]["scenes"][1]["start_ms"] = 1000
    elif change == "no_layout":
        scene["photo_layout"] = None
    elif change == "foreign_primary":
        scene["photo_layout"]["primary_element_id"] = "missing"
    else:
        ids = set()
        data["staging"]["photo_material_reviews"] = []
        for s in data["motion_plan"]["scenes"]:
            s["elements"][0].update(asset_id=None, role="text")
    with pytest.raises(AuthError, match="DIVERSITY_REQUIRED"):
        check(data, ids)


def test_environment_cannot_be_skipped_for_three_details_and_graphics_are_rejected():
    data, ids = case(4)
    for i, scene in enumerate(data["motion_plan"]["scenes"]):
        scene["elements"][0]["asset_id"] = f"assets/photo-{i + 1}.png"
    with pytest.raises(AuthError, match="ENVIRONMENT_BEAT_REQUIRED"):
        check(data, ids)
    data["motion_plan"]["scenes"][0]["elements"][0].update(role="graphic", asset_id=None)
    with pytest.raises(AuthError, match="DECORATION_FORBIDDEN"):
        check(data, ids)


def test_guard_composed_and_hash_checked(monkeypatch, tmp_path):
    comp = artifact(finish_case())
    code = guarded_photo_scene_init(comp, CONTEXT)
    assert (
        code.index("function installPhotoFinish")
        < code.index("function installPhotoPolish")
        < code.index("function installPhotoGuard")
    )
    fake = tmp_path / "changed.js"
    fake.write_text("changed")
    monkeypatch.setattr("app.services.motion_photo_polish.POLISH_PATH", fake)
    with pytest.raises(AuthError, match="POLISH_GUARD_CHANGED"):
        polish_scene_init(comp, CONTEXT, comp.scene_init)


def test_video_capture_does_not_receive_photo_supplement():
    from uuid import uuid4

    body, _, _ = photo_case()
    video = body.model_copy(update={"source_asset_id": uuid4(), "review_checkpoints": True, "automatic_plan": False})
    assert "photo_polish_contract" not in capture_motion_guidance(video)


@pytest.mark.parametrize("count", [1, 2, 3])
def test_soundtrack_is_not_an_inventory_photo_and_cannot_replace_missing_review(count):
    data, ids = case(count)
    ids.add("assets/photo-music.mp3")
    check(data, ids)
    data["staging"]["photo_material_reviews"].pop()
    with pytest.raises(AuthError, match="INVENTORY_REVIEW_REQUIRED"):
        check(data, ids)


def test_plan_admission_with_photo_soundtrack_preserves_all_other_gates():
    from dataclasses import replace

    from app.adapters.motion_html_renderer import RenderAsset
    from app.services.motion_illustrations import validate_declarations

    _, prepared, plan = photo_case()
    soundtrack = RenderAsset("assets/photo-music.mp3", "audio/mpeg", b"synthetic", "0" * 64)
    prepared = replace(prepared, assets=(*prepared.assets, soundtrack))
    validate_declarations(plan, prepared)
    data = plan.model_dump(mode="json")
    data["staging"]["photo_material_reviews"] = []
    with pytest.raises(AuthError, match="INVENTORY_REVIEW_REQUIRED"):
        validate_declarations(type(plan).model_validate(data), prepared)


def test_historical_v1_v2_keep_their_guard_and_rules():
    from app.services.motion_photo_polish import PHOTO_POLISH_CONTRACT_V1, PHOTO_POLISH_CONTRACT_V2

    body, prepared, _ = photo_case()
    comp = artifact(finish_case())
    for contract in (PHOTO_POLISH_CONTRACT_V1, PHOTO_POLISH_CONTRACT_V2):
        old = {**prepared.context, "photo_polish_contract": contract}
        assert capture_motion_guidance(body, previous=old)["photo_polish_contract"] == contract
        assert photo_intent_rules(old).endswith(contract["rules"])
        assert "const localScrim" not in polish_scene_init(comp, old, comp.scene_init)
    assert "const localScrim" in polish_scene_init(comp, CONTEXT, comp.scene_init)


def test_v3_replay_keeps_exact_rules_guard_and_old_energy_admission():
    from app.services.motion_photo_polish import PHOTO_POLISH_CONTRACT_V3, V3_POLISH_PATH

    body, prepared, _ = photo_case()
    context = {**prepared.context, "photo_polish_contract": PHOTO_POLISH_CONTRACT_V3}
    assert capture_motion_guidance(body, previous=context)["photo_polish_contract"] == PHOTO_POLISH_CONTRACT_V3
    assert photo_intent_rules(context).endswith(PHOTO_POLISH_CONTRACT_V3["rules"])
    data, ids = case()
    data["motion_plan"]["scenes"][1]["elements"][0]["beats"][0]["phase"] = "hold"
    comp = artifact(data)
    validate_photo_polish(comp, context, asset_ids=ids)
    assert V3_POLISH_PATH.read_text() in polish_scene_init(comp, context, "original")
    with pytest.raises(AuthError, match="CONTINUITY_REQUIRED"):
        check(data, ids)


@pytest.mark.parametrize("change", ["slow", "gap", "coverage", "overlap", "edge", "no_primary"])
def test_primary_continuity_cannot_be_replaced_by_text_or_overlapping_beats(change):
    data, ids = case(1)
    scene = data["motion_plan"]["scenes"][1]
    photo = scene["elements"][0]
    beat = photo["beats"][0]
    text = deepcopy(photo)
    text.update(id="moving-text", role="text", asset_id=None)
    photo["related_element_ids"] = [text["id"]]
    scene["elements"].append(text)
    if change == "slow":
        beat["end_state"] = "scale=1.041 x_pct=0 y_pct=0"
    elif change == "gap":
        beat["end_ms"] = 7000
        photo["beats"].append(dict(beat, start_ms=9000, end_ms=10000))
    elif change == "edge":
        beat["start_ms"] = 5501
    elif change == "no_primary":
        scene["photo_layout"] = None
    else:
        # Three 400ms gaps pass the gap cap but fail 80% total coverage.
        beat.update(start_ms=5400, end_ms=7000)
        photo["beats"].append(dict(beat, start_ms=7400, end_ms=9600))
        if change == "overlap":
            photo["beats"].append(deepcopy(beat))
    with pytest.raises(ValidationError if change == "overlap" else AuthError):
        check(data, ids)


def test_primary_continuity_boundary_and_clipping_do_not_mutate_plan():
    data, ids = case()
    beat = data["motion_plan"]["scenes"][1]["elements"][0]["beats"][0]
    beat.update(start_ms=5500, end_ms=9500, end_state="scale=1.08 x_pct=0 y_pct=0")
    before = deepcopy(data)
    from app.services.motion_photo_polish import PHOTO_POLISH_CONTRACT_V5

    validate_photo_polish(
        artifact(data), {**CONTEXT, "photo_polish_contract": PHOTO_POLISH_CONTRACT_V5}, asset_ids=ids
    )  # historical boundary: exactly 80%, gaps 500ms and scale 0.01/s
    with pytest.raises(AuthError, match="CONTINUOUS_TRANSFORM_REQUIRED"):
        check(data, ids)
    assert data == before
    beat.update(start_ms=4500, end_ms=10500, end_state="scale=1.10 x_pct=0 y_pct=0")
    with pytest.raises(ValidationError, match="inside the scene"):
        check(data, ids)


def handoff_case():
    data, ids = case()
    scene = data["motion_plan"]["scenes"][0]
    scene["end_ms"] = 5200
    beat = scene["elements"][0]["beats"][0]
    scene["elements"][0]["beats"].append(dict(beat, phase="exit", start_ms=5000, end_ms=5200))
    moment = data["staging"]["moments"][0]
    moment["scene_id"] = scene["id"]
    moment["transition"].update(start_ms=5000, end_ms=5200, next_scene_id=data["motion_plan"]["scenes"][1]["id"])
    return data, ids


@pytest.mark.parametrize("change", ["early", "mismatch", "absent", "long"])
def test_new_capture_rejects_unexecutable_handoff_before_implementation(change):
    data, ids = handoff_case()
    h = data["staging"]["moments"][0]["transition"]
    if change == "early":
        h["start_ms"] = 4900
    elif change == "mismatch":
        h["start_ms"] = 5050
    elif change == "absent":
        data["staging"]["moments"][0]["transition"] = None
    else:
        h["end_ms"] = 5600
    with pytest.raises(AuthError, match="HANDOFF_WINDOW_INVALID"):
        check(data, ids)


def test_handoff_valid_and_v4_replay_keeps_exact_executor(monkeypatch, tmp_path):
    from app.services.motion_photo_polish import PHOTO_POLISH_CONTRACT_V4

    data, ids = handoff_case()
    check(data, ids)
    data["staging"]["moments"][0]["transition"]["start_ms"] = 4900
    comp = artifact(data)
    old = {**CONTEXT, "photo_polish_contract": PHOTO_POLISH_CONTRACT_V4}
    validate_photo_polish(comp, old, asset_ids=ids)
    previous = polish_scene_init(comp, old, comp.scene_init)
    assert "PhotoTimingV1" not in previous
    assert '"continuity":' in previous
    new = polish_scene_init(comp, CONTEXT, comp.scene_init)
    assert new.index("PhotoTimingV1") < new.index(comp.scene_init)
    fake = tmp_path / "bad-timing.js"
    fake.write_text("changed")
    monkeypatch.setattr("app.services.motion_photo_polish.TIMING_PATH", fake)
    with pytest.raises(AuthError, match="TIMING_CHANGED"):
        polish_scene_init(comp, CONTEXT, comp.scene_init)
