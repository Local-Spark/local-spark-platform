"""A visual reservation and the caller's intent commit or roll back together."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.visual_cost_ledger import VisualCostLedger
from app.tests.integration.test_visual_cost_ledger import _business

pytestmark = pytest.mark.integration


async def test_reservation_shares_commit_and_rollback_with_caller(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, operation = await _business(admin, tenant), uuid4()
    cfg = settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    db = Database(cfg, correlator=True)
    ledger = VisualCostLedger(cfg, db)
    arguments = (tenant, business, actor, operation, "fake", "synthetic", "a" * 64, 70)
    try:
        # A caller-owned audit event stands in for its durable
        # intent: no reservation or audit may survive if the intent rolls back.
        with pytest.raises(RuntimeError, match="rollback"):
            async with db.transaction(tenant, actor) as session:
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,'test.visual_intent',:business)"""),
                    {"tenant": tenant, "actor": actor, "operation": operation, "business": business},
                )
                result = await ledger.reserve_in_transaction(session, *arguments)
                assert result.created
                raise RuntimeError("rollback")
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM audit_events WHERE operation_id=:op"), {"op": operation})
                == 0
            )
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant}
                )
                == 0
            )
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_cost_events WHERE tenant_id=:t"), {"t": tenant})
                == 0
            )
        async with db.transaction(tenant, actor) as session:
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'test.visual_intent',:business)"""),
                {"tenant": tenant, "actor": actor, "operation": operation, "business": business},
            )
            result = await ledger.reserve_in_transaction(session, *arguments)
            assert result.created
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM audit_events WHERE operation_id=:op"), {"op": operation})
                == 1
            )
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant}
                )
                == 1
            )
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_cost_events WHERE tenant_id=:t"), {"t": tenant})
                == 1
            )
        replay = await ledger.reserve(*arguments)
        assert not replay.created and replay.id == result.id
    finally:
        await db.close()
