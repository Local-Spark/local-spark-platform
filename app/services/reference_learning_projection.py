"""Pure projection of derived reference learnings.

This module does not load data, prove provenance, analyze content, or authorize
model input. Callers must provide owner-scoped selections and trusted analysis
records and enforce the gates documented alongside the generation integration.
"""

import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

_DISALLOWED_TEXT = re.compile(r"(?:https?://|www\.|@|[<>\x00-\x1f\x7f])", re.IGNORECASE)


class LearningProjectionError(ValueError):
    """Stable error without reference content."""


class _Immutable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SelectedReferenceVersion(_Immutable):
    """Server-loaded selection and its exact profile-association version."""

    reference_id: UUID
    association_version: StrictInt = Field(ge=1)


class DerivedPattern(_Immutable):
    """A derived pattern, not a post, image, caption or business fact.

    Text remains untrusted: formatting validation alone cannot prove that it is
    derivative or safe against prompt injection.
    """

    dimension: Literal["visual", "editorial"]
    observation: str = Field(min_length=1, max_length=240, repr=False)

    @field_validator("observation")
    @classmethod
    def observation_is_bounded(cls, value: str) -> str:
        if value != value.strip() or _DISALLOWED_TEXT.search(value):
            raise ValueError("invalid derived pattern")
        return value


class ReferenceLearning(_Immutable):
    """Immutable result whose producer and selection must be verified elsewhere."""

    reference_id: UUID
    association_version: StrictInt = Field(ge=1)
    analysis_id: UUID
    source: Literal["instagram_feed"]
    status: Literal["completed", "partial"]
    patterns: tuple[DerivedPattern, ...] = Field(min_length=1, max_length=10)


class ReferenceLearningSnapshot(_Immutable):
    """Snapshot preserves provenance; no source posts or profiles are fields."""

    references: tuple[ReferenceLearning, ...]

    def model_input(self) -> list[dict[str, object]]:
        """Return only untrusted derived data, omitting internal identities."""
        return [
            {
                "origem": "feed_instagram",
                "status": "parcial" if entry.status == "partial" else "concluido",
                "padroes": [
                    {"dimensao": pattern.dimension, "observacao": pattern.observation} for pattern in entry.patterns
                ],
            }
            for entry in self.references
        ]


def project_reference_learnings(
    selected: tuple[SelectedReferenceVersion, ...],
    learnings: tuple[ReferenceLearning, ...],
) -> ReferenceLearningSnapshot:
    """Keep only records for the exact selected association, in selection order.

    Absence yields no data. The caller, not this function, must prove owner
    authorization, selection freshness, provenance and derived-only content.
    """
    if (
        not isinstance(selected, tuple)
        or not all(isinstance(item, SelectedReferenceVersion) for item in selected)
        or not isinstance(learnings, tuple)
        or not all(isinstance(item, ReferenceLearning) for item in learnings)
    ):
        raise LearningProjectionError("REFERENCE_LEARNING_INVALID")
    versions: dict[UUID, int] = {}
    for selected_item in selected:
        if selected_item.reference_id in versions:
            raise LearningProjectionError("REFERENCE_LEARNING_SELECTION_DUPLICATE")
        versions[selected_item.reference_id] = selected_item.association_version
    eligible: dict[UUID, ReferenceLearning] = {}
    for record in learnings:
        if versions.get(record.reference_id) != record.association_version:
            continue
        if record.reference_id in eligible:
            raise LearningProjectionError("REFERENCE_LEARNING_DUPLICATE")
        eligible[record.reference_id] = record
    return ReferenceLearningSnapshot(
        references=tuple(eligible[item.reference_id] for item in selected if item.reference_id in eligible)
    )
