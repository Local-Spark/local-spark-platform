"""Owner-selected historical baseline and explicit preservation obligations."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ElementID = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class ElementEvolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    baseline_element_id: ElementID
    disposition: Literal["preserve", "replace"]
    target_element_ids: tuple[ElementID, ...] = Field(min_length=1, max_length=8)
    function: str = Field(min_length=1, max_length=400)
    expected_result: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_targets(self) -> Self:
        if len(set(self.target_element_ids)) != len(self.target_element_ids):
            raise ValueError("Duplicate evolution target")
        if self.disposition == "preserve" and self.target_element_ids != (self.baseline_element_id,):
            raise ValueError("Preservation keeps the declared element identity")
        return self


class MotionEvolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["motion-evolution-v1", "motion-evolution-v2"] = "motion-evolution-v1"
    baseline_request_id: UUID
    baseline_number: int = Field(strict=True, ge=0, le=2)
    baseline_video_sha256: Digest
    owner_reference_confirmed: Literal[True]
    hypothesis: str = Field(min_length=1, max_length=1000)
    elements: tuple[ElementEvolution, ...] = Field(default=(), max_length=120)
    functions: tuple["MotionQualityFunction", ...] = Field(default=(), max_length=24, exclude_if=lambda v: not v)
    reuse_illustration_ids: tuple[Annotated[str, Field(pattern=r"^assets/illustration-[a-z0-9-]+\.png$")], ...] = Field(
        default=(), max_length=4
    )

    @model_validator(mode="after")
    def unique_elements(self) -> Self:
        if (self.version == "motion-evolution-v1") != bool(self.elements) or (
            self.version == "motion-evolution-v2"
        ) != bool(self.functions):
            raise ValueError("Evolution v1 binds elements; v2 binds functions independently of representation")
        if len({f.id for f in self.functions}) != len(self.functions):
            raise ValueError("Duplicate quality function")
        ids = [item.baseline_element_id for item in self.elements]
        if len(ids) != len(set(ids)) or len(self.reuse_illustration_ids) != len(set(self.reuse_illustration_ids)):
            raise ValueError("Duplicate evolution selection")
        return self


class MotionQualityFunction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: ElementID
    function: str = Field(min_length=1, max_length=1000)
    baseline_element_ids: tuple[ElementID, ...] = Field(min_length=1, max_length=16)
    evidence_at_ms: tuple[Annotated[int, Field(strict=True, ge=0, lt=60000)], ...] = Field(min_length=1, max_length=8)
    observation: str = Field(min_length=1, max_length=1000)
    verification: str = Field(min_length=1, max_length=1000)
