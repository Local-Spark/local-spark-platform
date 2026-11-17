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

    async def prepare(
        self, row: dict[str, Any], token: UUID, prepared: PreparedMotionInput, *, restore: bool = False
    ) -> PreparedMotionInput:
        photo = prepared.context.get("photo_motion", {})
        if photo.get("music_policy") != POLICY:
            return prepared
        mood = music_mood(prepared.context["request"]["instruction"])
        if mood == "neutral":
            facts = " ".join(fact["statement"] for fact in prepared.context.get("confirmed_facts", []))
            mood = music_mood(facts)
        settings = self.effects.requests.settings
        reserve = settings.elevenlabs_music_reservation_usd_micros
        duration = max(15000, prepared.duration_ms)
        rate = settings.elevenlabs_music_usd_micros_per_minute
        estimate = (duration * rate + 59999) // 60000
        enabled = bool(
            settings.elevenlabs_music_execution_enabled
            and settings.elevenlabs_api_key
            and settings.elevenlabs_music_commercial_rights_confirmed
            and reserve > 0
            and rate > 0
            and estimate <= reserve
            and settings.elevenlabs_music_monthly_budget_usd_micros >= reserve
        )
        if mood is None or (not restore and not enabled):
            return self.silent(prepared, "requested_silence" if mood is None else "music_not_configured")
        if prepared.soundtrack is not None:
            raise AuthError("MOTION_AUDIO_SELECTION_CONFLICT", 409)
        operation = uuid5(row["operation_id"], "music:0")
        key = f"{POLICY}:{mood}:{duration}"
        result, generate = await self.cache.select(row, token, operation, key, reserve, restore=restore)
        if generate:
            if not await self.effects.capacity(row, token, reserve):
                # No dispatch: retain conservative hold and record stable silent decision.
                result = {"status": "music_budget_unavailable"}
                await self.cache.save(row, token, operation, result)
            else:
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
                    if code not in {
                        "MOTION_REQUEST_BUDGET_EXCEEDED",
                        "VISUAL_BUDGET_DISABLED",
                        "VISUAL_BUDGET_EXCEEDED",
                        "CREATION_LAB_RUN_BUDGET_EXCEEDED",
                        "CREATION_LAB_ADMIN_BUDGET_EXCEEDED",
                        "CREATION_LAB_EXECUTION_DISABLED",
                    }:
                        raise
                    result = {"status": "music_budget_unavailable"}
                    await self.cache.save(row, token, operation, result)
                    return self.silent(prepared, result["status"])
                try:
                    provider = self.provider or ElevenLabsMusic(settings)
                    media = await provider.generate(payload)
                    decoded_duration = await inspect_supplemental_audio(media)
                    if decoded_duration * 1000 < prepared.duration_ms:
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
                finally:
                    # Estimate is not an invoice. Unknown cost retains the full hold.
                    await self.effects.ledger.finish(
                        row["tenant_id"], row["actor_id"], reservation.id, actual_usd_micros=None
                    )
        if result is None:
            return self.silent(prepared, "music_budget_unavailable")
        if result["status"] != "ready":
            return self.silent(prepared, result["status"])
        data = base64.b64decode(result["data"], validate=True)
        if not data or hashlib.sha256(data).hexdigest() != result["sha256"]:
            raise AuthError("MOTION_MUSIC_CACHE_CHANGED", 409)
        asset = RenderAsset("assets/photo-music.mp3", "audio/mpeg", data, result["sha256"])
        if (
            await inspect_supplemental_audio(FetchedMedia(data, asset.mime_type, asset.sha256)) * 1000
            < prepared.duration_ms
        ):
            raise AuthError("MOTION_MUSIC_TOO_SHORT", 409)
        soundtrack = music_soundtrack(asset.id, prepared.duration_ms)
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

    @staticmethod
    def silent(prepared: PreparedMotionInput, status: str) -> PreparedMotionInput:
        return replace(
            prepared,
            context={**prepared.context, "photo_motion": {**prepared.context["photo_motion"], "music_status": status}},
        )
