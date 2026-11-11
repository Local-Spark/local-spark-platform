"""Representative full scene frames, never evidence of temporal or audio quality."""

from typing import TypedDict

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError


class StoryboardMoment(TypedDict):
    scene_id: str
    message: str
    requested_ms: int
    frame_index: int


def storyboard_moments(composition: HTMLMotionComposition | MotionConstructionPlan) -> tuple[StoryboardMoment, ...]:
    plan = composition.motion_plan
    if plan is None or composition.scene_direction is None:
        raise AuthError("MOTION_STORYBOARD_PLAN_REQUIRED", 409)
    result: list[StoryboardMoment] = []
    indexes: set[int] = set()
    for scene in plan.scenes:
        ms = scene.keyframe_ms
        if ms is None or not scene.start_ms <= ms < scene.end_ms:
            raise AuthError("MOTION_STORYBOARD_MOMENT_REQUIRED", 409)
        index = ms * 30 // 1000
        if (indexes and index <= max(indexes)) or not scene.start_ms * 30 <= index * 1000 < scene.end_ms * 30:
            raise AuthError("MOTION_STORYBOARD_MOMENT_INVALID", 409)
        indexes.add(index)
        result.append({"scene_id": scene.id, "message": scene.message, "requested_ms": ms, "frame_index": index})
    return tuple(result)
