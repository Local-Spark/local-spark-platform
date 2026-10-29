"""Canonical financial writes and visual admissions share the commercial lock."""

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.auth import AuthError
from app.services.billing import revoke_sponsorship
from app.services.billing_processor import BillingProcessor
from app.services.visual_admission import VisualAdmissionChecks
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_provider_execution import visual_continuation_allowed
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


async def _ready_subscription(admin, database, seeded, settings, billing_database):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    job = {"id": uuid4(), "tenant_id": tenant, "actor_id": actor}
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM billing_sponsorships WHERE tenant_id=:tenant"), {"tenant": tenant})
        await connection.execute(
            text("""INSERT INTO billing_accounts(tenant_id,livemode,status,paid_until)
              VALUES(:tenant,false,'active',now()+interval '1 day')"""),
            {"tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO billing_jobs(id,tenant_id,actor_id,livemode,kind,dedupe_key)
              VALUES(:id,:tenant_id,:actor_id,false,'reconcile',:key)"""),
            {**job, "key": f"synthetic-reconcile:{job['id']}"},
        )
    processor = BillingProcessor(settings, billing_database, AsyncMock())
    account = await processor.claim_account(tenant, False)
    return tenant, business, actor, admission, processor, account, job


@pytest.mark.parametrize("snapshot", [{"blocked": True}, {"status": "canceled"}])
async def test_financial_snapshot_waits_for_admission_commit(
    admin, database, billing_database, seeded, settings, monkeypatch, snapshot
):
    tenant, business, actor, admission, processor, account, job = await _ready_subscription(
        admin, database, seeded, settings, billing_database
    )
    entered, release, saving = asyncio.Event(), asyncio.Event(), asyncio.Event()
    original_validate = VisualAdmissionChecks.validate
    from app.services import billing_processor

    original_lock = billing_processor.lock_commercial_change

    async def paused_validation(self, *args):
        await original_validate(self, *args)
        entered.set()
        await release.wait()

    async def observed_save_lock(*args):
        saving.set()
        await original_lock(*args)

    monkeypatch.setattr(VisualAdmissionChecks, "validate", paused_validation)
    monkeypatch.setattr(billing_processor, "lock_commercial_change", observed_save_lock)
    admitted = asyncio.create_task(
        VisualConsentGate(database).admit(tenant, business, actor, uuid4(), uuid4(), 1, admission=admission)
    )
    saved = None
    try:
        await asyncio.wait_for(entered.wait(), 5)
        saved = asyncio.create_task(processor.save(job, account, {"status": "reconciled"}, snapshot))
        await asyncio.wait_for(saving.wait(), 5)
        assert not saved.done()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0
            assert await connection.scalar(text("SELECT NOT blocked AND status='active' FROM billing_accounts"))
    finally:
        release.set()
    assert await asyncio.wait_for(admitted, 5)
    await asyncio.wait_for(saved, 5)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='in_flight'")) == 1
        assert await connection.scalar(text("SELECT blocked OR status='canceled' FROM billing_accounts"))
        assert (
            await connection.scalar(text("SELECT count(*) FROM billing_audit WHERE action='billing.reconciled'")) == 1
        )
    processor.provider.assert_not_called()


async def test_revocation_waiting_since_before_admission_uses_actual_change_time(
    admin, database, seeded, settings, monkeypatch
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    staff, preview = seeded["a2"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": staff})
    from app.services import billing

    original_validate = VisualAdmissionChecks.validate
    original_lock = billing.lock_commercial_change
    admitted_lock, release, revoker_waiting = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def pause_admission(self, *args):
        await original_validate(self, *args)
        admitted_lock.set()
        await release.wait()

    async def observe_revocation_lock(*args):
        revoker_waiting.set()
        await original_lock(*args)

    monkeypatch.setattr(VisualAdmissionChecks, "validate", pause_admission)
    monkeypatch.setattr(billing, "lock_commercial_change", observe_revocation_lock)
    # Its transaction starts before admission. A transaction-time revoked_at
    # would therefore falsely classify this later revocation as historical.
    async with database.transaction(tenant, staff) as revoker:
        started_at = await revoker.scalar(text("SELECT transaction_timestamp()"))
        admitted = asyncio.create_task(
            VisualConsentGate(database).admit(tenant, business, actor, preview, uuid4(), 1, admission=admission)
        )
        revoked = None
        try:
            await asyncio.wait_for(admitted_lock.wait(), 5)
            revoked = asyncio.create_task(revoke_sponsorship(revoker, tenant, staff))
            await asyncio.wait_for(revoker_waiting.wait(), 5)
            assert not revoked.done()
        finally:
            release.set()
        assert await asyncio.wait_for(admitted, 5)
        await asyncio.wait_for(revoked, 5)
        revoked_at = await revoker.scalar(
            text("SELECT revoked_at FROM billing_sponsorships WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
        async with admin.connect() as connection:
            admitted_at = await connection.scalar(
                text("SELECT created_at FROM visual_consent_runs WHERE preview_id=:preview"), {"preview": preview}
            )
        assert started_at < admitted_at <= revoked_at
    worker = Database(admission.settings, correlator=True)
    try:
        async with worker.transaction(tenant, actor) as session:
            assert not await visual_continuation_allowed(session, tenant, admitted_at)
    finally:
        await worker.close()


@pytest.mark.parametrize("snapshot", [{"blocked": True}, {"status": "canceled"}])
async def test_financial_snapshot_committed_first_prevents_admission(
    admin, database, billing_database, seeded, settings, monkeypatch, snapshot
):
    tenant, business, actor, admission, processor, account, job = await _ready_subscription(
        admin, database, seeded, settings, billing_database
    )
    from app.services import billing_processor

    original_lock = billing_processor.lock_commercial_change
    original_validate = VisualAdmissionChecks.validate
    locked, release, validating = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def paused_save_lock(*args):
        await original_lock(*args)
        locked.set()
        await release.wait()

    async def observed_validation(self, *args):
        validating.set()
        await original_validate(self, *args)

    monkeypatch.setattr(billing_processor, "lock_commercial_change", paused_save_lock)
    monkeypatch.setattr(VisualAdmissionChecks, "validate", observed_validation)
    saved = asyncio.create_task(processor.save(job, account, {"status": "reconciled"}, snapshot))
    admitted = None
    try:
        await asyncio.wait_for(locked.wait(), 5)
        admitted = asyncio.create_task(
            VisualConsentGate(database).admit(tenant, business, actor, uuid4(), uuid4(), 1, admission=admission)
        )
        await asyncio.wait_for(validating.wait(), 5)
        assert not admitted.done()
    finally:
        release.set()
    await asyncio.wait_for(saved, 5)
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        await asyncio.wait_for(admitted, 5)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0
    processor.provider.assert_not_called()
