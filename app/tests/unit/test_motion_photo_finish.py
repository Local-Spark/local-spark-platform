"""S1–S3 reject the v9 regressions without upgrading historical captures."""

from copy import deepcopy

import pytest

from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_finish import (
    PHOTO_FINISH_CONTRACT,
    finish_enabled,
    finish_scene_init,
    validate_photo_finish,
)
from app.services.motion_photo_hard import guarded_photo_scene_init
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, photo_intent_rules
from app.tests.unit.test_motion_photo_hard import artifact, exception, hard_case
from app.tests.unit.test_motion_photo_planning import ASSET_ID, photo_case

CTX = {"photo_intent_contract": PHOTO_INTENT_CONTRACT, "photo_finish_contract": PHOTO_FINISH_CONTRACT}


def finish_case():
    data = hard_case()
    final = data["motion_plan"]["scenes"][-1]
    final["elements"][1]["beats"][0]["end_state"] = "scale=1.10 x_pct=0 y_pct=0"
    final["elements"][-1]["beats"][0].update(phase="enter", end_ms=11000, end_state="scale=1.10 x_pct=0 y_pct=0")
    _, _, plan = photo_case()
    data["staging"] = plan.staging.model_dump(mode="json")
    data["staging"]["photo_identity_reviews"] = [
        {"asset_id": ASSET_ID, "verdict": "clean", "evidence": "No visible marks"}
    ]
    return data


def check(data, *, context=CTX, logo=True):
    validate_photo_finish(
        artifact(data), context, handoff_end=11000, asset_ids={ASSET_ID, "assets/logo.png"} if logo else {ASSET_ID}
    )


def test_new_capture_and_old_replay_preserve_v10_bytes_and_music():
    body, prepared, _ = photo_case()
    old = deepcopy(prepared.context)
    old.pop("photo_polish_contract", None)
    old.pop("photo_finish_contract")
    replay = capture_motion_guidance(body, previous=old)
    assert "photo_finish_contract" not in replay
    assert replay["photo_intent_contract"] == PHOTO_INTENT_CONTRACT
    new = capture_motion_guidance(body)
    assert new["photo_finish_contract"] == PHOTO_FINISH_CONTRACT
    assert capture_motion_guidance(body, previous=new)["photo_finish_contract"] == PHOTO_FINISH_CONTRACT
    assert new["photo_motion"] == replay["photo_motion"]
    assert photo_intent_rules(CTX).endswith(PHOTO_FINISH_CONTRACT["rules"])
    assert photo_intent_rules(old) == PHOTO_INTENT_CONTRACT["rules"]


def test_policy_pin_and_absent_policy():
    assert not finish_enabled({})
    with pytest.raises(AuthError, match="FINISH_CONTRACT_CHANGED"):
        finish_enabled({"photo_finish_contract": {"version": "changed"}})
    check(hard_case(), context={})
    comp = artifact(hard_case())
    assert finish_scene_init(comp, {}) == comp.scene_init
    assert "photo_identity_reviews" not in photo_case()[2].staging.model_dump(mode="json")


@pytest.mark.parametrize("duration,accepted", [(2000, True), (2001, False), (5000, False)])
def test_stories_exception_has_short_hard_limit(duration, accepted):
    data = finish_case()
    scene = data["motion_plan"]["scenes"][1]
    exception(scene)
    scene["end_ms"] = 5000 + duration
    scene["elements"][0]["beats"][0]["end_ms"] = scene["end_ms"]
    scene["keyframe_ms"] = 6000
    # Following cover begins when the short exception ends.
    data["motion_plan"]["scenes"][-1]["start_ms"] = scene["end_ms"]
    if accepted:
        check(data)
    else:
        with pytest.raises(AuthError, match="SHORT_EXCEPTION_REQUIRED"):
            check(data)


@pytest.mark.parametrize("index", [0, 1])
def test_tiny_closing_photo_or_logo_motion_is_rejected_even_with_energetic_other_elements(index):
    data = finish_case()
    data["motion_plan"]["scenes"][-1]["elements"][index]["beats"][0]["end_state"] = "scale=1.041 x_pct=0 y_pct=0"
    with pytest.raises(AuthError, match="CLOSING_ENERGY_REQUIRED"):
        check(data)


@pytest.mark.parametrize(
    "phase,end,code", [("hold", 11000, "TYPOGRAPHY_REQUIRED"), ("exit", 12000, "CTA_WINDOW_INVALID")]
)
def test_text_cannot_only_hold_or_exit_during_cta_reading(phase, end, code):
    data = finish_case()
    data["motion_plan"]["scenes"][-1]["elements"][-1]["beats"][0].update(phase=phase, end_ms=end)
    with pytest.raises(AuthError, match=code):
        check(data)


@pytest.mark.parametrize(
    "change", ["missing", "no_staging", "third_party", "uncertain", "blank", "foreign", "duplicate"]
)
def test_selected_third_party_and_unreviewed_materials_require_revision(change):
    data = finish_case()
    reviews = data["staging"]["photo_identity_reviews"]
    if change == "no_staging":
        data["staging"] = None
    elif change == "missing":
        data["staging"].pop("photo_identity_reviews")
    elif change in {"third_party", "uncertain"}:
        reviews[0]["verdict"] = change
        reviews[0]["evidence"] = "Legible Belize / Mackbear / watermark"
    elif change == "blank":
        reviews[0]["evidence"] = " "
    elif change == "foreign":
        reviews[0]["asset_id"] = "assets/photo-other.png"
    else:
        reviews.append(deepcopy(reviews[0]))
    with pytest.raises(AuthError, match="IDENTITY_REQUIRES_PLAN_REVISION"):
        check(data)
    check(data, logo=False)


def test_valid_finish_guard_is_ordered_before_v2_and_pinned(monkeypatch, tmp_path):
    data = finish_case()
    check(data)
    comp = artifact(data)
    code = guarded_photo_scene_init(comp, CTX)
    assert code.index("function installPhotoFinish") < code.index("function installPhotoGuard")
    assert '"typography":' in code
    fake = tmp_path / "changed.js"
    fake.write_text("changed")
    monkeypatch.setattr("app.services.motion_photo_finish.FINISH_PATH", fake)
    with pytest.raises(AuthError, match="FINISH_GUARD_CHANGED"):
        finish_scene_init(comp, CTX)
