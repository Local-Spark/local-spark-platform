"""Routing and isolation of the discovery simulation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from temporalio.exceptions import ActivityError

from app.core.config import Settings
from app.services import outbox
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_discovery import ReferenceDiscoveryWorkflow


async def test_discovery_event_routes_to_temporal(monkeypatch):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    item = outbox.ClaimedEvent(event, fencing_token=1, event_type="reference.search_requested")
    client = SimpleNamespace(start_workflow=AsyncMock())
    finished = AsyncMock(return_value=True)
    monkeypatch.setattr(outbox, "claim_events", AsyncMock(return_value=[item]))
    monkeypatch.setattr(outbox, "finish_event", finished)
    owner = uuid4()
    assert await outbox.dispatch_once(object(), client, SimpleNamespace(temporal_task_queue="test"), owner) == 1
    args, options = client.start_workflow.await_args
    assert args == ("ReferenceDiscoveryWorkflow", event)
    assert options["id"] == f"reference-discovery/{event.tenant_id}/{event.event_id}"
    assert finished.await_args.kwargs["success"] is True


async def test_workflow_calls_only_the_simulation_activity(monkeypatch):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    activity = AsyncMock(return_value="simulated")
    monkeypatch.setattr("app.workflows.reference_discovery.workflow.execute_activity", activity)
    assert await ReferenceDiscoveryWorkflow().run(event) == "simulated"
    assert activity.await_args.args == ("simulate_reference_discovery", event)


async def test_workflow_compensates_after_confirmed_simulation_failure(monkeypatch):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    error = ActivityError(
        "failed",
        scheduled_event_id=1,
        started_event_id=2,
        identity="test",
        activity_type="test",
        activity_id="test",
        retry_state=None,
    )
    activity = AsyncMock(side_effect=[error, "stale"])
    monkeypatch.setattr("app.workflows.reference_discovery.workflow.execute_activity", activity)
    assert await ReferenceDiscoveryWorkflow().run(event) == "stale"
    assert [call.args[0] for call in activity.await_args_list] == [
        "simulate_reference_discovery",
        "fail_reference_simulation",
    ]


def test_simulated_discovery_cannot_be_configured_in_production(settings):
    values = settings.model_dump()
    values.update({"environment": "staging", "reference_discovery_mode": "fake"})
    with pytest.raises(ValidationError, match="limited to local"):
        Settings(_env_file=None, **values)
