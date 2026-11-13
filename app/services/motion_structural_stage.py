"""Build the v3 stage in code. Speech, the measured subject and the rendered pixels decide the edit."""

import html
import json
import struct
import zlib
from typing import Any

from app.services.motion_structural_floor import structural_floor_enabled

MEDIA_DIFF_MIN = 8.0
DEFAULT_RECT = [0.32, 0.42, 0.36, 0.28]
SPEECH_DUCKING = {"threshold": 0.05, "ratio": 8, "attack_ms": 15, "release_ms": 250}


def _cues(context: dict[str, Any]) -> list[dict[str, Any]]:
    raw = (context.get("speech_result") or {}).get("cues") or []
    return [cue for cue in raw if isinstance(cue, dict) and "start_ms" in cue and "end_ms" in cue]


def _snap(beat: dict[str, Any], cues: list[dict[str, Any]]) -> dict[str, Any]:
    inside = [cue for cue in cues if beat["start_ms"] <= int(cue["start_ms"]) < beat["end_ms"]]
    if not inside:
        return beat
    spoken = " ".join(str(cue.get("text") or "").strip() for cue in inside).strip()
    snapped = dict(beat)
    snapped["start_ms"] = int(inside[0]["start_ms"])
    snapped["end_ms"] = max(int(inside[-1]["end_ms"]), snapped["start_ms"] + 1)
    if spoken:
        snapped["text"] = spoken
    return snapped


def beats_from_plan(
    plan: Any, cues: list[dict[str, Any]] | None = None, rect: list[float] | None = None
) -> list[dict[str, Any]]:
    box = rect or DEFAULT_RECT
    beats: list[dict[str, Any]] = []
    for scene in plan.scenes:
        mechanisms: list[str] = []
        copy = scene.message
        for element in scene.elements:
            mechanisms.extend(element.mechanism_ids)
            if element.kind == "text" and element.text:
                copy = element.text
        beats.append(
            _snap(
                {
                    "id": scene.id,
                    "start_ms": scene.start_ms,
                    "end_ms": scene.end_ms,
                    "scale": scene.structural_scale or "medium",
                    "mechanism": mechanisms[0] if mechanisms else "axis_type_in",
                    "mechanisms": mechanisms,
                    "text": copy,
                    "rect": box,
                },
                cues or [],
            )
        )
    return beats


def compose_structural_stage(
    plan: Any,
    source_asset_id: str,
    cues: list[dict[str, Any]] | None = None,
    rect: list[float] | None = None,
) -> tuple[str, str]:
    """Return HTML and scene_init. Text lives inside the media stage."""
    records = beats_from_plan(plan, cues, rect)
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


def _paeth(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    if abs(estimate - left) <= abs(estimate - up) and abs(estimate - left) <= abs(estimate - up_left):
        return left
    if abs(estimate - up) <= abs(estimate - up_left):
        return up
    return up_left


def decode_png_rgb(png: bytes) -> tuple[bytes, int, int]:
    """Decode a non-interlaced 8-bit RGB or RGBA PNG. No other formats."""
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("STRUCTURAL_FRAME_INVALID")
    position, width, height, color, data = 8, 0, 0, 0, bytearray()
    while position + 8 <= len(png):
        length, kind = struct.unpack(">I4s", png[position : position + 8])
        chunk = png[position + 8 : position + 8 + length]
        if len(chunk) != length:
            raise ValueError("STRUCTURAL_FRAME_INVALID")
        if kind == b"IHDR":
            width, height, depth, color, compression, png_filter, interlace = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or color not in (2, 6) or compression or png_filter or interlace:
                raise ValueError("STRUCTURAL_FRAME_INVALID")
        elif kind == b"IDAT":
            data.extend(chunk)
        elif kind == b"IEND":
            break
        position += 12 + length
    if not width or not data:
        raise ValueError("STRUCTURAL_FRAME_INVALID")
    raw = zlib.decompress(bytes(data))
    channels = 3 if color == 2 else 4
    stride = width * channels
    rows = []
    cursor = 0
    previous = bytearray(stride)
    for _ in range(height):
        png_filter, cursor = raw[cursor], cursor + 1
        row = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        if png_filter == 1:
            for index in range(stride):
                row[index] = (row[index] + (row[index - channels] if index >= channels else 0)) & 255
        elif png_filter == 2:
            for index in range(stride):
                row[index] = (row[index] + previous[index]) & 255
        elif png_filter == 3:
            for index in range(stride):
                left = row[index - channels] if index >= channels else 0
                row[index] = (row[index] + ((left + previous[index]) // 2)) & 255
        elif png_filter == 4:
            for index in range(stride):
                left = row[index - channels] if index >= channels else 0
                up_left = previous[index - channels] if index >= channels else 0
                row[index] = (row[index] + _paeth(left, previous[index], up_left)) & 255
        elif png_filter != 0:
            raise ValueError("STRUCTURAL_FRAME_INVALID")
        previous = row
        rows.append(bytes(row[index] for index in range(stride) if color == 2 or index % 4 != 3))
    return b"".join(rows), width, height


def measure_subject_rect(frames: Any) -> list[float] | None:
    """Box of pixels that differ from the corners. None when the frame has no subject."""
    png = next((getattr(frame, "png", b"") for frame in frames), b"")
    if not png:
        return None
    try:
        rgb, width, height = decode_png_rgb(png)
    except (ValueError, zlib.error):
        return None
    corners = []
    for y, x0 in ((0, 0), (0, width - 4), (height - 4, 0), (height - 4, width - 4)):
        for row in range(max(y, 0), min(y + 4, height)):
            for column in range(max(x0, 0), min(x0 + 4, width)):
                offset = (row * width + column) * 3
                corners.append(rgb[offset : offset + 3])
    background = tuple(sum(pixel[channel] for pixel in corners) // len(corners) for channel in range(3))
    min_x, min_y, max_x, max_y, count = width, height, 0, 0, 0
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            if sum(abs(rgb[offset + channel] - background[channel]) for channel in range(3)) <= 80:
                continue
            count += 1
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)
    if count < width * height // 100 or max_x <= min_x or max_y <= min_y:
        return None
    pad_x, pad_y = width * 0.04, height * 0.04
    left = max(0.0, (min_x - pad_x) / width)
    top = max(0.0, (min_y - pad_y) / height)
    right = min(1.0, (max_x + pad_x) / width)
    bottom = min(1.0, (max_y + pad_y) / height)
    return [round(left, 4), round(top, 4), round(max(right - left, 0.12), 4), round(max(bottom - top, 0.12), 4)]


def stage_if_structural(composition: Any, context: dict[str, Any], assets: Any, frames: Any = ()) -> Any:
    """Replace model HTML with the stage. No-op unless v3 was selected."""
    if not structural_floor_enabled(context.get("structural_floor")) or composition.motion_plan is None:
        return composition
    page, scene = compose_structural_stage(
        composition.motion_plan, source_asset_id(assets), _cues(context), measure_subject_rect(frames)
    )
    return composition.model_copy(update={"html": page, "scene_init": scene})


def duck_for_speech(audio: dict[str, Any] | None, context: dict[str, Any]) -> dict[str, Any] | None:
    """Lower music while the original voice is present. No-op without v3, words or a music bed."""
    if audio is None or not structural_floor_enabled(context.get("structural_floor")) or not _cues(context):
        return audio
    tracks = audio.get("tracks") or []
    if audio.get("ducking") or not any(track.get("role") == "music" for track in tracks):
        return audio
    return {**audio, "ducking": dict(SPEECH_DUCKING)}


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


def prove_storyboard_frames(moments: Any, evidence: Any) -> None:
    """Compare the rendered start and end of each structural beat."""
    grouped: dict[str, dict[str, bytes]] = {}
    for moment, frame in zip(moments, evidence, strict=False):
        kind = str(moment.get("kind") or "")
        if kind.startswith("structural_"):
            grouped.setdefault(moment["scene_id"], {})[kind] = frame.png
    for ends in grouped.values():
        start = ends.get("structural_start") or ends.get("structural_mid")
        finish = ends.get("structural_end")
        if start is None or finish is None:
            raise ValueError("STRUCTURAL_BEAT_UNPROVEN")
        before, width, height = decode_png_rgb(start)
        after, _, _ = decode_png_rgb(finish)
        prove_beat_pixels(before, after, width, height)
