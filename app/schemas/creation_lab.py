"""Administrative rehearsal input; creating a draft never authorizes provider IO."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LabDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    tenant_id: UUID
    business_id: UUID
    format: Literal["photo", "story", "reel"]
    mode: Literal["automatic", "accompanied"]
    instruction: str = Field(min_length=1, max_length=4000, repr=False, pattern=r"\S")
    budget_usd_micros: int = Field(strict=True, gt=0, le=9_223_372_036_854_775_807)


class LabCollectionSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    photo_ids: list[UUID] = Field(max_length=4)

    @field_validator("photo_ids")
    @classmethod
    def unique_photos(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Duplicate collection photos")
        return sorted(value)


class LabFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    version_id: UUID
    note: str = Field(min_length=1, max_length=4000, pattern=r"\S", repr=False)
    timestamp_ms: int | None = Field(default=None, strict=True, ge=0, le=60000)


class LabStart(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    source_attachment_id: UUID | None = None


class LabContinuation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    note: str = Field(min_length=1, max_length=2000, pattern=r"\S", repr=False)
    stage: Literal["catalog", "editorial", "plan", "render", "storyboard"] | None = None
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
