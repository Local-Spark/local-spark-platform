"""Photo P1–P3 guidance preserves plan identity and historical snapshot semantics."""

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
    wire = json.dumps(payload, ensure_ascii=False)
    for conflicting in ("sem exigir movimento contínuo", "sem exigir zoom ou scale", "movimento suave quando pedido"):
        assert conflicting not in wire
    assert sent["authorized_context"]["staging_contract"]["version"] == "motion-staging-photo-v2"
    assert "Ken Burns contínuo" in sent["authorized_context"]["executor_contract"]["integration_policy"]
    if implementation:
        assert sent["photo_implementation_intent"] == implementation_intent(plan)
        assert sent["plan_sha256"] == sent["photo_implementation_intent"]["plan_sha256"]
    else:
        assert "photo_implementation_intent" not in sent


def test_v1_snapshot_replay_and_provider_projection_keep_original_contract():
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V1
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import resolve_html_motion_skill

    body, prepared, plan = photo_case()
    skill_id, digest, instructions = resolve_html_motion_skill("reel")
    old = {
        **prepared.context,
        "photo_intent_contract": dict(PHOTO_INTENT_CONTRACT_V1),
        "repertoire": capture_repertoire("business-reel-v5"),
        "skill": {"id": skill_id, "sha256": digest, "instructions": instructions},
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "repertoire", "skill", "photo_motion"):
        assert replay[key] == old[key]
    intent = implementation_intent(plan, PHOTO_INTENT_CONTRACT_V1)
    assert intent["version"] == "motion-photo-intent-v1"
    assert "visual_execution" not in intent
    prepared = prepare_implementation_materials(plan, replace(prepared, context=old))
    job = replace(
        request(),
        context=prepared.context,
        assets=prepared.assets,
        source_frames=(),
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
        construction_plan=plan,
    )
    payload = provider().build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["photo_implementation_intent"] == intent


def test_new_photo_snapshots_pin_executable_examples_without_changing_video_defaults():
    from app.services.motion_skills import resolve_html_motion_skill

    _, prepared, plan = photo_case()
    assert prepared.context["skill"]["id"] == "instagram-reel-photo-v14"
    assert resolve_html_motion_skill("reel")[0] == "instagram-reel-v13"
    pack = prepared.context["repertoire"]
    assert pack["id"] == "business-reel-v6"
    example = next(e for e in pack["examples"] if e["id"] == "photo-reel")
    assert "window.makePhotoReelMotion" in example["content"]
    assert "animatePhoto(ms)" in example["integration"]
    assert "P1:" in implementation_intent(plan)["visual_execution"]


@pytest.mark.parametrize("legacy_intent", [False, True])
def test_historical_photo_staging_and_rules_replay_without_upgrade(legacy_intent):
    from app.schemas.motion_production import MotionConstructionPlan
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V1
    from app.services.motion_photos import PHOTO_MOTION_RULES
    from app.services.motion_staging import PHOTO_STAGING_CONTRACT_V1, validate_staging

    body, prepared, plan = photo_case()
    old = {
        **prepared.context,
        "staging_contract": dict(PHOTO_STAGING_CONTRACT_V1),
        "photo_motion": {**prepared.context["photo_motion"], "rules": PHOTO_MOTION_RULES},
        "executor_contract": {**prepared.context["executor_contract"], "integration_policy": PHOTO_MOTION_RULES},
        "photo_intent_contract": PHOTO_INTENT_CONTRACT_V1 if legacy_intent else PHOTO_INTENT_CONTRACT,
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("staging_contract", "photo_motion", "executor_contract", "photo_intent_contract"):
        assert replay[key] == old[key]
    data = plan.model_dump(mode="json")
    data["staging"]["version"] = "motion-staging-photo-v1"
    validate_staging(
        MotionConstructionPlan.model_validate(data),
        replay | {"available_materials": prepared.context["available_materials"]},
    )
    with pytest.raises(AuthError, match="MOTION_STAGING_CONTRACT_CHANGED"):
        validate_staging(plan, replay)


def test_new_photo_rules_also_cover_silent_non_staged_capture():
    from uuid import uuid4

    from app.schemas.motion_production import MotionRequest

    body = MotionRequest(
        operation_id=uuid4(), source_asset_id=None, photo_duration_ms=15000, instruction="Reel silencioso de fotos"
    )
    captured = capture_motion_guidance(body)
    for rules in (
        captured["photo_motion"]["rules"],
        captured["executor_contract"]["integration_policy"],
        captured["creative_contract"]["media_visibility_policy"],
    ):
        assert "Ken Burns contínuo" in rules
        assert "movimento suave quando pedido" not in rules
