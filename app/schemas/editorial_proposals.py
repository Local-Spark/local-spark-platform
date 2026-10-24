"""Owner-visible proposals; hypotheses are never promoted to confirmed facts."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProposalDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=4, max_length=120)
    format: Literal["photo", "carousel", "short_video", "story"]
    angle: str = Field(min_length=8, max_length=300)
    fact_ids: list[UUID] = Field(max_length=10)
    hypotheses: list[Annotated[str, Field(min_length=4, max_length=160)]] = Field(max_length=5)
    questions: list[Annotated[str, Field(min_length=4, max_length=160)]] = Field(max_length=5)
    scene_plan: list[Literal["material", "fact", "cta"]] = Field(default_factory=list, max_length=3)
    script: list["ScriptScene"] = Field(default_factory=list, max_length=3)


class ScriptScene(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["material", "fact", "cta"]
    visual: Literal["source_material", "brand_card"]
    on_screen_text: str = Field(min_length=3, max_length=240)
    voiceover: str = Field(min_length=3, max_length=240)
    fact_ids: list[UUID] = Field(max_length=1)
    source_asset_id: UUID | None = None


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
    review_state: Literal["accepted", "changes_requested"] | None = None
    review_note: str | None = None


class ScriptReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    operation_id: UUID
    decision: Literal["accepted", "changes_requested"]
    note: str | None = Field(default=None, max_length=600)

    @model_validator(mode="after")
    def require_change_note(self):  # type: ignore[no-untyped-def]
        if self.decision == "changes_requested" and not self.note:
            raise ValueError("A change request requires a note")
        return self


class EditorialAIConsent(BaseModel):
    accepted: bool


class EditorialAIStatus(EditorialAIConsent):
    provider_enabled: bool
