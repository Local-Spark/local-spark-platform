"""Current CRUD keeps durable audit without emitting legacy receipt events."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.business import BusinessCreate
from app.services.brand_kits import BrandKitService
from app.services.business import BusinessAlreadyExists, IdempotencyConflict, create_business, fingerprint


def _session_with_savepoint():
    session = AsyncMock()
    session.begin_nested = MagicMock(return_value=MagicMock())
    return session


async def test_business_creation_keeps_atomic_audit_and_idempotent_response_without_receipt():
    tenant, actor = uuid4(), uuid4()
    session = _session_with_savepoint()
    session.scalar.side_effect = ["owner", None, uuid4()]

    async def execute(statement, parameters):
        result = MagicMock()
        if "FROM idempotency_records" in str(statement):
            result.mappings.return_value.one_or_none.return_value = None
        if "INSERT INTO businesses" in str(statement):
            result.mappings.return_value.one.return_value = {
                "id": parameters["id"],
                "tenant_id": parameters["tenant"],
                "name": parameters["name"],
                "timezone": parameters["timezone"],
                "created_at": datetime(2026, 10, 27, tzinfo=UTC),
            }
        return result

    session.execute.side_effect = execute
    created = await create_business(session, tenant, actor, "create-once", BusinessCreate(name="Café"))
    calls = [(str(call.args[0]), call.args[1]) for call in session.execute.await_args_list]
    assert not any("outbox_events" in statement for statement, _ in calls)
    audit = [parameters for statement, parameters in calls if "INSERT INTO audit_events" in statement]
    assert audit == [
        {
            "tenant": tenant,
            "actor": actor,
            "operation": created.operation_id,
            "resource": created.business.id,
        }
    ]
    saved = [parameters for statement, parameters in calls if "UPDATE idempotency_records" in statement]
    assert len(saved) == 1
    assert json.loads(saved[0]["response"])["operation_id"] == str(created.operation_id)
    assert saved[0]["key"] == "create-once"


@pytest.mark.parametrize("matching", [True, False])
async def test_business_idempotency_insert_race_reloads_existing_command(matching):
    tenant, actor, business, operation = (uuid4() for _ in range(4))
    payload = BusinessCreate(name="Café")
    existing = {
        "request_hash": fingerprint(payload if matching else BusinessCreate(name="Other")),
        "response": {
            "business": {
                "id": business,
                "tenant_id": tenant,
                "name": payload.name,
                "timezone": payload.timezone,
                "created_at": datetime(2026, 10, 27, tzinfo=UTC),
            },
            "operation_id": operation,
        },
    }
    session = _session_with_savepoint()
    session.scalar.side_effect = ["owner", None, None]

    async def execute(statement, parameters):
        result = MagicMock()
        if "FROM idempotency_records" in str(statement):
            result.mappings.return_value.one_or_none.return_value = None
            result.mappings.return_value.one.return_value = existing
        return result

    session.execute.side_effect = execute
    if matching:
        result = await create_business(session, tenant, actor, "race-key", payload)
        assert result.replayed and result.business.id == business and result.operation_id == operation
    else:
        with pytest.raises(IdempotencyConflict):
            await create_business(session, tenant, actor, "race-key", payload)


@pytest.mark.parametrize(
    "sqlstate,constraint,exception",
    [
        ("23505", "one_business_per_tenant", BusinessAlreadyExists),
        ("23505", "another_constraint", IntegrityError),
        ("23503", "one_business_per_tenant", IntegrityError),
        ("23505", None, IntegrityError),
    ],
)
async def test_business_only_maps_its_own_identified_unique_constraint(sqlstate, constraint, exception):
    tenant, actor = uuid4(), uuid4()
    session = _session_with_savepoint()
    session.scalar.side_effect = ["owner", None, uuid4()]
    original = Exception("database failure")
    original.sqlstate = sqlstate
    original.constraint_name = constraint

    async def execute(statement, parameters):
        result = MagicMock()
        if "FROM idempotency_records" in str(statement):
            result.mappings.return_value.one_or_none.return_value = None
        if "INSERT INTO businesses" in str(statement):
            raise IntegrityError(str(statement), parameters, original)
        return result

    session.execute.side_effect = execute
    with pytest.raises(exception):
        await create_business(session, tenant, actor, "constraint-key", BusinessCreate(name="Café"))


async def test_kit_change_records_only_transactional_audit():
    tenant, business, actor, operation = (uuid4() for _ in range(4))
    session = AsyncMock()
    await BrandKitService._record(session, tenant, business, actor, operation, "brand_kit.confirmed", 2)
    session.execute.assert_awaited_once()
    statement, parameters = session.execute.await_args.args
    assert "INSERT INTO audit_events" in str(statement)
    assert "outbox_events" not in str(statement)
    assert parameters == {
        "tenant": tenant,
        "actor": actor,
        "operation": operation,
        "action": "brand_kit.confirmed",
        "business": business,
    }
