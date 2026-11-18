"""CTA multi-shadow regression, immutable v2 and explicit capture pin."""

import hashlib
from copy import deepcopy

import pytest

from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_hard import guarded_photo_scene_init
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT
from app.services.motion_photo_readability import (
    PHOTO_READABILITY_CONTRACT,
    READABILITY_GUARD_PATH,
    readability_enabled,
)
from app.tests.unit.test_motion_photo_hard import artifact, hard_case
from app.tests.unit.test_motion_photo_planning import photo_case


def test_capture_pins_v3_and_never_upgrades_v10_replay():
    body, prepared, _ = photo_case()
    new = prepared.context
    assert new["photo_readability_contract"] == PHOTO_READABILITY_CONTRACT
    assert capture_motion_guidance(body, previous=new)["photo_readability_contract"] == PHOTO_READABILITY_CONTRACT
    old = deepcopy(new)
    old.pop("photo_readability_contract")
    replay = capture_motion_guidance(body, previous=old)
    assert "photo_readability_contract" not in replay
    assert replay["photo_intent_contract"] == PHOTO_INTENT_CONTRACT
    assert replay["photo_finish_contract"] == old["photo_finish_contract"]


def test_shadow_contract_validated_and_guard_pinned(monkeypatch, tmp_path):
    assert not readability_enabled({})
    assert readability_enabled({"photo_readability_contract": PHOTO_READABILITY_CONTRACT})
    with pytest.raises(AuthError, match="READABILITY_CONTRACT_CHANGED"):
        readability_enabled({"photo_readability_contract": {"version": "changed"}})
    assert (
        hashlib.sha256(READABILITY_GUARD_PATH.read_bytes()).hexdigest()
        == PHOTO_READABILITY_CONTRACT["dom_guard_sha256"]
    )
    comp = artifact(hard_case())
    ctx = {"photo_intent_contract": PHOTO_INTENT_CONTRACT}
    assert "readableShadow" not in guarded_photo_scene_init(comp, ctx)
    ctx["photo_readability_contract"] = PHOTO_READABILITY_CONTRACT
    assert "readableShadow" in guarded_photo_scene_init(comp, ctx)
    fake = tmp_path / "changed.js"
    fake.write_text("changed")
    monkeypatch.setattr("app.services.motion_photo_readability.READABILITY_GUARD_PATH", fake)
    with pytest.raises(AuthError, match="MOTION_PHOTO_GUARD_CHANGED"):
        guarded_photo_scene_init(comp, ctx)
