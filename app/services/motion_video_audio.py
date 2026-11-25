"""Server-owned EDL audio and local licensed additions; never dispatch a music provider."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from app.services.auth import AuthError
from app.services.motion_video_capabilities import validate_edl

if TYPE_CHECKING:
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan

DUCK = {"threshold": 0.02, "ratio": 6, "attack_ms": 15, "release_ms": 250}


def edited_original(artifact: Any) -> list[dict[str, Any]]:
    if artifact.audio.mode == "silent":
        return []
    return [
        dict(
            asset_id="assets/source.mp4",
            role="original",
            offset_ms=s.start_ms,
            trim_start_ms=s.video_layout.edit.source_in_ms,
            trim_end_ms=s.video_layout.edit.source_out_ms,
            volume=1,
            fade_in_ms=0,
            fade_out_ms=0,
        )
        for s in artifact.motion_plan.scenes
    ]


def compile_video_audio(
    prepared: "PreparedMotionInput", artifact: "HTMLMotionComposition | MotionConstructionPlan"
) -> dict[str, Any] | None:
    validate_edl(artifact, prepared.context)
    tracks = edited_original(artifact)
    # Base additions were authorized before planning, and are not supplied by model output.
    base = prepared.context.get("video_audio_base", prepared.context.get("authorized_soundtrack")) or {}
    assert artifact.motion_plan is not None
    duration = artifact.motion_plan.duration_ms
    for track in base.get("tracks", []):
        if track["role"] == "original" or track["offset_ms"] >= duration:
            continue
        length = min(track["trim_end_ms"] - track["trim_start_ms"], duration - track["offset_ms"])
        fade_in = min(track["fade_in_ms"], length)
        tracks.append(
            {
                **track,
                "trim_end_ms": track["trim_start_ms"] + length,
                "fade_in_ms": fade_in,
                "fade_out_ms": min(track["fade_out_ms"], length - fade_in),
            }
        )
    catalog = {item["id"]: item for item in prepared.context.get("sound_library", {}).get("items", [])}
    if artifact.audiovisual:
        for sound in artifact.audiovisual.sounds:
            if catalog[sound.candidate_id].get("license") != "CC0-1.0":
                raise AuthError("MOTION_VIDEO_SOUND_LICENSE_REQUIRED", 409)
            tracks.append(
                {
                    "asset_id": f"assets/sfx-{sound.candidate_id}.mp3",
                    "role": "effect",
                    **sound.model_dump(
                        include={"offset_ms", "trim_start_ms", "trim_end_ms", "volume", "fade_in_ms", "fade_out_ms"}
                    ),
                }
            )
    if not tracks:
        return None
    if len(tracks) > 16:
        raise AuthError("MOTION_VIDEO_AUDIO_TRACK_LIMIT", 409)
    music = any(t["role"] == "music" for t in tracks)
    return {
        "version": "motion-audio-v3",
        "mode": "mix",
        "tracks": tracks,
        "ducking": dict(DUCK) if music and artifact.audio.mode != "silent" else None,
    }


def apply_video_audio(
    prepared: "PreparedMotionInput", artifact: "HTMLMotionComposition | MotionConstructionPlan"
) -> "PreparedMotionInput":
    context = dict(prepared.context)
    context.setdefault("video_audio_base", context.get("authorized_soundtrack"))
    assert artifact.motion_plan is not None
    duration = artifact.motion_plan.duration_ms
    context["output"] = {**context.get("output", {}), "duration_ms": duration}
    prepared = replace(prepared, context=context, duration_ms=duration)
    soundtrack = compile_video_audio(prepared, artifact)
    return replace(
        prepared,
        soundtrack=soundtrack,
        context={
            **context,
            "authorized_soundtrack": soundtrack,
            "video_audio_edl": edited_original(artifact),
            "video_mix_status": "music_duck_ready"
            if soundtrack and soundtrack["ducking"]
            else "music_ready"
            if soundtrack and any(t["role"] == "music" for t in soundtrack["tracks"])
            else context.get("video_music_status", "no_eligible_music"),
            "sound_listening_status": "requires_human_listening",
        },
    )
