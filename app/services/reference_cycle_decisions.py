"""Pure contract for explicit retention decisions at a new reference cycle.

This module does not prove a publication, load a selection, or persist a
decision. A future transaction must freeze exactly one requirement per cycle,
using the first published result and the previously selected identities, while
holding the same lock as selection changes. Later radius searches must reuse
that frozen requirement rather than construct another one.
"""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID


class CycleDecisionError(ValueError):
    """Stable error without provider data."""


@dataclass(frozen=True)
class PreviousSelection:
    place_identity: UUID
    origin_cycle: UUID


@dataclass(frozen=True)
class CycleDecisionRequirement:
    cycle_id: UUID
    first_result_id: UUID
    required_place_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class RetentionDecision:
    place_identity: UUID
    action: Literal["keep", "remove"]


@dataclass(frozen=True)
class CycleDecisionConfirmation:
    cycle_id: UUID
    first_result_id: UUID
    decisions: tuple[RetentionDecision, ...]


def prepare_cycle_decisions(
    cycle_id: UUID,
    first_result_id: UUID,
    previously_selected: tuple[PreviousSelection, ...],
    first_result_places: tuple[UUID, ...],
) -> CycleDecisionRequirement:
    """Describe the old selections outside the first published list only."""
    if (
        not isinstance(cycle_id, UUID)
        or not isinstance(first_result_id, UUID)
        or not isinstance(previously_selected, tuple)
        or len(previously_selected) > 3
        or not all(
            isinstance(item, PreviousSelection)
            and isinstance(item.place_identity, UUID)
            and isinstance(item.origin_cycle, UUID)
            and item.origin_cycle != cycle_id
            for item in previously_selected
        )
        or not isinstance(first_result_places, tuple)
        or len(first_result_places) > 10
        or not all(isinstance(item, UUID) for item in first_result_places)
    ):
        raise CycleDecisionError("REFERENCE_CYCLE_DECISION_INVALID")
    selected_ids = tuple(item.place_identity for item in previously_selected)
    if len(set(selected_ids)) != len(selected_ids) or len(set(first_result_places)) != len(first_result_places):
        raise CycleDecisionError("REFERENCE_CYCLE_DECISION_INVALID")
    offered = set(first_result_places)
    return CycleDecisionRequirement(
        cycle_id=cycle_id,
        first_result_id=first_result_id,
        required_place_ids=tuple(place for place in selected_ids if place not in offered),
    )


def confirm_cycle_decisions(
    requirement: CycleDecisionRequirement,
    decisions: tuple[RetentionDecision, ...],
) -> CycleDecisionConfirmation:
    """Require one explicit action for every identity in the frozen scope."""
    if (
        not isinstance(requirement, CycleDecisionRequirement)
        or not isinstance(requirement.cycle_id, UUID)
        or not isinstance(requirement.first_result_id, UUID)
        or not isinstance(requirement.required_place_ids, tuple)
        or len(requirement.required_place_ids) > 3
        or not all(isinstance(item, UUID) for item in requirement.required_place_ids)
        or len(set(requirement.required_place_ids)) != len(requirement.required_place_ids)
        or not isinstance(decisions, tuple)
        or not all(
            isinstance(item, RetentionDecision)
            and isinstance(item.place_identity, UUID)
            and item.action in ("keep", "remove")
            for item in decisions
        )
    ):
        raise CycleDecisionError("REFERENCE_CYCLE_DECISION_INVALID")
    choices = {item.place_identity: item for item in decisions}
    if len(choices) != len(decisions) or set(choices) != set(requirement.required_place_ids):
        raise CycleDecisionError("REFERENCE_CYCLE_DECISION_INCOMPLETE")
    return CycleDecisionConfirmation(
        cycle_id=requirement.cycle_id,
        first_result_id=requirement.first_result_id,
        decisions=tuple(choices[identity] for identity in requirement.required_place_ids),
    )
