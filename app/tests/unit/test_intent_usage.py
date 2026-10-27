"""Conservative cost accounting rejects invalid estimates and unconfigured budgets."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.intent_usage import estimate_micros, finish_intent, reserve_intent


@pytest.mark.parametrize("values", [(-1, 0, 42000, 0), (1, -1, 42000, 0), (1, 0, 0, 0), (1, 0, 42000, -1)])
def test_rejects_invalid_cost_inputs(values):
    with pytest.raises(ValueError):
        estimate_micros(*values)


def test_rounds_up_to_the_smallest_billable_unit():
    assert estimate_micros(1, 0, 42000, 0) == 1
    assert estimate_micros(64000, 0, 42000, 0) == 2688


@pytest.mark.parametrize(
    "daily,digest,model,tokens",
    [
        (0, "a" * 64, "jev", 1),
        (1, "short", "jev", 1),
        (1, "a" * 64, "", 1),
        (1, "a" * 64, "x" * 121, 1),
        (1, "a" * 64, "jev", 0),
    ],
)
async def test_never_reserves_or_calls_provider_without_valid_guard(daily, digest, model, tokens):
    session = MagicMock()
    with pytest.raises(AuthError, match="INTENT_BUDGET_DISABLED"):
        await reserve_intent(
            session,
            tenant=uuid4(),
            business=uuid4(),
            actor=uuid4(),
            operation=uuid4(),
            request_hash=digest,
            model=model,
            input_rate=42000,
            output_rate=0,
            max_input_tokens=tokens,
            max_output_tokens=0,
            daily_limit=daily,
        )
    session.execute.assert_not_called()


async def test_missing_or_previously_settled_operation_does_not_create_a_second_audit():
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = None
    session = MagicMock(execute=AsyncMock(return_value=result))
    await finish_intent(
        session,
        tenant=uuid4(),
        operation=uuid4(),
        input_tokens=None,
        output_tokens=None,
        input_rate=42000,
        output_rate=0,
    )
    assert session.execute.await_count == 1
