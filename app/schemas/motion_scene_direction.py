"""Visual meaning and composition, linked to the existing timed motion plan."""

from typing import Annotated, Literal

from pydantic import Field

from app.schemas.motion_plan import Identifier, PlanModel

DirectionText = Annotated[str, Field(min_length=1, max_length=400, pattern=r"\S")]


class ElementDirection(PlanModel):
    element_id: Identifier
    depicts: DirectionText
    appearance: DirectionText
    # Generated illustrations are explicitly declared and acquired by the service.
    construction: Literal["code", "authorized_asset", "component", "generated_asset"]
    component_id: Identifier | None = Field(default=None, exclude_if=lambda value: value is None)


class SceneDirection(PlanModel):
    scene_id: Identifier
    brief_basis: DirectionText
    visual_representation: DirectionText
    composition: DirectionText
    narrative_action: DirectionText
    attention_order: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    elements: tuple[ElementDirection, ...] = Field(min_length=1, max_length=16)


class MotionSceneDirection(PlanModel):
    version: Literal["scene-direction-v1"]
    scenes: tuple[SceneDirection, ...] = Field(min_length=1, max_length=12)
