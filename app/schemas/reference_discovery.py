"""A local-only simulation; never presented as a real search result."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


class DiscoveryRead(BaseModel):
    id: UUID
    operation_id: UUID
    state: Literal["pending", "simulated", "stale"]
    mode: Literal["fake"] = "fake"
    created_at: datetime
    completed_at: datetime | None


class DiscoveryFixtureRead(BaseModel):
    id: UUID
    discovery_id: UUID
    fixture_number: int
    canonical_id: UUID
    selected: bool = False
    similarity: Literal["scripted_suitable"] = "scripted_suitable"
    reputation_score: Decimal
    reputation_status: Literal["scored"]
    reputation_formula_version: str
    fixture_version: str
    mode: Literal["fake"] = "fake"


class FixtureSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    candidate_ids: list[UUID] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def unique_candidates(self) -> "FixtureSelectionRequest":
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("Select distinct fixtures")
        return self


class FixtureSelectionRead(BaseModel):
    operation_id: UUID
    candidate_ids: list[UUID]
    locked_until: datetime
    mode: Literal["fake"] = "fake"


class FixtureSelectionState(BaseModel):
    candidate_ids: list[UUID]
    locked_until: datetime | None
    mode: Literal["fake"] = "fake"
