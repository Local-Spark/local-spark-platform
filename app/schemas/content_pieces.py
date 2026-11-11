"""Exact-version review of private pieces, independent of publication."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.content_deliveries import VisualReviewConfirmation

PieceFormat = Literal["photo", "story", "reel", "story_video", "carousel_motion"]


class PieceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PieceFromPreview(PieceModel):
    operation_id: UUID
    preview_id: UUID


class PieceArtifactRead(PieceModel):
    id: UUID
    position: int = Field(ge=0, le=19)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mime_type: Literal["image/png", "image/jpeg", "video/mp4"]
    size_bytes: int = Field(gt=0)


class PieceVersionRead(PieceModel):
    id: UUID
    number: int
    parent_id: UUID | None
    artifacts: list[PieceArtifactRead]
    created_at: datetime


class PieceRead(PieceModel):
    id: UUID
    simulated: bool = False
    format: PieceFormat
    state: Literal["ready_for_review", "changes_requested", "approved"]
    current_version_id: UUID
    approved_version_id: UUID | None
    versions: list[PieceVersionRead]
    created_at: datetime


class PieceDecision(PieceModel):
    operation_id: UUID
    version_id: UUID
    decision: Literal["approve", "request_changes"]
    # Position and hash are repeated deliberately: an approval covers the ordered set.
    artifacts: list[PieceArtifactRead] = Field(min_length=1, max_length=20)
    confirmations: list[VisualReviewConfirmation] = Field(default_factory=list, max_length=20)
    note: str | None = Field(default=None, min_length=1, max_length=2000)
    page_positions: list[int] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def coherent(self) -> "PieceDecision":
        if [item.position for item in self.artifacts] != list(range(len(self.artifacts))):
            raise ValueError("PIECE_ARTIFACT_ORDER_INVALID")
        if len({item.id for item in self.artifacts}) != len(self.artifacts):
            raise ValueError("PIECE_ARTIFACT_DUPLICATE")
        if self.decision == "approve":
            if [item.preview_sha256 for item in self.confirmations] != [item.sha256 for item in self.artifacts]:
                raise ValueError("PIECE_REVIEW_INCOMPLETE")
            if self.page_positions:
                raise ValueError("PIECE_APPROVAL_MUST_COVER_ALL_PAGES")
        elif self.note is None or not self.note.strip():
            raise ValueError("PIECE_CHANGE_NOTE_REQUIRED")
        if self.page_positions != sorted(set(self.page_positions)) or any(
            position < 0 or position >= len(self.artifacts) for position in self.page_positions
        ):
            raise ValueError("PIECE_CHANGE_PAGES_INVALID")
        return self


class PieceDecisionRead(PieceModel):
    operation_id: UUID
    piece_id: UUID
    version_id: UUID
    decision: Literal["approve", "request_changes"]
    created_at: datetime
