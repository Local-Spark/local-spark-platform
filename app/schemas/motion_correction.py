"""An explicit absolute interval, including transition allowance, for one correction."""

from typing import Self

from pydantic import Field, model_validator

from app.schemas.motion_plan import Identifier, Moment, PlanModel


class MotionCorrectionRegion(PlanModel):
    scene_id: Identifier
    element_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    start_ms: Moment
    end_ms: Moment
    margin_before_ms: int = Field(strict=True, ge=0, le=1000)
    margin_after_ms: int = Field(strict=True, ge=0, le=1000)

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if self.end_ms <= self.start_ms or len(set(self.element_ids)) != len(self.element_ids):
            raise ValueError("Correction needs a positive interval and distinct elements")
        if self.start_ms < self.margin_before_ms or self.end_ms + self.margin_after_ms > 60000:
            raise ValueError("Transition margins must stay on the absolute source timeline")
        return self

    @property
    def window(self) -> tuple[int, int]:
        return self.start_ms - self.margin_before_ms, self.end_ms + self.margin_after_ms
