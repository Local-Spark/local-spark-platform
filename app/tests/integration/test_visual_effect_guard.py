"""Concrete owner/worker guard with PostgreSQL and an injected image stub."""

import asyncio
import hashlib
import io
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import text

from app.adapters.visual_ai import VisualResult
from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_brand_finish import VisualBrandFinishService
from app.services.visual_cost_ledger import VisualCostLedger
from app.services.visual_effect_guard import DatabaseVisualEffectGuard
from app.services.visual_provider_execution import VisualSubmissionClaims
from app.services.visual_real_orchestrator import VisualRealOrchestrator, VisualRunScope
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


@pytest.fixture
async def guarded_case(admin, database, seeded, settings):
    tenant, business, actor, catalog, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
        }
    )
    worker = Database(cfg, correlator=True)
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    owner_media = MediaPreviewService(cfg, database, store)
    request = PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake")
    preview = await owner_media.request_candidate(tenant, business, actor, request)
    claim = (await claim_previews(worker, uuid4()))[0]
    scope = VisualRunScope(
        tenant,
        business,
        actor,
        preview.id,
        admission.proposal,
        request.operation_id,
        claim.fence,
        True,
        admission.fingerprint,
        visual_recipe=preview.visual_recipe,
    )
    output = io.BytesIO()
    Image.new("RGB", (1024, 1280), "navy").save(output, format="PNG")
    data = output.getvalue()
    result = VisualResult(data, "image/png", hashlib.sha256(data).hexdigest(), 1024, 1280, None, None)
    provider = SimpleNamespace(generate=AsyncMock(return_value=result))
    guard = DatabaseVisualEffectGuard(cfg, database, worker, reserved_usd_micros=70)
    ledger = VisualCostLedger(cfg, worker)
    service = VisualRealOrchestrator(
        guard=guard,
        brand=VisualBrandFinishService(cfg, database, store),
        provider=provider,
        ledger=ledger,
        claims=guard.claims,
        store=store,
        signing_key=cfg.meta_encryption_key.get_secret_value(),
    )
    try:
        yield SimpleNamespace(
            tenant=tenant,
            business=business,
            actor=actor,
            catalog=catalog,
            cfg=cfg,
            worker=worker,
            store=store,
            owner_media=owner_media,
            preview=preview,
            scope=scope,
            provider=provider,
            guard=guard,
            ledger=ledger,
            service=service,
            result=result,
        )
    finally:
        await worker.close()


async def _run_state(database, c):
    async with database.transaction(c.tenant, c.actor) as session:
        return await session.scalar(
            text("SELECT state FROM visual_consent_runs WHERE preview_id=:id"), {"id": c.preview.id}
        )


async def test_concrete_guard_completes_private_preview_once_and_keeps_unknown_cost(admin, database, guarded_case):
    c = guarded_case
    assert await c.service.run(c.scope) == "completed"
    assert await c.service.run(c.scope) == "not_started"
    c.provider.generate.assert_awaited_once()
    c.store.put.assert_awaited_once()
    c.store.delete.assert_not_awaited()
    assert await _run_state(database, c) == "finished"
    key = await c.owner_media.file_key(c.tenant, c.business, c.actor, c.preview.id, review=True)
    assert key == c.store.put.await_args.args[0]
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"
        assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 1


async def test_concrete_guard_defers_source_change_until_provider_response(admin, database, guarded_case):
    c = guarded_case
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(_):
        entered.set()
        await release.wait()
        return c.result

    c.provider.generate.side_effect = generate
    task = asyncio.create_task(c.service.run(c.scope))
    try:
        await asyncio.wait_for(entered.wait(), 10)
        c.catalog["expected_version"], c.catalog["operation_id"] = 1, str(uuid4())
        c.catalog["offerings"][0]["name"] = "Novo croissant"
        pending = await BusinessCatalogService(database).update(
            c.tenant, c.business, c.actor, CatalogUpdate.model_validate(c.catalog)
        )
        assert pending.version == 1 and pending.pending_change is not None
        with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
            await c.owner_media.request_candidate(
                c.tenant,
                c.business,
                c.actor,
                PreviewRequest(
                    operation_id=uuid4(),
                    proposal_id=c.scope.proposal,
                    generation_mode="visual_fake",
                ),
            )
    finally:
        release.set()
    assert await asyncio.wait_for(task, 20) == "completed"
    assert (await BusinessCatalogService(database).read(c.tenant, c.business, c.actor)).version == 2
    listed = await c.owner_media.list(c.tenant, c.business, c.actor)
    assert listed[0].created_before_change
    assert await c.owner_media.file_key(c.tenant, c.business, c.actor, c.preview.id, review=True)


@pytest.mark.parametrize("mutation", ["blocked", "revoked", "membership", "user"])
async def test_access_change_after_owner_proof_blocks_worker_claim(
    admin, database, guarded_case, monkeypatch, mutation
):
    c = guarded_case
    original = VisualSubmissionClaims.claim

    async def mutate(self, *args, **kwargs):
        assert kwargs["admitted_at"] is not None
        async with admin.begin() as connection:
            params = {"tenant": c.tenant, "actor": c.actor}
            if mutation == "blocked":
                await connection.execute(
                    text("UPDATE billing_accounts SET blocked=true WHERE tenant_id=:tenant"), params
                )
                # The fixture uses sponsorship. Explicit financial blocking must
                # remain distinct even when that sponsorship has not expired.
                await connection.execute(
                    text("""INSERT INTO billing_accounts(tenant_id,livemode,blocked)
                  VALUES(:tenant,false,true) ON CONFLICT(tenant_id,livemode) DO UPDATE SET blocked=true"""),
                    params,
                )
            elif mutation == "revoked":
                await connection.execute(
                    text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"), params
                )
            elif mutation == "membership":
                await connection.execute(
                    text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"), params
                )
            else:
                await connection.execute(text("UPDATE user_accounts SET active=false WHERE id=:actor"), params)
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(VisualSubmissionClaims, "claim", mutate)
    assert await c.service.run(c.scope) == "uncertain"
    c.provider.generate.assert_not_awaited()
    c.store.put.assert_not_awaited()
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT state FROM visual_consent_runs")) == "in_flight"
        assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "submitted"
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 0


async def test_financial_expiry_after_admission_allows_completion_not_new_creation(
    admin, database, guarded_case, monkeypatch
):
    c = guarded_case
    original = c.guard.admit

    async def expire(scope):
        admitted = await original(scope)
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE billing_sponsorships SET starts_at=now()-interval '2 days',"
                    " ends_at=now()-interval '1 second' WHERE tenant_id=:tenant"
                ),
                {"tenant": c.tenant},
            )
        return admitted

    monkeypatch.setattr(c.guard, "admit", expire)
    assert await c.service.run(c.scope) == "completed"
    assert await c.owner_media.file_key(c.tenant, c.business, c.actor, c.preview.id, review=True)
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        await c.owner_media.request_candidate(
            c.tenant,
            c.business,
            c.actor,
            PreviewRequest(
                operation_id=uuid4(),
                proposal_id=c.scope.proposal,
                generation_mode="visual_fake",
            ),
        )
    c.provider.generate.assert_awaited_once()


async def test_lost_reservation_acknowledgement_preserves_admission_and_hold(
    admin, database, guarded_case, monkeypatch
):
    from app.services.visual_attempts import VisualAttemptService

    c = guarded_case
    original = VisualAttemptService.reserve

    async def lose(self, *args, **kwargs):
        await original(self, *args, **kwargs)
        raise RuntimeError("lost reservation commit")

    monkeypatch.setattr(VisualAttemptService, "reserve", lose)
    with pytest.raises(RuntimeError, match="lost reservation commit"):
        await c.service.run(c.scope)
    assert await _run_state(database, c) == "in_flight"
    c.provider.generate.assert_not_awaited()
    assert await c.service.run(c.scope) == "not_started"
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 1
        assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70


async def test_budget_rejection_has_proven_abort_and_never_calls_provider(admin, database, guarded_case):
    from app.services.visual_cost_ledger import VisualCostError

    c = guarded_case
    c.guard.reserved_usd_micros = 101
    with pytest.raises(VisualCostError, match="VISUAL_BUDGET_EXCEEDED"):
        await c.service.run(c.scope)
    assert await _run_state(database, c) == "finished"
    c.provider.generate.assert_not_awaited()
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 0


async def test_concurrent_orchestrators_and_cross_tenant_scope_cannot_duplicate(admin, database, guarded_case, seeded):
    c = guarded_case
    other = replace(c.scope, tenant=seeded["t2"], actor=seeded["a2"])
    assert await c.service.run(other) == "not_started"
    results = await asyncio.gather(c.service.run(c.scope), c.service.run(c.scope))
    assert sorted(results) == ["completed", "not_started"]
    c.provider.generate.assert_awaited_once()


async def test_known_late_response_stops_replacement_fence_and_releases_source_change(admin, database, guarded_case):
    c = guarded_case
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(_):
        entered.set()
        await release.wait()
        return c.result

    c.provider.generate.side_effect = generate
    task = asyncio.create_task(c.service.run(c.scope))
    try:
        await asyncio.wait_for(entered.wait(), 10)
        c.catalog["expected_version"], c.catalog["operation_id"] = 1, str(uuid4())
        c.catalog["offerings"][0]["name"] = "Croissant atualizado"
        pending = await BusinessCatalogService(database).update(
            c.tenant, c.business, c.actor, CatalogUpdate.model_validate(c.catalog)
        )
        assert pending.pending_change is not None
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE media_previews SET dispatch_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": c.preview.id},
            )
        replacement = (await claim_previews(c.worker, uuid4()))[0]
        assert replacement.fence > c.scope.fence
    finally:
        release.set()
    assert await asyncio.wait_for(task, 20) == "stale"
    assert await _run_state(database, c) == "finished"
    assert (await BusinessCatalogService(database).read(c.tenant, c.business, c.actor)).version == 2
    assert await c.service.run(replace(c.scope, fence=replacement.fence)) == "not_started"
    c.provider.generate.assert_awaited_once()
    c.store.put.assert_not_awaited()


@pytest.mark.parametrize("lost_commit", ["claim", "output"])
async def test_unknown_claim_or_output_commit_never_retries_or_deletes_possible_result(
    admin, database, guarded_case, monkeypatch, lost_commit
):
    c = guarded_case
    target, name = (c.guard.claims, "claim") if lost_commit == "claim" else (c.guard, "commit")
    original = getattr(target, name)

    async def lost_ack(*args, **kwargs):
        assert await original(*args, **kwargs)
        raise RuntimeError("commit acknowledgement lost")

    monkeypatch.setattr(target, name, lost_ack)
    with pytest.raises(RuntimeError, match="commit acknowledgement lost"):
        await c.service.run(c.scope)
    assert await _run_state(database, c) == "in_flight"
    assert await c.service.run(c.scope) == "not_started"
    assert c.provider.generate.await_count == int(lost_commit == "output")
    c.store.delete.assert_not_awaited()
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        assert await connection.scalar(text("SELECT object_key FROM media_previews")) == (
            c.store.put.await_args.args[0] if lost_commit == "output" else None
        )
