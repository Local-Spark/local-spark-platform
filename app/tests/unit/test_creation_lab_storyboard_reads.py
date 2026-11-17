"""Storyboard authorization/expiry and byte checks survive shorter read transactions."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.creation_lab_checkpoints import storyboard_frame


@pytest.mark.parametrize("case", ["ok", "expired", "missing", "index", "changed"])
async def test_storyboard_decodes_outside_transaction_and_rechecks(settings, monkeypatch, case):
    active = False
    calls = 0
    row = {"expired": case == "expired", "payload_ciphertext": "encrypted"}
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = None if case == "missing" else row
    session = SimpleNamespace(execute=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(*args):
        nonlocal active
        active = True
        try:
            yield session
        finally:
            active = False

    def decode(value):
        nonlocal calls
        assert not active
        calls += 1
        return {"value": {"frames": [{"sha256": "changed" if case == "changed" and calls == 2 else "original"}]}}

    read = AsyncMock(return_value=b"png")
    monkeypatch.setattr("app.services.creation_lab_checkpoints.LabMotionStoryboards.read_png", read)
    requests = SimpleNamespace(
        settings=settings,
        run_id=uuid4(),
        database=SimpleNamespace(transaction=transaction),
        execution=SimpleNamespace(guard=AsyncMock()),
        context=SimpleNamespace(open=decode),
    )
    errors = {
        "expired": "CREATION_LAB_TRACE_EXPIRED",
        "missing": "CREATION_LAB_CHECKPOINT_NOT_FOUND",
        "index": "CREATION_LAB_FRAME_NOT_FOUND",
        "changed": "MOTION_STORYBOARD_BYTES_CHANGED",
    }
    if case == "ok":
        assert await storyboard_frame(requests, uuid4(), 0) == b"png"
        assert calls == 2
    else:
        with pytest.raises(AuthError, match=errors[case]):
            await storyboard_frame(requests, uuid4(), 1 if case == "index" else 0)
    assert all(call.kwargs["read_only"] for call in requests.execution.guard.await_args_list)
