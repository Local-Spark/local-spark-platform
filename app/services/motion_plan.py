"""Bind planned direction to the immutable request before rendering any provider output."""

from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_creative import (
    CREATIVE_CONTRACT_VERSION,
    PROVIDED_DIRECTION_CONTRACT_VERSION,
    SUPPORTED_CREATIVE_CONTRACTS,
)
from app.services.motion_elements import elements_hash
from app.services.motion_evolution import validate_evolution_plan
from app.services.motion_quality import validate_quality_plan
from app.services.motion_sound_library import validate_sound_design
from app.services.motion_speech import validate_speech_plan
from app.services.motion_staging import validate_staging
from app.services.motion_structural_floor import (
    StructuralFloorRejected,
    enforce_structural_floor,
    validate_structural_execution,
)
from app.services.motion_visual_direction import validate_direction_fidelity


def requires_motion_plan(context: dict[str, Any]) -> bool:
    contract = context.get("creative_contract")
    if contract is None:
        return False
    if not isinstance(contract, dict) or contract.get("version") not in SUPPORTED_CREATIVE_CONTRACTS:
        raise AuthError("MOTION_CREATIVE_CONTRACT_UNKNOWN", 409)
    return bool(
        contract["version"]
        in {
            "reel-creative-v2",
            "reel-creative-v3",
            CREATIVE_CONTRACT_VERSION,
            PROVIDED_DIRECTION_CONTRACT_VERSION,
            "reel-creative-v6",
            "reel-creative-v7",
            "reel-creative-v8",
            "reel-creative-v9",
        }
    )


def requires_scene_direction(context: dict[str, Any]) -> bool:
    requires_motion_plan(context)  # Reject unknown contracts before provider admission.
    return bool(
        (context.get("creative_contract") or {}).get("version")
        in {
            "reel-creative-v3",
            CREATIVE_CONTRACT_VERSION,
            PROVIDED_DIRECTION_CONTRACT_VERSION,
            "reel-creative-v6",
            "reel-creative-v7",
            "reel-creative-v8",
            "reel-creative-v9",
        }
    )


def validate_scene_direction(
    composition: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any]
) -> None:
    direction = composition.scene_direction
    if direction is None:
        if requires_scene_direction(context):
            raise AuthError("MOTION_SCENE_DIRECTION_REQUIRED", 409)
        return
    plan = composition.motion_plan
    if plan is None:
        raise AuthError("MOTION_SCENE_DIRECTION_PLAN_REQUIRED", 409)
    if [scene.scene_id for scene in direction.scenes] != [scene.id for scene in plan.scenes]:
        raise AuthError("MOTION_SCENE_DIRECTION_SCENES_INVALID", 409)
    for scene, design in zip(plan.scenes, direction.scenes, strict=True):
        elements = {element.id: element for element in scene.elements}
        ids = [element.element_id for element in design.elements]
        if len(ids) != len(set(ids)) or set(ids) != set(elements):
            raise AuthError("MOTION_SCENE_DIRECTION_ELEMENTS_INVALID", 409)
        if len(set(design.attention_order)) != len(design.attention_order) or not set(design.attention_order) <= set(
            elements
        ):
            raise AuthError("MOTION_SCENE_DIRECTION_ATTENTION_INVALID", 409)
        for element in design.elements:
            if element.construction == "component":
                if elements_hash(context) is None or elements[element.element_id].role != "graphic":
                    raise AuthError("MOTION_SCENE_COMPONENT_UNAVAILABLE", 409)
                available = context["creative_contract"]["element_library"]["items"]
                if element.component_id not in {item["id"] for item in available}:
                    raise AuthError("MOTION_SCENE_COMPONENT_UNAVAILABLE", 409)
                continue
            if element.component_id is not None:
                raise AuthError("MOTION_SCENE_COMPONENT_UNEXPECTED", 409)
            asset_id = elements[element.element_id].asset_id
            expected = "authorized_asset" if asset_id is not None else "code"
            if asset_id is not None and asset_id.startswith("assets/illustration-"):
                if asset_id not in {item.asset_id for item in composition.illustrations}:
                    raise AuthError("MOTION_ILLUSTRATION_UNDECLARED", 409)
                expected = "generated_asset"
            if element.construction != expected:
                raise AuthError("MOTION_SCENE_DIRECTION_SOURCE_INVALID", 409)


def validate_motion_plan(
    composition: HTMLMotionComposition | MotionConstructionPlan,
    context: dict[str, Any],
    *,
    duration_ms: int,
    asset_ids: set[str],
) -> None:
    validate_speech_plan(composition, context)
    required = requires_motion_plan(context)
    validate_direction_fidelity(composition, context)
    validate_evolution_plan(composition, context)
    validate_sound_design(composition, context)
    validate_quality_plan(composition, context)
    validate_staging(composition, context)
    try:
        enforce_structural_floor(composition.motion_plan, context)
        validate_structural_execution(composition, context)
    except StructuralFloorRejected:
        raise AuthError("MOTION_STRUCTURAL_FLOOR_REJECTED", 409) from None
    plan = composition.motion_plan
    if plan is None:
        if required:
            raise AuthError("MOTION_PLAN_REQUIRED", 409)
        validate_scene_direction(composition, context)
        return
    validate_scene_direction(composition, context)
    if plan.duration_ms != duration_ms:
        raise AuthError("MOTION_PLAN_DURATION_CHANGED", 409)
    if plan.style_id is not None and plan.style_id not in {item["id"] for item in context.get("styles", [])}:
        raise AuthError("MOTION_PLAN_STYLE_UNAVAILABLE", 409)
    for scene in plan.scenes:
        for element in scene.elements:
            if element.asset_id is not None and element.asset_id not in asset_ids:
                raise AuthError("MOTION_PLAN_ASSET_UNAVAILABLE", 409)
