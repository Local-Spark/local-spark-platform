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
    generation_mode: Literal["local", "visual_fake", "visual_ai"] = "visual_ai"
    visual_skill_id: Literal["instagram-feed-v1", "instagram-story-v1"] | None = None

    @model_validator(mode="after")
    def adjustment_requires_parent(self) -> "PreviewRequest":
        if self.visual_skill_id is not None and self.generation_mode not in {"visual_ai", "visual_fake"}:
            raise ValueError("VISUAL_SKILL_REQUIRES_AI")
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
    visual_skill_id: Literal["instagram-feed-v1", "instagram-story-v1"] | None = None
    visual_recipe: Literal["legacy_overlay", "full_piece_v1"] = "legacy_overlay"
    created_before_change: bool = False
    sha256: str | None = None
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
