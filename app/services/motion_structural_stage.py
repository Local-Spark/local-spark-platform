"""Build the v3 stage in code. The model does not own the page when this floor is on."""

import html
import json
from typing import Any

from app.services.motion_structural_floor import structural_floor_enabled

MEDIA_DIFF_MIN = 8.0


def beats_from_plan(plan: Any) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for scene in plan.scenes:
        mechanisms: list[str] = []
        copy = scene.message
        for element in scene.elements:
            mechanisms.extend(element.mechanism_ids)
            if element.kind == "text" and element.text:
                copy = element.text
        beats.append(
            {
                "id": scene.id,
                "start_ms": scene.start_ms,
                "end_ms": scene.end_ms,
                "scale": scene.structural_scale or "medium",
                "mechanism": mechanisms[0] if mechanisms else "axis_type_in",
                "mechanisms": mechanisms,
                "text": copy,
                "rect": [0.32, 0.42, 0.36, 0.28],
            }
        )
    return beats


def compose_structural_stage(plan: Any, source_asset_id: str) -> tuple[str, str]:
    """Return HTML and scene_init. Text lives inside the media stage."""
    records = beats_from_plan(plan)
    declared = "".join(
        f'<i data-mechanism="{html.escape(name)}" hidden></i>' for beat in records for name in beat["mechanisms"]
    )
    payload = json.dumps(
        [
            {key: beat[key] for key in ("id", "start_ms", "end_ms", "scale", "mechanism", "text", "rect")}
            for beat in records
        ],
        ensure_ascii=False,
    )
    page = f"""<!doctype html>
<meta charset="utf-8">
<style>
html,body{{margin:0;background:#1c1410}}
#stage{{position:relative;width:720px;height:1280px;overflow:hidden;background:#1c1410}}
video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#word{{position:absolute;left:8%;width:84%;top:58%;color:#f6f1e8;font:700 72px/1.05 sans-serif;text-align:center}}
#plate{{position:absolute;left:0;right:0;bottom:0;height:0;overflow:hidden;background:#f6f1e8;color:#1c1410}}
#plate-text{{padding:48px;font:700 42px/1.15 sans-serif}}
</style>
<div id="stage" data-stage="media">
  <video id="media" src="{html.escape(source_asset_id)}" muted playsinline></video>
  <div id="glyph"><video id="glyph-media" src="{html.escape(source_asset_id)}" muted playsinline></video></div>
  <div id="word"></div>
  <div id="plate"><div id="plate-text"></div></div>
  {declared}
</div>
<script type="application/json" id="structural-beats">{payload}</script>
"""
    scene = "window.seek=async(ms)=>{await MechanismsV1.seek(ms);};"
    return page, scene


def source_asset_id(assets: Any) -> str:
    for asset in assets:
        if str(getattr(asset, "mime_type", "")).startswith("video/"):
            return asset.id
    return "assets/source.mp4"


def stage_if_structural(composition: Any, context: dict[str, Any], assets: Any) -> Any:
    """Replace model HTML with the stage. No-op unless v3 was selected."""
    if not structural_floor_enabled(context.get("structural_floor")) or composition.motion_plan is None:
        return composition
    page, scene = compose_structural_stage(composition.motion_plan, source_asset_id(assets))
    return composition.model_copy(update={"html": page, "scene_init": scene})


def prove_beat_pixels(start: bytes, end: bytes, width: int, height: int) -> None:
    """Reject a beat whose media rectangle did not change. Raw RGB, no decoder."""
    expected = width * height * 3
    if len(start) != expected or len(end) != expected or width < 2 or height < 2:
        raise ValueError("STRUCTURAL_FRAME_INVALID")
    top = int(height * 0.12)
    bottom = int(height * 0.82)
    total = 0
    count = 0
    for y in range(top, bottom):
        row = y * width * 3
        for offset in range(row, row + width * 3):
            total += abs(start[offset] - end[offset])
            count += 1
    if total / count < MEDIA_DIFF_MIN:
        raise ValueError("STRUCTURAL_MEDIA_UNCHANGED")
