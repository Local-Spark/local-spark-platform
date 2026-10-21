from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.business import BusinessCreate
from app.services.localities import cities_by_code


class OnboardingCreate(BusinessCreate):
    category: str = Field(min_length=1, max_length=60)
    city: str = Field(min_length=1, max_length=100)
    state_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    city_ibge_code: str | None = Field(default=None, pattern=r"^\d{7}$")
    description: str = Field(min_length=1, max_length=1000)
    phone: str = Field(min_length=8, max_length=30, pattern=r"^\+?[\d\s()\-]+$")
    brand_color: str = Field(default="#6557ed", pattern=r"^#[0-9a-fA-F]{6}$")
    accept_terms: Literal[True]
    accept_privacy: Literal[True]
    terms_version: Literal["2026-10"] = "2026-10"

    @model_validator(mode="after")
    def validate_locality(self) -> "OnboardingCreate":
        if self.state_code is None and self.city_ibge_code is None:
            return self  # Compatibility with profiles created before structured localities.
        city = cities_by_code().get(self.city_ibge_code or "")
        if city is None or city.state_code != self.state_code or city.name != self.city:
            raise ValueError("Select a city matching its IBGE code and state")
        return self


class OnboardingResult(BaseModel):
    tenant_id: UUID
    business_id: UUID
    replayed: bool = False


class UserRead(BaseModel):
    id: UUID
    display_name: str
    email: str | None
    email_verified: bool


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    role: str
    business_count: int
    onboarding_completed: bool


class SessionRead(BaseModel):
    user: UserRead
    organizations: list[OrganizationRead]
    is_staff: bool
