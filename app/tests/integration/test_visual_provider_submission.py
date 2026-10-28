"""Durable one-shot provider claims against PostgreSQL; never contacts a provider."""

import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.adapters.visual_ai import VisualRequest, VisualResult
from app.db.session import Database
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_context import VisualContextSnapshot
from app.services.visual_cost_ledger import VisualCostLedger
from app.services.visual_provider_execution import (
    VisualSubmissionClaims,
    VisualSubmissionError,
    VisualSubmissionIdentity,
    execute_visual_submission,
)
from app.services.visual_requests import PreparedVisualRequest, visual_request_digest
from app.tests.integration.test_visual_attempts import preview
from app.tests.integration.test_visual_cost_ledger import _business

pytestmark = pytest.mark.integration


async def _setup(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    item, operation = await preview(admin, tenant, business, actor), uuid4()
    cfg = settings.model_copy(
        update={"visual_ai_monthly_budget_usd_micros": 100, "visual_ai_global_monthly_budget_usd_micros": 100}
    )
    db = Database(cfg, correlator=True)
    request = VisualRequest(
        prompt="fictitious",
        model="gpt-image-2.5-flare-2026-09-08",
        quality="medium",
        size="1024x1280",
        output_format="png",
        request_id=uuid4(),
    )
    async with admin.connect() as conn:
        proposal = await conn.scalar(text("SELECT proposal_id FROM media_previews WHERE id=:id"), {"id": item})
    context = VisualContextSnapshot(tenant, business, proposal, uuid4(), uuid4(), "photo", 1, 0, 1, "a" * 64)
    digest = visual_request_digest("synthetic-key", context, (), request)
    prepared = PreparedVisualRequest(context, (), digest, request)
    identity = VisualSubmissionIdentity(tenant, business, actor, item, operation, 1, digest, "openai")
    attempt = await VisualAttemptService(cfg, db).reserve(
        tenant, business, actor, item, 1, operation, "openai", request.model, identity.request_hash, 70
    )
    return cfg, db, identity, prepared, attempt


async def test_concurrent_submit_has_one_external_call_and_keeps_uncertain_hold(admin, seeded, settings):
    cfg, db, identity, prepared, attempt = await _setup(admin, seeded, settings)
    request = prepared.request
    provider = MagicMock()
    output = VisualResult(b"synthetic", "image/png", "a" * 64, 1024, 1280, {"output_tokens": 1}, None)
    provider.generate = AsyncMock(return_value=output)
    claims = VisualSubmissionClaims(db)
    ledger = VisualCostLedger(cfg, db)
    try:
        assert not await claims.claim(
            replace(identity, fence=2), attempt.reservation.id, request.model, prepared.context.proposal_id
        )
        assert not await claims.claim(
            replace(identity, request_hash="b" * 64),
            attempt.reservation.id,
            request.model,
            prepared.context.proposal_id,
        )
        assert not await claims.claim(identity, attempt.reservation.id, "other-model", prepared.context.proposal_id)
        assert not await claims.claim(identity, attempt.reservation.id, request.model, uuid4())
        args = dict(
            identity=identity,
            prepared=prepared,
            signing_key="synthetic-key",
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
        results = await asyncio.gather(
            execute_visual_submission(**args), execute_visual_submission(**args), return_exceptions=True
        )
        assert sum(value is output for value in results) == 1
        assert sum(isinstance(value, VisualSubmissionError) for value in results) == 1
        provider.generate.assert_awaited_once()
        async with admin.connect() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            "SELECT state,actual_usd_micros FROM visual_cost_reservations WHERE tenant_id=:t AND id=:id"
                        ),
                        {"t": identity.tenant, "id": attempt.reservation.id},
                    )
                )
                .mappings()
                .one()
            )
            assert row["state"] == "uncertain" and row["actual_usd_micros"] is None
            assert (
                await conn.scalar(
                    text(
                        "SELECT count(*) FROM visual_cost_events WHERE tenant_id=:t "
                        "AND reservation_id=:id AND action='uncertain'"
                    ),
                    {"t": identity.tenant, "id": attempt.reservation.id},
                )
                == 1
            )
        assert not await claims.claim(identity, attempt.reservation.id, request.model, prepared.context.proposal_id)
    finally:
        await db.close()


async def test_failure_after_claim_cannot_cause_a_second_submission(admin, seeded, settings):
    cfg, db, identity, prepared, attempt = await _setup(admin, seeded, settings)
    provider = MagicMock()
    provider.generate = AsyncMock(side_effect=RuntimeError("synthetic provider failure"))
    claims, ledger = VisualSubmissionClaims(db), VisualCostLedger(cfg, db)
    args = dict(
        identity=identity,
        prepared=prepared,
        signing_key="synthetic-key",
        attempt=attempt,
        provider=provider,
        ledger=ledger,
        claims=claims,
    )
    try:
        with pytest.raises(RuntimeError, match="synthetic provider failure"):
            await execute_visual_submission(**args)
        with pytest.raises(VisualSubmissionError):
            await execute_visual_submission(**args)
        provider.generate.assert_awaited_once()
        async with admin.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT state FROM visual_cost_reservations WHERE tenant_id=:t AND id=:id"),
                    {"t": identity.tenant, "id": attempt.reservation.id},
                )
                == "uncertain"
            )
    finally:
        await db.close()


@pytest.mark.parametrize("mutation", ["deactivate", "change_role", "deactivate_user"])
async def test_owner_lost_after_reservation_cannot_claim_or_call_provider(admin, seeded, settings, mutation):
    cfg, db, identity, prepared, attempt = await _setup(admin, seeded, settings)
    provider = MagicMock()
    provider.generate = AsyncMock()
    params = {"tenant": identity.tenant, "actor": identity.actor}
    async with admin.begin() as conn:
        if mutation == "deactivate":
            await conn.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"), params
            )
        elif mutation == "change_role":
            await conn.execute(
                text("UPDATE memberships SET role='viewer' WHERE tenant_id=:tenant AND actor_id=:actor"), params
            )
        else:
            await conn.execute(text("UPDATE user_accounts SET active=false WHERE id=:actor"), params)
    try:
        with pytest.raises(VisualSubmissionError, match="VISUAL_SUBMISSION_NOT_NEW"):
            await execute_visual_submission(
                identity=identity,
                prepared=prepared,
                signing_key="synthetic-key",
                attempt=attempt,
                provider=provider,
                ledger=VisualCostLedger(cfg, db),
                claims=VisualSubmissionClaims(db),
            )
        provider.generate.assert_not_awaited()
        async with admin.connect() as conn:
            state = await conn.scalar(
                text("SELECT state FROM visual_cost_reservations WHERE tenant_id=:tenant AND id=:reservation"),
                {"tenant": identity.tenant, "reservation": attempt.reservation.id},
            )
            assert state == "submitted"
    finally:
        await db.close()
