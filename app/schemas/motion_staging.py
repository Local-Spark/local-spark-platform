"""Executable links from content direction to materials and review intervals."""

from typing import Literal

from pydantic import Field

from app.schemas.motion_plan import Description, Identifier, Moment, PlanModel


class StagedTransition(PlanModel):
    next_scene_id: Identifier
    start_ms: Moment
    end_ms: Moment
    element_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    origin: Description
    crossing: Description
    destination: Description


class StagedMoment(PlanModel):
    scene_id: Identifier
    contribution: Description
    protagonist_id: Identifier
    media_relation: Literal["recording_dominant", "photo_dominant", "integrated", "graphic"]
    material_element_ids: tuple[Identifier, ...] = Field(max_length=16)
    development: Description
    sustained_value: Description
    inspect_start_ms: Moment
    inspect_end_ms: Moment
    transition: StagedTransition | None


class PhotoIdentityReview(PlanModel):
    asset_id: str = Field(pattern=r"^assets/photo-[A-Za-z0-9_.-]+$")
    verdict: Literal["clean", "third_party", "uncertain"]
    evidence: Description


class MotionStaging(PlanModel):
    photo_identity_reviews: tuple[PhotoIdentityReview, ...] | None = Field(
        default=None, exclude_if=lambda value: value is None, max_length=192
    )
    version: Literal["motion-staging-v1", "motion-staging-photo-v1", "motion-staging-photo-v2"]
    moments: tuple[StagedMoment, ...] = Field(min_length=1, max_length=12)
    unavailable_materials: tuple[Description, ...] = Field(max_length=8)
