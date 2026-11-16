"""A terminal replay must close instead of keeping the client in a polling loop."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1 import creation_lab


@pytest.mark.parametrize("state", ["completed", "failed", "uncertain", "cancelled"])
async def test_terminal_stream_delivers_final_event_and_closes(monkeypatch, state):
    actor, run = uuid4(), uuid4()
    final = {"sequence": 1, "kind": f"run.{state}"}
    service = SimpleNamespace(
        events=AsyncMock(side_effect=[[], [final], []]),
        get=AsyncMock(return_value={"state": state}),
    )
    monkeypatch.setattr(creation_lab, "drafts", lambda _: service)
    sleep = AsyncMock(side_effect=AssertionError("A finished stream must not sleep or poll again"))
    monkeypatch.setattr(creation_lab.asyncio, "sleep", sleep)
    request = SimpleNamespace(
        headers={"authorization": "Bearer local-token"},
        is_disconnected=AsyncMock(return_value=False),
        app=SimpleNamespace(
            state=SimpleNamespace(
                identity_verifier=SimpleNamespace(authenticate=AsyncMock(return_value=SimpleNamespace(actor_id=actor)))
            )
        ),
    )
    response = await creation_lab.stream_events(request, actor, run, "0")
    chunks = [chunk async for chunk in response.body_iterator]
    assert len(chunks) == 2
    assert f"run.{state}" in chunks[0]
    assert "event: stream.finished" in chunks[1]
    sleep.assert_not_awaited()
