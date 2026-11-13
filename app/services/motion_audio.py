"""Compose owner-selected sound around, never instead of, the original branch."""

from typing import Any

from app.schemas.motion_production import MotionDucking, MotionSoundEvent
from app.services.auth import AuthError


def compile_soundtrack(
    original: dict[str, Any],
    events: tuple[MotionSoundEvent, ...],
    ducking: MotionDucking | None,
    materials: dict[str, dict[str, Any]],
    duration_ms: int,
) -> dict[str, Any] | None:
    if not events:
        if ducking is not None:
            raise AuthError("MOTION_AUDIO_DUCKING_INVALID", 409)
        return None
    if original.get("mode") == "silent" and original.get("tracks") == []:
        originals: list[dict[str, Any]] = []
    elif original.get("mode") == "mix" and len(original.get("tracks", [])) == 1:
        source = original["tracks"][0]
        if (
            source.get("asset_id") != "assets/source.mp4"
            or source.get("volume") != 1
            or source.get("offset_ms") != 0
            or source.get("trim_start_ms") != 0
        ):
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
        originals = [{**source, "role": "original", "fade_in_ms": 0, "fade_out_ms": 0}]
    else:
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    if ducking is not None and (not originals or not any(event.role == "music" for event in events)):
        raise AuthError("MOTION_AUDIO_DUCKING_INVALID", 409)
    tracks = list(originals)
    for event in events:
        material = materials.get(str(event.asset_id))
        if material is None or event.offset_ms + event.trim_end_ms - event.trim_start_ms > duration_ms:
            raise AuthError("MOTION_AUDIO_MATERIAL_UNAVAILABLE", 409)
        tracks.append(
            {
                "asset_id": material["asset_id"],
                "offset_ms": event.offset_ms,
                "trim_start_ms": event.trim_start_ms,
                "trim_end_ms": event.trim_end_ms,
                "volume": event.volume,
                "role": event.role,
                "fade_in_ms": event.fade_in_ms,
                "fade_out_ms": event.fade_out_ms,
            }
        )
    result = {
        "version": "motion-audio-v2",
        "mode": "mix",
        "tracks": tracks,
        "ducking": ducking.model_dump(mode="json") if ducking else None,
    }
    validate_original_branch(result, original)
    return result


def validate_original_branch(soundtrack: dict[str, Any], original: dict[str, Any]) -> None:
    """Protect the original branch independently of model output and audio additions."""
    tracks = soundtrack.get("tracks")
    if soundtrack.get("version") != "motion-audio-v2" or not isinstance(tracks, list):
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    source_tracks = [track for track in tracks if track.get("role") == "original"]
    if original == {"mode": "silent", "tracks": []}:
        if source_tracks:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    elif original.get("mode") == "mix" and len(original.get("tracks", [])) == 1:
        expected = {**original["tracks"][0], "role": "original", "fade_in_ms": 0, "fade_out_ms": 0}
        if len(source_tracks) != 1 or not tracks or tracks[0] != expected:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    else:
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    if any(track.get("asset_id") == "assets/source.mp4" and track.get("role") != "original" for track in tracks):
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
