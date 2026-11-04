from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.reference_execution_store import (
    ExecutionCandidate,
    ExecutionEffect,
    ExecutionState,
    ranked_candidates,
)


def candidate(score, level, position, place="other"):
    return ExecutionCandidate(
        candidate_id=uuid4(),
        place_id=place,
        reputation_score=Decimal(score),
        reputation_formula_version="penalized-3.4-v1",
        similarity_level=level,
        source_position=position,
    )


def test_shortlist_uses_own_score_then_jev_similarity_then_original_order_and_excludes_owner():
    owner = candidate("10", "high", 1, "owner")
    medium = candidate("8", "medium", 3)
    highlater = candidate("8", "high", 4)
    highearlier = candidate("8", "high", 2)
    higher = candidate("9", "low", 5)
    extra = tuple(candidate("7", "low", n) for n in range(6, 20))
    result = ranked_candidates((owner, medium, highlater, highearlier, higher, *extra), "owner")
    assert len(result) == 10
    assert result[:4] == (higher, highearlier, highlater, medium)
    assert ranked_candidates((), "owner") == ()


def state(**changes):
    values = dict(
        state="pending",
        cycle_id=uuid4(),
        context_version=1,
        request_mac="a" * 64,
        batch_id=uuid4(),
        source_batch_mac="b" * 64,
        effects=tuple(
            ExecutionEffect(
                id=uuid4(),
                event=uuid4(),
                provider=provider,
                purpose="discovery",
                state="completed_filtered",
                token=uuid4(),
                output=None,
            )
            for provider in ("google", "jev")
        ),
        candidates=(),
    )
    return ExecutionState(**{**values, **changes})


def test_recovery_context_uses_only_existing_provider_fences():
    value = state()
    tenant, business, actor, search = [uuid4() for _ in range(4)]
    context = value.commit_context(tenant, business, actor, search)
    assert context.google_token == value.effects[0].token
    assert context.jev_event == value.effects[1].event
    assert context.batch == value.batch_id
    assert value.effect("apify", "discovery") is None


@pytest.mark.parametrize("change", ["batch", "source", "google", "jev", "google_token", "jev_token"])
def test_incomplete_recovery_cannot_construct_a_publication(change):
    value = state()
    if change == "batch":
        value = value.model_copy(update={"batch_id": None})
    elif change == "source":
        value = value.model_copy(update={"source_batch_mac": None})
    elif change == "google":
        value = value.model_copy(update={"effects": value.effects[1:]})
    elif change == "jev":
        value = value.model_copy(update={"effects": value.effects[:1]})
    else:
        effects = list(value.effects)
        index = 0 if change == "google_token" else 1
        effects[index] = effects[index].model_copy(update={"token": None})
        value = value.model_copy(update={"effects": tuple(effects)})
    with pytest.raises(ValueError, match="REFERENCE_EXECUTION_INCOMPLETE"):
        value.commit_context(*[uuid4() for _ in range(4)])
