"""Owner-facing location metadata; raw provider addresses never leave the activity."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeocodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    address_version: int = Field(gt=0, strict=True)


class GeocodeConfirmation(GeocodeRequest):
    geocode_id: UUID
    candidate_id: UUID


class LocationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeocodeRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    address_version: int
    geocode_id: UUID | None = None
    status: Literal["unrequested", "pending", "resolved", "confirmation_required", "not_found", "uncertain"]
    coordinates: LocationCandidate | None = None
    candidates: list[LocationCandidate] = Field(default_factory=list)
