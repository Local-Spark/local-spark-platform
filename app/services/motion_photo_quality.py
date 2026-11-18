"""Versioned photo plan checks; declarations are not evidence of rendered motion."""

from typing import Any

from app.schemas.motion_plan import MotionElementPlan
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_photo_energy import validate_photo_energy
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, PHOTO_INTENT_CONTRACT_V4, PHOTO_INTENT_CONTRACT_V5


def _moves_until(element: MotionElementPlan, start: int, end: int) -> bool:
    covered = start
    for beat in element.beats:
        if beat.end_ms <= covered:
            continue
        if beat.start_ms > covered or beat.phase != "transform" or beat.start_state == beat.end_state:
            return False
        covered = beat.end_ms
    return covered == end


def validate_photo_quality(
    artifact: HTMLMotionComposition | MotionConstructionPlan,
    context: dict[str, Any],
    *,
    asset_ids: set[str],
) -> None:
    if context.get("photo_intent_contract") not in (
        PHOTO_INTENT_CONTRACT_V4,
        PHOTO_INTENT_CONTRACT_V5,
        PHOTO_INTENT_CONTRACT,
    ):
        return
    plan = artifact.motion_plan
    if plan is None:
        raise AuthError("MOTION_PLAN_REQUIRED", 409)
    for scene in plan.scenes:
        for element in scene.elements:
            hold_start = None
            previous_end = -1
            for beat in element.beats:
                if beat.phase == "hold":
                    if hold_start is None or beat.start_ms != previous_end:
                        hold_start = beat.start_ms
                    if beat.end_ms - hold_start > 2500:
                        raise AuthError("MOTION_PHOTO_HOLD_TOO_LONG", 409)
                else:
                    hold_start = None
                previous_end = beat.end_ms

    final = plan.scenes[-1]
    handoff_end = max(
        (beat.end_ms for element in final.elements for beat in element.beats if beat.phase == "enter"),
        default=final.start_ms,
    )
    if artifact.staging is not None:
        for moment in artifact.staging.moments:
            if moment.transition is not None and moment.transition.next_scene_id == final.id:
                handoff_end = moment.transition.end_ms
    if not final.start_ms <= handoff_end < plan.duration_ms:
        raise AuthError("MOTION_PHOTO_CLOSING_WINDOW_INVALID", 409)
    photos = [e for e in final.elements if e.role == "image" and (e.asset_id or "").startswith("assets/photo-")]
    logos = [e for e in final.elements if e.role == "image" and e.asset_id == "assets/logo.png"]
    if not photos or ("assets/logo.png" in asset_ids and not logos):
        raise AuthError("MOTION_PHOTO_CLOSING_MATERIAL_REQUIRED", 409)
    if not all(_moves_until(e, handoff_end, plan.duration_ms) for e in photos + logos):
        raise AuthError("MOTION_PHOTO_CLOSING_MOTION_REQUIRED", 409)

    if context.get("photo_intent_contract") == PHOTO_INTENT_CONTRACT:
        validate_photo_energy(plan)
