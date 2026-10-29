"""An unreserved simulation closes only after an acknowledged terminal proof."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services import visual_admission_recovery as recovery
from app.services.auth import AuthError


def _setup(settings, monkeypatch):
    ids = tuple(uuid4() for _ in range(5))
    tenant, business, actor, preview, operation = ids
    row = {
        "id": preview,
        "tenant_id": tenant,
        "business_id": business,
        "actor_id": actor,
        "operation_id": operation,
        "state": "rendering",
        "object_key": None,
        "sha256": None,
        "error_code": None,
    }
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    owner_session = SimpleNamespace(scalar=AsyncMock(return_value=7))
    worker_session = SimpleNamespace(execute=AsyncMock(return_value=result), scalar=AsyncMock(side_effect=[True, None]))
    events = []
    faults = SimpleNamespace(owner_commit=None, worker_commit=None)

    @asynccontextmanager
    async def owner_transaction(*_args):
        events.append("owner.begin")
        yield owner_session
        events.append("owner.commit")
        if faults.owner_commit is not None:
            raise faults.owner_commit

    @asynccontextmanager
    async def worker_transaction(*_args):
        events.append("worker.begin")
        yield worker_session
        events.append("worker.commit")
        if faults.worker_commit is not None:
            raise faults.worker_commit

    async def finish(*_args):
        events.append("gate.finish")

    owner = SimpleNamespace(transaction=MagicMock(side_effect=owner_transaction))
    worker = SimpleNamespace(transaction=MagicMock(side_effect=worker_transaction))
    gate = SimpleNamespace(_lock=AsyncMock(), finish=AsyncMock(side_effect=finish))
    audit = AsyncMock()
    monkeypatch.setattr(recovery, "VisualConsentGate", MagicMock(return_value=gate))
    monkeypatch.setattr(recovery, "_audit", audit)
    cfg = settings.model_copy(update={"environment": "testing", "visual_ai_mode": "fake"})
    service = recovery.VisualAdmissionRecovery(cfg, worker, owner)
    return SimpleNamespace(
        service=service,
        owner=owner,
        worker=worker,
        owner_session=owner_session,
        worker_session=worker_session,
        result=result,
        row=row,
        ids=ids,
        gate=gate,
        audit=audit,
        events=events,
        faults=faults,
    )


@pytest.mark.parametrize(
    "environment,mode", [("production", "fake"), ("staging", "fake"), ("testing", "off"), ("development", "openai")]
)
async def test_only_local_fake_can_recover_without_touching_pools(settings, monkeypatch, environment, mode):
    context = _setup(settings, monkeypatch)
    context.service.settings = context.service.settings.model_copy(
        update={"environment": environment, "visual_ai_mode": mode}
    )
    assert not await context.service.recover(*context.ids)
    context.owner.transaction.assert_not_called()
    context.worker.transaction.assert_not_called()
    context.gate.finish.assert_not_awaited()


async def test_missing_admission_has_no_worker_side_effect(settings, monkeypatch):
    context = _setup(settings, monkeypatch)
    context.owner_session.scalar.return_value = None
    assert not await context.service.recover(*context.ids)
    context.worker.transaction.assert_not_called()
    context.gate.finish.assert_not_awaited()
    query, params = context.owner_session.scalar.await_args.args
    assert "preview_id=:preview AND operation_id=:operation" in str(query)
    assert params["actor"] == context.ids[2]


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"state": "pending"},
        {"state": "completed"},
        {"state": "purging"},
        {"object_key": "private/result.png"},
        {"sha256": "a" * 64},
    ],
)
async def test_missing_or_ineligible_preview_cannot_become_abort_proof(settings, monkeypatch, change):
    context = _setup(settings, monkeypatch)
    if change is None:
        context.result.mappings.return_value.one_or_none.return_value = None
    else:
        context.row.update(change)
    assert not await context.service.recover(*context.ids)
    context.worker_session.scalar.assert_not_awaited()
    context.gate.finish.assert_not_awaited()
    context.audit.assert_not_awaited()
    assert context.worker_session.execute.await_count == 1
    query = str(context.worker_session.execute.await_args.args[0])
    assert "generation_mode='visual_fake' FOR UPDATE" in query


async def test_live_or_older_fence_remains_blocking(settings, monkeypatch):
    context = _setup(settings, monkeypatch)
    context.worker_session.scalar.side_effect = [None]
    assert not await context.service.recover(*context.ids)
    query, params = context.worker_session.scalar.await_args.args
    assert "dispatch_fence>=:fence" in str(query)
    assert "dispatch_fence>:fence" in str(query)
    assert "dispatch_lease_until<=clock_timestamp()" in str(query)
    assert params["fence"] == 7
    context.audit.assert_not_awaited()
    context.gate.finish.assert_not_awaited()
    assert context.worker_session.execute.await_count == 1


async def test_attempt_or_unbound_reservation_prevents_release(settings, monkeypatch):
    context = _setup(settings, monkeypatch)
    context.worker_session.scalar.side_effect = [True, 1]
    assert not await context.service.recover(*context.ids)
    context.audit.assert_not_awaited()
    context.gate.finish.assert_not_awaited()
    assert context.worker_session.execute.await_count == 2
    lock_query, lock_params = context.worker_session.execute.await_args.args
    assert "pg_advisory_xact_lock" in str(lock_query) and lock_params == {"key": str(context.ids[0])}
    proof_query, params = context.worker_session.scalar.await_args.args
    assert "FROM visual_ai_attempts" in str(proof_query)
    assert "preview_id=:preview OR operation_id=:operation" in str(proof_query)
    assert "FROM visual_cost_reservations" in str(proof_query)
    assert params["operation"] == context.ids[4]


@pytest.mark.parametrize("state", ["rendering", "failed"])
async def test_terminal_proof_commits_before_original_owner_finishes(settings, monkeypatch, state):
    context = _setup(settings, monkeypatch)
    context.row["state"] = state
    assert await context.service.recover(*context.ids)
    assert context.events == ["owner.begin", "owner.commit", "worker.begin", "worker.commit", "gate.finish"]
    assert context.worker_session.execute.await_count == 3
    query = str(context.worker_session.execute.await_args.args[0])
    assert "state='failed',error_code='VISUAL_ADMISSION_ABORTED'" in query
    assert "dispatch_owner=NULL,dispatch_lease_until=NULL" in query
    tenant, business, actor, _, operation = context.ids
    context.gate.finish.assert_awaited_once_with(tenant, business, actor, operation, 7)
    context.audit.assert_awaited_once_with(context.worker_session, context.row, "visual.unreserved_admission_aborted")


async def test_repeating_terminal_proof_only_retries_owner_finish(settings, monkeypatch):
    context = _setup(settings, monkeypatch)
    context.row.update(state="failed", error_code="VISUAL_ADMISSION_ABORTED")
    assert await context.service.recover(*context.ids)
    assert context.worker_session.execute.await_count == 2
    context.audit.assert_not_awaited()
    context.gate.finish.assert_awaited_once()


@pytest.mark.parametrize("commit", ["owner_commit", "worker_commit"])
async def test_lost_commit_acknowledgement_never_finishes_owner_admission(settings, monkeypatch, commit):
    context = _setup(settings, monkeypatch)
    setattr(context.faults, commit, RuntimeError("commit acknowledgement lost"))
    with pytest.raises(RuntimeError, match="commit acknowledgement lost"):
        await context.service.recover(*context.ids)
    context.gate.finish.assert_not_awaited()
    if commit == "owner_commit":
        context.worker.transaction.assert_not_called()
    else:
        # The first commit may have succeeded. A subsequent invocation uses its
        # durable terminal marker instead of modifying or auditing it again.
        context.row.update(state="failed", error_code="VISUAL_ADMISSION_ABORTED")
        context.worker_session.scalar.side_effect = [True, None]
        context.faults.worker_commit = None
        assert await context.service.recover(*context.ids)
        context.gate.finish.assert_awaited_once()
        context.audit.assert_awaited_once()


async def test_lost_owner_access_cannot_cross_to_worker_recovery(settings, monkeypatch):
    context = _setup(settings, monkeypatch)
    context.gate._lock.side_effect = AuthError("BUSINESS_OWNER_REQUIRED", 403)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await context.service.recover(*context.ids)
    context.worker.transaction.assert_not_called()
    context.gate.finish.assert_not_awaited()
