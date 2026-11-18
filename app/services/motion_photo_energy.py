"""N2 checks numeric plan declarations, never rendered pixels or crop geometry."""

import math
import re

from app.schemas.motion_plan import MotionBeat, MotionPlan
from app.services.auth import AuthError

_NUMBER = r"(-?(?:\d+(?:\.\d+)?|\.\d+))"
_STATE = re.compile(rf"scale={_NUMBER} x_pct={_NUMBER} y_pct={_NUMBER}")


def _state(value: str) -> tuple[float, ...] | None:
    match = _STATE.fullmatch(value)
    if match is None:
        return None
    values = tuple(float(number) for number in match.groups())
    if not all(math.isfinite(number) for number in values) or values[0] <= 0:
        return None
    return values


def energetic(beat: MotionBeat) -> bool:
    if beat.phase != "transform" or beat.curve.kind != "linear":
        return False
    start, end = _state(beat.start_state), _state(beat.end_state)
    if start is None or end is None:
        return False
    seconds = (beat.end_ms - beat.start_ms) / 1000
    return any(
        abs(b - a) + 1e-9 >= minimum * seconds for a, b, minimum in zip(start, end, (0.01, 0.5, 0.5), strict=True)
    )


def validate_photo_energy(plan: MotionPlan) -> None:
    intervals = []
    for scene in plan.scenes:
        photos = [e for e in scene.elements if e.role == "image" and (e.asset_id or "").startswith("assets/photo-")]
        related = {identifier for photo in photos for identifier in photo.related_element_ids}
        candidates = photos + [e for e in scene.elements if e.id in related and e.role in {"text", "graphic"}]
        intervals.extend(
            (beat.start_ms, beat.end_ms) for element in candidates for beat in element.beats if energetic(beat)
        )
    covered = 0
    for start, end in sorted(intervals) + [(plan.duration_ms, plan.duration_ms)]:
        if start - covered > 2500:
            raise AuthError("MOTION_PHOTO_ENERGY_REQUIRED", 409)
        covered = max(covered, end)
