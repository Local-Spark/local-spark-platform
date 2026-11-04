"""Relay and deterministic workflow routing for local reference effects."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from temporalio.common import WorkflowIDReusePolicy

from app.services import outbox
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_effect import (
    ReferenceCostProjectionWorkflow,
    ReferenceEffectProjectionWorkflow,
    ReferenceEffectWorkflow,
)


def _event() -> BusinessEvent:
    return BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})


@pytest.mark.parametrize(
    "event_type,workflow_type,prefix",
    [
        ("reference.effect_requested", "ReferenceEffectWorkflow", "reference-effect"),
        ("reference.cost_changed", "ReferenceCostProjectionWorkflow", "reference-cost-projection"),
        ("reference.effect_completed", "ReferenceEffectProjectionWorkflow", "reference-effect-projection"),
    ],
)
async def test_relay_routes_reference_effect_events(monkeypatch, event_type, workflow_type, prefix):
    event = _event()
    item = outbox.ClaimedEvent(event, fencing_token=1, event_type=event_type)
    client = SimpleNamespace(start_workflow=AsyncMock())
    finished = AsyncMock(return_value=True)
    monkeypatch.setattr(outbox, "claim_events", AsyncMock(return_value=[item]))
    monkeypatch.setattr(outbox, "finish_event", finished)
    owner = uuid4()
    assert await outbox.dispatch_once(object(), client, SimpleNamespace(temporal_task_queue="test"), owner) == 1
    args, options = client.start_workflow.await_args
    assert args == (workflow_type, event)
    assert options["id"] == f"{prefix}/{event.tenant_id}/{event.event_id}"
    assert options["id_reuse_policy"] == WorkflowIDReusePolicy.REJECT_DUPLICATE
    assert finished.await_args.kwargs["success"] is True


@pytest.mark.parametrize(
    "workflow_class,activity_name,result",
    [
        (ReferenceEffectWorkflow, "simulate_reference_effect", "simulated"),
        (ReferenceCostProjectionWorkflow, "project_reference_cost", "projected"),
        (ReferenceEffectProjectionWorkflow, "project_reference_effect", "projected"),
    ],
)
async def test_workflow_runs_only_its_local_activity(monkeypatch, workflow_class, activity_name, result):
    event = _event()
    execute = AsyncMock(return_value=result)
    monkeypatch.setattr("app.workflows.reference_effect.workflow.execute_activity", execute)
    assert await workflow_class().run(event) == result
    args, kwargs = execute.await_args
    assert args == (activity_name, event)
    assert kwargs["start_to_close_timeout"] == timedelta(seconds=30)
    assert kwargs["retry_policy"].maximum_attempts == 0


async def test_worker_registers_fake_effect_activities_only_when_explicitly_enabled(settings, monkeypatch):
    from app.entrypoints import worker

    db = AsyncMock()
    fake_activities = SimpleNamespace(simulate_effect=AsyncMock(), project_cost=AsyncMock(), project_effect=AsyncMock())
    configured = settings.model_copy(update={"reference_discovery_mode": "fake"})
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: db)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    effect_factory = MagicMock(return_value=fake_activities)
    monkeypatch.setattr(worker, "ReferenceEffectActivities", effect_factory)
    runner = MagicMock(run=AsyncMock())
    temporal_worker = MagicMock(return_value=runner)
    monkeypatch.setattr(worker, "Worker", temporal_worker)
    await worker.run_worker()
    effect_factory.assert_called_once_with(db, configured, db)
    assert ReferenceEffectWorkflow in temporal_worker.call_args.kwargs["workflows"]
    assert ReferenceCostProjectionWorkflow in temporal_worker.call_args.kwargs["workflows"]
    assert ReferenceEffectProjectionWorkflow in temporal_worker.call_args.kwargs["workflows"]
    assert fake_activities.simulate_effect in temporal_worker.call_args.kwargs["activities"]
    assert fake_activities.project_cost in temporal_worker.call_args.kwargs["activities"]
    assert fake_activities.project_effect in temporal_worker.call_args.kwargs["activities"]


async def test_fake_effect_worker_requires_restricted_database(settings, monkeypatch):
    from app.entrypoints import worker

    configured = settings.model_copy(update={"reference_discovery_mode": "fake", "correlator_database_url": None})
    db = AsyncMock()
    connect = AsyncMock()
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: db)
    monkeypatch.setattr(worker, "connect_temporal", connect)
    with pytest.raises(RuntimeError, match="REFERENCE_RECOVERY_DATABASE_REQUIRED"):
        await worker.run_worker()
    connect.assert_not_awaited()
    db.close.assert_awaited_once()
