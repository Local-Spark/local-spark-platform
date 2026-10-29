"""Recover only proven unreserved simulations across the existing restricted roles."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_admission_recovery import VisualAdmissionRecovery
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


@pytest.fixture
async def recovery_case(admin, database, seeded, settings):
    tenant, business, actor, catalog, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    worker = Database(cfg, correlator=True)
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    preview = await MediaPreviewService(cfg, database, store).request_candidate(
        tenant,
        business,
        actor,
        PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
    )
    claim = (await claim_previews(worker, uuid4()))[0]
    operation = uuid5(NAMESPACE_URL, f"visual-preview:{preview.id}")
    gate = VisualConsentGate(database)
    assert await gate.admit(tenant, business, actor, preview.id, operation, claim.fence, admission=admission)
    try:
        yield SimpleNamespace(
            tenant=tenant,
            business=business,
            actor=actor,
            catalog=catalog,
            cfg=cfg,
            worker=worker,
            store=store,
            preview=preview,
            claim=claim,
            operation=operation,
            gate=gate,
            recovery=VisualAdmissionRecovery(cfg, worker, database),
            args=(tenant, business, actor, preview.id, operation),
            reserve_args=(tenant, business, actor, preview.id, claim.fence, operation, "fake", "test", "a" * 64, 70),
        )
    finally:
        await worker.close()


async def _expire(admin, case):
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE media_previews SET dispatch_lease_until=now()-interval '1 second' WHERE id=:id"),
            {"id": case.preview.id},
        )


async def _in_flight(database, case):
    async with database.transaction(case.tenant, case.actor) as session:
        return await session.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='in_flight'"))


async def test_crash_between_admission_and_reservation_recovers_on_redispatch(admin, database, recovery_case):
    c = recovery_case
    c.catalog["expected_version"], c.catalog["operation_id"] = 1, str(uuid4())
    c.catalog["offerings"][0]["name"] = "Croissant atualizado"
    pending = await BusinessCatalogService(database).update(
        c.tenant, c.business, c.actor, CatalogUpdate.model_validate(c.catalog)
    )
    assert pending.pending_change is not None and pending.version == 1
    # No acknowledgement of an owner admission permits a second execution.
    assert not await c.gate.admit(*c.args, c.claim.fence)
    assert not await c.recovery.recover(*c.args)
    await _expire(admin, c)
    claim = (await claim_previews(c.worker, uuid4()))[0]
    assert claim.fence > c.claim.fence
    renderer = MediaPreviewService(c.cfg, c.worker, c.store, database)
    assert await renderer.render(c.preview.id, claim.fence) == "failed"
    assert await _in_flight(database, c) == 0
    current = await BusinessCatalogService(database).read(c.tenant, c.business, c.actor)
    assert current.version == 2 and current.pending_change is None
    assert current.offerings[0].name == "Croissant atualizado"
    with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
        await VisualAttemptService(c.cfg, c.worker).reserve(*c.reserve_args)
    assert await renderer.render(c.preview.id, c.claim.fence) == "skipped"
    c.store.put.assert_not_awaited()
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM audit_events WHERE action='visual.unreserved_admission_aborted'")
            )
            == 1
        )


@pytest.mark.parametrize("lost_commit", ["worker", "owner"])
async def test_lost_recovery_commit_acknowledgement_repeats_only_reconciliation(
    admin, database, recovery_case, monkeypatch, lost_commit
):
    c = recovery_case
    await _expire(admin, c)
    if lost_commit == "worker":
        original = c.worker.transaction

        @asynccontextmanager
        async def lost_ack(*args):
            async with original(*args) as session:
                yield session
            raise RuntimeError("lost worker commit acknowledgement")

        monkeypatch.setattr(c.worker, "transaction", lost_ack)
    else:
        original = VisualConsentGate.finish

        async def lost_ack(self, *args, **kwargs):
            await original(self, *args, **kwargs)
            raise RuntimeError("lost owner commit acknowledgement")

        monkeypatch.setattr(VisualConsentGate, "finish", lost_ack)
    with pytest.raises(RuntimeError, match="commit acknowledgement"):
        await c.recovery.recover(*c.args)
    assert await _in_flight(database, c) == int(lost_commit == "worker")
    monkeypatch.undo()
    assert await c.recovery.recover(*c.args)
    assert await c.recovery.recover(*c.args)
    assert await _in_flight(database, c) == 0
    with pytest.raises(VisualCostError, match="VISUAL_PREVIEW_FENCE_INVALID"):
        await VisualAttemptService(c.cfg, c.worker).reserve(*c.reserve_args)
    async with admin.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM audit_events WHERE action='visual.unreserved_admission_aborted'")
            )
            == 1
        )


@pytest.mark.parametrize("financial_state", ["submitted", "uncertain", "unbound"])
async def test_financial_evidence_never_releases_admission(admin, database, recovery_case, financial_state):
    c = recovery_case
    ledger = VisualCostLedger(c.cfg, c.worker)
    if financial_state == "unbound":
        reservation = await ledger.reserve(c.tenant, c.business, c.actor, c.operation, "fake", "test", "a" * 64, 70)
    else:
        attempt = await VisualAttemptService(c.cfg, c.worker).reserve(*c.reserve_args)
        reservation = attempt.reservation
    if financial_state == "uncertain":
        await ledger.finish(c.tenant, c.actor, reservation.id, actual_usd_micros=None)
    await _expire(admin, c)
    assert not await c.recovery.recover(*c.args)
    assert await _in_flight(database, c) == 1
    with pytest.raises(VisualCostError, match="VISUAL_BUDGET_EXCEEDED"):
        await ledger.reserve(c.tenant, c.business, c.actor, uuid4(), "fake", "test", "b" * 64, 31)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT sum(reserved_usd_micros) FROM visual_cost_reservations")) == 70
    c.store.put.assert_not_awaited()


async def test_recovery_cannot_assume_another_owner_or_revoked_author(admin, database, recovery_case, seeded):
    c = recovery_case
    await _expire(admin, c)
    # Another active owner has data access, but cannot take over the run.
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": c.tenant, "actor": seeded["a2"]},
        )
    assert not await c.recovery.recover(c.tenant, c.business, seeded["a2"], c.preview.id, c.operation)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await c.recovery.recover(seeded["t2"], c.business, seeded["a2"], c.preview.id, c.operation)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": c.tenant, "actor": c.actor},
        )
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await c.recovery.recover(*c.args)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='in_flight'")) == 1


async def test_reservation_commit_before_recovery_is_preserved(admin, database, recovery_case, monkeypatch):
    c = recovery_case
    entered, release = asyncio.Event(), asyncio.Event()
    original = VisualAttemptService.reserve_in_transaction

    async def pause(self, *args):
        result = await original(self, *args)
        entered.set()
        await release.wait()
        return result

    monkeypatch.setattr(VisualAttemptService, "reserve_in_transaction", pause)
    task = asyncio.create_task(VisualAttemptService(c.cfg, c.worker).reserve(*c.reserve_args))
    recovery = None
    try:
        await asyncio.wait_for(entered.wait(), 5)
        # Recovery waits on the same preview lock; it cannot read an absent,
        # uncommitted attempt and release the admission ahead of this commit.
        recovery = asyncio.create_task(c.recovery.recover(*c.args))
        await asyncio.sleep(0.05)
        assert not recovery.done()
    finally:
        release.set()
    assert (await asyncio.wait_for(task, 5)).created
    assert not await asyncio.wait_for(recovery, 5)
    await _expire(admin, c)
    assert not await c.recovery.recover(*c.args)
    assert await _in_flight(database, c) == 1
