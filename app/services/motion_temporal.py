"""Bounded, deterministic sampling of planned events; evidence is decoded video, never plan text."""

from dataclasses import dataclass
from typing import Any

from app.adapters.motion_html_renderer import RenderedFrame
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError

MAX_EVENTS = 3
MAX_FRAMES = 20
POLICY = {"version": "motion-temporal-v1", "max_frames": MAX_FRAMES, "max_events": MAX_EVENTS}
POLICY_V2 = {"version": "motion-temporal-v2", "max_frames": MAX_FRAMES, "max_events": MAX_EVENTS}
POLICY_V3 = {"version": "motion-temporal-v3", "max_frames": MAX_FRAMES, "max_events": MAX_EVENTS}
POLICY_V4: dict[str, Any] = {"version": "motion-temporal-v4", "max_frames": 48, "max_events": 16}
POLICY_V5: dict[str, Any] = {**POLICY_V4, "version": "motion-temporal-v5"}
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
    if policy not in (POLICY, POLICY_V2, POLICY_V3, POLICY_V4, POLICY_V5):
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


def events(composition: HTMLMotionComposition, policy: dict[str, Any] = POLICY) -> tuple[list[TemporalEvent], int]:
    plan = composition.motion_plan
    if plan is None:
        raise AuthError("MOTION_TEMPORAL_PLAN_REQUIRED", 409)
    count = (plan.duration_ms * 30 + 999) // 1000
    candidates: list[TemporalEvent] = []

    def add(identifier: str, scene: str, element: str | None, kind: str, start: int, end: int) -> None:
        # Neighbours, boundaries and midpoint, snapped to actual 30-fps frames.
        first, last = start * 30 // 1000, end * 30 // 1000
        points = (
            (first, (first + last) // 2, last)
            if policy in (POLICY_V4, POLICY_V5)
            else (first - 1, first, (first + last) // 2, last, last + 1)
        )
        if policy == POLICY_V5 and kind == "reading":
            points = (first - 1, first, min(count - 1, (start * 30 + 999) // 1000), (first + last) // 2, last)
        indices = tuple(sorted({max(0, min(count - 1, i)) for i in points}))
        candidates.append(TemporalEvent(identifier, scene, element, kind, start, end, indices))

    for scene_index, scene in enumerate(plan.scenes):
        if scene_index:
            start = max(0, scene.start_ms - 100)
            end = min(plan.duration_ms, max(scene.start_ms + 100, plan.scenes[scene_index - 1].end_ms))
            if policy in (POLICY_V3, POLICY_V4, POLICY_V5):
                # Follow overlapping entry/exit beats through the actual handoff,
                # including a delayed entry that begins as the outgoing object leaves.
                handoff = [
                    beat
                    for part in plan.scenes[scene_index - 1 : scene_index + 1]
                    for element in part.elements
                    for beat in element.beats
                    if beat.phase in {"enter", "exit"}
                ]
                while True:
                    linked = [beat for beat in handoff if beat.start_ms <= end and beat.end_ms >= start]
                    expanded = (min([start, *(b.start_ms for b in linked)]), max([end, *(b.end_ms for b in linked)]))
                    if expanded == (start, end):
                        break
                    start, end = expanded
            add(
                f"transition-{scene.id}",
                scene.id,
                None,
                "transition",
                start,
                min(plan.duration_ms, scene.start_ms + 100) if policy == POLICY else end,
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
    if policy in (POLICY_V4, POLICY_V5):
        # Explicit staging intervals are obligations, not an arbitrary frame quota.
        candidates.clear()
        if composition.staging is None:
            raise AuthError("MOTION_STAGING_REQUIRED", 409)
        for moment in composition.staging.moments:
            add(
                f"moment-{moment.scene_id}",
                moment.scene_id,
                moment.protagonist_id,
                "staging",
                moment.inspect_start_ms,
                moment.inspect_end_ms,
            )
            if moment.transition is not None:
                transition = moment.transition
                add(
                    f"transition-{transition.next_scene_id}",
                    transition.next_scene_id,
                    None,
                    "transition",
                    transition.start_ms,
                    transition.end_ms,
                )
        if policy == POLICY_V5:
            final = plan.scenes[-1]
            if final.photo_closing is not None:
                cta = next(e for e in final.elements if e.id == final.photo_closing.cta_element_id)
                start = max([final.start_ms] + [b.end_ms for b in cta.beats if b.phase == "enter"])
                add(f"reading-{cta.id}", final.id, cta.id, "reading", start, final.end_ms)
        # Transitions first, then widest temporal gaps. All omitted IDs remain visible below.
        ranked = sorted(candidates, key=lambda e: (e.kind not in {"transition", "reading"}, e.start_ms, e.id))
        selected: list[TemporalEvent] = []
        used = {round(i * (count - 1) / 4) for i in range(5)}
        while ranked and len(selected) < POLICY_V4["max_events"]:
            best = min(
                ranked,
                key=lambda e: (
                    e.kind not in {"transition", "reading"},
                    -min((abs(e.start_ms - s.start_ms) for s in selected), default=plan.duration_ms),
                    e.start_ms,
                    e.id,
                ),
            )
            ranked.remove(best)
            if len(used | set(best.indices)) <= POLICY_V4["max_frames"]:
                selected.append(best)
                used.update(best.indices)
        return sorted(selected, key=lambda e: (e.start_ms, e.id)), len(candidates)
    total = len(candidates)
    if policy in (POLICY_V2, POLICY_V3):
        transitions = [event for event in candidates if event.kind == "transition"]
        # Reserve one window for a meaningful action whenever possible.
        actions = [event for event in candidates if event.kind not in {"transition", "hold", "exit"}]
        slots = min(len(transitions), MAX_EVENTS - bool(actions))
        selected = (
            [transitions[round(i * (len(transitions) - 1) / (slots - 1))] for i in range(slots)]
            if slots > 1
            else transitions[:slots]
        )
        roles = {element.id: element.role for scene in plan.scenes for element in scene.elements}
        for event in sorted(
            actions,
            key=lambda event: (
                roles.get(event.element_id or "") != "image",
                event.kind != "speech",
                abs((event.start_ms + event.end_ms) - plan.duration_ms),
                event.id,
            ),
        ):
            if len(selected) == MAX_EVENTS:
                break
            if any(abs(event.start_ms - other.start_ms) < 250 for other in selected):
                continue
            selected.append(event)
        for event in candidates:
            if len(selected) == MAX_EVENTS:
                break
            if event not in selected and all(abs(event.start_ms - other.start_ms) >= 250 for other in selected):
                selected.append(event)
        return sorted(selected, key=lambda event: (event.start_ms, event.id)), total
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
    policy = context["creative_contract"]["temporal_review"]
    selected, _ = events(composition, policy)
    assert composition.motion_plan is not None
    count = (composition.motion_plan.duration_ms * 30 + 999) // 1000
    plan = composition.motion_plan
    from app.services.motion_video_capabilities import enabled, quality_unlocked

    dense = enabled(context) and quality_unlocked(context)
    limit = 64 if dense else int(policy.get("max_frames", MAX_FRAMES))

    def _ms(index: int) -> int | None:
        value = (index * 1000 + 29) // 30
        return value if 0 <= index < count and value < plan.duration_ms else None

    # Event windows first so truncation never drops required temporal evidence.
    primary: list[int] = []
    seen: set[int] = set()
    for event in selected:
        for index in event.indices:
            ms = _ms(index)
            if ms is not None and ms not in seen:
                seen.add(ms)
                primary.append(ms)
    secondary: list[int] = []
    opening = plan.scenes[0]
    extras = {round(i * (count - 1) / 4) for i in range(5)}
    mid_ms = (opening.start_ms + opening.end_ms) // 2
    extras.add(mid_ms * 30 // 1000)
    for scene in plan.scenes:
        extras.add(scene.start_ms * 30 // 1000)
        extras.add(max(scene.start_ms, scene.end_ms - 1) * 30 // 1000)
        if dense:
            span = scene.end_ms - scene.start_ms
            if span >= 800:
                for frac in (0.25, 0.5, 0.75):
                    extras.add(int(scene.start_ms + span * frac) * 30 // 1000)
    for index in sorted(extras):
        ms = _ms(max(0, min(count - 1, index)))
        if ms is not None and ms not in seen:
            seen.add(ms)
            secondary.append(ms)
    ordered = primary + secondary
    if len(ordered) <= limit:
        return tuple(sorted(ordered))
    # Preserve all primary samples; fill remaining slots from secondary evenly.
    kept = list(primary[:limit])
    room = limit - len(kept)
    if room > 0 and secondary:
        step = max(1, (len(secondary) - 1) / max(1, room - 1)) if room > 1 else 0
        for i in range(room):
            candidate = secondary[round(i * step)]
            if candidate not in kept:
                kept.append(candidate)
    return tuple(sorted(kept)[:limit])


def evidence_manifest(
    composition: HTMLMotionComposition,
    frames: tuple[RenderedFrame, ...],
    version: str,
    policy: dict[str, Any] = POLICY,
) -> dict[str, Any]:
    selected, total = events(composition, policy)
    assert composition.motion_plan is not None
    plan_end = composition.motion_plan.duration_ms
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
                **(
                    {
                        "minimum_reading_ms": 1500,
                        "last_frame_end_ms": min(plan_end, (event.indices[-1] + 1) * 1000 / 30),
                    }
                    if policy == POLICY_V5 and event.kind == "reading"
                    else {}
                ),
                "complete": len(available) == len(expected) and len(available) >= 3,
                "evidence": [{"version": version, "at_ms": f.ms, "sha256": f.sha256} for f in available],
            }
        )
    return {
        "policy": policy,
        "events": windows,
        "total_events": total,
        "omitted_events": total - len(selected),
        **(
            {
                "covered_scene_ids": [
                    scene.id
                    for scene in composition.motion_plan.scenes
                    if any(event.start_ms < scene.end_ms and event.end_ms > scene.start_ms for event in selected)
                ],
                "uncovered_scene_ids": [
                    scene.id
                    for scene in composition.motion_plan.scenes
                    if not any(event.start_ms < scene.end_ms and event.end_ms > scene.start_ms for event in selected)
                ],
                "omitted_transitions": max(
                    0, len(composition.motion_plan.scenes) - 1 - sum(event.kind == "transition" for event in selected)
                ),
                "incomplete_events": sum(not item["complete"] for item in windows),
            }
            if policy in (POLICY_V2, POLICY_V3, POLICY_V4, POLICY_V5)
            else {}
        ),
        **(
            {
                "omitted_event_ids": sorted(
                    (
                        (
                            {f"moment-{m.scene_id}" for m in composition.staging.moments}
                            | {
                                f"transition-{m.transition.next_scene_id}"
                                for m in composition.staging.moments
                                if m.transition
                            }
                        )
                        | (
                            {f"reading-{composition.motion_plan.scenes[-1].photo_closing.cta_element_id}"}
                            if policy == POLICY_V5 and composition.motion_plan.scenes[-1].photo_closing
                            else set()
                        )
                    )
                    - {e.id for e in selected}
                ),
                "coverage_complete": total == len(selected) and all(w["complete"] for w in windows),
            }
            if policy in (POLICY_V4, POLICY_V5) and composition.staging is not None
            else {}
        ),
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
        "current": evidence_manifest(composition, frames, "current", context["creative_contract"]["temporal_review"]),
        "previous": evidence_manifest(
            previous, previous_frames, "previous", context["creative_contract"]["temporal_review"]
        )
        if previous and previous.motion_plan
        else None,
    }
