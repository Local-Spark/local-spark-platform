"""Owner result/selection contracts; provider projections are never client input."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OccurrenceChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result_id: UUID
    candidate_id: UUID


class ReferenceRetentionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    place_identity: UUID
    action: Literal["keep", "remove"]


class ReferenceSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    cycle_id: UUID
    selection: tuple[OccurrenceChoice, ...] = Field(min_length=1, max_length=3)
    first_result_id: UUID | None = None
    decisions: tuple[ReferenceRetentionDecision, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def distinct_choices(self) -> "ReferenceSelectionRequest":
        if len({(item.result_id, item.candidate_id) for item in self.selection}) != len(self.selection):
            raise ValueError("Repeated reference occurrence")
        if len({item.place_identity for item in self.decisions}) != len(self.decisions):
            raise ValueError("Repeated retention decision")
        if self.decisions and self.first_result_id is None:
            raise ValueError("Retention decisions require their first published result")
        return self


class ReferenceSelectionRead(BaseModel):
    operation_id: UUID
    cycle_id: UUID
    locked_until: datetime
    selection: tuple[OccurrenceChoice, ...]


class ReferenceOccurrenceRead(BaseModel):
    cycle_id: UUID
    result_id: UUID
    candidate_id: UUID
    place_identity: UUID
    place_id: str
    position: int
    reputation_score: Decimal
    reputation_formula_version: str
    jev_recommendation_rank: int | None
    instagram_handle: str | None
    profile_source: Literal["apify", "owner"] | None
    profile_version: int = 0


class ReferenceSearchRead(BaseModel):
    search_id: UUID
    radius_km: int
    state: str
    published: bool
    recommendation_status: Literal["completed", "unavailable"]
    execution_status: str = "pending"
    family_root_id: UUID | None = None
    family_current_search_id: UUID | None = None
    family_status: str = "pending"
    can_retry_family: bool = False
    candidates: tuple[ReferenceOccurrenceRead, ...]


class ReferenceCycleReviewRead(BaseModel):
    cycle_id: UUID
    first_result_id: UUID
    required_place_ids: tuple[UUID, ...]


class ReferenceResultsRead(BaseModel):
    discovery_available: bool = False
    cycle_id: UUID | None
    locked_until: datetime | None
    searches: tuple[ReferenceSearchRead, ...]
    selected: tuple[ReferenceOccurrenceRead, ...]
    cycle_review: ReferenceCycleReviewRead | None
