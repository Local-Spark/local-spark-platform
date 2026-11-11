"""Read-only destination locking proof; no live provider calls."""

import asyncio
import hashlib
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import make_url, text
from sqlalchemy.exc import DBAPIError

from app.services.content_deliveries import ContentDeliveryService
from app.services.phone_verification import PhoneVerificationService
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_link import WhatsAppLinkService
from app.tests.integration.test_content_delivery import _visual_candidate_case

pytestmark = pytest.mark.integration


def pause_final_worker_session(database):
    original = database.sessions
    reached, release = asyncio.Event(), asyncio.Event()
    count = 0

    @asynccontextmanager
    async def wrapper():
        nonlocal count
        count += 1
        # First reads event, second reads preview, third writes delivery.
        if count == 3:
            reached.set()
            await release.wait()
        async with original() as session:
            yield session

    database.sessions = wrapper
    return reached, release


async def wait_for_delivery_barrier(delivered, reached):
    """Bound preparation separately from the lock behavior under observation."""
    waiting = asyncio.create_task(reached.wait())
    try:
        done, _ = await asyncio.wait((delivered, waiting), timeout=60, return_when=asyncio.FIRST_COMPLETED)
        if not done:
            pytest.fail("delivery did not reach its lock-test barrier within the preparation deadline")
        if delivered in done:
            await delivered
            pytest.fail("delivery finished without reaching its lock-test barrier")
        assert waiting in done
    finally:
        if not waiting.done():
            waiting.cancel()
        await asyncio.gather(waiting, return_exceptions=True)


async def cancel_unfinished(*tasks):
    pending = [task for task in tasks if task is not None]
    for task in pending:
        if not task.done():
            task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


async def test_restricted_role_row_locks_and_tenant_isolation(admin, database, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview, _ = await _visual_candidate_case(
        admin, seeded, settings, database
    )
    other = uuid4()
    try:
        async with admin.begin() as conn:
            await conn.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:t,'Other','UTC')"),
                {"id": other, "t": seeded["t2"]},
            )
            await conn.execute(
                text("""INSERT INTO business_profiles(tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:t,:id,'Food','Rio','Test','+5511999999999','#6557ed')"""),
                {"id": other, "t": seeded["t2"]},
            )
        async with app_db.transaction(tenant, actor) as session:
            runtime_url = make_url(cfg.database_url.get_secret_value())
            assert await session.scalar(text("SELECT current_user")) == runtime_url.username
            assert not await session.scalar(
                text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user")
            )
            assert await session.scalar(
                text("SELECT phone FROM business_profiles WHERE tenant_id=:t AND business_id=:b FOR UPDATE"),
                {"t": tenant, "b": business},
            )
            assert await session.scalar(
                text("SELECT sender_hash FROM whatsapp_channel_links WHERE tenant_id=:t AND business_id=:b FOR UPDATE"),
                {"t": tenant, "b": business},
            )
            assert (
                await session.scalar(
                    text("SELECT phone FROM business_profiles WHERE tenant_id=:t AND business_id=:b FOR UPDATE"),
                    {"t": seeded["t2"], "b": other},
                )
                is None
            )
        async with worker_db.sessions() as session:
            worker_url = make_url(cfg.correlator_database_url.get_secret_value())
            assert await session.scalar(text("SELECT current_user")) == worker_url.username
            assert not await session.scalar(
                text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user")
            )
            assert not await session.scalar(
                text("SELECT has_column_privilege(current_user,'business_profiles','phone','SELECT')")
            )
    finally:
        await worker_db.close()
        await app_db.close()


async def test_phone_change_waits_for_simulated_delivery(admin, database, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview, _ = await _visual_candidate_case(
        admin, seeded, settings, database
    )
    reached, release = pause_final_worker_session(worker_db)
    delivered = changed = None
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivered = asyncio.create_task(service.record(event, preview))
        await wait_for_delivery_barrier(delivered, reached)
        changed = asyncio.create_task(
            PhoneVerificationService(cfg, app_db, AsyncMock()).update_phone(tenant, business, actor, "+5511888888888")
        )
        await asyncio.sleep(0.15)
        assert not changed.done(), "phone update passed while destination was locked"
        release.set()
        delivery_id = await asyncio.wait_for(delivered, 2)
        assert delivery_id is not None
        assert (await asyncio.wait_for(changed, 2))["destination"] == "+5511888888888"
        async with admin.connect() as conn:
            old_hash = await conn.scalar(
                text("SELECT recipient_hash FROM content_deliveries WHERE id=:id"), {"id": delivery_id}
            )
            assert old_hash == sender_hash(cfg, "+5511999999999")
            assert (
                await conn.scalar(
                    text("SELECT phone FROM business_profiles WHERE tenant_id=:t AND business_id=:b"),
                    {"t": tenant, "b": business},
                )
                == "+5511888888888"
            )
    finally:
        release.set()
        await cancel_unfinished(delivered, changed)
        await worker_db.close()
        await app_db.close()


async def test_link_confirmation_waits_for_simulated_delivery(admin, database, seeded, settings, monkeypatch):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview, _ = await _visual_candidate_case(
        admin, seeded, settings, database
    )
    cfg = cfg.model_copy(update={"meta_webhook_mode": "cloud"})
    token, request, proof = "synthetic-token", uuid4(), uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO whatsapp_link_challenges
          (tenant_id,business_id,actor_id,request_id,token_hash,sender_hash,state,expires_at)
          VALUES(:t,:b,:a,:r,:token,:sender,'pending',now()+interval '1 hour')"""),
            {
                "t": tenant,
                "b": business,
                "a": actor,
                "r": request,
                "token": hashlib.sha256(token.encode()).hexdigest(),
                "sender": sender_hash(cfg, "+5511999999999"),
            },
        )
    reached, release = pause_final_worker_session(worker_db)
    delivered = confirmed = None
    try:
        linker = WhatsAppLinkService(cfg, app_db, worker_db)
        monkeypatch.setattr(linker, "_find_proof", AsyncMock(return_value=proof))
        delivered = asyncio.create_task(ContentDeliveryService(cfg, app_db, worker_db).record(event, preview))
        await wait_for_delivery_barrier(delivered, reached)
        confirmed = asyncio.create_task(linker.confirm(tenant, business, actor))
        await asyncio.sleep(0.15)
        assert not confirmed.done(), "link confirmation passed while destination was locked"
        release.set()
        assert await asyncio.wait_for(delivered, 2)
        assert (await asyncio.wait_for(confirmed, 2))["status"] == "linked"
    finally:
        release.set()
        await cancel_unfinished(delivered, confirmed)
        await worker_db.close()
        await app_db.close()


async def test_destination_lock_timeout_does_not_record_delivery(admin, database, seeded, settings, monkeypatch):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview, _ = await _visual_candidate_case(
        admin, seeded, settings, database
    )
    original_transaction = app_db.transaction
    reached, release = asyncio.Event(), asyncio.Event()
    delivered = None

    @asynccontextmanager
    async def gated_transaction(tenant_id, actor_id):
        async with original_transaction(tenant_id, actor_id) as session:
            execute = session.execute

            async def gated_execute(statement, *args, **kwargs):
                sql = " ".join(str(statement).split())
                if "FROM business_profiles" in sql and "FOR UPDATE" in sql:
                    reached.set()
                    await release.wait()
                return await execute(statement, *args, **kwargs)

            monkeypatch.setattr(session, "execute", gated_execute)
            yield session

    try:
        async with app_db.transaction(tenant, actor) as blocker:
            await blocker.execute(
                text("SELECT phone FROM business_profiles WHERE tenant_id=:t AND business_id=:b FOR UPDATE"),
                {"t": tenant, "b": business},
            )
            monkeypatch.setattr(app_db, "transaction", gated_transaction)
            delivered = asyncio.create_task(ContentDeliveryService(cfg, app_db, worker_db).record(event, preview))
            # Preparatory reads are not part of the database lock-timeout proof.
            # Observe early completion too, so a missing lock never strands the barrier.
            await wait_for_delivery_barrier(delivered, reached)
            release.set()
            with pytest.raises(DBAPIError) as failure:
                await asyncio.wait_for(delivered, 5)
            assert failure.value.orig.sqlstate == "55P03"
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM content_deliveries WHERE source_event_id=:id"), {"id": event}
                )
                == 0
            )
    finally:
        release.set()
        await cancel_unfinished(delivered)
        await worker_db.close()
        await app_db.close()
