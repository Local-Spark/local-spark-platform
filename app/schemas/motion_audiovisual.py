"""Reviewable planning choices; declared intent never certifies unseen/unheard output."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.motion_plan import Identifier


class DesignModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class MotionFunctionCoverage(DesignModel):
    function_id: Identifier
    target_element_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    disposition: Literal["preserve_function", "replace_representation", "satisfy_requirement"]
    justification: str = Field(min_length=1, max_length=1000)
    verification: str = Field(min_length=1, max_length=1000)
    limitations: str = Field(min_length=1, max_length=1000)


class MotionPlannedSound(DesignModel):
    candidate_id: Identifier
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scene_id: Identifier
    element_id: Identifier
    action_start_ms: int = Field(strict=True, ge=0, lt=60000)
    action_end_ms: int = Field(strict=True, gt=0, le=60000)
    purpose: str = Field(min_length=1, max_length=1000)
    # These are proposals; source duplication and intelligibility require listening.
    listening_checks: tuple[Literal["suitability", "source_duplication", "voice_intelligibility"], ...] = Field(
        min_length=3, max_length=3
    )
    trim_start_ms: int = Field(strict=True, ge=0, lt=60000)
    trim_end_ms: int = Field(strict=True, gt=0, le=60000)
    offset_ms: int = Field(strict=True, ge=0, lt=60000)
    volume: float = Field(strict=True, gt=0, le=1)
    fade_in_ms: int = Field(strict=True, ge=0, le=60000)
    fade_out_ms: int = Field(strict=True, ge=0, le=60000)

    @model_validator(mode="after")
    def bounded(self) -> Self:
        duration = self.trim_end_ms - self.trim_start_ms
        if (
            duration <= 0
            or self.action_end_ms <= self.action_start_ms
            or self.offset_ms + duration > 60000
            or self.fade_in_ms + self.fade_out_ms > duration
            or set(self.listening_checks) != {"suitability", "source_duplication", "voice_intelligibility"}
            or not float(self.volume * 1000000).is_integer()
        ):
            raise ValueError("Sound needs a bounded action, mix interval and all listening checks")
        return self


class MotionSoundOmission(DesignModel):
    candidate_id: Identifier
    reason: str = Field(min_length=1, max_length=1000)


class MotionAudiovisualDesign(DesignModel):
    interpretation: str = Field(min_length=1, max_length=2000)
    functions: tuple[MotionFunctionCoverage, ...] = Field(max_length=24)
    sounds: tuple[MotionPlannedSound, ...] = Field(max_length=8)
    omitted_sounds: tuple[MotionSoundOmission, ...] = Field(max_length=8)
    limitations: tuple[str, ...] = Field(min_length=1, max_length=12)
