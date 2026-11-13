"""Pinned public sound files, available offline; metadata never substitutes for listening."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.adapters.motion_html_renderer import RenderAsset
from app.services.auth import AuthError
from app.services.motion_audio import validate_original_branch
from app.services.motion_quality import QUALITY_CONTRACT

if TYPE_CHECKING:
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan

ROOT = Path(__file__).resolve().parents[1] / "assets/motion_sounds"
LIBRARIES = {"public-cc0-v1": "27585d59dc871497b3dd6681487fc44c34228c4615f74378654fc577d9a08c99"}


def capture_sound_library(identifier: str) -> dict[str, Any]:
    if identifier not in LIBRARIES:
        raise AuthError("MOTION_SOUND_LIBRARY_UNAVAILABLE", 409)
    try:
        data = (ROOT / identifier / "manifest.json").read_bytes()
        if hashlib.sha256(data).hexdigest() != LIBRARIES[identifier]:
            raise ValueError
        result: dict[str, Any] = json.loads(data)
        return result
    except (OSError, ValueError) as exc:
        raise AuthError("MOTION_SOUND_LIBRARY_CHANGED", 409) from exc


def load_sound_library(context: dict[str, Any]) -> tuple[RenderAsset, ...]:
    library = context.get("sound_library")
    selected = context.get("request", {}).get("sound_library_id")
    if selected is None and library is None:
        return ()
    if library != capture_sound_library(selected):
        raise AuthError("MOTION_SOUND_LIBRARY_CHANGED", 409)
    assets = []
    for item in library["items"]:
        try:
            data = (ROOT / selected / item["file"]).read_bytes()
            if len(data) != item["size_bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError
        except (OSError, ValueError) as exc:
            raise AuthError("MOTION_SOUND_FILE_CHANGED", 409) from exc
        assets.append(RenderAsset(f"assets/sfx-{item['id']}.mp3", item["mime_type"], data, item["sha256"]))
    return tuple(assets)


def verify_sound_assets(context: dict[str, Any], assets: tuple[RenderAsset, ...]) -> None:
    for expected in load_sound_library(context):
        if [a for a in assets if a.id == expected.id] != [expected]:
            raise AuthError("MOTION_SOUND_FILE_CHANGED", 409)


def validate_sound_design(artifact: "MotionConstructionPlan | HTMLMotionComposition", context: dict[str, Any]) -> None:
    if not context.get("request", {}).get("propose_direction"):
        return
    design, plan = artifact.audiovisual, artifact.motion_plan
    if design is None or plan is None:
        raise AuthError("MOTION_AUDIOVISUAL_DESIGN_REQUIRED", 409)
    if design.functions and context.get("evolution") is None and context.get("quality_contract") is None:
        raise AuthError("MOTION_QUALITY_FUNCTION_COVERAGE_UNEXPECTED", 409)
    catalog = {item["id"]: item for item in context.get("sound_library", {}).get("items", [])}
    selected = {sound.candidate_id for sound in design.sounds}
    omitted = [item.candidate_id for item in design.omitted_sounds]
    if selected & set(omitted) or len(set(omitted)) != len(omitted) or selected | set(omitted) != set(catalog):
        raise AuthError("MOTION_SOUND_SELECTION_UNACCOUNTED", 409)
    identities = set()
    for sound in design.sounds:
        item = catalog[sound.candidate_id]
        available_ms = item["duration_ms"]
        assessment = context.get("audio_assessment")
        if assessment is not None:
            measured = next(
                (m for m in assessment["measurements"] if m["asset_id"] == f"assets/sfx-{sound.candidate_id}.mp3"), None
            )
            if (
                measured is None
                or measured["sha256"] != item["sha256"]
                or type(measured["decoded_duration_ms"]) is not int
                or not 0 < measured["decoded_duration_ms"] <= 60000
            ):
                raise AuthError("MOTION_SOUND_ANALYSIS_CHANGED", 409)
            available_ms = min(available_ms, measured["decoded_duration_ms"])
        scene = next((s for s in plan.scenes if s.id == sound.scene_id), None)
        element = next((e for e in scene.elements if e.id == sound.element_id), None) if scene else None
        source = context.get("source", {})
        source_content_action = (
            context.get("quality_contract") == QUALITY_CONTRACT
            and element is not None
            and element.role == "video"
            and element.asset_id == source.get("asset_id")
            and sound.action_end_ms <= source.get("duration_ms", 0)
        )
        key = (sound.candidate_id, sound.offset_ms)
        if (
            sound.candidate_sha256 != item["sha256"]
            or sound.trim_end_ms > available_ms
            or sound.offset_ms + sound.trim_end_ms - sound.trim_start_ms > plan.duration_ms
            or scene is None
            or element is None
            or not scene.start_ms <= sound.action_start_ms < sound.action_end_ms <= scene.end_ms
            or sound.offset_ms >= sound.action_end_ms
            or sound.offset_ms + sound.trim_end_ms - sound.trim_start_ms <= sound.action_start_ms
            or not any(
                (beat.phase != "hold" or source_content_action)
                and beat.start_ms <= sound.action_start_ms
                and sound.action_end_ms <= beat.end_ms
                for beat in element.beats
            )
            or key in identities
        ):
            raise AuthError("MOTION_SOUND_ACTION_INVALID", 409)
        identities.add(key)


def apply_planned_sound(
    prepared: "PreparedMotionInput", artifact: "MotionConstructionPlan | HTMLMotionComposition"
) -> "PreparedMotionInput":
    if not prepared.context.get("request", {}).get("propose_direction"):
        return prepared
    validate_sound_design(artifact, prepared.context)
    verify_sound_assets(prepared.context, prepared.assets)
    assert artifact.audiovisual is not None
    sounds = artifact.audiovisual.sounds
    if not sounds:
        return prepared
    tracks = [{**track, "role": "original", "fade_in_ms": 0, "fade_out_ms": 0} for track in prepared.audio["tracks"]]
    for sound in sounds:
        tracks.append(
            {
                "asset_id": f"assets/sfx-{sound.candidate_id}.mp3",
                "role": "effect",
                **sound.model_dump(
                    include={"offset_ms", "trim_start_ms", "trim_end_ms", "volume", "fade_in_ms", "fade_out_ms"}
                ),
            }
        )
    soundtrack = {"version": "motion-audio-v2", "mode": "mix", "tracks": tracks, "ducking": None}
    validate_original_branch(soundtrack, prepared.audio)
    return replace(
        prepared,
        soundtrack=soundtrack,
        context={
            **prepared.context,
            "authorized_soundtrack": soundtrack,
            "sound_listening_status": "unreviewed_suitability_source_duplication_voice_intelligibility",
        },
    )
