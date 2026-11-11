"""Owner-supplied speech timing; a reviewed assertion, never inferred from a brief."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.schemas.motion_plan import Identifier, Moment, PlanModel


class MotionSpeechCue(PlanModel):
    id: Identifier
    text: str = Field(min_length=1, max_length=400, pattern=r"\S", repr=False)
    confidence: float | None = Field(default=None, ge=0, le=1, exclude_if=lambda v: v is None)
    start_ms: Moment
    end_ms: Moment

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.end_ms <= self.start_ms:
            raise ValueError("Speech cue must have positive duration")
        return self


class MotionSpeechTiming(PlanModel):
    version: Literal["motion-speech-v1"]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provenance: Literal["owner_reviewed", "local_asr_unreviewed"]
    alignment: Literal["segment", "word"]
    # May cover selected passages only; omitted regions are not declared silent.
    cues: tuple[MotionSpeechCue, ...] = Field(max_length=300, repr=False)
    focus_cue_ids: tuple[Identifier, ...] = Field(max_length=12)

    @model_validator(mode="after")
    def ordered_unique_cues(self) -> Self:
        if self.provenance == "owner_reviewed" and (not self.cues or not self.focus_cue_ids):
            raise ValueError("Reviewed speech requires cues and selected focuses")
        seen: set[str] = set()
        end = 0
        for cue in self.cues:
            if cue.id in seen or cue.start_ms < end:
                raise ValueError("Speech cues must be unique, ordered and non-overlapping")
            seen.add(cue.id)
            end = cue.end_ms
        if len(set(self.focus_cue_ids)) != len(self.focus_cue_ids) or not set(self.focus_cue_ids) <= seen:
            raise ValueError("Speech focuses must identify distinct supplied cues")
        return self
