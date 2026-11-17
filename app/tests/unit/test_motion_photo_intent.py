"""A3 preserves plan intent and historical snapshots without effect requirements."""

import json
from dataclasses import replace

import pytest

from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_generation import construction_plan_hash
from app.services.motion_materials import prepare_implementation_materials
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, implementation_intent, photo_intent_rules
from app.tests.unit.test_motion_ai import provider, request
from app.tests.unit.test_motion_photo_planning import photo_case


def test_capture_and_replay_do_not_upgrade_historical_requests():
    body, prepared, _ = photo_case()
    assert prepared.context["photo_intent_contract"] == PHOTO_INTENT_CONTRACT
    assert capture_motion_guidance(body, previous=prepared.context)["photo_intent_contract"] == PHOTO_INTENT_CONTRACT
    historical = dict(prepared.context)
    historical.pop("photo_intent_contract")
    assert "photo_intent_contract" not in capture_motion_guidance(body, previous=historical)
    assert photo_intent_rules(historical) == ""
    with pytest.raises(AuthError, match="MOTION_PHOTO_INTENT_CONTRACT_INVALID"):
        photo_intent_rules({"photo_intent_contract": {"version": "unknown"}})


def test_projection_preserves_typography_progression_handoff_and_plan_hash():
    _, _, plan = photo_case()
    before = plan.model_dump(mode="json")
    intent = implementation_intent(plan)
    assert intent["plan_sha256"] == construction_plan_hash(plan)
    for scene, projection, direction, moment in zip(
        plan.motion_plan.scenes, intent["scenes"], plan.scene_direction.scenes, plan.staging.moments, strict=True
    ):
        assert projection["direction"] == direction.model_dump(mode="json")
        assert projection["progression_and_handoff"] == moment.model_dump(mode="json")
        assert projection["typography"] == [e.model_dump(mode="json") for e in scene.elements if e.role == "text"]
        assert (projection["start_ms"], projection["end_ms"]) == (scene.start_ms, scene.end_ms)
    assert plan.model_dump(mode="json") == before


@pytest.mark.parametrize("implementation", [False, True])
def test_real_provider_receives_intent_for_planning_and_code(implementation):
    _, prepared, plan = photo_case()
    if implementation:
        prepared = prepare_implementation_materials(plan, prepared)
    job = replace(
        request(),
        context=prepared.context,
        assets=prepared.assets,
        source_frames=(),
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
        construction_plan=plan if implementation else None,
    )
    payload = provider().build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert PHOTO_INTENT_CONTRACT["rules"] in payload["instructions"]
    if implementation:
        assert sent["photo_implementation_intent"] == implementation_intent(plan)
        assert sent["plan_sha256"] == sent["photo_implementation_intent"]["plan_sha256"]
    else:
        assert "photo_implementation_intent" not in sent
