"""Owner-visible status of private image and video previews."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, model_validator


class VisualAIConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: StrictBool


class VisualAIStatus(VisualAIConsent):
    provider_enabled: bool
    state: Literal["active", "revocation_pending", "revoked"]


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    proposal_id: UUID
    parent_preview_id: UUID | None = None
    emphasis: Literal["balanced", "photo", "text"] = "balanced"
    generation_mode: Literal["local", "visual_fake", "visual_ai"] = "local"

    @model_validator(mode="after")
    def adjustment_requires_parent(self) -> "PreviewRequest":
        if self.generation_mode in {"visual_fake", "visual_ai"} and self.parent_preview_id is not None:
            raise ValueError("VISUAL_ADJUSTMENT_UNAVAILABLE")
        if self.parent_preview_id is None and self.emphasis != "balanced":
            raise ValueError("PREVIEW_PARENT_REQUIRED")
        return self


class PreviewRead(BaseModel):
    id: UUID
    proposal_id: UUID
    candidate: bool
    parent_preview_id: UUID | None
    emphasis: Literal["balanced", "photo", "text"]
    revision: int
    state: Literal["pending", "rendering", "completed", "failed"]
    generation_mode: Literal["local", "visual_fake", "visual_ai"] = "local"
    created_before_change: bool = False
    error_code: str | None
    context_version: int
    source_asset_id: UUID | None
    fact_ids: list[UUID]
    template_version: int
    mime_type: Literal["image/jpeg", "video/mp4"]
    width: int | None
    height: int | None
    duration_ms: int | None
    created_at: datetime
    expires_at: datetime
