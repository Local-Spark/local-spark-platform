"""Meaningful service edge cases without external providers."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from temporalio.exceptions import ApplicationError

from app.services.auth import AuthError
from app.services.reference_discovery import ReferenceDiscoveryService
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_discovery_activities import ReferenceDiscoveryActivities, _RevokedOwner


def rows(*, one=None, one_or_none=None):
    result = MagicMock()
    result.mappings.return_value.one.return_value = one
    result.mappings.return_value.one_or_none.return_value = one_or_none
    return result


@pytest.fixture
def service(monkeypatch):
    session, database = AsyncMock(), MagicMock()

    @asynccontextmanager
    async def transaction(*args):
        yield session

    database.transaction = transaction
    session.scalar.return_value = None
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr("app.services.reference_discovery.lock_reference_head", AsyncMock())
    monkeypatch.setattr("app.services.reference_discovery.reserve_simulated_radius", AsyncMock(return_value=uuid4()))
    return ReferenceDiscoveryService(SimpleNamespace(reference_discovery_mode="fake"), database), session


@pytest.fixture
def record():
    return {
        "id": uuid4(),
        "operation_id": uuid4(),
        "state": "pending",
        "created_at": datetime.now(UTC),
        "completed_at": None,
    }


def context(preference):
    return {
        "version": 1,
        "category": "food",
        "document": {"preferences": {"reference_search": preference, "business_terms": ["Café"]}},
    }


async def test_request_missing_preferences_manual_and_replay(service, record):
    svc, session = service
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    session.execute.side_effect = [rows(one_or_none=record)]
    assert (await svc.request(tenant, business, actor, operation)).id == record["id"]
    for current in (None, context(None)):
        session.execute.side_effect = [rows(), rows(one_or_none=current)]
        with pytest.raises(AuthError, match="REFERENCE_SEARCH_PREFERENCE_REQUIRED"):
            await svc.request(tenant, business, actor, operation)
    session.execute.side_effect = [rows(), rows(one_or_none=context({"scope": "national"}))]
    with pytest.raises(AuthError, match="REFERENCE_SCOPE_NOT_SUPPORTED"):
        await svc.request(tenant, business, actor, operation)


async def test_search_requires_terms_and_waits_for_queued_context(service):
    svc, session = service
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    session.scalar.return_value = 1
    session.execute.side_effect = [rows()]
    with pytest.raises(AuthError, match="REFERENCE_CONTEXT_CHANGE_PENDING"):
        await svc.request(tenant, business, actor, operation)
    session.scalar.return_value = None
    current = context({"scope": "national"})
    current["document"]["preferences"]["business_terms"] = []
    session.execute.side_effect = [rows(), rows(one_or_none=current)]
    with pytest.raises(AuthError, match="REFERENCE_TERMS_REQUIRED"):
        await svc.request(tenant, business, actor, operation)
    manual = {
        "scope": "local",
        "radius_km": 5,
        "origin": {"method": "manual", "address": {"city": "Rio", "state_code": "RJ"}},
    }
    session.execute.side_effect = [rows(), rows(one_or_none=context(manual))]
    with pytest.raises(AuthError, match="REFERENCE_ORIGIN_REQUIRES_GEOCODING"):
        await svc.request(tenant, business, actor, operation)


async def test_request_concurrent_conflict_and_success(service, record):
    svc, session = service
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    current = context(
        {
            "scope": "local",
            "radius_km": 5,
            "origin": {"method": "device", "coordinates": {"latitude": -23.55, "longitude": -46.63, "confirmed": True}},
        }
    )
    session.execute.side_effect = [rows(), rows(one_or_none=current), rows(), rows(one=record)]
    assert (await svc.request(tenant, business, actor, operation)).id == record["id"]
    session.execute.side_effect = [
        rows(),
        rows(one_or_none=current),
        rows(one_or_none=record),
        MagicMock(),
        MagicMock(),
    ]
    assert (await svc.request(tenant, business, actor, operation)).id == record["id"]
    svc.settings.reference_discovery_mode = "disabled"
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await svc.request(tenant, business, actor, operation)


async def test_read_requires_existing_resource(service, record):
    svc, session = service
    tenant, business, actor, discovery = [uuid4() for _ in range(4)]
    session.execute.side_effect = [rows(), rows(one_or_none=record)]
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_NOT_FOUND"):
        await svc.read(tenant, business, actor, discovery)
    assert (await svc.read(tenant, business, actor, discovery)).id == record["id"]


async def test_discovery_list_only_returns_simulations(service, record):
    svc, session = service
    result = MagicMock()
    result.mappings.return_value.all.return_value = [record]
    session.execute.return_value = result
    result_list = await svc.list_discoveries(uuid4(), uuid4(), uuid4())
    assert len(result_list) == 1 and result_list[0].mode == "fake"


async def test_fixture_list_is_isolated_and_rejects_missing_discovery(service):
    svc, session = service
    tenant, business, actor, discovery = [uuid4() for _ in range(4)]
    session.scalar.side_effect = [None, discovery]
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_NOT_FOUND"):
        await svc.fixtures(tenant, business, actor, discovery)
    result = MagicMock()
    result.mappings.return_value.all.return_value = [
        {
            "id": uuid4(),
            "discovery_id": discovery,
            "fixture_number": 1,
            "canonical_id": uuid4(),
            "reputation_score_snapshot": Decimal("9.424"),
            "reputation_formula_version": "penalized-3.4-v1",
            "reputation_fixture_version": "synthetic-v1",
        }
    ]
    session.execute.return_value = result
    fixtures = await svc.fixtures(tenant, business, actor, discovery)
    assert len(fixtures) == 1 and fixtures[0].mode == "fake"
    svc.settings.reference_discovery_mode = "disabled"
    with pytest.raises(AuthError, match="REFERENCE_DISCOVERY_DISABLED"):
        await svc.fixtures(tenant, business, actor, discovery)


async def test_fixture_list_uses_persisted_full_precision_and_versions(service, monkeypatch):
    svc, session = service
    tenant, business, actor, discovery = [uuid4() for _ in range(4)]
    session.scalar.return_value = discovery
    result = MagicMock()
    result.mappings.return_value.all.return_value = [
        {
            "id": uuid4(),
            "discovery_id": discovery,
            "fixture_number": number,
            "canonical_id": uuid4(),
            "reputation_score_snapshot": score,
            "reputation_formula_version": "test-formula-v1",
            "reputation_fixture_version": "synthetic-v1",
        }
        for number, score in (
            (3, Decimal("9.4249")),
            (1, Decimal("9.4241")),
            (2, Decimal("9.4249")),
        )
    ]
    session.execute.return_value = result

    from app.services import reference_simulated_candidates

    def forbidden_recompute():
        raise AssertionError("Saved scores must not be recomputed from current fixtures")

    monkeypatch.setattr(reference_simulated_candidates, "simulated_candidates", forbidden_recompute)
    output = await svc.fixtures(tenant, business, actor, discovery)
    assert [item.fixture_number for item in output] == [2, 3, 1]
    assert [item.reputation_score for item in output] == [Decimal("9.42")] * 3
    assert all(item.reputation_formula_version == "test-formula-v1" for item in output)
    assert all(item.fixture_version == "synthetic-v1" for item in output)


async def test_activity_rejects_missing_intent(monkeypatch):
    session, database = AsyncMock(), MagicMock()

    @asynccontextmanager
    async def transaction(*args):
        yield session

    database.transaction = transaction
    monkeypatch.setattr("app.workflows.reference_discovery_activities.lock_reference_head", AsyncMock())
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    session.scalar.return_value = {
        "business_id": event.business_id,
        "actor_id": event.actor_id,
        "operation_id": event.operation_id,
    }
    session.execute.return_value = rows()
    with pytest.raises(ApplicationError, match="Discovery intent unavailable"):
        await ReferenceDiscoveryActivities(
            database, SimpleNamespace(reference_discovery_mode="fake")
        ).simulate_discovery(event)


async def test_activity_rejects_inconsistent_processed_event(monkeypatch):
    session, database = AsyncMock(), MagicMock()

    @asynccontextmanager
    async def transaction(*args):
        yield session

    database.transaction = transaction
    monkeypatch.setattr("app.workflows.reference_discovery_activities.lock_reference_head", AsyncMock())
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    session.scalar.side_effect = [
        {"business_id": event.business_id, "actor_id": event.actor_id, "operation_id": event.operation_id},
        True,
        None,
    ]
    session.execute.return_value = rows(one_or_none={"state": "pending"})
    with pytest.raises(ApplicationError, match="Processed event has no terminal discovery"):
        await ReferenceDiscoveryActivities(
            database, SimpleNamespace(reference_discovery_mode="fake")
        ).simulate_discovery(event)


async def test_failure_compensation_recovers_revoked_owner(monkeypatch):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    activity = ReferenceDiscoveryActivities(MagicMock(), SimpleNamespace(reference_discovery_mode="fake"), MagicMock())
    monkeypatch.setattr(activity, "_perform", AsyncMock(side_effect=_RevokedOwner()))
    recover = AsyncMock(return_value="stale")
    monkeypatch.setattr("app.workflows.reference_discovery_activities.recover_revoked", recover)
    assert await activity.fail_discovery(event) == "stale"
    recover.assert_awaited_once_with(activity.recovery_database, event, "search")
