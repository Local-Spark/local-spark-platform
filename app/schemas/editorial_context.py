"""Bounded, owner-confirmed editorial facts and preferences."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class EditorialPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    goal: Literal["awareness", "sales", "appointments"] | None = None
    tone: Literal["friendly", "direct", "playful", "professional"] | None = None
    avoided_topics: list[str] = Field(default_factory=list, max_length=10)
    posts_per_week: int | None = Field(default=None, ge=0, le=7)
    cta_destination: CtaDestination | None = None

    @model_validator(mode="after")
    def bound_topics(self):  # type: ignore[no-untyped-def]
        topics = [item.strip() for item in self.avoided_topics]
        if any(not item or len(item) > 80 for item in topics) or len(set(topics)) != len(topics):
            raise ValueError("Avoided topics must be unique and between 1 and 80 characters")
        self.avoided_topics = topics
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
