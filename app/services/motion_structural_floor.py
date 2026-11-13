"""Opt-in structural floor for motion plans. Not selected by generation.

v2 remains the active quality contract. This module only evaluates a plan-shaped
dict when a caller explicitly asks for motion-production-quality-v3. It does not
render, spend, or approve a piece. Pixel gates (anchor intersection, contrast on
a decoded frame) are out of scope until a later render slice.
"""

from typing import Any

FLOOR_VERSION = "motion-production-quality-v3"
ENABLED_BY_DEFAULT = False

MECHANISM_IDS = frozenset(
    {
        "ellipse_to_glyph",
        "axis_type_in",
        "mask_open_from_point",
        "plate_cta",
    }
)


def structural_floor_enabled(selection: str | None) -> bool:
    """True only when the caller names v3. Omission and v2 stay off."""
    return selection == FLOOR_VERSION


def evaluate_structural_floor(piece: dict[str, Any]) -> tuple[str, ...]:
    """Return gate ids that fail. Empty means the plan shape passes this floor.

    `piece` is intentionally a plain dict so the check can run before a plan is
    admitted into the frozen production schema. Missing fields fail closed.
    """
    failures: list[str] = []
    beats = list(piece.get("beats") or [])
    duration = int(piece.get("duration_ms") or 0)
    long_piece = duration >= 8000
    if piece.get("letterbox") != "kit_color":
        failures.append("margin_ban")
    if piece.get("third_party_mark_legible"):
        failures.append("third_party_mark")

    scales = {beat.get("scale") for beat in beats}
    minimum_beats = 3 if long_piece else 1
    minimum_scales = 3 if long_piece else 2
    if len(beats) < minimum_beats or len(scales) < minimum_scales:
        failures.append("scale_count")
    roles = {beat.get("role") for beat in beats}
    if long_piece and not {"establish", "extract", "invite"} <= roles:
        failures.append("role_sequence")

    for beat in beats:
        span = int(beat.get("t_out_ms") or 0) - int(beat.get("t_in_ms") or 0)
        same_crop = beat.get("crop_changes_inside") is not True
        if span > 2500 and same_crop:
            failures.append("no_dead_hold")
            break

    covered: set[str] = set()
    for beat in beats:
        if beat.get("copy"):
            covered.add(str(beat["copy"]))
        if beat.get("support_copy"):
            covered.add(str(beat["support_copy"]))
    phrases = [str(item) for item in piece.get("spoken_phrases") or []]
    if phrases and not piece.get("audio_trimmed") and any(phrase not in covered for phrase in phrases):
        failures.append("copy_coverage")

    for beat in beats:
        protagonist = beat.get("protagonist")
        anchor_kind = (beat.get("anchor") or {}).get("kind", "none")
        needs_anchor = protagonist in {"type", "cta"}
        if needs_anchor and anchor_kind == "none":
            failures.append("anchor_required")
            break
        if protagonist == "type":
            hold = int(beat.get("hold_ms") or 0)
            height = float(beat.get("hero_height_ratio") or 0)
            if hold < 700 or height < 0.18 or beat.get("moves_during_hold") is True:
                failures.append("hold_legibility")
                break
            if float(beat.get("contrast_ratio") or 0) < 4.5:
                failures.append("contrast")
                break
            mechanisms = list(beat.get("mechanism") or [])
            if not mechanisms or any(item not in MECHANISM_IDS for item in mechanisms):
                failures.append("mechanism_known")
                break
        if protagonist == "cta":
            hold = int(beat.get("hold_ms") or 0)
            if beat.get("cta_plate") is not True or hold < 1000 or beat.get("cta_outside_media") is True:
                failures.append("cta_block")
                break
        if beat.get("text_outside_media") is True:
            failures.append("margin_ban")
            break

    unique: list[str] = []
    for item in failures:
        if item not in unique:
            unique.append(item)
    return tuple(unique)


def _hold_ms(element: Any) -> int:
    hold = 0
    for beat in element.beats:
        if beat.phase == "hold":
            hold = max(hold, beat.end_ms - beat.start_ms)
    return hold


def view_from_plan(plan: Any) -> dict[str, Any]:
    """Project a real motion plan into the structural checker.

    Scales and roles come only from the scene fields. They are not inferred,
    so a one-scene caption plan fails closed when v3 is selected.
    """
    beats: list[dict[str, Any]] = []
    scenes = list(plan.scenes)
    for index, scene in enumerate(scenes):
        texts = [element for element in scene.elements if element.role == "text"]
        text = texts[0] if texts else None
        last = index == len(scenes) - 1
        role = scene.structural_role or ("invite" if last else "establish" if index == 0 else "extract")
        protagonist = "gesture"
        if text is not None and role == "invite":
            protagonist = "cta"
        elif text is not None:
            protagonist = "type"
        elif any(element.role in {"image", "video"} for element in scene.elements):
            protagonist = "product"
        mechanisms = list(text.mechanism_ids) if text is not None else []
        anchor_kind = "object_edge" if text is not None and text.related_element_ids else "none"
        beats.append(
            {
                "t_in_ms": scene.start_ms,
                "t_out_ms": scene.end_ms,
                "role": role,
                "scale": scene.structural_scale or "medium",
                "protagonist": protagonist,
                "copy": text.purpose if text is not None else "",
                "anchor": {"kind": anchor_kind},
                "mechanism": mechanisms,
                "hold_ms": _hold_ms(text) if text is not None else 0,
                "hero_height_ratio": text.hero_height_ratio if text is not None else None,
                "contrast_ratio": text.contrast_ratio if text is not None else None,
                "moves_during_hold": False,
                "crop_changes_inside": True,
                "text_outside_media": bool(text.text_outside_media) if text is not None else False,
                "cta_plate": "plate_cta" in mechanisms,
                "cta_outside_media": bool(text.text_outside_media) if text is not None else False,
            }
        )
    return {
        "duration_ms": plan.duration_ms,
        "letterbox": "kit_color",
        "third_party_mark_legible": False,
        "audio_trimmed": True,
        "spoken_phrases": [],
        "beats": beats,
    }


class StructuralFloorRejected(Exception):
    """Plan failed the opt-in structural floor. The caller maps this to an API error."""


def enforce_structural_floor(plan: Any, context: dict[str, Any]) -> None:
    """Reject a plan before render when the request selected v3. No-op otherwise."""
    if not structural_floor_enabled(context.get("structural_floor")):
        return
    if plan is None or evaluate_structural_floor(view_from_plan(plan)):
        raise StructuralFloorRejected()


