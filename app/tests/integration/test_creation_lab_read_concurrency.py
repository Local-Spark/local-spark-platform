"""Private readers overlap without bypassing writer fences or staff revocation."""

from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.creation_lab_execution import CreationLabExecution

pytestmark = pytest.mark.integration


async def test_readers_overlap_but_writers_remain_exclusive(admin, database, seeded, settings):
    actor, business, run = seeded["a1"], uuid4(), uuid4()
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
             instruction_ciphertext,budget_usd_micros,flow_version)
            VALUES(:run,:actor,:tenant,:business,:run,:hash,'reel','automatic',:cipher,3000000,2)"""),
            {
                "run": run,
                "actor": actor,
                "tenant": seeded["t1"],
                "business": business,
                "hash": "a" * 64,
                "cipher": execution.cipher.seal({"instruction": "Synthetic"}),
            },
        )
    action = "admin.creation_lab.storyboard.read"
    async with database.transaction(UUID(int=0), actor) as first:
        await execution.guard(first, actor, run, action, read_only=True)
        async with database.transaction(UUID(int=0), actor) as second:
            await second.execute(text("SET LOCAL lock_timeout = '200ms'"))
            assert (await execution.guard(second, actor, run, action, read_only=True))["id"] == run
            assert not await second.scalar(
                text("SELECT pg_try_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)}
            )
    async with database.transaction(UUID(int=0), actor) as writer:
        await execution.guard(writer, actor, run, "admin.creation_lab.checkpoint.decide")
        async with database.transaction(UUID(int=0), actor) as reader:
            assert not await reader.scalar(
                text("SELECT pg_try_advisory_xact_lock_shared(hashtextextended(:key,120))"), {"key": str(run)}
            )
    async with admin.begin() as session:
        assert (
            await session.scalar(text("SELECT count(*) FROM platform_audit WHERE action=:action"), {"action": action})
            == 2
        )
        await session.execute(text("UPDATE platform_staff SET active=false WHERE actor_id=:actor"), {"actor": actor})
    async with database.transaction(UUID(int=0), actor) as session:
        with pytest.raises(AuthError, match="CREATION_LAB_RUN_NOT_FOUND"):
            await execution.guard(session, actor, run, action, read_only=True)
