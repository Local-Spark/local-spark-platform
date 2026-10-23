"""Owner-visible proposals; hypotheses are never promoted to confirmed facts."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposalDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=4, max_length=120)
    format: Literal["photo", "carousel", "short_video", "story"]
    angle: str = Field(min_length=8, max_length=300)
    fact_ids: list[UUID] = Field(max_length=10)
    hypotheses: list[Annotated[str, Field(min_length=4, max_length=160)]] = Field(max_length=5)
    questions: list[Annotated[str, Field(min_length=4, max_length=160)]] = Field(max_length=5)


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    source_asset_id: UUID | None = None


class ProposalRead(BaseModel):
    id: UUID
    state: Literal["pending", "dispatching", "submitted", "completed", "rejected", "budget_exceeded", "uncertain"]
    context_version: int
    source_asset_id: UUID | None
    document: ProposalDraft | None
    error_code: str | None
    created_at: datetime
    expires_at: datetime


class EditorialAIConsent(BaseModel):
    accepted: bool


class EditorialAIStatus(EditorialAIConsent):
    provider_enabled: bool
