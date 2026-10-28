"""Read-only destination locking proof; no live provider calls."""

import asyncio
import hashlib
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.content_deliveries import ContentDeliveryService
from app.services.phone_verification import PhoneVerificationService
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_link import WhatsAppLinkService
from app.tests.integration.test_content_delivery import _candidate_case

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


async def test_restricted_role_row_locks_and_tenant_isolation(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
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
            assert await session.scalar(text("SELECT current_user")) == "meu_braco_direito_runtime"
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
            assert await session.scalar(text("SELECT current_user")) == "meu_braco_direito_router"
            assert not await session.scalar(
                text("SELECT has_column_privilege(current_user,'business_profiles','phone','SELECT')")
            )
    finally:
        await worker_db.close()
        await app_db.close()


async def test_phone_change_waits_for_simulated_delivery(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    reached, release = pause_final_worker_session(worker_db)
    delivered = changed = None
    try:
        service = ContentDeliveryService(cfg, app_db, worker_db)
        delivered = asyncio.create_task(service.record(event, preview))
        await asyncio.wait_for(reached.wait(), 2)
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
        for task in (delivered, changed):
            if task and not task.done():
                task.cancel()
        await worker_db.close()
        await app_db.close()


async def test_link_confirmation_waits_for_simulated_delivery(admin, seeded, settings, monkeypatch):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
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
        await asyncio.wait_for(reached.wait(), 2)
        confirmed = asyncio.create_task(linker.confirm(tenant, business, actor))
        await asyncio.sleep(0.15)
        assert not confirmed.done(), "link confirmation passed while destination was locked"
        release.set()
        assert await asyncio.wait_for(delivered, 2)
        assert (await asyncio.wait_for(confirmed, 2))["status"] == "linked"
    finally:
        release.set()
        for task in (delivered, confirmed):
            if task and not task.done():
                task.cancel()
        await worker_db.close()
        await app_db.close()


async def test_destination_lock_timeout_does_not_record_delivery(admin, seeded, settings):
    cfg, app_db, worker_db, tenant, business, actor, _, event, preview = await _candidate_case(admin, seeded, settings)
    try:
        async with app_db.transaction(tenant, actor) as blocker:
            await blocker.execute(
                text("SELECT phone FROM business_profiles WHERE tenant_id=:t AND business_id=:b FOR UPDATE"),
                {"t": tenant, "b": business},
            )
            with pytest.raises(DBAPIError):
                await asyncio.wait_for(ContentDeliveryService(cfg, app_db, worker_db).record(event, preview), 5)
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM content_deliveries WHERE source_event_id=:id"), {"id": event}
                )
                == 0
            )
    finally:
        await worker_db.close()
        await app_db.close()
