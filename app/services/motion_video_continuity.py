"""Structural continuity for video plans: fill beat holes without inventing creative layers."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from app.services.auth import AuthError
from app.services.motion_video_capabilities import design_schema_enabled, state

_SHELL_STYLE = re.compile(r"(<(?:html|body|main)\b[^>]*?\sstyle=\")([^\"]*)(\")", re.IGNORECASE)
_SHELL_OPEN = re.compile(r"<(html|body|main)\b(?![^>]*\sstyle=)([^>]*)>", re.IGNORECASE)


def _layer_state(raw: str) -> dict[str, float] | None:
    try:
        return state(raw)
    except AuthError:
        return None


def _hold(start_ms: int, end_ms: int, raw_state: str, trajectory: str) -> dict[str, Any]:
    return {
        "phase": "hold",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "start_state": raw_state,
        "end_state": raw_state,
        "trajectory": trajectory,
        "curve": {"kind": "linear", "parameters": []},
    }


def _bridge_beats(beats: list[dict[str, Any]], scene_start: int, scene_end: int) -> list[dict[str, Any]]:
    if not beats or any(_layer_state(b["start_state"]) is None or _layer_state(b["end_state"]) is None for b in beats):
        return beats
    ordered = sorted((dict(b) for b in beats), key=lambda b: (b["start_ms"], b["end_ms"]))
    trajectory = ordered[0].get("trajectory") or "sustain"
    if ordered[0]["start_ms"] > scene_start:
        ordered.insert(0, _hold(scene_start, ordered[0]["start_ms"], ordered[0]["start_state"], trajectory))
    bridged = [ordered[0]]
    for beat in ordered[1:]:
        previous = bridged[-1]
        if beat["start_ms"] > previous["end_ms"]:
            bridged.append(_hold(previous["end_ms"], beat["start_ms"], previous["end_state"], trajectory))
            previous = bridged[-1]
        if beat["start_ms"] == previous["end_ms"] and beat["start_state"] != previous["end_state"]:
            beat = {**beat, "start_state": previous["end_state"]}
        bridged.append(beat)
    if bridged[-1]["end_ms"] < scene_end:
        bridged.append(_hold(bridged[-1]["end_ms"], scene_end, bridged[-1]["end_state"], trajectory))
    return bridged


def _ensure_video_related(element: dict[str, Any], video_element_id: str) -> None:
    related = list(element.get("related_element_ids") or [])
    if video_element_id not in related:
        element["related_element_ids"] = [*related, video_element_id]


def _center_floor(box: dict[str, Any], *, min_width: float, min_height: float) -> dict[str, Any]:
    width = max(float(box.get("width") or 0), min_width)
    height = max(float(box.get("height") or 0), min_height)
    x = float(box.get("x") or 0)
    y = float(box.get("y") or 0)
    cx, cy = x + float(box.get("width") or 0) / 2, y + float(box.get("height") or 0) / 2
    x = min(max(0.0, cx - width / 2), 1.0 - width)
    y = min(max(0.0, cy - height / 2), 1.0 - height)
    return {**box, "x": x, "y": y, "width": width, "height": height}


def _clamp_layer_floors(design: dict[str, Any], elements: dict[str, dict[str, Any]]) -> None:
    for layer in design.get("layers") or []:
        box = layer.get("box") or {}
        element = elements.get(layer.get("element_id") or "")
        if layer.get("shape") in {"bar", "rounded"} and float(box.get("width") or 0) + 1e-9 < 0.04:
            layer["box"] = _center_floor(box, min_width=0.04, min_height=float(box.get("height") or 0.01))
            box = layer["box"]
        if (
            element
            and element.get("role") == "image"
            and int(layer.get("z_index") or 0) > 10
            and (float(box.get("width") or 0) + 1e-9 < 0.5 or float(box.get("height") or 0) + 1e-9 < 0.5)
        ):
            layer["box"] = _center_floor(box, min_width=0.5, min_height=0.5)


def _safe_handoff_transition(layout: dict[str, Any], design: dict[str, Any]) -> None:
    edit = layout.get("edit")
    if not isinstance(edit, dict) or edit.get("transition") not in {"dissolve", "fade"}:
        return
    full = {"x": 0, "y": 0, "width": 1, "height": 1}
    if any(
        (layer.get("box") or {}) == full and int(layer.get("z_index") or 0) < 10
        for layer in design.get("layers") or []
    ):
        return
    edit["transition"] = "cut"


def normalize_video_motion_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Fill beat gaps, wire text→video relations, and floor layer boxes for gates."""
    result = deepcopy(plan)
    for scene in result.get("scenes") or []:
        layout = scene.get("video_layout")
        if not isinstance(layout, dict):
            continue
        video_id = layout.get("video_element_id")
        elements = {e["id"]: e for e in scene.get("elements") or [] if isinstance(e, dict) and "id" in e}
        design = layout.get("design")
        if isinstance(design, dict):
            _clamp_layer_floors(design, elements)
            _safe_handoff_transition(layout, design)
        start_ms = int(scene["start_ms"])
        end_ms = int(scene["end_ms"])
        for element in scene.get("elements") or []:
            if element.get("role") == "text" and isinstance(video_id, str):
                _ensure_video_related(element, video_id)
            if element.get("role") in {"text", "graphic", "image"}:
                element["beats"] = _bridge_beats(list(element.get("beats") or []), start_ms, end_ms)
    return result


def _clear_chrome_style(style: str) -> str:
    kept: list[str] = []
    for part in style.split(";"):
        declaration = part.strip()
        if not declaration:
            continue
        key = declaration.split(":", 1)[0].strip().lower()
        if (
            key == "background"
            or key.startswith("background-")
            or key == "box-shadow"
            or key.startswith("border")
            or key == "overflow"
            or key.startswith("overflow-")
        ):
            continue
        kept.append(declaration)
    kept.append("background:transparent")
    kept.append("overflow:visible")
    return ";".join(kept)


def normalize_video_html(html: str) -> str:
    """Clear painted html/body/main chrome; cream page canvas fails UNPLANNED_OVERLAY."""

    def replace_style(match: re.Match[str]) -> str:
        return match.group(1) + _clear_chrome_style(match.group(2)) + match.group(3)

    cleared = _SHELL_STYLE.sub(replace_style, html)

    def ensure_style(match: re.Match[str]) -> str:
        return f'<{match.group(1)}{match.group(2)} style="background:transparent;overflow:visible">'

    return _SHELL_OPEN.sub(ensure_style, cleared)


def _video_plan(plan: dict[str, Any] | None) -> bool:
    return any(isinstance(scene.get("video_layout"), dict) for scene in (plan or {}).get("scenes") or [])


def maybe_normalize_video_plan(plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not design_schema_enabled(context):
        return plan
    return normalize_video_motion_plan(plan)


def maybe_normalize_video_html(html: str, plan: dict[str, Any] | None, context: dict[str, Any] | None = None) -> str:
    del context  # API symmetry with plan normalize; video chrome is safe whenever video_layout exists.
    if not _video_plan(plan):
        return html
    return normalize_video_html(html)


def _design_layer_ids(plan: dict[str, Any] | None) -> list[str]:
    ids: list[str] = []
    for scene in (plan or {}).get("scenes") or []:
        design = ((scene.get("video_layout") or {}).get("design") or {}) if isinstance(scene, dict) else {}
        for layer in design.get("layers") or []:
            element_id = layer.get("element_id") if isinstance(layer, dict) else None
            if isinstance(element_id, str) and element_id and element_id not in ids:
                ids.append(element_id)
    return ids


def normalize_video_scene_init(scene_init: str, plan: dict[str, Any] | None) -> str:
    """Stop model scene_init from fighting capabilities-owned design.layers."""
    ids = _design_layer_ids(plan)
    if not ids or not scene_init:
        return scene_init
    cleaned = scene_init
    marker = (
        ".forEach(([id,i])=>{const node=document.getElementById(id);"
        "if(node)node.style.display=i===index?'block':'none';});"
    )
    while marker in cleaned:
        end = cleaned.index(marker) + len(marker)
        start = cleaned.rfind("[[", 0, cleaned.index(marker))
        if start < 0 or not any(item in cleaned[start:end] for item in ids):
            break
        cleaned = cleaned[:start] + cleaned[end:]
    # Keep MotionV1 from animating runtime-owned layer nodes.
    cleaned = cleaned.replace(
        "MotionV1.timeline(tracks)",
        "MotionV1.timeline(tracks.filter(t=>!" + json.dumps(ids) + ".includes(t.id)))",
    )
    return cleaned


def maybe_normalize_video_scene_init(
    scene_init: str, plan: dict[str, Any] | None, context: dict[str, Any] | None = None
) -> str:
    del context
    if not _video_plan(plan):
        return scene_init
    return normalize_video_scene_init(scene_init, plan)
