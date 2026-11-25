"""A1: internal instrumental selection/generation, funded before dispatch."""

import base64
import hashlib
import re
import unicodedata
from dataclasses import replace
from typing import Any, Protocol
from uuid import UUID, uuid5

from app.adapters.elevenlabs_music import ElevenLabsMusic
from app.adapters.material_media import FetchedMedia
from app.adapters.motion_html_renderer import RenderAsset
from app.adapters.motion_inputs import PreparedMotionInput
from app.adapters.motion_media import inspect_supplemental_audio
from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects
from app.services.motion_music_cache import MusicCache
from app.services.motion_photos import music_soundtrack
from app.services.visual_cost_ledger import VisualCostError

POLICY = "elevenlabs-music-v1"
MODEL = "music_v2_5"
MOODS = {
    "cafe": "Warm relaxed acoustic cafe jazz, piano and brushed drums, gentle background instrumental.",
    "calm": "Calm warm acoustic instrumental, gentle soft piano, relaxed background music.",
    "energetic": "Upbeat bright rhythmic instrumental, lively percussion, positive background music.",
    "neutral": "Warm positive modern instrumental, light rhythm, unobtrusive background music.",
}
_BUDGET_SILENCE = {
    "MOTION_REQUEST_BUDGET_EXCEEDED",
    "VISUAL_BUDGET_DISABLED",
    "VISUAL_BUDGET_EXCEEDED",
    "CREATION_LAB_RUN_BUDGET_EXCEEDED",
    "CREATION_LAB_ADMIN_BUDGET_EXCEEDED",
    "CREATION_LAB_EXECUTION_DISABLED",
}


def music_mood(instruction: str) -> str | None:
    normalized = unicodedata.normalize("NFKD", instruction.lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    if re.search(r"\b(sem (som|audio|musica|trilha)|silencio|silencioso|mudo|no music|silent)\b", normalized):
        return None
    for mood, words in (
        ("cafe", "cafe|jazz|cafeteria"),
        ("calm", "calmo|suave|relaxante|aconchegante"),
        ("energetic", "energetico|animado|festa|dinamico"),
    ):
        if re.search(r"\b(" + words + r")\b", normalized):
            return mood
    return "neutral"


class MusicProvider(Protocol):
    async def generate(self, payload: dict[str, Any]) -> FetchedMedia: ...


class MotionMusic:
    def __init__(self, effects: MotionEffects, provider: MusicProvider | None = None):
        self.effects = effects
        self.provider = provider
        self.cache = MusicCache(effects)

    def _funding(self, duration_ms: int) -> tuple[bool, int, int, int]:
        settings = self.effects.requests.settings
        reserve = settings.elevenlabs_music_reservation_usd_micros
        rate = settings.elevenlabs_music_usd_micros_per_minute
        estimate = (duration_ms * rate + 59999) // 60000
        enabled = bool(
            settings.elevenlabs_music_execution_enabled
            and settings.elevenlabs_api_key
            and settings.elevenlabs_music_commercial_rights_confirmed
            and reserve > 0
            and rate > 0
            and estimate <= reserve
            and settings.elevenlabs_music_monthly_budget_usd_micros >= reserve
        )
        return enabled, reserve, rate, estimate

    def _resolve_mood(self, prepared: PreparedMotionInput) -> str | None:
        mood = music_mood(prepared.context["request"]["instruction"])
        if mood == "neutral":
            facts = " ".join(fact["statement"] for fact in prepared.context.get("confirmed_facts", []))
            mood = music_mood(facts)
        return mood

    async def prepare(
        self, row: dict[str, Any], token: UUID, prepared: PreparedMotionInput, *, restore: bool = False
    ) -> PreparedMotionInput:
        from app.services.motion_video_capabilities import enabled as video_enabled

        if video_enabled(prepared.context):
            return await self.video_music(row, token, prepared, restore=restore)
        photo = prepared.context.get("photo_motion", {})
        if photo.get("music_policy") != POLICY:
            return prepared
        mood = self._resolve_mood(prepared)
        duration = max(15000, prepared.duration_ms)
        enabled, reserve, rate, estimate = self._funding(duration)
        if mood is None or (not restore and not enabled):
            return self.silent(prepared, "requested_silence" if mood is None else "music_not_configured")
        if prepared.soundtrack is not None:
            raise AuthError("MOTION_AUDIO_SELECTION_CONFLICT", 409)
        operation = uuid5(row["operation_id"], "music:0")
        result = await self._select_or_generate(
            row,
            token,
            operation,
            mood,
            duration,
            prepared.duration_ms,
            reserve,
            rate,
            estimate,
            restore=restore,
        )
        if result is None:
            return self.silent(prepared, "music_budget_unavailable")
        if result["status"] != "ready":
            return self.silent(prepared, result["status"])
        asset, soundtrack = await self._ready_asset(result, prepared.duration_ms, "assets/photo-music.mp3")
        return replace(
            prepared,
            assets=(*prepared.assets, asset),
            soundtrack=soundtrack,
            context={
                **prepared.context,
                "authorized_soundtrack": soundtrack,
                "photo_motion": {**photo, "music_status": "ready", "music_sha256": asset.sha256},
            },
        )

    async def video_music(
        self, row: dict[str, Any], token: UUID, prepared: PreparedMotionInput, *, restore: bool
    ) -> PreparedMotionInput:
        """Same elevenlabs-music-v1 gates as photo; duck/mix stays in motion-audio-v3."""
        mood = self._resolve_mood(prepared)
        if prepared.soundtrack is not None:
            return replace(
                prepared,
                context={
                    **prepared.context,
                    "video_audio_base": prepared.soundtrack,
                    "video_music_status": "authorized_selection",
                },
            )
        if mood is None:
            return replace(prepared, context={**prepared.context, "video_music_status": "requested_silence"})
        duration = max(15000, prepared.duration_ms)
        enabled, reserve, rate, estimate = self._funding(duration)
        operation = uuid5(row["operation_id"], "video-music-library:0")
        key = f"{POLICY}:{mood}:{duration}"
        if not enabled:
            result, _generate = await self.cache.select(
                row, token, operation, key, 0, restore=restore, existing_only=True
            )
            if result is None or result["status"] != "ready":
                return replace(
                    prepared, context={**prepared.context, "video_music_status": "music_not_configured"}
                )
            return await self._attach_video(prepared, result, "existing_cache_ready")
        result = await self._select_or_generate(
            row,
            token,
            operation,
            mood,
            duration,
            prepared.duration_ms,
            reserve,
            rate,
            estimate,
            restore=restore,
        )
        if result is None or result["status"] != "ready":
            status = "music_budget_unavailable" if result is None else result["status"]
            return replace(prepared, context={**prepared.context, "video_music_status": status})
        return await self._attach_video(prepared, result, "ready")

    async def _select_or_generate(
        self,
        row: dict[str, Any],
        token: UUID,
        operation: UUID,
        mood: str,
        duration: int,
        min_duration_ms: int,
        reserve: int,
        rate: int,
        estimate: int,
        *,
        restore: bool,
    ) -> dict[str, Any] | None:
        key = f"{POLICY}:{mood}:{duration}"
        result, generate = await self.cache.select(row, token, operation, key, reserve, restore=restore)
        if not generate:
            return result
        if not await self.effects.capacity(row, token, reserve):
            result = {"status": "music_budget_unavailable"}
            await self.cache.save(row, token, operation, result)
            return result
        payload = {
            "model_id": MODEL,
            "prompt": MOODS[mood],
            "music_length_ms": duration,
            "force_instrumental": True,
        }
        try:
            reservation = await self.effects.reserve_submission(
                row,
                token,
                operation,
                "generate",
                {
                    "purpose": POLICY,
                    "payload": payload,
                    "rate_usd_micros_per_minute": rate,
                    "estimated_usd_micros": estimate,
                },
                reserve,
                "elevenlabs",
                MODEL,
            )
        except (AuthError, VisualCostError) as exc:
            code = getattr(exc, "code", str(exc))
            if code not in _BUDGET_SILENCE:
                raise
            result = {"status": "music_budget_unavailable"}
            await self.cache.save(row, token, operation, result)
            return result
        try:
            provider = self.provider or ElevenLabsMusic(self.effects.requests.settings)
            media = await provider.generate(payload)
            decoded_duration = await inspect_supplemental_audio(media)
            if decoded_duration * 1000 < min_duration_ms:
                raise AuthError("MOTION_MUSIC_TOO_SHORT", 502)
            result = {
                "status": "ready",
                "sha256": media.sha256,
                "mood": mood,
                "duration_ms": round(decoded_duration * 1000),
                "data": base64.b64encode(media.data).decode(),
            }
            await self.effects.received(
                row, token, operation, {k: v for k, v in result.items() if k != "data"}, estimate
            )
            await self.cache.save(row, token, operation, result)
            return result
        finally:
            # Estimate is not an invoice. Unknown cost retains the full hold.
            await self.effects.ledger.finish(
                row["tenant_id"], row["actor_id"], reservation.id, actual_usd_micros=None
            )

    async def _ready_asset(
        self, result: dict[str, Any], duration_ms: int, asset_id: str
    ) -> tuple[RenderAsset, dict[str, Any]]:
        data = base64.b64decode(result["data"], validate=True)
        if not data or hashlib.sha256(data).hexdigest() != result["sha256"]:
            raise AuthError("MOTION_MUSIC_CACHE_CHANGED", 409)
        asset = RenderAsset(asset_id, "audio/mpeg", data, result["sha256"])
        if (
            await inspect_supplemental_audio(FetchedMedia(data, asset.mime_type, asset.sha256)) * 1000
            < duration_ms
        ):
            raise AuthError("MOTION_MUSIC_TOO_SHORT", 409)
        return asset, music_soundtrack(asset.id, duration_ms)

    async def _attach_video(
        self, prepared: PreparedMotionInput, result: dict[str, Any], status: str
    ) -> PreparedMotionInput:
        asset, soundtrack = await self._ready_asset(result, prepared.duration_ms, "assets/video-music.mp3")
        # Original remains in authorized_audio; server compiles it through the EDL after planning.
        return replace(
            prepared,
            assets=(*prepared.assets, asset),
            soundtrack=soundtrack,
            context={
                **prepared.context,
                "authorized_soundtrack": soundtrack,
                "video_audio_base": soundtrack,
                "video_music_status": status,
            },
        )

    @staticmethod
    def silent(prepared: PreparedMotionInput, status: str) -> PreparedMotionInput:
        return replace(
            prepared,
            context={**prepared.context, "photo_motion": {**prepared.context["photo_motion"], "music_status": status}},
        )
