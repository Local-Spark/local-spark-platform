"""BL02 durable event routing and workflow contracts."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError

from app.services import outbox
from app.workflows.activities import FoundationActivities
from app.workflows.contracts import BusinessEvent
from app.workflows.foundation import BrandKitChangedWorkflow


def _event() -> BusinessEvent:
    return BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})


@pytest.mark.parametrize(
    "event_type,workflow_type,workflow_prefix",
    [
        ("business.created", "BusinessCreatedWorkflow", "business-created"),
        ("brand_kit.changed", "BrandKitChangedWorkflow", "brand-kit-changed"),
    ],
)
async def test_relay_routes_claimed_event_type_to_matching_workflow(
    monkeypatch, event_type, workflow_type, workflow_prefix
):
    event = _event()
    item = outbox.ClaimedEvent(event, fencing_token=2, event_type=event_type)
    claim = AsyncMock(return_value=[item])
    finish = AsyncMock(return_value=True)
    client = SimpleNamespace(start_workflow=AsyncMock())
    monkeypatch.setattr(outbox, "claim_events", claim)
    monkeypatch.setattr(outbox, "finish_event", finish)
    owner, database = uuid4(), object()

    assert await outbox.dispatch_once(database, client, SimpleNamespace(temporal_task_queue="bl02"), owner) == 1
    claim.assert_awaited_once_with(database, owner, limit=5)
    client.start_workflow.assert_awaited_once()
    args, kwargs = client.start_workflow.await_args
    assert args == (workflow_type, event)
    assert kwargs["id"] == f"{workflow_prefix}/{event.tenant_id}/{event.event_id}"
    assert kwargs["task_queue"] == "bl02"
    finish.assert_awaited_once_with(database, item, owner, success=True)


@pytest.mark.parametrize("outcome", ["duplicate", "unavailable", "unknown_type", "lease_lost"])
async def test_relay_is_safe_on_duplicate_failure_and_lost_lease(monkeypatch, outcome):
    event = _event()
    event_type = "unknown" if outcome == "unknown_type" else "brand_kit.changed"
    item = outbox.ClaimedEvent(event, fencing_token=1, event_type=event_type)
    client = SimpleNamespace(start_workflow=AsyncMock())
    if outcome == "duplicate":
        client.start_workflow.side_effect = WorkflowAlreadyStartedError("existing", "BrandKitChangedWorkflow")
    elif outcome == "unavailable":
        client.start_workflow.side_effect = ConnectionError("offline")
    finish = AsyncMock(return_value=outcome != "lease_lost")
    warning = Mock()
    monkeypatch.setattr(outbox, "claim_events", AsyncMock(return_value=[item]))
    monkeypatch.setattr(outbox, "finish_event", finish)
    monkeypatch.setattr(outbox.logger, "warning", warning)
    database, owner = object(), uuid4()

    assert await outbox.dispatch_once(database, client, SimpleNamespace(temporal_task_queue="bl02"), owner) == 1
    finish.assert_awaited_once_with(database, item, owner, success=outcome not in {"unavailable", "unknown_type"})
    if outcome == "unknown_type":
        client.start_workflow.assert_not_awaited()
    if outcome == "lease_lost":
        assert warning.call_args.args == ("outbox.lease_lost",)


@pytest.mark.parametrize("result", ["recorded", "duplicate", None])
async def test_brand_kit_workflow_requires_string_activity_result(monkeypatch, result):
    execute = AsyncMock(return_value=result)
    monkeypatch.setattr("app.workflows.foundation.workflow.execute_activity", execute)
    event = _event()
    if result is None:
        with pytest.raises(TypeError, match="Brand kit activity returned an invalid result"):
            await BrandKitChangedWorkflow().run(event)
    else:
        assert await BrandKitChangedWorkflow().run(event) == result
    execute.assert_awaited_once()
    args, kwargs = execute.await_args
    assert args == ("record_brand_kit_changed", event)
    assert kwargs["result_type"] is str


@pytest.mark.parametrize("row", [None, {"event_type": "business.created"}, {"event_type": "brand_kit.changed"}])
async def test_brand_kit_activity_rejects_missing_wrong_type_or_wrong_payload(row):
    event = _event()
    actual_row = None if row is None else {**row, "payload": {"business_id": "wrong"}}
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: actual_row))
        ),
        scalar=AsyncMock(),
    )

    class Database:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            assert (tenant, actor) == (UUID(event.tenant_id), UUID(event.actor_id))
            yield session

    with pytest.raises(ApplicationError, match="durable intent"):
        await FoundationActivities(Database()).record_brand_kit_changed(event)
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize("inserted,expected", [(None, "duplicate"), ("event-id", "recorded")])
async def test_brand_kit_activity_records_once_for_durable_intent(inserted, expected):
    event = _event()
    row = {
        "event_type": "brand_kit.changed",
        "payload": {
            "business_id": event.business_id,
            "actor_id": event.actor_id,
            "operation_id": event.operation_id,
        },
    }
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))),
        scalar=AsyncMock(return_value=inserted),
    )

    class Database:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            yield session

    assert await FoundationActivities(Database()).record_brand_kit_changed(event) == expected
    session.execute.assert_awaited_once()
    session.scalar.assert_awaited_once()
