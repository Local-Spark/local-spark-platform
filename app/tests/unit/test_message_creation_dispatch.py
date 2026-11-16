"""Regression contracts for transport parity and private output isolation.

These tests use no database, provider or customer material.
"""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.services.auth import AuthError
from app.services.creation_lab_runner import CreationLabRunner
from app.services.message_creation_delivery import persist_product_result, record_product_message
from app.workflows.contracts import BusinessEvent


@pytest.mark.parametrize("origin", ["lab", "whatsapp"])
@pytest.mark.parametrize("format", ["auto", "photo", "story", "reel"])
async def test_new_messages_share_one_coordinator(monkeypatch, origin, format):
    from app.services import creation_lab_runner, message_creation

    run, actor, tenant, business = [uuid4() for _ in range(4)]
    event = BusinessEvent(str(uuid5(run, "creation_lab.requested")), str(tenant), str(business), str(actor), str(run))
    row = {
        "id": run,
        "actor_id": actor,
        "tenant_id": tenant,
        "business_id": business,
        "origin": origin,
        "flow_version": 2,
        "format": format,
    }
    session = SimpleNamespace(scalar=AsyncMock(return_value="creation_lab.requested"))

    @asynccontextmanager
    async def transaction(*_):
        yield session

    database = SimpleNamespace(transaction=transaction)
    adapter = SimpleNamespace(execution=SimpleNamespace(guard=AsyncMock(return_value=row)), scope=AsyncMock())
    monkeypatch.setattr(creation_lab_runner, "LabMotionRequests", lambda *_: adapter)
    common = AsyncMock(return_value="awaiting_reply")
    monkeypatch.setattr(message_creation, "MessageCreation", lambda *_: SimpleNamespace(execute=common))
    old_images = AsyncMock(side_effect=AssertionError("Legacy image path must not handle a new message"))
    monkeypatch.setattr(creation_lab_runner, "LabImageRunner", old_images)
    settings = object()
    assert await CreationLabRunner(settings, database).run(event) == "awaiting_reply"
    common.assert_awaited_once_with(event)
    old_images.assert_not_called()


async def test_mismatched_business_never_reaches_coordinator(monkeypatch):
    from app.services import creation_lab_runner, message_creation

    run, actor, tenant, business = [uuid4() for _ in range(4)]
    event = BusinessEvent(str(uuid5(run, "creation_lab.requested")), str(tenant), str(business), str(actor), str(run))
    adapter = SimpleNamespace(
        execution=SimpleNamespace(guard=AsyncMock(return_value={"tenant_id": tenant, "business_id": uuid4()}))
    )

    @asynccontextmanager
    async def transaction(*_):
        yield object()

    monkeypatch.setattr(creation_lab_runner, "LabMotionRequests", lambda *_: adapter)
    common = AsyncMock()
    monkeypatch.setattr(message_creation, "MessageCreation", common)
    with pytest.raises(AuthError) as error:
        await CreationLabRunner(object(), SimpleNamespace(transaction=transaction)).run(event)
    assert error.value.code == "CREATION_LAB_EVENT_MISMATCH"
    common.assert_not_called()


async def test_lab_output_never_writes_product_piece_or_delivery():
    session = SimpleNamespace(execute=AsyncMock())
    await persist_product_result(session, {"origin": "lab"}, object())
    await record_product_message(session, {"origin": "lab"}, object(), "private", kind="result", sha="a" * 64)
    session.execute.assert_not_called()


@pytest.mark.parametrize("seconds", [1, 59, 60, 61, 179, 180])
def test_transcription_reservation_bounds_usage_without_another_budget(seconds):
    from app.services.audio_costs import transcription_cost

    reservation, estimate = transcription_cost(seconds)
    assert 0 < estimate <= reservation <= 13_500
    assert estimate == seconds * 75


@pytest.mark.parametrize("seconds", [0, -1, 181, True, 1.5])
def test_transcription_rejects_unbounded_or_invalid_duration(seconds):
    from app.services.audio_costs import transcription_cost

    with pytest.raises(ValueError, match="AUDIO_DURATION_INVALID"):
        transcription_cost(seconds)
