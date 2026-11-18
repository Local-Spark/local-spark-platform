"""R1–R3 admission and DOM guard assembly; no pixel inspection or crop correction."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_photo_energy import _state, energetic
from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, PHOTO_INTENT_CONTRACT_V9

GUARD_PATH = Path(__file__).resolve().parents[1] / "assets/motion_photo/photo-guard-v1.js"
GUARD_SHA256 = "613ab2765a44d194793ef44c888709e9acfec68660e1e75d4ee88ef941c649f8"

GUARD_V2_PATH = GUARD_PATH.with_name("photo-guard-v2.js")


def validate_photo_layout(artifact: HTMLMotionComposition | MotionConstructionPlan, *, handoff_end: int) -> None:
    plan = artifact.motion_plan
    assert plan is not None
    photographic = []
    exceptions = []
    for scene in plan.scenes:
        photos = {e.id: e for e in scene.elements if (e.asset_id or "").startswith("assets/photo-")}
        if not photos:
            if scene.photo_layout is not None:
                raise AuthError("MOTION_PHOTO_LAYOUT_INVALID", 409)
            continue
        photographic.append(scene)
        layout = scene.photo_layout
        if layout is None or layout.primary_element_id not in photos:
            raise AuthError("MOTION_PHOTO_LAYOUT_REQUIRED", 409)
        exception = layout.crop_exception
        if layout.mode == "contain_blur":
            if (
                exception is None
                or exception.asset_id != photos[layout.primary_element_id].asset_id
                or not all(
                    value.strip()
                    for value in (exception.essential_region, exception.alternatives_rejected, exception.safe_motion)
                )
            ):
                raise AuthError("MOTION_PHOTO_CROP_EXCEPTION_REQUIRED", 409)
            exceptions.append(scene)
        elif exception is not None:
            raise AuthError("MOTION_PHOTO_LAYOUT_INVALID", 409)
    # Count exclusive cover time, not summed scene durations: overlaps cannot launder a long exception.
    boundaries = sorted({0, plan.duration_ms, *(t for s in plan.scenes for t in (s.start_ms, s.end_ms))})
    cover_ms = sum(
        end - start
        for start, end in zip(boundaries, boundaries[1:], strict=False)
        if any(s.start_ms <= start < s.end_ms for s in photographic if s not in exceptions)
        and not any(s.start_ms <= start < s.end_ms for s in exceptions)
    )
    if len(exceptions) > 1 or len(exceptions) * 3 > len(photographic) or cover_ms * 3 < plan.duration_ms * 2:
        raise AuthError("MOTION_PHOTO_COVER_DOMINANCE_REQUIRED", 409)
    final = plan.scenes[-1]
    closing = final.photo_closing
    elements = {e.id: e for e in final.elements}
    logos = [e.id for e in final.elements if e.asset_id == "assets/logo.png"]
    if (
        any(s.photo_closing is not None for s in plan.scenes[:-1])
        or closing is None
        or closing.cta_element_id not in elements
        or elements[closing.cta_element_id].role != "text"
        or (closing.brand_element_id is not None and closing.brand_element_id not in logos)
        or (logos and closing.brand_element_id not in logos)
    ):
        raise AuthError("MOTION_PHOTO_CLOSING_OVERLAY_REQUIRED", 409)
    for element in final.elements:
        if element.asset_id == "assets/logo.png" or (element.asset_id or "").startswith("assets/photo-"):
            for beat in element.beats:
                if beat.end_ms > handoff_end and (
                    beat.curve.kind != "linear"
                    or _state(beat.start_state) is None
                    or _state(beat.end_state) is None
                    or _state(beat.start_state) == _state(beat.end_state)
                ):
                    raise AuthError("MOTION_PHOTO_EXECUTABLE_MOTION_REQUIRED", 409)


def guarded_photo_scene_init(composition: HTMLMotionComposition, context: dict[str, Any]) -> str:
    """Wrap the existing executor. Reject mismatches; never silently animate a different approved plan."""
    contract = context.get("photo_intent_contract")
    if contract not in (PHOTO_INTENT_CONTRACT_V9, PHOTO_INTENT_CONTRACT):
        return composition.scene_init
    source = (GUARD_PATH if contract == PHOTO_INTENT_CONTRACT_V9 else GUARD_V2_PATH).read_bytes()
    if hashlib.sha256(source).hexdigest() != contract["dom_guard_sha256"]:
        raise AuthError("MOTION_PHOTO_GUARD_CHANGED", 409)
    plan = composition.motion_plan
    assert plan is not None
    final = plan.scenes[-1]
    handoff_end = max((b.end_ms for e in final.elements for b in e.beats if b.phase == "enter"), default=final.start_ms)
    if composition.staging is not None:
        for moment in composition.staging.moments:
            if moment.transition is not None and moment.transition.next_scene_id == final.id:
                handoff_end = moment.transition.end_ms
    validate_photo_layout(composition, handoff_end=handoff_end)
    scenes = []
    for scene in plan.scenes:
        photos = [e for e in scene.elements if (e.asset_id or "").startswith("assets/photo-")]
        related = {identifier for e in photos for identifier in e.related_element_ids}
        candidates = photos + [e for e in scene.elements if e.id in related and e.role in {"text", "graphic"}]
        scenes.append(
            {
                **scene.model_dump(mode="json"),
                **_exit_handoff(composition, scene.id, contract),
                **(
                    {"cta_read_start": photo_cta_read_start(composition, handoff_end)}
                    if contract == PHOTO_INTENT_CONTRACT and scene == final
                    else {}
                ),
                "energy": [
                    {
                        "id": e.id,
                        "start": b.start_ms,
                        "end": b.end_ms,
                        "a": _state(b.start_state),
                        "z": _state(b.end_state),
                    }
                    for e in candidates
                    for b in e.beats
                    if energetic(b, stronger=True)
                ],
                "closing_motion": [
                    {
                        "id": e.id,
                        "start": b.start_ms,
                        "end": b.end_ms,
                        "a": _state(b.start_state),
                        "z": _state(b.end_state),
                    }
                    for e in scene.elements
                    if e in photos or e.asset_id == "assets/logo.png"
                    for b in e.beats
                    if scene == final and b.end_ms > handoff_end
                ],
            }
        )
    payload = json.dumps({"scenes": scenes, "handoff_end": handoff_end, "end": plan.duration_ms}, ensure_ascii=True)
    return composition.scene_init + "\n;(" + source.decode() + ")(" + payload + ");"


def _exit_handoff(composition: HTMLMotionComposition, scene_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    if contract != PHOTO_INTENT_CONTRACT or composition.staging is None:
        return {}
    assert composition.motion_plan is not None
    scenes = {s.id: s for s in composition.motion_plan.scenes}
    scene = scenes[scene_id]
    for moment in composition.staging.moments:
        h = moment.transition
        if moment.scene_id != scene_id or h is None:
            continue
        next_scene = scenes[h.next_scene_id]
        if 0 < h.end_ms - h.start_ms <= 500 and max(
            scene.start_ms, next_scene.start_ms
        ) <= h.start_ms < h.end_ms <= min(scene.end_ms, next_scene.end_ms):
            return {"exit_handoff": {"start": h.start_ms, "end": h.end_ms, "next_scene_id": h.next_scene_id}}
    return {}


def photo_cta_read_start(artifact: HTMLMotionComposition | MotionConstructionPlan, handoff_end: int) -> int:
    assert artifact.motion_plan is not None
    final = artifact.motion_plan.scenes[-1]
    assert final.photo_closing is not None
    cta = next(e for e in final.elements if e.id == final.photo_closing.cta_element_id)
    start = max(handoff_end, max((b.end_ms for b in cta.beats if b.phase == "enter"), default=final.start_ms))
    if artifact.motion_plan.duration_ms - start < 1500:
        raise AuthError("MOTION_PHOTO_CTA_WINDOW_INVALID", 409)
    return start
