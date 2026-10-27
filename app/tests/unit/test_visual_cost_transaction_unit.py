"""Visual reservation must not own or commit a caller's atomic transaction."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger, _reservation_digest


def _mapping(value):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = value
    result.mappings.return_value.one.return_value = value
    return result


def _params():
    return {
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "operation": uuid4(),
        "provider": "fake",
        "model": "synthetic",
        "request_hash": "a" * 64,
        "reserved_usd_micros": 70,
    }


async def test_new_reservation_uses_existing_transaction_without_committing(settings):
    params = _params()
    row = {"id": uuid4(), "state": "submitted", "reserved_usd_micros": 70, "actual_usd_micros": None}
    session = MagicMock()
    session.in_transaction.return_value = True
    session.execute = AsyncMock(side_effect=[None, _mapping(None), _mapping(row), None])
    session.scalar = AsyncMock(return_value=0)
    session.commit = AsyncMock()
    database = MagicMock()
    ledger = VisualCostLedger(settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100}), database)
    result = await ledger.reserve_in_transaction(session, **params)
    assert result.created and result.id == row["id"]
    statements = [str(call.args[0]) for call in session.execute.await_args_list]
    assert "pg_advisory_xact_lock" in statements[0]
    assert "INSERT INTO visual_cost_reservations" in statements[2]
    assert "INSERT INTO visual_cost_events" in statements[3]
    session.commit.assert_not_awaited()
    database.transaction.assert_not_called()


async def test_replay_does_not_create_second_reservation_or_grant_new_dispatch(settings):
    params = _params()
    digest = _reservation_digest(
        *(params[k] for k in ("business", "actor", "provider", "model", "request_hash", "reserved_usd_micros"))
    )
    row = {
        "id": uuid4(),
        "state": "submitted",
        "request_hash": digest,
        "reserved_usd_micros": 70,
        "actual_usd_micros": None,
    }
    session = MagicMock()
    session.in_transaction.return_value = True
    session.execute = AsyncMock(side_effect=[None, _mapping(row)])
    session.scalar = AsyncMock()
    ledger = VisualCostLedger(settings, MagicMock())
    result = await ledger.reserve_in_transaction(session, **params)
    assert not result.created and result.id == row["id"]
    assert session.execute.await_count == 2
    session.scalar.assert_not_awaited()


async def test_transaction_and_input_guards_run_before_database_effects(settings):
    session = MagicMock()
    session.in_transaction.return_value = False
    session.execute = AsyncMock()
    ledger = VisualCostLedger(settings, MagicMock())
    params = _params()
    with pytest.raises(VisualCostError, match="VISUAL_TRANSACTION_REQUIRED"):
        await ledger.reserve_in_transaction(session, **params)
    with pytest.raises(VisualCostError, match="INVALID_RESERVATION"):
        await ledger.reserve_in_transaction(session, **{**params, "request_hash": "invalid"})
    session.execute.assert_not_awaited()
    with pytest.raises(VisualCostError, match="INVALID_RESERVATION"):
        await ledger.reserve(**{**params, "provider": ""})
    ledger.database.transaction.assert_not_called()
