"""Public board metadata contains no source code, storage keys or execution token."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.motion_production import MotionModel


class StoryboardDecision(MotionModel):
    operation_id: UUID
    version_id: UUID
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approve", "reject"]
    feedback: str | None = Field(default=None, max_length=2000, repr=False)


class StoryboardFrame(MotionModel):
    scene_id: str
    message: str
    at_ms: int
    sha256: str


class StoryboardRead(MotionModel):
    version_id: UUID
    content_sha256: str
    state: Literal["awaiting_approval", "approved", "rejected", "rendering"]
    frames: tuple[StoryboardFrame, ...]
