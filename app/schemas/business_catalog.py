"""Owner-confirmed products, services and time-bounded promotions."""

from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

CatalogState = Literal["draft", "active", "archived"]


class Offering(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    kind: Literal["product", "service"]
    state: CatalogState = "draft"
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=120)
    aliases: list[str] = Field(default_factory=list, max_length=20)
    position: int = Field(default=0, ge=0, le=1000000)
    price_minor: int | None = Field(default=None, ge=0, le=1000000000, strict=True)
    currency: Literal["BRL"] = "BRL"
    price_valid_until: date | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=10080, strict=True)
    booking_instructions: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_offering(self) -> Self:
        aliases = [alias.strip() for alias in self.aliases]
        if any(not alias or len(alias) > 120 for alias in aliases):
            raise ValueError("Aliases must contain between 1 and 120 characters")
        if len({alias.casefold() for alias in aliases}) != len(aliases):
            raise ValueError("Aliases must be unique")
        self.aliases = aliases
        if (self.price_minor is None) != (self.price_valid_until is None):
            raise ValueError("Price and price_valid_until must be provided together")
        if self.kind == "product" and (self.duration_minutes is not None or self.booking_instructions is not None):
            raise ValueError("Duration and booking instructions are only available for services")
        return self


class OfferingPromotion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    offering_id: UUID
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    state: CatalogState = "draft"
    price_minor: int | None = Field(default=None, ge=0, le=1000000000, strict=True)
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("Promotion ends_at must be after starts_at")
        return self


class CatalogContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offerings: list[Offering] = Field(default_factory=list)
    promotions: list[OfferingPromotion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        offerings = {item.id: item for item in self.offerings}
        if len(offerings) != len(self.offerings):
            raise ValueError("Offering ids must be unique")
        if len({item.id for item in self.promotions}) != len(self.promotions):
            raise ValueError("Promotion ids must be unique")
        for promotion in self.promotions:
            offering = offerings.get(promotion.offering_id)
            if offering is None:
                raise ValueError("A promotion must refer to an offering in this business catalog")
            if promotion.state == "active" and offering.state != "active":
                raise ValueError("An active promotion requires an active offering")
        return self


class CatalogUpdate(CatalogContent):
    operation_id: UUID
    expected_version: int = Field(ge=0, strict=True)


class CatalogRead(CatalogContent):
    version: int
    updated_at: datetime | None = None


class CatalogHistoryItem(BaseModel):
    version: int
    created_at: datetime
    actor_id: UUID
