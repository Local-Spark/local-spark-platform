"""Current CRUD keeps durable audit without emitting legacy receipt events."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.schemas.business import BusinessCreate
from app.services.brand_kits import BrandKitService
from app.services.business import create_business


async def test_business_creation_keeps_atomic_audit_and_idempotent_response_without_receipt():
    tenant, actor = uuid4(), uuid4()
    session = AsyncMock()
    session.scalar.side_effect = ["owner", uuid4()]

    async def execute(statement, parameters):
        result = MagicMock()
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
