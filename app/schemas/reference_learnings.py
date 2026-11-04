"""Owner projection of persisted derived patterns and their actual analysis state."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.reference_learning_projection import DerivedPattern


class ReferenceLearningRead(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: UUID
    association_version: int | None = Field(ge=1)
    source: Literal["owner", "suggested"]
    instagram_handle: str | None = Field(max_length=30, repr=False)
    profile_name: str | None = Field(default=None, max_length=200, repr=False)
    analysis_status: Literal["not_requested", "pending", "unavailable", "completed", "partial"]
    update_status: Literal["scheduled", "running", "waiting"] | None
    last_analyzed_at: datetime | None
    next_analysis_at: datetime | None
    patterns: tuple[DerivedPattern, ...] = Field(max_length=10, repr=False)

    @model_validator(mode="after")
    def patterns_match_analysis(self) -> Self:
        analyzed = self.analysis_status in {"completed", "partial"}
        if bool(self.patterns) != analyzed:
            raise ValueError("inconsistent persisted analysis")
        if analyzed and (self.association_version is None or self.last_analyzed_at is None):
            raise ValueError("missing persisted analysis identity")
        return self


class ReferenceLearningsRead(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    references: tuple[ReferenceLearningRead, ...]

    @model_validator(mode="after")
    def references_are_unique(self) -> Self:
        if len({entry.reference_id for entry in self.references}) != len(self.references):
            raise ValueError("duplicate reference")
        return self
