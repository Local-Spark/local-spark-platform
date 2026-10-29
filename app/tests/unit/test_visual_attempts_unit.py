"""Fence and reservation decisions never dispatch an external effect themselves."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.visual_attempts import VisualAttemptService
from app.services.visual_cost_ledger import VisualCostError, VisualReservation


def mapped(value):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = value
    return result


def setup(settings, *, row=True, owner=True, previous=None, reservation=None):
    tenant, business, actor, preview, operation = (uuid4() for _ in range(5))
    params = {
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "preview": preview,
        "fence": 1,
        "operation": operation,
        "provider": "fake",
        "model": "synthetic",
        "request_hash": "a" * 64,
        "reserved_usd_micros": 100,
    }
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[True, owner, True])
    session.execute = AsyncMock(side_effect=[mapped({"id": preview} if row else None), mapped(previous), None])

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    database = MagicMock()
    database.transaction = transaction
    service = VisualAttemptService(settings, database)
    service.ledger.reserve_in_transaction = AsyncMock(
        return_value=reservation or VisualReservation(uuid4(), "submitted", 100, None, True)
    )
    return service, session, params


async def test_new_fenced_reservation_records_intent_in_same_transaction(settings):
    service, session, params = setup(settings)
    result = await service.reserve(**params)
    assert result.created and result.reservation.created
    assert "FOR UPDATE" in str(session.execute.await_args_list[0].args[0])
    assert "INSERT INTO visual_ai_attempts" in str(session.execute.await_args_list[2].args[0])
    assert service.ledger.reserve_in_transaction.await_args.args[0] is session
    assert "clock_timestamp()" in str(session.scalar.await_args_list[0].args[0])
    assert "clock_timestamp()" in str(session.scalar.await_args_list[2].args[0])


async def test_stale_fence_and_inactive_owner_cannot_reserve(settings):
    service, _, params = setup(settings, row=False)
    with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
        await service.reserve(**params)
    service.ledger.reserve_in_transaction.assert_not_awaited()
    service, _, params = setup(settings, owner=False)
    with pytest.raises(VisualCostError, match="VISUAL_OWNER_REQUIRED"):
        await service.reserve(**params)
    service.ledger.reserve_in_transaction.assert_not_awaited()


@pytest.mark.parametrize("expired_after_ledger", [False, True])
async def test_expiry_after_lock_wait_never_records_attempt(settings, expired_after_ledger):
    service, session, params = setup(settings)
    session.scalar.side_effect = [True, True, False] if expired_after_ledger else [False]
    with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
        await service.reserve(**params)
    assert service.ledger.reserve_in_transaction.await_count == int(expired_after_ledger)
    assert all("INSERT INTO visual_ai_attempts" not in str(call.args[0]) for call in session.execute.await_args_list)


async def test_same_operation_replay_never_creates_a_second_attempt(settings):
    service, session, params = setup(settings)
    reservation = VisualReservation(uuid4(), "submitted", 100, None, False)
    previous = {
        "operation_id": params["operation"],
        "actor_id": params["actor"],
        "request_hash": params["request_hash"],
        "reservation_id": reservation.id,
    }
    session.execute.side_effect = [mapped({"id": params["preview"]}), mapped(previous)]
    service.ledger.reserve_in_transaction.return_value = reservation
    result = await service.reserve(**params)
    assert not result.created and result.reservation.id == reservation.id
    assert session.execute.await_count == 2


@pytest.mark.parametrize("different", ["operation_id", "actor_id", "request_hash"])
async def test_replay_with_changed_identity_is_rejected(settings, different):
    service, session, params = setup(settings)
    previous = {
        "operation_id": params["operation"],
        "actor_id": params["actor"],
        "request_hash": params["request_hash"],
        "reservation_id": uuid4(),
    }
    previous[different] = uuid4() if different != "request_hash" else "b" * 64
    session.execute.side_effect = [mapped({"id": params["preview"]}), mapped(previous)]
    with pytest.raises(VisualCostError, match="VISUAL_ATTEMPT_CONFLICT"):
        await service.reserve(**params)
    service.ledger.reserve_in_transaction.assert_not_awaited()


@pytest.mark.parametrize("created,matching", [(True, True), (False, False)])
async def test_inconsistent_reservation_never_authorizes_send(settings, created, matching):
    service, session, params = setup(settings)
    reservation = VisualReservation(uuid4(), "submitted", 100, None, created)
    previous = {
        "operation_id": params["operation"],
        "actor_id": params["actor"],
        "request_hash": params["request_hash"],
        "reservation_id": reservation.id if matching else uuid4(),
    }
    session.execute.side_effect = [mapped({"id": params["preview"]}), mapped(previous)]
    service.ledger.reserve_in_transaction.return_value = reservation
    with pytest.raises(VisualCostError, match="VISUAL_ATTEMPT_INCONSISTENT"):
        await service.reserve(**params)


async def test_existing_unbound_reservation_is_uncertain_and_not_resent(settings):
    reservation = VisualReservation(uuid4(), "uncertain", 100, None, False)
    service, session, params = setup(settings, reservation=reservation)
    with pytest.raises(VisualCostError, match="VISUAL_RESERVATION_UNBOUND"):
        await service.reserve(**params)
    assert session.execute.await_count == 2
