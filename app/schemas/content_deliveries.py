"""Owner-facing candidate and exact-version publication decisions."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator


class VisualReviewConfirmation(BaseModel):
    """Human confirmation for a particular generated file, not an automated verdict."""

    model_config = ConfigDict(extra="forbid")

    preview_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    price_and_terms: StrictBool
    spelling: StrictBool
    identity: StrictBool
    fidelity: StrictBool
    legibility: StrictBool

    @model_validator(mode="after")
    def all_reviewed(self) -> "VisualReviewConfirmation":
        if not all((self.price_and_terms, self.spelling, self.identity, self.fidelity, self.legibility)):
            raise ValueError("VISUAL_REVIEW_INCOMPLETE")
        return self


class ContentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    decision: Literal["approve", "request_changes"]
    note: str | None = Field(default=None, max_length=500)
    scheduled_at: AwareDatetime | None = None
    visual_review: VisualReviewConfirmation | None = None


class ContentDeliveryRead(BaseModel):
    id: UUID
    preview_id: UUID | None
    kind: Literal["candidate", "clarification"]
    message_body: str
    caption: str | None = None
    delivery_state: Literal["delivered", "failed", "uncertain"]
    decision_state: Literal["pending", "approved", "changes_requested", "expired"] | None
    review_note: str | None
    publish_state: Literal["pending", "dispatching", "published", "unknown", "failed"] | None
    publication_id: str | None
    scheduled_at: datetime | None
    created_at: datetime
    expires_at: datetime
