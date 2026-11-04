"""An owner correction of an existing suggested business's Instagram profile."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.owner_references import instagram_handle


class ReferenceProfileWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    expected_version: int = Field(ge=0, strict=True)
    result_id: UUID
    candidate_id: UUID
    instagram_handle: str = Field(min_length=1, max_length=200)

    @field_validator("instagram_handle")
    @classmethod
    def normalize_handle(cls, value: str) -> str:
        return instagram_handle(value)


class ReferenceProfileRead(BaseModel):
    place_identity: UUID
    version: int
    instagram_handle: str
    profile_source: Literal["owner"] = "owner"
    updated_at: datetime
