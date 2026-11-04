"""Explicit decisions are frozen per new cycle, not recalculated per radius."""

from uuid import uuid4

import pytest

from app.services.reference_cycle_decisions import (
    CycleDecisionError,
    CycleDecisionRequirement,
    PreviousSelection,
    RetentionDecision,
    confirm_cycle_decisions,
    prepare_cycle_decisions,
)


def test_decisions_cover_only_old_selections_outside_the_first_list():
    cycle, old, result, other_result, a, b, c = [uuid4() for _ in range(7)]
    requirement = prepare_cycle_decisions(
        cycle,
        result,
        (PreviousSelection(a, old), PreviousSelection(b, old), PreviousSelection(c, old)),
        (b, uuid4()),
    )
    assert requirement.required_place_ids == (a, c)
    confirmation = confirm_cycle_decisions(requirement, (RetentionDecision(c, "remove"), RetentionDecision(a, "keep")))
    assert confirmation.cycle_id == cycle and confirmation.first_result_id == result
    assert confirmation.decisions == (RetentionDecision(a, "keep"), RetentionDecision(c, "remove"))
    # Another radius is not an input to confirmation: the same frozen result
    # and explicit actions remain the authority for the cycle.
    assert other_result != confirmation.first_result_id
    assert confirm_cycle_decisions(requirement, confirmation.decisions) == confirmation


def test_first_search_and_empty_published_list_are_explicit():
    cycle, old, result, place = [uuid4() for _ in range(4)]
    no_prior = prepare_cycle_decisions(cycle, result, (), ())
    assert no_prior.required_place_ids == ()
    assert confirm_cycle_decisions(no_prior, ()).decisions == ()
    empty = prepare_cycle_decisions(cycle, result, (PreviousSelection(place, old),), ())
    assert empty.required_place_ids == (place,)


def test_incomplete_extra_and_duplicate_actions_fail_closed():
    cycle, old, result, a, b = [uuid4() for _ in range(5)]
    requirement = prepare_cycle_decisions(cycle, result, (PreviousSelection(a, old),), ())
    for decisions in (
        (),
        (RetentionDecision(b, "keep"),),
        (RetentionDecision(a, "keep"), RetentionDecision(a, "keep")),
    ):
        with pytest.raises(CycleDecisionError, match="REFERENCE_CYCLE_DECISION_INCOMPLETE"):
            confirm_cycle_decisions(requirement, decisions)


def test_invalid_or_same_cycle_inputs_are_rejected():
    cycle, old, result, place = [uuid4() for _ in range(4)]
    valid = (PreviousSelection(place, old),)
    bad = (
        (None, result, valid, ()),
        (cycle, None, valid, ()),
        (cycle, result, list(valid), ()),
        (cycle, result, valid * 4, ()),
        (cycle, result, (object(),), ()),
        (cycle, result, (PreviousSelection("not-uuid", old),), ()),
        (cycle, result, (PreviousSelection(place, "not-uuid"),), ()),
        (cycle, result, (PreviousSelection(place, cycle),), ()),
        (cycle, result, valid, []),
        (cycle, result, valid, tuple(uuid4() for _ in range(11))),
        (cycle, result, valid, ("not-uuid",)),
        (cycle, result, valid * 2, ()),
        (cycle, result, valid, (place, place)),
    )
    for args in bad:
        with pytest.raises(CycleDecisionError, match="REFERENCE_CYCLE_DECISION_INVALID"):
            prepare_cycle_decisions(*args)


def test_forged_requirements_and_invalid_actions_fail_closed():
    cycle, result, place = uuid4(), uuid4(), uuid4()
    requirement = CycleDecisionRequirement(cycle, result, (place,))
    bad = (
        (None, ()),
        (CycleDecisionRequirement(None, result, ()), ()),
        (CycleDecisionRequirement(cycle, None, ()), ()),
        (CycleDecisionRequirement(cycle, result, []), ()),
        (CycleDecisionRequirement(cycle, result, tuple(uuid4() for _ in range(4))), ()),
        (CycleDecisionRequirement(cycle, result, ("not-uuid",)), ()),
        (CycleDecisionRequirement(cycle, result, (place, place)), ()),
        (requirement, []),
        (requirement, (object(),)),
        (requirement, (RetentionDecision("not-uuid", "keep"),)),
        (requirement, (RetentionDecision(place, "maybe"),)),
    )
    for req, actions in bad:
        with pytest.raises(CycleDecisionError, match="REFERENCE_CYCLE_DECISION_INVALID"):
            confirm_cycle_decisions(req, actions)
