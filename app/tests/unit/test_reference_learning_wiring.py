from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from temporalio.exceptions import ApplicationError

from app.services import outbox
from app.tests.unit.test_reference_execution_wiring import configured as discovery_configured
from app.tests.unit.test_reference_learning_execution import event, window
from app.workflows import reference_learning as workflow_module
from app.workflows.reference_learning import ReferenceLearningWorkflow
from app.workflows.reference_learning_activities import ReferenceLearningActivities


def configured(settings, **changes):
    return discovery_configured(settings).model_copy(
        update={
            "reference_learning_execution_enabled": True,
            "reference_feed_actor_build": "1.2.3",
            "reference_feed_tariff_version": "v1",
            "reference_feed_credential_version": "v1",
            "reference_feed_reserved_usd_micros": 100_000,
            "reference_post_reserved_usd_micros": 3_000,
            **changes,
        }
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_learning_execution_enabled", False),
        ("environment", "production"),
        ("correlator_database_url", None),
        ("reference_provider_hmac_key", None),
        ("reference_provider_hmac_key", SecretStr("short")),
        ("reference_provider_key_version", ""),
        ("reference_provider_pilot_id", None),
        ("typesafe_api_key", None),
        ("typesafe_api_key", SecretStr(" ")),
        ("reference_jev_tariff_version", ""),
        ("reference_jev_credential_version", ""),
        ("reference_post_reserved_usd_micros", 0),
        ("reference_apify_api_token", None),
        ("reference_apify_api_token", SecretStr(" ")),
        ("reference_feed_actor_build", ""),
        ("reference_feed_tariff_version", ""),
        ("reference_feed_credential_version", ""),
        ("reference_feed_reserved_usd_micros", 0),
    ],
)
def test_required_learning_configuration(settings, field, value):
    assert not configured(settings, **{field: value}).reference_learning_ready()


def test_learning_defaults_off_and_does_not_require_google(settings):
    assert not settings.reference_learning_ready()
    assert configured(
        settings, reference_google_api_key=None, reference_discovery_execution_enabled=False
    ).reference_learning_ready()


@pytest.mark.parametrize("future", [True, False])
async def test_workflow_waits_for_due_date_polls_same_run_and_retries_budget(monkeypatch, future):
    now = datetime.now(UTC)
    w = window()
    item = event(w)
    execute = AsyncMock(
        side_effect=[
            (now + timedelta(days=180) if future else now).isoformat(),
            "pending",
            "budget_unavailable",
            "partial",
        ]
    )
    sleep = AsyncMock()
    monkeypatch.setattr(workflow_module.workflow, "now", lambda: now)
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    monkeypatch.setattr(workflow_module.workflow, "sleep", sleep)
    assert await ReferenceLearningWorkflow().run(item) == "partial"
    assert [c.args[0] for c in sleep.await_args_list] == ([timedelta(days=180)] if future else []) + [
        timedelta(seconds=10),
        timedelta(hours=1),
    ]
    assert all(c.args[1] == item for c in execute.await_args_list)


async def test_cancelled_schedule_never_runs_effect(monkeypatch):
    execute = AsyncMock(return_value="cancelled")
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    assert await ReferenceLearningWorkflow().run(event(window())) == "cancelled"
    execute.assert_awaited_once()


async def test_long_poll_history_continues_with_only_event_identity(monkeypatch):
    class Continued(Exception):
        pass

    item = event(window())
    execute = AsyncMock(side_effect=[datetime.now(UTC).isoformat()] + ["pending"] * 180)

    def continued(value):
        assert value == item
        raise Continued

    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    monkeypatch.setattr(workflow_module.workflow, "now", lambda: datetime.now(UTC))
    monkeypatch.setattr(workflow_module.workflow, "sleep", AsyncMock())
    monkeypatch.setattr(workflow_module.workflow, "continue_as_new", continued)
    with pytest.raises(Continued):
        await ReferenceLearningWorkflow().run(item)


async def test_activities_expose_only_schedule_and_stable_errors(monkeypatch):
    w = window()
    item = event(w)
    executor = SimpleNamespace(
        store=SimpleNamespace(load=AsyncMock(return_value=w)), run=AsyncMock(return_value="completed")
    )
    activities = ReferenceLearningActivities(executor)
    assert await activities.reference_learning_schedule(item) == w.scheduled_at.isoformat()
    assert await activities.execute_reference_learning(item) == "completed"
    executor.store.load.return_value = w.model_copy(update={"state": "cancelled"})
    assert await activities.reference_learning_schedule(item) == "cancelled"
    executor.store.load.side_effect = ValueError("private source")
    executor.run.side_effect = ValueError("private caption")
    for call in [activities.reference_learning_schedule, activities.execute_reference_learning]:
        with pytest.raises(ApplicationError, match="Reference learning unavailable") as error:
            await call(item)
        assert "private" not in str(error.value)


async def test_relay_dispatches_learning_by_window_identity(settings, monkeypatch):
    s = configured(settings)
    item = outbox.ClaimedEvent(event(window()), 1, "reference.learning_requested")
    claim = AsyncMock(return_value=[item])
    client = SimpleNamespace(start_workflow=AsyncMock())
    monkeypatch.setattr(outbox, "claim_events", claim)
    monkeypatch.setattr(outbox, "finish_event", AsyncMock(return_value=True))
    assert await outbox.dispatch_once(object(), client, s, uuid4()) == 1
    assert claim.await_args.kwargs["include_learning"] is True
    assert client.start_workflow.await_args.args[0] == "ReferenceLearningWorkflow"
    assert (
        client.start_workflow.await_args.kwargs["id"]
        == f"reference-learning/{item.event.tenant_id}/{item.event.operation_id}"
    )


async def test_worker_registers_learning_only_with_explicit_config(settings, monkeypatch):
    from app.entrypoints import worker

    database, running = AsyncMock(), MagicMock(run=AsyncMock())
    factory = MagicMock(return_value=SimpleNamespace(run=AsyncMock()))
    constructor = MagicMock(return_value=running)
    monkeypatch.setattr(worker, "get_settings", lambda: configured(settings))
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    monkeypatch.setattr(worker, "ReferenceLearningExecution", factory)
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert worker.ReferenceLearningWorkflow in constructor.call_args.kwargs["workflows"]
    methods = {method.__name__ for method in constructor.call_args.kwargs["activities"]}
    assert {"reference_learning_schedule", "execute_reference_learning"} <= methods
    assert factory.call_args.args[0] is database


@pytest.mark.parametrize("state", ["disabled", "configuration_unavailable"])
async def test_restorable_learning_configuration_waits_and_resumes_same_window(monkeypatch, state):
    execute = AsyncMock(side_effect=[datetime.now(UTC).isoformat(), state, "completed"])
    sleep = AsyncMock()
    monkeypatch.setattr(workflow_module.workflow, "now", lambda: datetime.now(UTC))
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    monkeypatch.setattr(workflow_module.workflow, "sleep", sleep)
    item = event(window())
    assert await ReferenceLearningWorkflow().run(item) == "completed"
    sleep.assert_awaited_once_with(timedelta(hours=1))
    assert all(call.args[1] == item for call in execute.await_args_list)
