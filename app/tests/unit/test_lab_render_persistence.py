"""Render evidence is encrypted outside the lock and uses a bounded DB deadline."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.creation_lab_motion_output import LabMotionOrchestrator


@pytest.mark.parametrize("failure", [None, "57014", "23505"])
async def test_evidence_deadline_is_scoped_and_encryption_precedes_transaction(failure):
    active = False
    events = []
    session = AsyncMock()

    async def execute(statement, parameters=None):
        events.append((str(statement), parameters))
        if failure and "INSERT INTO creation_lab_trace" in str(statement):
            error = Exception("private diagnostic must not escape")
            error.sqlstate = failure
            raise DBAPIError("private sql", {}, error, hide_parameters=True)

    session.execute.side_effect = execute

    @asynccontextmanager
    async def transaction(*args):
        nonlocal active
        active = True
        yield session
        active = False

    def seal(value):
        assert not active
        return str(value)

    run, actor, token, operation = uuid4(), uuid4(), uuid4(), uuid4()
    target = object.__new__(LabMotionOrchestrator)
    target.run_id = run
    target.requests = SimpleNamespace(
        database=SimpleNamespace(transaction=transaction), context=SimpleNamespace(open=lambda _: {"fixture": True})
    )
    target.execution = SimpleNamespace(
        cipher=SimpleNamespace(seal=seal), guard=AsyncMock(), fence=lambda *args: None, event=AsyncMock()
    )
    artifact = PieceArtifact(uuid4(), "synthetic/video.mp4", "a" * 64, "video/mp4", 10)
    args = ({"id": run, "actor_id": actor}, token, 0, operation, artifact, "c", "e", "d")
    if failure == "57014":
        with pytest.raises(AuthError, match="CREATION_LAB_RENDER_EVIDENCE_TIMEOUT"):
            await target.persist_render(*args)
    elif failure:
        with pytest.raises(DBAPIError):
            await target.persist_render(*args)
    else:
        await target.persist_render(*args)
        assert sum("INSERT INTO creation_lab_trace" in sql for sql, _ in events) == 3
        assert events[-1][0] == "SET LOCAL statement_timeout = '10s'"
        target.execution.event.assert_awaited_once()
    assert events[1][0] == "SET LOCAL statement_timeout = '60s'"
    if failure:
        target.execution.event.assert_not_awaited()


async def test_foreign_run_is_rejected_before_decrypting():
    target = object.__new__(LabMotionOrchestrator)
    target.run_id = uuid4()
    with pytest.raises(AuthError, match="CREATION_LAB_RUN_MISMATCH"):
        await target.persist_render({"id": uuid4()}, uuid4(), 0, uuid4(), None, "c", "e", "d")
