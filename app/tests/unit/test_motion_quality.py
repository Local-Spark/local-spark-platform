"""A product quality floor must work without any previous customer piece or baseline."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.motion_html_renderer import RenderAsset
from app.services.auth import AuthError
from app.services.motion_construction import plan_motion
from app.services.motion_context import capture_motion_guidance
from app.services.motion_generation import provided_output_enabled
from app.services.motion_quality import (
    LEGACY_QUALITY_CONTRACT,
    QUALITY_CONTRACT,
    planning_input,
    require_quality_readiness,
    validate_quality_context,
    validate_quality_input,
    validate_quality_plan,
)
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_audiovisual import natural_body, natural_context, natural_plan, natural_prepared
from app.tests.unit.test_motion_plan import planned


def job():
    p = natural_prepared()
    return replace(request(), context=p.context, assets=p.assets, source_frames=p.source_frames)


def test_new_piece_planner_has_independent_floor_and_no_previous_piece_in_its_real_input():
    value = job()
    payload = provider().build_request(value)
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    ctx = sent["authorized_context"]
    assert ctx["quality_contract"] == QUALITY_CONTRACT
    assert ctx["creative_contract"]["version"] == "reel-creative-v9"
    assert not {"calibration", "counterexample", "reference_scope"} & ctx["creative_contract"].keys()
    assert "evolution" not in ctx and "evolution" not in ctx["request"]
    assert "historical_baseline" not in sent
    assert sent["current_composition"] is None and sent["previous_composition"] is None
    assert value.baseline_frames == ()
    assert "quality_contract define os requisitos" in payload["instructions"]
    assert "Preserve funções da base" not in ctx["preparation_contract"]["rules"]
    validate_quality_plan(natural_plan(), ctx)


@pytest.mark.parametrize("change", ["missing", "changed", "selection", "history"])
def test_missing_or_tampered_profile_and_historical_context_are_rejected(change):
    ctx = natural_context()
    if change == "missing":
        ctx.pop("quality_contract")
    elif change == "changed":
        ctx["quality_contract"] = {**ctx["quality_contract"], "version": "forged"}
    elif change == "selection":
        ctx["request"]["evolution"] = {"baseline_request_id": str(uuid4())}
    else:
        ctx["evolution"] = {"composition": "An older customer piece"}
    with pytest.raises(AuthError, match="MOTION_QUALITY_"):
        provided_output_enabled(ctx)


@pytest.mark.parametrize("change", ["frames", "evidence", "material", "composition", "previous"])
def test_previous_piece_evidence_cannot_be_smuggled_into_initial_production_planning(change):
    value = job()
    if change == "frames":
        value = replace(value, baseline_frames=(frame(100),))
    elif change == "evidence":
        value.context["request"]["preparation"]["evidence"][0]["kind"] = "baseline"
    elif change == "material":
        value.context["available_materials"] = [{"role": "reused_illustration"}]
    elif change == "composition":
        value = replace(value, composition=planned())
    else:
        value = replace(value, incumbent_composition=planned())
    with pytest.raises(AuthError, match="HISTORICAL_CONTEXT_FORBIDDEN"):
        provider().build_request(value)


@pytest.mark.parametrize("change", ["missing", "duplicate", "foreign", "target", "disposition", "design", "plan"])
def test_plan_must_account_for_every_product_requirement_with_its_own_targets(change):
    artifact = natural_plan()
    data = artifact.model_dump(mode="json")
    fs = data["audiovisual"]["functions"]
    if change == "missing":
        fs.pop()
    elif change == "duplicate":
        fs[-1] = deepcopy(fs[0])
    elif change == "foreign":
        fs[0]["function_id"] = "former-customer-scene"
    elif change == "target":
        fs[0]["target_element_ids"] = ["absent"]
    elif change == "disposition":
        fs[0]["disposition"] = "replace_representation"
    elif change == "design":
        data["audiovisual"] = None
    else:
        artifact = planned().model_copy(update={"motion_plan": None})
    if change != "plan":
        artifact = artifact.model_validate(data)
    with pytest.raises(AuthError, match="MOTION_QUALITY_COVERAGE_"):
        validate_quality_plan(artifact, natural_context())


@pytest.mark.parametrize("reason", ["unresolved", "speech"])
async def test_incomplete_production_preparation_stops_before_reservation_and_model(reason):
    p = natural_prepared()
    if reason == "unresolved":
        p.context["request"]["preparation"]["unresolved"] = ["Resolve relevant source information"]
    else:
        p.context["source"]["has_audio"] = True
    effects = SimpleNamespace(capacity=AsyncMock(), model=AsyncMock())
    with pytest.raises(AuthError, match="(UNRESOLVED|SPEECH_REQUIRED)"):
        await plan_motion(effects, provider(), {"operation_id": uuid4()}, uuid4(), p)
    effects.capacity.assert_not_awaited()
    effects.model.assert_not_awaited()


def test_legacy_paths_and_current_candidate_corrections_keep_their_existing_rules():
    assert not validate_quality_context({})
    validate_quality_input(request())
    validate_quality_plan(planned(), {})
    require_quality_readiness({})
    ctx = natural_context()
    require_quality_readiness(ctx)
    ctx["source"]["has_audio"] = True
    ctx["transcript"] = {"scope": "synthetic readiness; speech validators separately check bytes/timing"}
    require_quality_readiness(ctx)
    validate_quality_input(replace(job(), kind="correct", composition=planned(), incumbent_composition=planned()))


def test_new_floor_requires_visual_development_even_for_the_simple_client_message():
    ctx = natural_context()
    artifact = natural_plan()
    functions = tuple(f for f in artifact.audiovisual.functions if f.function_id != "visual_development")
    seven = artifact.model_copy(
        update={"audiovisual": artifact.audiovisual.model_copy(update={"functions": functions})}
    )
    with pytest.raises(AuthError, match="MOTION_QUALITY_COVERAGE_INVALID"):
        validate_quality_plan(seven, ctx)
    old = {**ctx, "quality_contract": LEGACY_QUALITY_CONTRACT}
    validate_quality_plan(seven, old)
    assert planning_input(old, []) is None and planning_input({}, []) is None
    assert capture_motion_guidance(natural_body(), previous=old)["quality_contract"] == LEGACY_QUALITY_CONTRACT
    assert "mesmo quando o cliente pede apenas um Reel" in QUALITY_CONTRACT["rules"]


def test_planning_projection_does_not_infer_human_listening_from_files_or_measurements():
    sent = json.loads(provider().build_request(job())["input"][0]["content"][0]["text"])
    planning = sent["planning_input"]
    assert planning["visual_development"]["required_by"] == "product_quality_profile_not_client_technical_wording"
    assert not planning["sound"]["system_listening"]
    assert planning["sound"]["source"]["human_file_evidence"] == []
    assert all(c["human_file_evidence"] == [] for c in planning["sound"]["candidates"])
    assert all(c["event_and_mix_status"] == "not_planned_or_listened_yet" for c in planning["sound"]["candidates"])
    ctx = natural_context()
    ctx.pop("sound_library")
    assert planning_input(ctx, [])["sound"]["candidates"] == []


def test_hash_bound_owner_reports_reach_sound_planning_without_approving_events_or_mix():
    value = job()
    asset = value.assets[0]
    data = b"synthetic source with audio"
    digest = hashlib.sha256(data).hexdigest()
    value.context["source"].update(sha256=digest, has_audio=True)
    value = replace(value, assets=(*value.assets, RenderAsset("assets/source.mp4", "video/mp4", data, digest)))
    value.context["request"]["preparation"]["evidence"].extend(
        [
            {
                "id": "owner-sound",
                "kind": "audio",
                "asset_id": asset.id,
                "asset_sha256": asset.sha256,
                "observation": "Synthetic owner observation: suitable file.",
                "intended_use": "Consider in planning, without requiring an event.",
                "limitations": "No mix approval.",
            }
        ]
    )
    value.context["request"]["preparation"]["evidence"].append(
        {
            "id": "owner-source",
            "kind": "audio",
            "asset_id": "assets/source.mp4",
            "asset_sha256": digest,
            "observation": "Synthetic owner observation: clear voice.",
            "intended_use": "Inform source planning.",
            "limitations": "Does not review ASR or approve a mix.",
        }
    )
    sent = json.loads(provider().build_request(value)["input"][0]["content"][0]["text"])
    first, second = sent["planning_input"]["sound"]["candidates"]
    assert first["human_file_evidence"][0]["observation"] == "Synthetic owner observation: suitable file."
    assert second["human_file_evidence"] == []
    assert sent["planning_input"]["sound"]["source"]["human_file_evidence"][0]["id"] == "owner-source"
    assert first["event_and_mix_status"] == "not_planned_or_listened_yet"
    assert "pending future mix listening is not a standalone reason" in sent["planning_input"]["sound"]["rules"]
    value.context["request"]["preparation"]["evidence"][-2]["asset_sha256"] = "0" * 64
    with pytest.raises(AuthError, match="AUDIO_EVIDENCE_CHANGED"):
        provider().build_request(value)


def test_captured_v1_keeps_its_payload_without_the_new_projection():
    value = job()
    value.context["quality_contract"] = LEGACY_QUALITY_CONTRACT
    first = provider().build_request(value)
    assert "planning_input" not in json.loads(first["input"][0]["content"][0]["text"])
    recaptured = capture_motion_guidance(natural_body(), previous=value.context)
    assert recaptured["quality_contract"] == LEGACY_QUALITY_CONTRACT
    validate_quality_context(recaptured)


def test_recapture_preserves_the_entire_captured_legacy_guidance():
    prior = deepcopy(capture_motion_guidance(natural_body()))
    prior["quality_contract"] = LEGACY_QUALITY_CONTRACT
    body = natural_body(
        operation_id=prior["request"]["operation_id"], source_asset_id=prior["request"]["source_asset_id"]
    )
    assert capture_motion_guidance(body, previous=prior) == prior


def test_implementation_uses_the_exact_approved_plan_without_new_planning_obligations():
    value = job()
    plan = natural_plan()
    from app.services.motion_materials import prepare_implementation_materials
    from app.services.motion_sound_library import apply_planned_sound

    prepared = prepare_implementation_materials(plan, apply_planned_sound(natural_prepared(), plan))
    value = replace(value, context=prepared.context, construction_plan=plan)
    sent = json.loads(provider().build_request(value)["input"][0]["content"][0]["text"])
    assert "planning_input" not in sent
    assert sent["validated_plan"] == plan.model_dump(mode="json")
