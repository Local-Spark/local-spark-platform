"""Owner-facing candidate and exact-version publication decisions."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ContentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    decision: Literal["approve", "request_changes"]
    note: str | None = Field(default=None, max_length=500)
    scheduled_at: AwareDatetime | None = None


class ContentDeliveryRead(BaseModel):
    id: UUID
    preview_id: UUID | None
    kind: Literal["candidate", "clarification"]
    message_body: str
    delivery_state: Literal["delivered", "failed", "uncertain"]
    decision_state: Literal["pending", "approved", "changes_requested", "expired"] | None
    review_note: str | None
    publish_state: Literal["pending", "dispatching", "published", "unknown", "failed"] | None
    publication_id: str | None
    scheduled_at: datetime | None
    created_at: datetime
    expires_at: datetime
