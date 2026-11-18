"""O2 boundaries, gate routing and immutable N2 replay."""

from copy import deepcopy

import pytest

from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_energy import energetic
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V6
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V7 as PHOTO_INTENT_CONTRACT
from app.services.motion_photos import PHOTO_MOTION_RULES_V6
from app.services.motion_repertoire import capture_repertoire
from app.services.motion_skills import _SKILLS, load_motion_skill
from app.tests.unit.test_motion_photo_energy import beat
from app.tests.unit.test_motion_photo_planning import photo_case
from app.tests.unit.test_motion_photo_quality import quality_case, validate


@pytest.mark.parametrize(
    "end,ms,allowed",
    [
        ("scale=1.04 x_pct=0 y_pct=0", 2000, True),
        ("scale=1.039 x_pct=0 y_pct=0", 2000, False),
        ("scale=1.04 x_pct=0 y_pct=0", 2001, False),
        ("scale=1.02 x_pct=0 y_pct=0", 100, False),
        ("scale=1 x_pct=2 y_pct=0", 2000, True),
        ("scale=1 x_pct=0 y_pct=-2", 2000, True),
        ("scale=1 x_pct=1.99 y_pct=0", 100, False),
        ("scale=1 x_pct=2 y_pct=0", 2001, False),
        ("scale=1.039 x_pct=1.99 y_pct=1.99", 2000, False),
    ],
)
def test_rate_and_amplitude_must_both_pass_in_one_axis(end, ms, allowed):
    b = beat(end=end).model_copy(update={"end_ms": ms})
    assert energetic(b, stronger=True) is allowed


def test_v6_minimum_still_replays_but_v7_rejects_it():
    data, _, assets = quality_case()
    for scene in data["motion_plan"]["scenes"]:
        for element in scene["elements"]:
            if (element["asset_id"] or "").startswith("assets/photo-"):
                for b in element["beats"]:
                    b.update(
                        start_state="scale=1 x_pct=0 y_pct=0",
                        end_state=f"scale={1 + (b['end_ms'] - b['start_ms']) / 100000} x_pct=0 y_pct=0",
                    )
    validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT_V6}, assets)
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets)


def test_new_gate_accepts_crop_safe_related_overlay():
    data, _, assets = quality_case()
    for scene in data["motion_plan"]["scenes"]:
        photo = scene["elements"][0]
        overlay = deepcopy(photo)
        overlay.update(id=photo["id"] + "-copy", role="text", asset_id=None, related_element_ids=[])
        for b in photo["beats"]:
            b.update(start_state="scale=1 x_pct=0 y_pct=0", end_state="scale=1.001 x_pct=0 y_pct=0")
        for b in overlay["beats"]:
            b.update(start_state="scale=1 x_pct=0 y_pct=0", end_state="scale=1 x_pct=20 y_pct=0")
        photo["related_element_ids"] = [overlay["id"]]
        scene["elements"].append(overlay)
    validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets)
    for scene in data["motion_plan"]["scenes"]:
        scene["elements"][0]["related_element_ids"] = []
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate(data, {"photo_intent_contract": PHOTO_INTENT_CONTRACT}, assets)


def test_v6_snapshot_preserves_guidance_and_pinned_assets():
    body, prepared, _ = photo_case()
    old = deepcopy(prepared.context)
    old.update(photo_intent_contract=PHOTO_INTENT_CONTRACT_V6, repertoire=capture_repertoire("business-reel-v9"))
    identifier = "instagram-reel-photo-v17"
    digest = _SKILLS[identifier][1]
    old["skill"] = {"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")}
    old["photo_motion"]["rules"] = PHOTO_MOTION_RULES_V6
    result = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "repertoire", "skill", "photo_motion"):
        assert result[key] == old[key]
