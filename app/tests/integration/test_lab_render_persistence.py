"""Bounded evidence writes on restricted PostgreSQL, never a project database."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_motion_output import LabMotionOrchestrator

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("stale", [False, True])
async def test_render_evidence_has_scoped_deadline_atomicity_and_fence(admin, database, seeded, settings, stale):
    actor, business, run, token, operation = (seeded["a1"], uuid4(), uuid4(), uuid4(), uuid4())
    settings.creation_lab_actor_id = actor
    settings.meta_encryption_key = SecretStr(Fernet.generate_key().decode())
    execution = CreationLabExecution(settings, database)
    async with admin.begin() as session:
        await session.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": actor})
        await session.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Synthetic','UTC')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        await session.execute(
            text("""INSERT INTO creation_lab_runs
            (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,
             instruction_ciphertext,budget_usd_micros,flow_version,state,execution_token)
            VALUES(:run,:actor,:tenant,:business,:run,:hash,'reel','automatic',:cipher,3000000,2,'running',:token)"""),
            {
                "run": run,
                "actor": actor,
                "tenant": seeded["t1"],
                "business": business,
                "hash": "a" * 64,
                "cipher": execution.cipher.seal({"fixture": True}),
                "token": token,
            },
        )
        await session.execute(
            text("""INSERT INTO creation_lab_effects(id,run_id,kind,request_hash,state,reserved_usd_micros)
            VALUES(:id,:run,'render',:hash,'received',0)"""),
            {"id": operation, "run": run, "hash": "a" * 64},
        )
    observed = []

    class EvidenceSession:
        def __init__(self, session):
            self.session = session

        def __getattr__(self, name):
            return getattr(self.session, name)

        async def execute(self, statement, params=None):
            if "INSERT INTO creation_lab_trace" in str(statement):
                observed.append(await self.session.scalar(text("SHOW statement_timeout")))
                assert await self.session.scalar(text("SHOW lock_timeout")) == "3s"
                if params["stage"] == "frames":
                    # Deterministically exceed the former 10s deadline in the real DB.
                    await self.session.execute(text("SELECT pg_sleep(10.1)"))
            return await self.session.execute(statement, params)

    @asynccontextmanager
    async def transaction(*args):
        async with database.transaction(*args) as session:
            yield EvidenceSession(session)
            assert await session.scalar(text("SHOW statement_timeout")) == "10s"

    target = object.__new__(LabMotionOrchestrator)
    target.run_id = run
    target.requests = SimpleNamespace(database=SimpleNamespace(transaction=transaction), context=execution.cipher)
    target.execution = execution
    artifact = PieceArtifact(uuid4(), "synthetic/video.mp4", "a" * 64, "video/mp4", 10)
    frames = {"frames": [{"png": "synthetic" * 131072}]}
    args = (
        {"id": run, "actor_id": actor},
        uuid4() if stale else token,
        0,
        operation,
        artifact,
        execution.cipher.seal({"composition": "synthetic"}),
        execution.cipher.seal(frames),
        execution.cipher.seal({"diagnostics": "synthetic"}),
    )
    if stale:
        with pytest.raises(AuthError, match="CREATION_LAB_EXECUTION_FENCED"):
            await target.persist_render(*args)
        assert not observed
    else:
        await target.persist_render(*args)
        assert observed == ["1min", "1min", "1min"]
    async with database.transaction(UUID(int=0), actor) as session:
        assert await session.scalar(text("SHOW statement_timeout")) == "10s"
        assert await session.scalar(
            text("SELECT count(*) FROM creation_lab_versions WHERE run_id=:run"), {"run": run}
        ) == (0 if stale else 1)
        rows = (
            (
                await session.execute(
                    text("SELECT stage,payload_ciphertext FROM creation_lab_trace WHERE run_id=:run"), {"run": run}
                )
            )
            .mappings()
            .all()
        )
        assert len(rows) == (0 if stale else 3)
        if not stale:
            assert (
                execution.cipher.open(next(r["payload_ciphertext"] for r in rows if r["stage"] == "frames"))["value"]
                == frames
            )
        assert await session.scalar(
            text("SELECT count(*) FROM creation_lab_events WHERE run_id=:run AND kind='artifact.recorded'"),
            {"run": run},
        ) == (0 if stale else 1)
    async with database.transaction(UUID(int=0), seeded["a2"]) as session:
        assert not await session.scalar(
            text("SELECT count(*) FROM creation_lab_versions WHERE run_id=:run"), {"run": run}
        )
