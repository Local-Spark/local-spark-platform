"""Administrative rehearsal input; creating a draft never authorizes provider IO."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LabDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    tenant_id: UUID
    business_id: UUID
    format: Literal["auto"] = "auto"
    mode: Literal["automatic"] = "automatic"
    instruction: str = Field(default="", max_length=4000, repr=False)
    budget_usd_micros: int = Field(strict=True, gt=0, le=9_223_372_036_854_775_807)


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
