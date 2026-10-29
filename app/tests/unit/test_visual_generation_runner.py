"""Persisted mode/fence select a guarded effect; uncertainty never grants retry."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.material_media import MaterialStore
from app.adapters.visual_ai import OpenAIVisualProvider
from app.services import visual_generation_runner as module
from app.services.auth import AuthError


def _enabled(settings):
    return settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 100,
            "visual_ai_monthly_budget_usd_micros": 200,
            "visual_ai_global_monthly_budget_usd_micros": 300,
            "openai_api_key": SecretStr("synthetic-unused"),
            "meta_encryption_key": SecretStr("synthetic-signing-key"),
            "service_agreement_required": True,
            "correlator_database_url": settings.database_url,
        }
    )


def _mapped(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    return result


@pytest.fixture
def case(settings, monkeypatch):
    row = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "actor_id": uuid4(),
        "proposal_id": uuid4(),
        "operation_id": uuid4(),
        "candidate": True,
        "visual_fingerprint": "a" * 64,
        "generation_mode": "visual_ai",
        "dispatch_fence": 2,
        "state": "rendering",
    }
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = _mapped(row)

    @asynccontextmanager
    async def sessions(*_args):
        yield session

    database = SimpleNamespace(sessions=sessions, transaction=sessions)
    orchestrator = SimpleNamespace(run=AsyncMock(return_value="completed"))
    constructor = MagicMock(return_value=orchestrator)
    recovery = SimpleNamespace(recover=AsyncMock(return_value=False))
    monkeypatch.setattr(module, "VisualRealOrchestrator", constructor)
    monkeypatch.setattr(module, "VisualAdmissionRecovery", MagicMock(return_value=recovery))
    audit = AsyncMock()
    monkeypatch.setattr(module, "_audit", audit)
    provider, store = AsyncMock(), AsyncMock()
    cfg = _enabled(settings)
    runner = module.DatabaseVisualGenerationRunner(cfg, database, database, provider=provider, store=store)
    return SimpleNamespace(
        cfg=cfg,
        row=row,
        session=session,
        database=database,
        orchestrator=orchestrator,
        constructor=constructor,
        recovery=recovery,
        provider=provider,
        store=store,
        audit=audit,
        runner=runner,
    )


async def test_persisted_identity_builds_complete_guarded_runner(case):
    c = case
    assert await c.runner.run_preview(c.row["id"], 2) == "completed"
    scope = c.orchestrator.run.await_args.args[0]
    assert scope.preview == c.row["id"] and scope.operation == c.row["operation_id"]
    assert scope.tenant == c.row["tenant_id"] and scope.business == c.row["business_id"]
    assert scope.actor == c.row["actor_id"] and scope.proposal == c.row["proposal_id"]
    assert scope.fence == 2 and scope.candidate is True and scope.fingerprint == "a" * 64
    bindings = c.constructor.call_args.kwargs
    assert bindings["guard"].generation_mode == "visual_ai"
    assert bindings["guard"].reserved_usd_micros == 100
    assert bindings["claims"].guard is bindings["guard"]
    assert bindings["brand"].store is c.store and bindings["store"] is c.store
    assert bindings["provider"] is c.provider
    assert bindings["ledger"].database is c.database
    c.recovery.recover.assert_not_awaited()
    c.audit.assert_not_awaited()


def test_default_adapters_are_constructed_without_io(case):
    transport = httpx.MockTransport(lambda _: pytest.fail("constructor cannot call HTTP"))
    runner = module.DatabaseVisualGenerationRunner(case.cfg, case.database, case.database, transport=transport)
    bindings = case.constructor.call_args.kwargs
    assert isinstance(bindings["provider"], OpenAIVisualProvider)
    assert bindings["provider"]._transport is transport
    assert isinstance(runner.store, MaterialStore)


async def test_disabled_execution_never_reads_persisted_request(case):
    case.runner.settings = case.cfg.model_copy(update={"visual_ai_execution_enabled": False})
    with pytest.raises(AuthError, match="VISUAL_EXECUTION_DISABLED"):
        await case.runner.run_preview(case.row["id"], 2)
    case.session.execute.assert_not_awaited()
    with pytest.raises(AuthError, match="VISUAL_EXECUTION_DISABLED"):
        module.DatabaseVisualGenerationRunner(case.runner.settings, case.database, case.database)


@pytest.mark.parametrize("change", ["missing", "legacy", "fence", "completed", "failed", "pending"])
async def test_stale_duplicate_and_legacy_rows_never_construct_an_effect(case, change):
    row = dict(case.row)
    expected = "stale"
    if change == "missing":
        row = None
    elif change == "legacy":
        row["generation_mode"] = "visual_fake"
    elif change == "fence":
        row["dispatch_fence"] = 3
    else:
        row["state"] = expected = change
    case.session.execute.return_value = _mapped(row)
    assert await case.runner.run_preview(case.row["id"], 2) == expected
    case.orchestrator.run.assert_not_awaited()
    case.audit.assert_not_awaited()


@pytest.mark.parametrize("outcome", ["stale", "not_started"])
async def test_unstarted_run_uses_absence_proof_without_releasing_live_duplicate(case, outcome):
    case.orchestrator.run.return_value = outcome
    assert await case.runner.run_preview(case.row["id"], 2) == outcome
    case.recovery.recover.assert_awaited_once_with(
        case.row["tenant_id"],
        case.row["business_id"],
        case.row["actor_id"],
        case.row["id"],
        module.visual_operation(case.row["id"]),
    )
    case.audit.assert_not_awaited()


@pytest.mark.parametrize("failure", [None, RuntimeError("private provider detail"), asyncio.CancelledError()])
@pytest.mark.parametrize("still_current", [False, True])
async def test_unknown_outcome_projects_only_its_current_fence_and_preserves_hold(case, failure, still_current):
    case.orchestrator.run.return_value = "uncertain"
    case.orchestrator.run.side_effect = failure
    case.session.execute.side_effect = [_mapped(case.row), _mapped(case.row if still_current else None)]
    if isinstance(failure, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await case.runner.run_preview(case.row["id"], 2)
    else:
        assert await case.runner.run_preview(case.row["id"], 2) == "uncertain"
    projection = case.session.execute.await_args
    assert "state='rendering' AND dispatch_fence=:fence" in str(projection.args[0])
    assert "VISUAL_OUTCOME_UNCERTAIN" in str(projection.args[0])
    assert case.audit.await_count == int(still_current)
    case.recovery.recover.assert_not_awaited()
    case.provider.generate.assert_not_awaited()
