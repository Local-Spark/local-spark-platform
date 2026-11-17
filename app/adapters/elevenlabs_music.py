"""Bounded, single-attempt Music transport. Funding belongs to the service."""

import hashlib
import json
from typing import Any

import httpx

from app.adapters.material_media import FetchedMedia
from app.core.config import Settings
from app.services.auth import AuthError

MAX_MUSIC_BYTES = 1024 * 1024
MAX_ERROR_BYTES = 16384
ERROR_CATEGORIES = frozenset(
    {
        "invalid_api_key",
        "missing_permissions",
        "quota_exceeded",
        "insufficient_credits",
        "rate_limit_exceeded",
        "too_many_concurrent_requests",
        "model_not_found",
        "invalid_model_id",
        "invalid_output_format",
        "bad_prompt",
    }
)


async def provider_failure(response: httpx.Response) -> AuthError:
    """Keep only HTTP status and a closed category set; never echo provider text."""
    code = f"MOTION_MUSIC_HTTP_{response.status_code}"
    body = bytearray()
    async for chunk in response.aiter_bytes():
        if len(body) + len(chunk) > MAX_ERROR_BYTES:
            return AuthError(code, 502)
        body.extend(chunk)
    try:
        data = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return AuthError(code, 502)
    detail = data.get("detail") if isinstance(data, dict) else None
    category = detail.get("status") if isinstance(detail, dict) else None
    if isinstance(category, str) and category in ERROR_CATEGORIES:
        code += "_" + category.upper()
    return AuthError(code, 502)


class ElevenLabsMusic:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate(self, payload: dict[str, Any]) -> FetchedMedia:
        if not self.settings.elevenlabs_music_execution_enabled or not self.settings.elevenlabs_api_key:
            raise AuthError("MOTION_MUSIC_DISABLED", 409)
        data = bytearray()
        try:
            async with httpx.AsyncClient(timeout=180, follow_redirects=False, trust_env=False) as client:
                async with client.stream(
                    "POST",
                    "https://api.elevenlabs.io/v1/music",
                    params={"output_format": "mp3_44100_128"},
                    headers={"xi-api-key": self.settings.elevenlabs_api_key.get_secret_value()},
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        raise await provider_failure(response)
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_MUSIC_BYTES:
                            raise AuthError("MOTION_MUSIC_TOO_LARGE", 502)
        except httpx.HTTPError:
            raise AuthError("MOTION_MUSIC_OUTCOME_UNCERTAIN", 502) from None
        if not data:
            raise AuthError("MOTION_MUSIC_EMPTY", 502)
        return FetchedMedia(bytes(data), "audio/mpeg", hashlib.sha256(data).hexdigest())
