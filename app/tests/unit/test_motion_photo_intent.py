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
    for rules in (
        PHOTO_INTENT_CONTRACT["rules"],
        prepared.context["skill"]["instructions"],
        prepared.context["photo_motion"]["rules"],
        prepared.context["executor_contract"]["integration_policy"],
        prepared.context["repertoire"]["rules"],
    ):
        assert "fecho 11–15 s" not in rules
        assert 'No HTML do fecho, renderize obrigatoriamente <img src="assets/logo.png"> visível' in rules
        assert "tempos de fecho/handoff do plano" in rules
        assert "declarar o asset no plano não basta" in rules
        assert "M1:" in rules and "M2:" in rules and "M3:" in rules
        assert all(marker in rules for marker in ("N1:", "N2:", "N3:"))
        assert "janela landscape central + barras blur" in rules
        assert "sem placa creme/editorial" in rules
        assert "scale=1.04 x_pct=0 y_pct=0" in rules
        assert "28%" in rules and "2500 ms" in rules
        assert "cartão creme com foto em janela" in rules
        assert "handoffEnd < end" in rules
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
    assert prepared.context["skill"]["id"] == "instagram-reel-photo-v19"
    assert resolve_html_motion_skill("reel")[0] == "instagram-reel-v13"
    pack = prepared.context["repertoire"]
    assert pack["id"] == "business-reel-v11"
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


@pytest.mark.parametrize("version", ["v1", "v2", "v3", "absent"])
@pytest.mark.parametrize("logo_available", [False, True])
@pytest.mark.parametrize("declared", [False, True])
def test_logo_required_only_for_new_contract_with_available_asset(version, logo_available, declared):
    from app.services.motion_photo_intent import (
        PHOTO_INTENT_CONTRACT_V1,
        PHOTO_INTENT_CONTRACT_V2,
        PHOTO_INTENT_CONTRACT_V3,
    )
    from app.services.motion_plan import validate_motion_plan

    _, _, plan = photo_case()
    # Isolate the plan binding from unrelated staging/quality validators.
    plan = plan.model_copy(update={"staging": None, "scene_direction": None, "audiovisual": None})
    contracts = {
        "v1": PHOTO_INTENT_CONTRACT_V1,
        "v2": PHOTO_INTENT_CONTRACT_V2,
        "v3": PHOTO_INTENT_CONTRACT_V3,
        "absent": None,
    }
    context = {"photo_intent_contract": contracts[version]}
    ids = {e.asset_id for s in plan.motion_plan.scenes for e in s.elements if e.asset_id}
    if logo_available:
        ids.add("assets/logo.png")
    if declared:
        # Keep the original image and add a real logo element, not brand_name text.
        element = (
            plan.motion_plan.scenes[0]
            .elements[0]
            .model_copy(update={"id": "logo", "role": "image", "asset_id": "assets/logo.png"})
        )
        first = plan.motion_plan.scenes[0].model_copy(
            update={"elements": (*plan.motion_plan.scenes[0].elements, element)}
        )
        plan = plan.model_copy(
            update={
                "motion_plan": plan.motion_plan.model_copy(update={"scenes": (first, *plan.motion_plan.scenes[1:])})
            }
        )
    error = (
        "MOTION_PHOTO_LOGO_REQUIRED"
        if version == "v3" and logo_available and not declared
        else "MOTION_PLAN_ASSET_UNAVAILABLE"
        if declared and not logo_available
        else None
    )
    if error:
        with pytest.raises(AuthError, match=error):
            validate_motion_plan(plan, context, duration_ms=15000, asset_ids=ids)
    else:
        validate_motion_plan(plan, context, duration_ms=15000, asset_ids=ids)


def test_v2_replay_keeps_original_rules_skill_and_repertoire():
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V2
    from app.services.motion_photos import PHOTO_MOTION_RULES_V2
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import _SKILLS, load_motion_skill

    body, prepared, plan = photo_case()
    identifier = "instagram-reel-photo-v14"
    digest = _SKILLS[identifier][1]
    old = {
        **prepared.context,
        "photo_intent_contract": PHOTO_INTENT_CONTRACT_V2,
        "skill": {"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")},
        "repertoire": capture_repertoire("business-reel-v6"),
        "photo_motion": {**prepared.context["photo_motion"], "rules": PHOTO_MOTION_RULES_V2},
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "skill", "repertoire", "photo_motion"):
        assert replay[key] == old[key]
    assert (
        implementation_intent(plan, PHOTO_INTENT_CONTRACT_V2)["visual_execution"] == PHOTO_INTENT_CONTRACT_V2["rules"]
    )
    assert "L1:" not in PHOTO_INTENT_CONTRACT_V2["rules"]


@pytest.mark.parametrize("role", ["text", "image"])
def test_new_photo_logo_rejects_missing_plan_and_text_substitute(role):
    from app.services.motion_plan import validate_motion_plan

    _, prepared, plan = photo_case()
    missing = plan.model_copy(update={"motion_plan": None})
    with pytest.raises(AuthError, match="MOTION_PHOTO_LOGO_REQUIRED"):
        validate_motion_plan(missing, prepared.context, duration_ms=15000, asset_ids={"assets/logo.png"})
    if role == "text":
        scene = plan.motion_plan.scenes[0]
        elements = tuple(e.model_copy(update={"role": "text", "asset_id": "assets/logo.png"}) for e in scene.elements)
        plan = plan.model_copy(
            update={
                "motion_plan": plan.motion_plan.model_copy(
                    update={"scenes": (scene.model_copy(update={"elements": elements}), *plan.motion_plan.scenes[1:])}
                )
            }
        )
    from app.adapters.motion_html_renderer import RenderAsset
    from app.services.motion_illustrations import validate_declarations
    from app.tests.unit.test_motion_ai import frame

    logo = frame()
    prepared = replace(
        prepared, assets=(*prepared.assets, RenderAsset("assets/logo.png", "image/png", logo.png, logo.sha256))
    )
    with pytest.raises(AuthError, match="MOTION_PHOTO_LOGO_REQUIRED"):
        validate_declarations(plan, prepared)


def test_v3_replay_keeps_logo_only_gate_and_exact_assets():
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V3
    from app.services.motion_photos import PHOTO_MOTION_RULES_V3
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import _SKILLS, load_motion_skill

    body, prepared, plan = photo_case()
    identifier = "instagram-reel-photo-v15"
    digest = _SKILLS[identifier][1]
    old = {
        **prepared.context,
        "photo_intent_contract": PHOTO_INTENT_CONTRACT_V3,
        "skill": {"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")},
        "repertoire": capture_repertoire("business-reel-v7"),
        "photo_motion": {**prepared.context["photo_motion"], "rules": PHOTO_MOTION_RULES_V3},
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "skill", "repertoire", "photo_motion"):
        assert replay[key] == old[key]
    assert (
        implementation_intent(plan, PHOTO_INTENT_CONTRACT_V3)["visual_execution"] == PHOTO_INTENT_CONTRACT_V3["rules"]
    )
    assert "M1:" not in PHOTO_INTENT_CONTRACT_V3["rules"]
    explicit = body.model_copy(update={"repertoire_id": "business-reel-v7"})
    assert capture_motion_guidance(explicit)["repertoire"]["id"] == "business-reel-v7"
    explicit = body.model_copy(update={"repertoire_id": "business-reel-v8"})
    captured = capture_motion_guidance(explicit)
    assert captured["repertoire"]["id"] == "business-reel-v8"
    assert captured["staging_contract"] == prepared.context["staging_contract"]


@pytest.mark.parametrize("implementation", [False, True])
def test_crop_feasibility_reaches_provider_without_mutating_plan(implementation):
    from app.services.motion_photo_intent import PHOTO_CROP_RULES

    _, prepared, plan = photo_case()
    before = construction_plan_hash(plan)
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
    assert PHOTO_CROP_RULES in payload["instructions"]
    for key in ("photo_motion", "executor_contract"):
        assert PHOTO_CROP_RULES in prepared.context[key]["rules" if key == "photo_motion" else "integration_policy"]
    assert construction_plan_hash(plan) == before
    assert "object-position só desloca esse recorte" in PHOTO_CROP_RULES
    assert "foto principal em contain" in PHOTO_CROP_RULES
    assert "continue retornando requires_plan_revision" in PHOTO_CROP_RULES


def test_v4_replay_preserves_crop_policy_and_quality_gates():
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V4
    from app.services.motion_photos import PHOTO_MOTION_RULES_V4
    from app.services.motion_plan import validate_motion_plan

    body, prepared, plan = photo_case()
    old = {
        **prepared.context,
        "photo_intent_contract": PHOTO_INTENT_CONTRACT_V4,
        "photo_motion": {**prepared.context["photo_motion"], "rules": PHOTO_MOTION_RULES_V4},
        "executor_contract": {**prepared.context["executor_contract"], "integration_policy": PHOTO_MOTION_RULES_V4},
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "photo_motion", "executor_contract", "skill", "repertoire"):
        assert replay[key] == old[key]
    assert (
        implementation_intent(plan, PHOTO_INTENT_CONTRACT_V4)["visual_execution"] == PHOTO_INTENT_CONTRACT_V4["rules"]
    )
    with pytest.raises(AuthError, match="MOTION_PHOTO_LOGO_REQUIRED"):
        validate_motion_plan(plan, old, duration_ms=15000, asset_ids={"assets/logo.png"})
    from app.services.motion_photo_quality import validate_photo_quality

    validate_photo_quality(plan, old, asset_ids=set())
    scene = plan.motion_plan.scenes[0]
    element = scene.elements[0]
    beat = element.beats[0].model_copy(update={"phase": "hold", "end_ms": 3000})
    changed = plan.model_copy(
        update={
            "motion_plan": plan.motion_plan.model_copy(
                update={
                    "scenes": (
                        scene.model_copy(update={"elements": (element.model_copy(update={"beats": (beat,)}),)}),
                        *plan.motion_plan.scenes[1:],
                    )
                }
            )
        }
    )
    with pytest.raises(AuthError, match="MOTION_PHOTO_HOLD_TOO_LONG"):
        validate_photo_quality(changed, old, asset_ids=set())


def test_v5_snapshot_replay_keeps_exact_crop_rules_skill_and_repertoire():
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT_V5
    from app.services.motion_photos import PHOTO_MOTION_RULES_V5
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import _SKILLS, load_motion_skill

    body, prepared, plan = photo_case()
    identifier = "instagram-reel-photo-v16"
    digest = _SKILLS[identifier][1]
    old = {
        **prepared.context,
        "photo_intent_contract": PHOTO_INTENT_CONTRACT_V5,
        "skill": {"id": identifier, "sha256": digest, "instructions": load_motion_skill(identifier, digest, "reel")},
        "repertoire": capture_repertoire("business-reel-v8"),
        "photo_motion": {**prepared.context["photo_motion"], "rules": PHOTO_MOTION_RULES_V5},
        "executor_contract": {**prepared.context["executor_contract"], "integration_policy": PHOTO_MOTION_RULES_V5},
    }
    replay = capture_motion_guidance(body, previous=old)
    for key in ("photo_intent_contract", "skill", "repertoire", "photo_motion", "executor_contract"):
        assert replay[key] == old[key]
    assert photo_intent_rules(old) == PHOTO_INTENT_CONTRACT_V5["rules"]
    assert implementation_intent(plan, PHOTO_INTENT_CONTRACT_V5)["version"] == "motion-photo-intent-v5"
