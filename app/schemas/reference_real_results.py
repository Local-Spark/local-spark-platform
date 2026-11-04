"""Allowlisted data for a future private reference-discovery result.

This internal-only contract does not admit a search, prove a provider effect,
call a provider, or persist anything. It must not be exposed as a client route
or written to a database without verifying the durable authorized effects and
their provenance for the same tenant, business and search.
In particular, raw Places ratings, counts, names, coordinates, websites and
responses are not valid fields. Profile handles are unverified options; their
presence does not establish ownership of a business account. The literal source
label is not evidence that an Apify effect returned the profile.

No display name is accepted yet. A future name must come from independently
proven Instagram profile data, bound to the relevant effect and profile;
Google Maps data retransmitted by an Apify actor does not satisfy this rule.
"""

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.owner_references import instagram_handle


class ApifyInstagramOption(BaseModel):
    """A proposed Instagram profile, not an association confirmed by the owner."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    handle: str = Field(min_length=1, max_length=200)
    source: Literal["apify"] = "apify"
    association: Literal["unverified"] = "unverified"

    @field_validator("handle")
    @classmethod
    def normalize_handle(cls, value: str) -> str:
        return instagram_handle(value)


class ReferenceRealCandidate(BaseModel):
    """Sanitized observation of one candidate in one search result."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    place_id: str = Field(min_length=1, max_length=2048)
    reputation_score: Annotated[Decimal, Field(ge=0, le=10)]
    reputation_formula_version: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    jev_recommendation_rank: int | None = Field(default=None, ge=1, le=3, strict=True)
    instagram_options: tuple[ApifyInstagramOption, ...] = Field(default_factory=tuple, max_length=100)

    @field_validator("place_id")
    @classmethod
    def valid_place_id(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Place ID must be nonempty and have no outer whitespace")
        return value

    @model_validator(mode="after")
    def unique_instagram_options(self) -> "ReferenceRealCandidate":
        handles = [option.handle for option in self.instagram_options]
        if len(set(handles)) != len(handles):
            raise ValueError("Instagram profile options must be distinct")
        return self


class ReferenceRealResultInput(BaseModel):
    """Ordered, sanitized batch tied to a future durable search and operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    search_id: UUID
    operation_id: UUID
    candidates: tuple[ReferenceRealCandidate, ...] = Field(default_factory=tuple, max_length=10)

    @model_validator(mode="after")
    def unique_places_and_recommendations(self) -> "ReferenceRealResultInput":
        place_ids = [candidate.place_id for candidate in self.candidates]
        if len(set(place_ids)) != len(place_ids):
            raise ValueError("Candidates must have distinct Place IDs")
        ranks = [item.jev_recommendation_rank for item in self.candidates if item.jev_recommendation_rank is not None]
        if len(set(ranks)) != len(ranks):
            raise ValueError("Jev recommendation ranks must be distinct")
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise ValueError("Jev recommendation ranks must form a sequence starting at one")
        return self
