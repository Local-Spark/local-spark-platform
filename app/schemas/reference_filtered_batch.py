"""Private allowlist for a future intermediate filtered batch writer.

This validates shape only. The caller must prove both provider fences, the
persisted Jev parent/source binding and search context in the committing
transaction. Never expose this contract as a client route.
"""

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FilteredBatchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    candidate_id: UUID
    place_id: str = Field(min_length=1, max_length=2048)
    reputation_score: Annotated[Decimal, Field(ge=0, le=10)]
    reputation_formula_version: Literal["penalized-3.4-v1"]

    @field_validator("place_id")
    @classmethod
    def check_place_id(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Place ID is invalid")
        return value


class FilteredBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: tuple[FilteredBatchCandidate, ...] = Field(max_length=20)

    @model_validator(mode="after")
    def distinct_candidate_and_place_ids(self) -> "FilteredBatch":
        ids = [candidate.candidate_id for candidate in self.candidates]
        places = [candidate.place_id for candidate in self.candidates]
        if len(ids) != len(set(ids)) or len(places) != len(set(places)):
            raise ValueError("Candidate IDs and Place IDs must be distinct")
        return self
