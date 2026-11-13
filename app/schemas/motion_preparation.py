"""Explicit intent provenance and evidence selection, never implicit artistic approval."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.motion_plan import Identifier


class PreparationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MotionDecisionBasis(PreparationModel):
    id: Identifier
    kind: Literal["requirement", "observation", "example", "hypothesis"]
    origin: Literal["client", "operator", "reference"]
    source_excerpt: str = Field(min_length=1, max_length=1000)
    interpretation: str = Field(min_length=1, max_length=1000)
    scope: Literal["request", "scene"]
    scene_ids: tuple[Identifier, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def scoped(self) -> Self:
        if (self.scope == "scene") != bool(self.scene_ids):
            raise ValueError("Scene scope requires scene identifiers")
        if self.kind == "requirement" and self.origin != "client":
            raise ValueError("Operator/reference choices must not become client requirements")
        return self


class MotionEvidenceSelection(PreparationModel):
    id: Identifier
    kind: Literal["source", "baseline", "reference", "material", "audio"]
    at_ms: tuple[Annotated[int, Field(strict=True, ge=0, lt=60000)], ...] = Field(default=(), max_length=12)
    reference_ids: tuple[Identifier, ...] = Field(default=(), max_length=8)
    asset_id: str | None = Field(default=None, pattern=r"^assets/[A-Za-z0-9_.-]{1,80}$")
    asset_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$", exclude_if=lambda value: value is None)
    scene_ids: tuple[Identifier, ...] = Field(default=(), max_length=12)
    observation: str = Field(min_length=1, max_length=1000)
    intended_use: str = Field(min_length=1, max_length=1000)
    limitations: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def selected(self) -> Self:
        if (
            bool(self.at_ms) != (self.kind in {"source", "baseline"})
            or bool(self.reference_ids) != (self.kind == "reference")
            or (self.asset_id is not None) != (self.kind in {"material", "audio"})
            or (self.asset_sha256 is not None) != (self.kind == "audio")
            or any(type(ms) is not int or not 0 <= ms < 60000 for ms in self.at_ms)
            or len(set(self.at_ms)) != len(self.at_ms)
            or len(set(self.reference_ids)) != len(self.reference_ids)
        ):
            raise ValueError("Evidence must identify exact, distinct supplied items")
        return self


class MotionPreparation(PreparationModel):
    version: Literal["motion-preparation-v1"] = "motion-preparation-v1"
    client_message: str = Field(min_length=1, max_length=4000)
    decisions: tuple[MotionDecisionBasis, ...] = Field(min_length=1, max_length=24)
    evidence: tuple[MotionEvidenceSelection, ...] = Field(min_length=1, max_length=24)
    unresolved: tuple[str, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def distinct(self) -> Self:
        if any(item.origin == "client" and item.source_excerpt not in self.client_message for item in self.decisions):
            raise ValueError("Client decisions must quote the preserved client message")
        if len({v.id for v in self.decisions}) != len(self.decisions) or len({v.id for v in self.evidence}) != len(
            self.evidence
        ):
            raise ValueError("Preparation identifiers must be distinct")
        return self


class MotionCheckpointDecision(PreparationModel):
    operation_id: UUID
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approve", "reject"]
    note: str = Field(min_length=1, max_length=2000)
