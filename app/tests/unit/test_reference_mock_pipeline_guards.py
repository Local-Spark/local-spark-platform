"""Fail-closed checks for non-network pipeline recovery and guards."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.services import reference_mock_pipeline as pipeline
from app.services.reference_jev_budget_guard import JevGuardStateError
from app.services.reference_jev_intent_guard import IntentJevBudgetGuard
from app.services.reference_mock_pipeline import ReferenceMockPipelineError, _recover, run_mock_reference_pipeline


async def test_intent_guard_refuses_wrong_or_repeated_effect_without_io(fake_database):
    effect = uuid4()
    guard = IntentJevBudgetGuard(fake_database, SimpleNamespace(effect=effect, event=uuid4()), uuid4())
    assert await guard.claim(uuid4(), None) is False
    guard._attempted = True
    assert await guard.claim(effect, None) is False
    with pytest.raises(JevGuardStateError):
        await guard.uncertain()
    with pytest.raises(JevGuardStateError):
        guard.execution_token()


async def test_recovery_allowlists_only_expected_states(fake_database):
    context = SimpleNamespace(
        tenant=uuid4(), actor=uuid4(), business=uuid4(), search=uuid4(), effect=uuid4(), event=uuid4()
    )
    session = AsyncMock()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def transaction(*args):
        yield session

    fake_database.transaction = transaction
    session.scalar.return_value = {"state": "empty", "batch_id": None}
    assert (await _recover(fake_database, context)).state == "empty"
    session.scalar.return_value = {"state": "unexpected", "batch_id": None}
    with pytest.raises(ReferenceMockPipelineError, match="REFERENCE_RECOVERY_INVALID"):
        await _recover(fake_database, context)


@pytest.mark.parametrize("snapshot", [None, {"batch_id": str(uuid4())}])
async def test_recovery_rejects_missing_or_unrelated_similarity_snapshot(fake_database, snapshot):
    from contextlib import asynccontextmanager

    context = SimpleNamespace(
        tenant=uuid4(), actor=uuid4(), business=uuid4(), search=uuid4(), effect=uuid4(), event=uuid4()
    )
    session = AsyncMock()
    session.scalar.side_effect = [{"state": "filtered", "batch_id": str(uuid4())}, snapshot]

    @asynccontextmanager
    async def transaction(*args):
        yield session

    fake_database.transaction = transaction
    with pytest.raises(ReferenceMockPipelineError, match="REFERENCE_RECOVERY_INVALID"):
        await _recover(fake_database, context)


def test_places_execution_token_cannot_be_read_before_claim(fake_database):
    from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard, PlacesGuardStateError

    guard = DatabasePlacesBudgetGuard(fake_database, SimpleNamespace(effect=uuid4()))
    with pytest.raises(PlacesGuardStateError, match="PLACES_EXECUTOR_NOT_CLAIMED"):
        guard.execution_token()


async def test_pipeline_rejects_non_mock_transport_before_reading_inputs(fake_database):
    with pytest.raises(ReferenceMockPipelineError, match="REFERENCE_MOCK_TRANSPORT_REQUIRED"):
        await run_mock_reference_pipeline(
            fake_database,
            None,
            google_transport=httpx.AsyncHTTPTransport(),
            jev_transport=httpx.MockTransport(lambda _: None),
        )


async def test_recovery_failure_leaves_unresolved_effect_held(fake_database, monkeypatch):
    context = SimpleNamespace(context_version=1, effect=uuid4())
    inputs = SimpleNamespace(
        google=context, context_version=1, google_key=None, place_type="cafe", latitude=0, longitude=0, radius_km=5
    )
    guard = SimpleNamespace(uncertain=AsyncMock(), intent_validated=lambda: True)
    provider = SimpleNamespace(search=AsyncMock(side_effect=ValueError("private")))
    monkeypatch.setattr(pipeline, "DatabasePlacesBudgetGuard", lambda *args: guard)
    monkeypatch.setattr(pipeline, "GooglePlacesNearby", lambda *args, **kwargs: provider)
    monkeypatch.setattr(pipeline, "_recover", AsyncMock(side_effect=ConnectionError("private")))
    transport = httpx.MockTransport(lambda _: None)
    with pytest.raises(ReferenceMockPipelineError, match="REFERENCE_MOCK_PIPELINE_INCOMPLETE") as error:
        await run_mock_reference_pipeline(fake_database, inputs, google_transport=transport, jev_transport=transport)
    assert "private" not in str(error.value)
    guard.uncertain.assert_awaited_once()
