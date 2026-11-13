"""Direction of movement, not a replacement renderer or a source of brand identity."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")]
Moment = Annotated[int, Field(strict=True, ge=0, le=60000)]
Description = Annotated[str, Field(min_length=1, max_length=400)]


class PlanModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class MotionCurve(PlanModel):
    kind: Literal["linear", "ease_in", "ease_out", "ease_in_out", "cubic_bezier", "spring"]
    # Cubic: x1,y1,x2,y2. Spring: stiffness,damping,mass. Named curves: empty.
    parameters: tuple[float, ...] = Field(max_length=4)

    @model_validator(mode="after")
    def valid_parameters(self) -> Self:
        p = self.parameters
        if self.kind == "cubic_bezier":
            if len(p) != 4 or not (0 <= p[0] <= 1 and 0 <= p[2] <= 1):
                raise ValueError("Cubic curve requires four controls with x in [0,1]")
        elif self.kind == "spring":
            if len(p) != 3 or any(value <= 0 for value in p):
                raise ValueError("Spring requires positive stiffness, damping and mass")
        elif p:
            raise ValueError("Named curves do not accept parameters")
        return self


class MotionBeat(PlanModel):
    speech_cue_id: Identifier | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
        description="Supplied speech cue whose onset anchors this movement; null for editorial motion.",
    )
    phase: Literal["enter", "hold", "transform", "exit"]
    start_ms: Moment
    end_ms: Moment
    start_state: Description
    end_state: Description
    trajectory: Description
    curve: MotionCurve

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.end_ms <= self.start_ms:
            raise ValueError("Movement must have a positive duration")
        return self


class MotionElementPlan(PlanModel):
    id: Identifier = Field(description="Globally unique across all scenes; use a scene prefix, e.g. scene2-cup.")
    role: Literal["text", "graphic", "image", "video"]
    asset_id: str | None = Field(default=None, pattern=r"^assets/[A-Za-z0-9_.-]{1,80}$")
    purpose: Description
    related_element_ids: tuple[Identifier, ...] = Field(max_length=16)
    coordination: Description
    beats: tuple[MotionBeat, ...] = Field(min_length=1, max_length=12)
    mechanism_ids: tuple[str, ...] = Field(default=(), max_length=4, exclude_if=lambda value: not value)
    hero_height_ratio: float | None = Field(default=None, exclude_if=lambda value: value is None)
    contrast_ratio: float | None = Field(default=None, exclude_if=lambda value: value is None)
    text_outside_media: bool = Field(default=False, exclude_if=lambda value: value is False)


class MotionScenePlan(PlanModel):
    id: Identifier
    start_ms: Moment
    end_ms: Moment
    message: Description
    keyframe_ms: Moment | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
        description=(
            "Absolute time from the start of the entire video, inside this scene. "
            "For a scene at 4000..8000 ms, 6000 is valid; 2000 is not a relative offset."
        ),
    )
    transition_to_next: Description
    elements: tuple[MotionElementPlan, ...] = Field(min_length=1, max_length=16)
    structural_scale: Literal["macro", "medium", "card"] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    structural_role: Literal["establish", "extract", "invite"] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class MotionPlan(PlanModel):
    version: Literal["motion-plan-v1"]
    identity_source: Literal["business_kit"]
    duration_ms: int = Field(strict=True, gt=0, le=60000)
    style_id: str | None = Field(default=None, min_length=1, max_length=100)
    scenes: tuple[MotionScenePlan, ...] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def timeline_and_links(self) -> Self:
        scene_ids: set[str] = set()
        element_ids: set[str] = set()
        covered_until = 0
        previous_start = -1
        for scene in self.scenes:
            if scene.id in scene_ids:
                raise ValueError("Scene identities must be unique")
            scene_ids.add(scene.id)
            if not previous_start <= scene.start_ms <= covered_until:
                raise ValueError("Scenes must be ordered and cover the timeline without gaps")
            if not scene.start_ms < scene.end_ms <= self.duration_ms:
                raise ValueError("Scene outside output timeline")
            previous_start = scene.start_ms
            covered_until = max(covered_until, scene.end_ms)
            for element in scene.elements:
                if element.id in element_ids:
                    raise ValueError("Element identities must be globally unique")
                element_ids.add(element.id)
                if (element.role in {"image", "video"}) != (element.asset_id is not None):
                    raise ValueError("Only image/video elements must identify their authorized asset")
                previous_end = scene.start_ms
                for beat in element.beats:
                    if not previous_end <= beat.start_ms < beat.end_ms <= scene.end_ms:
                        raise ValueError("Element movements must be ordered, non-overlapping and inside the scene")
                    previous_end = beat.end_ms
        if covered_until != self.duration_ms:
            raise ValueError("Scenes must cover the full output duration")
        for scene in self.scenes:
            for element in scene.elements:
                links = element.related_element_ids
                if len(set(links)) != len(links) or element.id in links or not set(links) <= element_ids:
                    raise ValueError("Element coordination must reference distinct other planned elements")
        return self
