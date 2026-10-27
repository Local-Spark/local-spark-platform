"""Integrated owner consent, durable billing and Jev briefing; no external calls."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.jev_intent_ai import JevDecision, JevIntentError
from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.editorial_proposals import EditorialProposalService
from app.services.intent_usage import reserve_intent
from app.services.jev_consent import JevConsentService
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("outcome", ["selected", "price", "uncertain", "unconsented", "budget"])
async def test_jev_requires_consent_and_budget_and_never_repeats_paid_effect(
    admin, database, seeded, settings, monkeypatch, outcome
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "typesafe_api_key": SecretStr("synthetic"),
            "intent_ai_mode": "jev",
            "intent_ai_model": "jev-1.14.0",
            "intent_ai_daily_budget_usd_micros": 1 if outcome == "budget" else 3000,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])
    consent = JevConsentService(cfg, database)
    assert await consent.status(tenant, business, actor) == {"accepted": False, "provider_enabled": True}
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await consent.status(tenant, business, seeded["viewer"])
    if outcome != "unconsented":
        assert (await consent.set(tenant, business, actor, True))["accepted"] is True
        assert (await consent.set(tenant, business, actor, True))["accepted"] is True
        assert (await consent.status(tenant, business, actor))["accepted"] is True
    call = AsyncMock(
        side_effect=JevIntentError("unknown") if outcome == "uncertain" else None,
        return_value=JevDecision(
            "price" if outcome == "price" else "content_request", "selected", item, "photo", 720, 15
        ),
    )
    monkeypatch.setattr("app.services.jev_interpreter.JevIntentProvider", lambda *args: SimpleNamespace(interpret=call))
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker)
        first = await activity.request_candidate_proposal(str(source))
        second = await activity.request_candidate_proposal(str(source))
        if outcome == "selected":
            assert UUID(first) and second == first
            assert call.await_count == 1
        elif outcome == "price":
            assert first == second == "briefing_needs_clarification"
            assert call.await_count == 1
        elif outcome == "uncertain":
            assert first == second == "briefing_unavailable"
            assert call.await_count == 1
        else:
            assert first in {"skipped", "briefing_unavailable"}
            assert second == first
            call.assert_not_awaited()
        async with admin.connect() as conn:
            rows = (
                (
                    await conn.execute(
                        text("SELECT * FROM editorial_intent_usage WHERE tenant_id=:tenant"), {"tenant": tenant}
                    )
                )
                .mappings()
                .all()
            )
            if outcome in {"unconsented", "budget"}:
                assert not rows
            else:
                assert len(rows) == 1 and rows[0]["reserved_micros"] == 2688
                assert rows[0]["state"] == ("uncertain" if outcome == "uncertain" else "completed")
                assert rows[0]["estimated_micros"] == (None if outcome == "uncertain" else 31)
            if outcome == "selected":
                row = (await conn.execute(text("SELECT intent_kind,suggested_format FROM editorial_briefings"))).one()
                assert tuple(row) == ("content_request", "photo")
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM editorial_intent_usage")) == 0
        if outcome == "selected":
            # Switching off Jev must not accidentally replace its consent with
            # the separately granted OpenAI permission when reading a briefing.
            disabled = cfg.model_copy(update={"intent_ai_mode": "disabled"})
            owner = EditorialProposalService(disabled, database)
            assert (await owner.list(tenant, business, actor))[0].briefing.status == "prepared"
            assert (await JevConsentService(cfg, database).set(tenant, business, actor, False))["accepted"] is False
            assert (await owner.list(tenant, business, actor))[0].briefing.status == "unavailable"
    finally:
        await worker.close()


async def test_budget_reservation_serializes_competing_jobs_and_detects_replay(admin, database, seeded):
    import asyncio
    from uuid import uuid4

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    operations = [uuid4(), uuid4()]

    async def reserve(operation, digest="a" * 64):
        async with database.transaction(tenant, actor) as session:
            return await reserve_intent(
                session,
                tenant=tenant,
                business=business,
                actor=actor,
                operation=operation,
                request_hash=digest,
                model="jev-1.14.0",
                input_rate=42000,
                output_rate=0,
                max_input_tokens=64000,
                max_output_tokens=0,
                daily_limit=2688,
            )

    outcomes = await asyncio.gather(*(reserve(operation) for operation in operations), return_exceptions=True)
    assert sum(outcome is True for outcome in outcomes) == 1
    assert sum(isinstance(outcome, AuthError) and outcome.code == "INTENT_BUDGET_EXCEEDED" for outcome in outcomes) == 1
    winner = operations[outcomes.index(True)]
    assert await reserve(winner) is False
    with pytest.raises(AuthError, match="INTENT_OPERATION_CONFLICT"):
        await reserve(winner, "b" * 64)
