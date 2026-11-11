"""A durable local transcription before motion generation; reuse through correction/storyboard."""

import math
from dataclasses import replace
from typing import Any, Protocol
from uuid import UUID, uuid5

from pydantic import ValidationError

from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_speech import MotionSpeechTiming
from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects
from app.services.motion_speech import speech_context, validate_speech_source
from app.services.motion_speech_policy import speech_policy


class SpeechRecognizer(Protocol):
    async def transcribe(self, source: bytes, sha256: str, policy: dict[str, Any]) -> dict[str, Any]: ...


def recognized_timing(result: dict[str, Any], source: dict[str, Any]) -> MotionSpeechTiming:
    try:
        words = result["words"]
        if not isinstance(words, list) or len(words) > 300:
            raise ValueError
        cues = []
        for index, word in enumerate(words):
            start, end = word["start"], word["end"]
            if any(type(t) not in (int, float) or not math.isfinite(t) for t in (start, end)):
                raise ValueError
            cues.append(
                {
                    "id": f"word-{index + 1}",
                    "text": word["text"],
                    "start_ms": round(start * 1000),
                    "end_ms": round(end * 1000),
                    "confidence": word["confidence"],
                }
            )
        timing = MotionSpeechTiming.model_validate(
            {
                "version": "motion-speech-v1",
                "source_sha256": source["sha256"],
                "provenance": "local_asr_unreviewed",
                "alignment": "word",
                "cues": cues,
                "focus_cue_ids": [],
            }
        )
        validate_speech_source(timing, source)
        if timing.cues and not any(cue.confidence is not None and cue.confidence >= 0.6 for cue in timing.cues):
            raise AuthError("MOTION_SPEECH_REVIEW_REQUIRED", 409)
        return timing
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise AuthError("MOTION_SPEECH_RESULT_INVALID", 409) from exc


class MotionSpeechRecognition:
    def __init__(self, effects: MotionEffects, recognizer: SpeechRecognizer | None):
        self.effects, self.recognizer = effects, recognizer

    async def prepare(self, row: dict[str, Any], token: UUID, prepared: PreparedMotionInput) -> PreparedMotionInput:
        policy = prepared.context.get("speech_recognition")
        if policy is None or prepared.context.get("request", {}).get("speech_timing") is not None:
            return prepared
        if self.recognizer is None or policy != speech_policy(self.effects.requests.settings):
            raise AuthError("MOTION_SPEECH_POLICY_CHANGED", 409)
        source = prepared.context["source"]
        operation = uuid5(row["operation_id"], "speech:0")
        await self.effects.claim(
            row,
            token,
            operation,
            "generate",
            {
                "purpose": "local_speech_recognition",
                "policy": policy,
                "source_sha256": source["sha256"],
            },
        )
        if not source["has_audio"]:
            await self.effects.received(row, token, operation, {"status": "no_audio_track"}, 0)
            return prepared
        asset = next(item for item in prepared.assets if item.id == source["asset_id"])
        result = await self.recognizer.transcribe(asset.data, source["sha256"], policy)
        # Persist bounded raw result before semantic validation; no retry or inferred replacement timing.
        await self.effects.received(row, token, operation, result, 0)
        timing = recognized_timing(result, source)
        context = {**prepared.context, "speech_result": timing.model_dump(mode="json")}
        context["transcript"] = speech_context(context, source)
        context["limitations"] = [
            "Local ASR word timing is unreviewed and estimated; original audio remains unchanged.",
            "Source sampling does not show continuous movement or prove audiovisual synchrony.",
        ]
        return replace(prepared, context=context)
