"""Cycle and selection service boundaries with non-network fixtures."""

import hashlib
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from temporalio.exceptions import ApplicationError

from app.schemas.reference_discovery import FixtureSelectionRequest
from app.services.auth import AuthError
from app.services.reference_cycles import FixtureSelectionService, reserve_simulated_radius
from app.services.reference_recovery import recover_revoked
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_selection import ReferenceSelectionWorkflow
from app.workflows.reference_selection_activities import ReferenceSelectionActivities


def rows(*, one=None, optional=None, all=None):
    result = MagicMock()
    result.mappings.return_value.one.return_value = one
    result.mappings.return_value.one_or_none.return_value = optional
    result.mappings.return_value.all.return_value = all
    return result


@pytest.fixture
def setup(monkeypatch):
    session, database = AsyncMock(), MagicMock()

    @asynccontextmanager
    async def transaction(*args):
        yield session

    database.transaction = transaction
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    return database, session


async def test_reserve_distinguishes_unused_used_and_expired_radius(monkeypatch):
    session, tenant, business, cycle = AsyncMock(), uuid4(), uuid4(), uuid4()
    head = AsyncMock(return_value={"cycle_id": cycle})
    monkeypatch.setattr("app.services.reference_cycles.lock_reference_head", head)
    session.execute.return_value = rows(one={"locked": True, "locked_until": datetime.now(UTC)})
    session.scalar.return_value = None
    assert await reserve_simulated_radius(session, tenant, business, 5) == cycle
    session.scalar.return_value = 1
    with pytest.raises(AuthError, match="REFERENCE_RADIUS_ALREADY_SEARCHED"):
        await reserve_simulated_radius(session, tenant, business, 5)
    session.execute.return_value = rows(one={"locked": False, "locked_until": None})
    session.scalar.return_value = 1
    with pytest.raises(AuthError, match="REFERENCE_RADIUS_ALREADY_SEARCHED"):
        await reserve_simulated_radius(session, tenant, business, 5)
    session.scalar.return_value = None
    assert await reserve_simulated_radius(session, tenant, business, 5) == cycle
    session.execute.return_value = rows(one={"locked": False, "locked_until": datetime.now(UTC)})
    assert await reserve_simulated_radius(session, tenant, business, 5) != cycle
    head.return_value = {"cycle_id": None}
    assert isinstance(await reserve_simulated_radius(session, tenant, business, 5), type(cycle))


async def test_selection_current_and_confirmation_boundaries(setup, monkeypatch):
    database, session = setup
    tenant, business, actor, cycle = uuid4(), uuid4(), uuid4(), uuid4()
    first, second, canonical = uuid4(), uuid4(), uuid4()
    settings = SimpleNamespace(reference_discovery_mode="fake")
    service = FixtureSelectionService(settings, database)
    session.scalar.return_value = None
    session.execute.return_value = rows(
        all=[{"id": first, "canonical_id": canonical}, {"id": second, "canonical_id": canonical}]
    )
    assert (await service.current(tenant, business, actor)).candidate_ids == [first]
    monkeypatch.setattr("app.services.reference_cycles.lock_reference_head", AsyncMock(return_value={"cycle_id": None}))
    payload = FixtureSelectionRequest(operation_id=uuid4(), candidate_ids=[first])
    session.execute.side_effect = [rows()]
    with pytest.raises(AuthError, match="REFERENCE_SELECTION_NO_CYCLE"):
        await service.confirm(tenant, business, actor, payload)
    monkeypatch.setattr(
        "app.services.reference_cycles.lock_reference_head", AsyncMock(return_value={"cycle_id": cycle})
    )
    session.execute.side_effect = [rows(), rows(all=[])]
    with pytest.raises(AuthError, match="REFERENCE_SELECTION_INVALID_CANDIDATE"):
        await service.confirm(tenant, business, actor, payload)
    duplicate = FixtureSelectionRequest(operation_id=uuid4(), candidate_ids=[first, second])
    session.execute.side_effect = [
        rows(),
        rows(all=[{"id": first, "canonical_id": canonical}, {"id": second, "canonical_id": canonical}]),
    ]
    with pytest.raises(AuthError, match="REFERENCE_SELECTION_DUPLICATE_ENTITY"):
        await service.confirm(tenant, business, actor, duplicate)
    until = datetime.now(UTC)
    session.scalar.return_value = until
    session.execute.side_effect = [
        rows(),
        rows(all=[{"id": first, "canonical_id": canonical}]),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    result = await service.confirm(tenant, business, actor, payload)
    assert result.candidate_ids == [first] and result.mode == "fake"
    digest = hashlib.sha256(json.dumps([str(first)], separators=(",", ":")).encode()).hexdigest()
    session.execute.side_effect = [rows(optional={"request_hash": digest, "response": result.model_dump(mode="json")})]
    assert await service.confirm(tenant, business, actor, payload) == result
    session.execute.side_effect = [rows(optional={"request_hash": "wrong"})]
    with pytest.raises(AuthError, match="REFERENCE_SELECTION_OPERATION_CONFLICT"):
        await service.confirm(tenant, business, actor, payload)
    settings.reference_discovery_mode = "disabled"
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await service.current(tenant, business, actor)
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await service.confirm(tenant, business, actor, payload)


async def test_recovery_rejects_invalid_events_restoration_and_absent_intents(setup):
    database, session = setup
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    payload = {"business_id": event.business_id, "actor_id": event.actor_id, "operation_id": event.operation_id}
    with pytest.raises(ApplicationError, match="Recovery database unavailable"):
        await recover_revoked(None, event, "search")
    session.scalar.side_effect = [{}]
    with pytest.raises(ApplicationError, match="Event does not match"):
        await recover_revoked(database, event, "search")
    session.scalar.side_effect = [payload, 1]
    with pytest.raises(ApplicationError, match="Owner access restored"):
        await recover_revoked(database, event, "search")
    session.scalar.side_effect = [payload, None, None, None]
    with pytest.raises(ApplicationError, match="Discovery intent unavailable"):
        await recover_revoked(database, event, "search")
    session.scalar.side_effect = [payload, None, None]
    with pytest.raises(ApplicationError, match="Selection intent unavailable"):
        await recover_revoked(database, event, "selection")
    session.scalar.side_effect = [payload, None, None, "stale"]
    assert await recover_revoked(database, event, "search") == "stale"
    session.scalar.side_effect = [payload, None, 1]
    assert await recover_revoked(database, event, "selection") == "recorded"


async def test_selection_activity_validates_intent_and_deduplicates(setup):
    database, session = setup
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    payload = {"business_id": event.business_id, "actor_id": event.actor_id, "operation_id": event.operation_id}
    activity = ReferenceSelectionActivities(database)
    session.scalar.side_effect = [{}]
    with pytest.raises(ApplicationError, match="Event does not match"):
        await activity.record_selection(event)
    session.scalar.side_effect = [payload, 1, None]
    with pytest.raises(ApplicationError, match="Selection intent unavailable"):
        await activity.record_selection(event)
    session.scalar.side_effect = [payload, 1, 1, None]
    assert await activity.record_selection(event) == "duplicate"
    session.scalar.side_effect = [payload, 1, 1, uuid4()]
    assert await activity.record_selection(event) == "recorded"


async def test_selection_workflow_routes_to_activity(monkeypatch):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    activity = AsyncMock(return_value="recorded")
    monkeypatch.setattr("app.workflows.reference_selection.workflow.execute_activity", activity)
    assert await ReferenceSelectionWorkflow().run(event) == "recorded"
    assert activity.await_args.args == ("record_reference_fixture_selection", event)
