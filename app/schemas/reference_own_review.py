"""Explicit review of possible own-business listings, without Google display data."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OwnReviewCandidate(BaseModel):
    place_id: str


class OwnBusinessReviewRead(BaseModel):
    search_id: UUID
    status: Literal["pending", "awaiting_confirmation", "resolved"]
    candidates: list[OwnReviewCandidate] = Field(default_factory=list)
    excluded_place_id: str | None = None


class OwnBusinessReviewConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    place_id: str | None

    @field_validator("place_id")
    @classmethod
    def valid_place(cls, value: str | None) -> str | None:
        if value is not None and (not 1 <= len(value) <= 2048 or value != value.strip()):
            raise ValueError("Invalid place identity")
        if value is not None:
            value.encode("utf-8")
        return value
