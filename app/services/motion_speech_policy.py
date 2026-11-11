"""Local speech is opt-in, versioned and separately provisioned; never downloads a model."""

import re
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.services.auth import AuthError


def speech_policy(settings: Settings) -> dict[str, Any] | None:
    if settings.motion_speech_mode == "disabled":
        return None
    if not Path(settings.motion_speech_model_directory).is_absolute() or not re.fullmatch(
        r"[a-f0-9]{64}", settings.motion_speech_model_sha256
    ):
        raise AuthError("MOTION_SPEECH_NOT_CONFIGURED", 409)
    return {
        "version": "local-word-speech-v1",
        "backend": "faster-whisper",
        "model_sha256": settings.motion_speech_model_sha256,
        "language": settings.motion_speech_language,
        "threads": settings.motion_speech_threads,
        "timeout_seconds": settings.motion_speech_timeout_seconds,
        "max_duration_ms": 60000,
        "provenance": "local_asr_unreviewed",
    }
