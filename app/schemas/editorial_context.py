"""Bounded, owner-confirmed editorial facts and preferences."""

from datetime import date, datetime
from typing import Literal
from unicodedata import normalize
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

StateCode = Literal[
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]


class ConfirmedFact(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    kind: Literal["product", "service", "price", "hours", "offer", "differentiator", "other"]
    statement: str = Field(min_length=3, max_length=240)
    source_detail: str = Field(min_length=3, max_length=120)
    valid_until: date | None = None

    @model_validator(mode="after")
    def require_validity_for_time_sensitive_facts(self):  # type: ignore[no-untyped-def]
        if self.kind in {"price", "hours", "offer"} and self.valid_until is None:
            raise ValueError("Price, hours and offer facts require valid_until")
        return self


class CtaDestination(BaseModel):
    """Commercial destination deliberately provided by the business owner."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: Literal["whatsapp", "phone", "ifood", "order_link", "booking_link", "physical_location", "instagram_direct"]
    value: str = Field(min_length=1, max_length=240)


class ReferenceAddress(BaseModel):
    """A manually supplied locality, not a geocoded or verified point."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    postal_code: str | None = Field(default=None, pattern=r"^\d{5}-?\d{3}$")
    state_code: StateCode | None = None
    city: str | None = Field(default=None, min_length=1, max_length=120)
    neighborhood: str | None = Field(default=None, min_length=1, max_length=120)
    street: str | None = Field(default=None, min_length=1, max_length=120)
    number: str | None = Field(default=None, min_length=1, max_length=30)
    complement: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def require_locality(self) -> "ReferenceAddress":
        if self.postal_code is None and (self.state_code is None or self.city is None):
            raise ValueError("Provide a postal code or both state and city")
        return self


class ReferenceCoordinates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    accuracy_m: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    confirmed: Literal[True]


class ReferenceOrigin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["manual", "device"]
    address: ReferenceAddress | None = None
    coordinates: ReferenceCoordinates | None = None

    @model_validator(mode="after")
    def validate_origin(self) -> "ReferenceOrigin":
        if self.method == "manual" and (self.address is None or self.coordinates is not None):
            raise ValueError("Manual origin requires an address and cannot yet have coordinates")
        if self.method == "device" and (self.coordinates is None or self.address is not None):
            raise ValueError("Device origin requires confirmed coordinates and no manual address")
        return self


class ReferenceSearchPreference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: Literal["local", "national"]
    radius_km: float | None = Field(default=None, ge=1, le=50, allow_inf_nan=False)
    origin: ReferenceOrigin | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ReferenceSearchPreference":
        if self.scope == "local" and (self.radius_km is None or self.origin is None):
            raise ValueError("Local scope requires a radius and origin")
        if self.scope == "national" and (self.radius_km is not None or self.origin is not None):
            raise ValueError("National scope cannot have a radius or origin")
        return self


class EditorialPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    goal: Literal["awareness", "sales", "appointments"] | None = None
    tone: Literal["friendly", "direct", "playful", "professional"] | None = None
    avoided_topics: list[str] = Field(default_factory=list, max_length=10)
    posts_per_week: int | None = Field(default=None, ge=0, le=7)
    cta_destination: CtaDestination | None = None
    reference_search: ReferenceSearchPreference | None = None
    business_terms: list[str] = Field(default_factory=list, max_length=50)
    business_characteristics: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def bound_topics(self):  # type: ignore[no-untyped-def]
        topics = [item.strip() for item in self.avoided_topics]
        if any(not item or len(item) > 80 for item in topics) or len(set(topics)) != len(topics):
            raise ValueError("Avoided topics must be unique and between 1 and 80 characters")
        self.avoided_topics = topics
        terms = [normalize("NFC", term.strip()) for term in self.business_terms]
        if any(not term or len(term) > 100 for term in terms) or len({term.casefold() for term in terms}) != len(terms):
            raise ValueError("Business terms must be distinct and between 1 and 100 characters")
        # Retain field presence so omission remains distinct from an explicit clear.
        object.__setattr__(self, "business_terms", terms)
        if self.business_characteristics == "":
            object.__setattr__(self, "business_characteristics", None)
        return self


class ContextContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[ConfirmedFact] = Field(default_factory=list, max_length=20)
    preferences: EditorialPreferences = Field(default_factory=EditorialPreferences)

    @model_validator(mode="after")
    def unique_fact_ids(self):  # type: ignore[no-untyped-def]
        if len({fact.id for fact in self.facts}) != len(self.facts):
            raise ValueError("Fact ids must be unique")
        return self


class ContextUpdate(ContextContent):
    expected_version: int = Field(ge=0)
    operation_id: UUID


class ContextRestore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=0)
    target_version: int = Field(gt=0)
    operation_id: UUID


class PendingContextChange(BaseModel):
    operation_id: UUID
    status: Literal["pending", "failed"] = "pending"
    error_code: str | None = None


class ContextRead(ContextContent):
    version: int
    updated_at: datetime | None = None
    hypotheses: list[str] = Field(default_factory=list)
    pending_change: PendingContextChange | None = None


class ContextHistoryItem(BaseModel):
    version: int
    created_at: datetime
    actor_id: UUID
