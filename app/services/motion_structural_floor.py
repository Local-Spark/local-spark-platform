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
