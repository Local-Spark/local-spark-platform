"""An admission refusal cannot silently raise its cap or replay any existing effect."""

from uuid import uuid4, uuid5

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.tests.integration.test_motion_production import create, motion_case  # noqa: F401
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


@pytest.fixture
async def refused(motion_case):  # noqa: F811
    c = motion_case
    c.requested = await create(c)
    image = c.cfg.motion_renderer_image
    c.cfg.motion_renderer_image = "sha256:" + "f" * 64
    with pytest.raises(AuthError, match="CONTEXT_CHANGED"):
        await c.runner.run(c.event)
    c.cfg.motion_renderer_image = image
    assert not c.provider.calls
    return c


async def test_explicit_zero_effect_recovery_retains_failed_parent_and_executes_once(refused):
    c = refused
    args = c.tenant, c.business, c.actor, c.requested.id
    child = await c.requests.recover_admission(*args)
    assert child.operation_id == uuid5(c.body.operation_id, "admission-recovery:1")
    assert await c.requests.recover_admission(*args) == child
    assert (await c.requests.get(*args)).state == "failed"
    event = BusinessEvent(
        str(uuid5(child.operation_id, "motion.requested")),
        str(c.tenant),
        str(c.business),
        str(c.actor),
        str(child.operation_id),
    )
    assert await c.runner.run(event) == "completed"
    assert await c.runner.run(event) == "already_claimed"
    assert c.provider.calls == ["generate", "review"]
    async with c.database.transaction(c.tenant, c.actor) as session:
        old = await c.requests.row(session, c.tenant, c.business, c.requested.id)
        new = await c.requests.row(session, c.tenant, c.business, child.id)
        assert old["state"] == "failed" and old["admitted_at"] is None
        assert old["budget_usd_micros"] == new["budget_usd_micros"]
        assert (
            await session.scalar(
                text("SELECT count(*) FROM audit_events WHERE operation_id=:o AND action='motion.requested'"),
                {"o": child.operation_id},
            )
            == 1
        )
    with pytest.raises(AuthError):
        await c.requests.recover_admission(uuid4(), c.business, c.actor, c.requested.id)


@pytest.mark.parametrize("change", ["state", "admitted", "effect", "source", "ceiling", "stored_cap"])
async def test_recovery_refuses_started_effects_stale_context_and_budget_changes(refused, admin, change):
    c = refused
    sql = {
        "state": "UPDATE motion_requests SET state='queued' WHERE id=:r",
        "admitted": "UPDATE motion_requests SET admitted_at=clock_timestamp() WHERE id=:r",
        "effect": """INSERT INTO motion_effects(tenant_id,business_id,request_id,operation_id,kind,state,
        request_hash,request_ciphertext) VALUES(:t,:b,:r,:o,'review','claimed',:h,:p)""",
        "source": "UPDATE whatsapp_material_assets SET sha256=:h WHERE id=:s",
        "stored_cap": "UPDATE motion_requests SET budget_usd_micros=3000 WHERE id=:r",
    }
    if change == "ceiling":
        c.cfg.motion_request_budget_usd_micros = 3000
    else:
        async with admin.begin() as session:
            await session.execute(
                text(sql[change]),
                {
                    "t": c.tenant,
                    "b": c.business,
                    "r": c.requested.id,
                    "o": uuid4(),
                    "h": "f" * 64,
                    "p": c.requests.context.seal({}),
                    "s": c.source,
                },
            )
    code = "INELIGIBLE" if change in {"state", "admitted", "effect"} else "CONTEXT_CHANGED"
    with pytest.raises(AuthError, match=code):
        await c.requests.recover_admission(c.tenant, c.business, c.actor, c.requested.id)
    assert not c.provider.calls
