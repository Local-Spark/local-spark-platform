"""Explicit operator observations about a received piece, distinct from provider critique."""

from typing import Literal

from pydantic import Field

from app.schemas.motion_preparation import PreparationModel


class RevisionFrame(PreparationModel):
    at_ms: int = Field(strict=True, ge=0, lt=60000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class MotionDirectionObservation(PreparationModel):
    version: Literal["motion-direction-observation-v1"] = "motion-direction-observation-v1"
    mp4_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frames: tuple[RevisionFrame, ...] = Field(min_length=2, max_length=8)
    observation: str = Field(min_length=1, max_length=1000)
