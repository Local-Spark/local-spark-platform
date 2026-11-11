"""A supplied visual brief precedes construction; it never implies human approval."""

import hashlib
import json
from typing import Any

from pydantic import ValidationError

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.services.auth import AuthError
from app.services.motion_creative import PROVIDED_DIRECTION_CONTRACT_VERSION
from app.services.motion_elements import elements_hash


def supplied_direction(context: dict[str, Any]) -> MotionSceneDirection | None:
    """Validate a standalone direction, before any timed plan or external effect."""
    contract = context.get("creative_contract") or {}
    raw = (context.get("request") or {}).get("scene_direction")
    provided_mode = contract.get("version") in {PROVIDED_DIRECTION_CONTRACT_VERSION, "reel-creative-v7"}
    if raw is None:
        if provided_mode:
            raise AuthError("MOTION_VISUAL_DIRECTION_REQUIRED", 409)
        return None
    if not provided_mode:
        raise AuthError("MOTION_VISUAL_DIRECTION_CONTRACT_REQUIRED", 409)
    try:
        direction = MotionSceneDirection.model_validate(raw)
    except ValidationError as exc:
        raise AuthError("MOTION_VISUAL_DIRECTION_INVALID", 409) from exc
    scenes: set[str] = set()
    elements: set[str] = set()
    for scene in direction.scenes:
        if scene.scene_id in scenes:
            raise AuthError("MOTION_VISUAL_DIRECTION_SCENES_INVALID", 409)
        scenes.add(scene.scene_id)
        ids = {element.element_id for element in scene.elements}
        if len(ids) != len(scene.elements) or ids & elements:
            raise AuthError("MOTION_VISUAL_DIRECTION_ELEMENTS_INVALID", 409)
        elements.update(ids)
        if len(set(scene.attention_order)) != len(scene.attention_order) or not set(scene.attention_order) <= ids:
            raise AuthError("MOTION_VISUAL_DIRECTION_ATTENTION_INVALID", 409)
        for element in scene.elements:
            if element.construction == "component":
                if elements_hash(context) is None or element.component_id not in {
                    item["id"] for item in contract["element_library"]["items"]
                }:
                    raise AuthError("MOTION_SCENE_COMPONENT_UNAVAILABLE", 409)
            elif element.component_id is not None:
                raise AuthError("MOTION_SCENE_COMPONENT_UNEXPECTED", 409)
            if element.construction == "generated_asset" and not context.get("illustration_generation"):
                raise AuthError("MOTION_VISUAL_DIRECTION_ILLUSTRATION_UNAVAILABLE", 409)
    return direction


def direction_input(context: dict[str, Any], *, review: bool = False) -> dict[str, Any]:
    """Label provenance in the model payload without duplicating the scene document."""
    direction = supplied_direction(context)
    encoded = (
        json.dumps(
            direction.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
        if direction is not None
        else None
    )
    if review:
        rules = (
            "A direção foi fornecida antes da construção; use-a como alvo ao avaliar a peça. "
            if direction is not None
            else "A direção é proposta pelo modelo, não uma decisão humana anterior à construção. "
        ) + "Direção e plano não provam execução nem aprovação; avalie somente as evidências disponíveis."
    else:
        rules = (
            "Siga a direção fornecida antes do código. Tempos/curvas ficam no motion_plan. "
            "Devolva a direção sem alterações, inclusive na correção. Fornecida não significa aprovada."
            if direction is not None
            else "Sem direção visual fornecida: scene_direction é uma proposta do modelo. "
            "Não anuncie planejamento independente ou aprovação humana inexistentes."
        )
    if not review and context.get("generation_contract") is not None:
        rules = (
            "Siga a direção fornecida antes do código; tempos e curvas ficam no motion_plan. "
            "O servidor preserva essa direção na composição: não devolva scene_direction. "
            "Fornecida não significa aprovada; correções também devem respeitá-la."
        )
    return {
        "version": "visual-direction-input-v1",
        "mode": "provided" if direction is not None else "model_proposed",
        "source": "request.scene_direction" if direction is not None else "model_response",
        "sha256": hashlib.sha256(encoded).hexdigest() if encoded is not None else None,
        "human_approval": "not_asserted",
        "rules": rules,
    }


def validate_direction_fidelity(
    composition: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any]
) -> None:
    direction = supplied_direction(context)
    if direction is not None and composition.scene_direction != direction:
        raise AuthError("MOTION_VISUAL_DIRECTION_CHANGED", 409)
