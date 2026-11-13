"""Representative full scene frames, never evidence of temporal or audio quality."""

from typing import Any, NotRequired, TypedDict

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_temporal import POLICY_V2, POLICY_V3, POLICY_V4, events, sample_times


class StoryboardMoment(TypedDict):
    scene_id: str
    message: str
    requested_ms: int
    frame_index: int
    event_id: NotRequired[str]
    kind: NotRequired[str]


def storyboard_upload_name(moment: StoryboardMoment) -> str:
    """Temporal/global samples need per-frame identities; retain legacy scene cards."""
    return f"{moment['scene_id']}:{moment['frame_index']}" if "kind" in moment else moment["scene_id"]


def storyboard_moments(
    composition: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any] | None = None
) -> tuple[StoryboardMoment, ...]:
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
    policy = ((context or {}).get("creative_contract") or {}).get("temporal_review")
    if policy not in (POLICY_V2, POLICY_V3, POLICY_V4) or not isinstance(composition, HTMLMotionComposition):
        return tuple(result)
    selected, _ = events(composition, policy)
    by_index: dict[int, StoryboardMoment] = {}
    messages = {scene.id: scene.message for scene in plan.scenes}
    for event in selected:
        for index in event.indices:
            if (index * 1000 + 29) // 30 >= plan.duration_ms:
                continue
            by_index.setdefault(
                index,
                {
                    "scene_id": event.scene_id,
                    "message": messages[event.scene_id],
                    "requested_ms": (index * 1000 + 29) // 30,
                    "frame_index": index,
                    "event_id": event.id,
                    "kind": event.kind,
                },
            )
    if policy in (POLICY_V3, POLICY_V4):
        for ms in sample_times(composition, context or {}):
            index = ms * 30 // 1000
            scene = next((s for s in plan.scenes if s.start_ms <= ms < s.end_ms), plan.scenes[-1])
            by_index.setdefault(
                index,
                {
                    "scene_id": scene.id,
                    "message": scene.message,
                    "requested_ms": ms,
                    "frame_index": index,
                    "kind": "global",
                },
            )
    for moment in result:
        if len(by_index) >= policy["max_frames"]:
            break
        by_index.setdefault(moment["frame_index"], moment)
    return tuple(by_index[index] for index in sorted(by_index))
