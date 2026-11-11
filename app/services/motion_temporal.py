"""Bounded, deterministic sampling of planned events; evidence is decoded video, never plan text."""

from dataclasses import dataclass
from typing import Any

from app.adapters.motion_html_renderer import RenderedFrame
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError

MAX_EVENTS = 3
MAX_FRAMES = 20
POLICY = {"version": "motion-temporal-v1", "max_frames": MAX_FRAMES, "max_events": MAX_EVENTS}
TEMPORAL_CRITERIA = {
    "continuity": "motion",
    "overlap": "composition",
    "reading_time": "legibility",
    "coordination": "motion",
}


def temporal_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("creative_contract")
    policy = contract.get("temporal_review") if isinstance(contract, dict) else None
    if policy is None:
        return False
    if policy != POLICY:
        raise AuthError("MOTION_TEMPORAL_POLICY_UNAVAILABLE", 409)
    return True


@dataclass(frozen=True)
class TemporalEvent:
    id: str
    scene_id: str
    element_id: str | None
    kind: str
    start_ms: int
    end_ms: int
    indices: tuple[int, ...]


def events(composition: HTMLMotionComposition) -> tuple[list[TemporalEvent], int]:
    plan = composition.motion_plan
    if plan is None:
        raise AuthError("MOTION_TEMPORAL_PLAN_REQUIRED", 409)
    count = (plan.duration_ms * 30 + 999) // 1000
    candidates: list[TemporalEvent] = []

    def add(identifier: str, scene: str, element: str | None, kind: str, start: int, end: int) -> None:
        # Neighbours, boundaries and midpoint, snapped to actual 30-fps frames.
        first, last = start * 30 // 1000, end * 30 // 1000
        indices = tuple(
            sorted({max(0, min(count - 1, i)) for i in (first - 1, first, (first + last) // 2, last, last + 1)})
        )
        candidates.append(TemporalEvent(identifier, scene, element, kind, start, end, indices))

    for scene_index, scene in enumerate(plan.scenes):
        if scene_index:
            add(
                f"transition-{scene.id}",
                scene.id,
                None,
                "transition",
                max(0, scene.start_ms - 100),
                min(plan.duration_ms, scene.start_ms + 100),
            )
        for element in scene.elements:
            for index, beat in enumerate(element.beats):
                if beat.phase != "hold" or element.role == "text":
                    add(
                        f"beat-{element.id}-{index}",
                        scene.id,
                        element.id,
                        "speech" if beat.speech_cue_id else beat.phase,
                        beat.start_ms,
                        beat.end_ms,
                    )
                next_start = element.beats[index + 1].start_ms if index + 1 < len(element.beats) else scene.end_ms
                if element.role == "text" and beat.phase != "exit" and next_start > beat.end_ms:
                    add(f"hold-{element.id}-{index}", scene.id, element.id, "hold", beat.end_ms, next_start)
    # Stable distribution across the piece, not only its opening. No inferred beat/audio alignment.
    candidates.sort(key=lambda event: (event.start_ms, event.end_ms, event.id))
    total = len(candidates)
    speech_events = [event for event in candidates if event.kind == "speech"]
    if speech_events:
        others = [event for event in candidates if event.kind != "speech"]
        candidates = (speech_events + others)[:MAX_EVENTS]
    elif total > MAX_EVENTS:
        candidates = [candidates[round(i * (total - 1) / (MAX_EVENTS - 1))] for i in range(MAX_EVENTS)]
    return candidates, total


def sample_times(composition: HTMLMotionComposition, context: dict[str, Any]) -> tuple[int, ...]:
    if not temporal_enabled(context):
        return ()
    selected, _ = events(composition)
    assert composition.motion_plan is not None
    count = (composition.motion_plan.duration_ms * 30 + 999) // 1000
    indices = {round(i * (count - 1) / 4) for i in range(5)}
    indices.update(index for event in selected for index in event.indices)
    # ceil(frame*1000/30) maps back to that frame in the renderer's floor conversion.
    return tuple(
        (index * 1000 + 29) // 30
        for index in sorted(indices)
        if (index * 1000 + 29) // 30 < composition.motion_plan.duration_ms
    )


def evidence_manifest(
    composition: HTMLMotionComposition, frames: tuple[RenderedFrame, ...], version: str
) -> dict[str, Any]:
    selected, total = events(composition)
    assert composition.motion_plan is not None
    by_time = {frame.ms: frame for frame in frames}
    windows = []
    for event in selected:
        expected = [round(index * 1000 / 30) for index in event.indices]
        available = [by_time[ms] for ms in expected if ms in by_time]
        windows.append(
            {
                "id": event.id,
                "scene_id": event.scene_id,
                "element_id": event.element_id,
                "kind": event.kind,
                "start_ms": event.start_ms,
                "end_ms": event.end_ms,
                "expected_times_ms": expected,
                "boundary_clipped": event.indices[0] == 0
                or event.indices[-1] == (composition.motion_plan.duration_ms * 30 + 999) // 1000 - 1,
                "complete": len(available) == len(expected) and len(available) >= 3,
                "evidence": [{"version": version, "at_ms": f.ms, "sha256": f.sha256} for f in available],
            }
        )
    return {
        "policy": POLICY,
        "events": windows,
        "total_events": total,
        "omitted_events": total - len(selected),
        "scope": "Somente eventos amostrados; plano é intenção. Sem prova de fluidez integral, sincronismo ou áudio.",
    }


def temporal_payload(
    context: dict[str, Any],
    composition: HTMLMotionComposition | None,
    frames: tuple[RenderedFrame, ...],
    previous: HTMLMotionComposition | None,
    previous_frames: tuple[RenderedFrame, ...],
) -> dict[str, Any] | None:
    if not temporal_enabled(context):
        return None
    if composition is None:
        raise AuthError("MOTION_TEMPORAL_PLAN_REQUIRED", 409)
    return {
        "current": evidence_manifest(composition, frames, "current"),
        "previous": evidence_manifest(previous, previous_frames, "previous")
        if previous and previous.motion_plan
        else None,
    }
