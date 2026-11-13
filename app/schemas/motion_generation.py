"""Compact construction response; full direction is retained by the server."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.schemas.motion_audiovisual import MotionAudiovisualDesign
from app.schemas.motion_plan import Description, Identifier, Moment, MotionCurve, MotionPlan
from app.schemas.motion_production import MotionAudio, MotionIllustration, MotionModel
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.schemas.motion_staging import MotionStaging


class ProvidedDirectionOutput(MotionModel):
    """Wire-only shape; persisted/reviewed compositions still include the full direction."""

    html: str = Field(min_length=1, max_length=2 * 1024 * 1024, repr=False)
    scene_init: str = Field(min_length=1, max_length=1024 * 1024, repr=False)
    concept: str = Field(min_length=1, max_length=4000)
    source_usage: str = Field(min_length=1, max_length=4000)
    audio: MotionAudio
    motion_plan: MotionPlan
    illustrations: tuple[MotionIllustration, ...] = Field(max_length=2)


class CompactMotionBeat(MotionModel):
    """Wire aliases avoid repeating long field names in every movement."""

    p: Literal["enter", "hold", "transform", "exit"]
    s: Moment
    e: Moment
    a: Description
    z: Description
    path: Description
    c: Literal["linear", "ease_in", "ease_out", "ease_in_out"] | MotionCurve
    cue: Identifier | None


class CompactMotionElement(MotionModel):
    id: Identifier
    role: Literal["text", "graphic", "image", "video"]
    asset_id: str | None = Field(pattern=r"^assets/[A-Za-z0-9_.-]{1,80}$")
    purpose: Description
    related_element_ids: tuple[Identifier, ...] = Field(max_length=16)
    coordination: Description
    beats: tuple[CompactMotionBeat, ...] = Field(min_length=1, max_length=12)


class CompactMotionScene(MotionModel):
    id: Identifier
    start_ms: Moment
    end_ms: Moment
    message: Description
    keyframe_ms: Moment | None
    transition_to_next: Description
    elements: tuple[CompactMotionElement, ...] = Field(min_length=1, max_length=16)


class CompactMotionPlan(MotionModel):
    version: Literal["motion-plan-v1"]
    identity_source: Literal["business_kit"]
    duration_ms: int = Field(strict=True, gt=0, le=60000)
    style_id: str | None = Field(min_length=1, max_length=100)
    scenes: tuple[CompactMotionScene, ...] = Field(min_length=1, max_length=12)


class CompactProvidedDirectionOutput(MotionModel):
    """V2 only on the wire; normal plan validators run after lossless expansion."""

    html: str = Field(min_length=1, max_length=2 * 1024 * 1024, repr=False)
    scene_init: str = Field(min_length=1, max_length=1024 * 1024, repr=False)
    concept: str = Field(min_length=1, max_length=4000)
    source_usage: str = Field(min_length=1, max_length=4000)
    audio: MotionAudio
    motion_plan: CompactMotionPlan
    illustrations: tuple[MotionIllustration, ...] = Field(max_length=2)


class MotionPlanningOutput(MotionModel):
    """First completion contains planning only; direction remains server-owned."""

    concept: str = Field(min_length=1, max_length=4000)
    source_usage: str = Field(min_length=1, max_length=4000)
    audio: MotionAudio
    illustrations: tuple[MotionIllustration, ...] = Field(max_length=2)
    motion_plan: CompactMotionPlan


class MotionAudiovisualPlanningOutput(MotionPlanningOutput):
    """Direction is proposed once; approval then freezes the entire planning artifact."""

    scene_direction: MotionSceneDirection
    audiovisual: MotionAudiovisualDesign


class MotionStagedPlanningOutput(MotionAudiovisualPlanningOutput):
    staging: MotionStaging


class MotionImplementationOutput(MotionModel):
    """Second completion cannot rewrite the validated plan, direction or audio."""

    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    html: str = Field(min_length=1, max_length=2 * 1024 * 1024, repr=False)
    scene_init: str = Field(min_length=1, max_length=1024 * 1024, repr=False)


class MotionImplementationOutputV4(MotionModel):
    """Asset-aware implementation can stop and request a separate plan revision."""

    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["implemented", "requires_plan_revision"]
    html: str | None = Field(min_length=1, max_length=2 * 1024 * 1024, repr=False)
    scene_init: str | None = Field(min_length=1, max_length=1024 * 1024, repr=False)
    revision_reason: str | None = Field(min_length=1, max_length=1000, repr=False)

    @model_validator(mode="after")
    def coherent_outcome(self) -> Self:
        if self.status == "implemented":
            if self.html is None or self.scene_init is None or self.revision_reason is not None:
                raise ValueError("Implemented requires code without a revision request")
        elif self.html is not None or self.scene_init is not None or self.revision_reason is None:
            raise ValueError("Revision requires a reason without executable code")
        return self
