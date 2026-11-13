"""Reconciliation preserves received bytes, old failure, cost holds and native approval boundaries."""

from unittest.mock import patch
from uuid import uuid4, uuid5

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.motion_context import digest
from app.services.motion_planning_recovery import MotionPlanningRecovery
from app.tests.integration.test_motion_checkpoints import checkpoint_case, decide, decision, event  # noqa: F401
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.unit.test_motion_ai import provider

pytestmark = pytest.mark.integration


@pytest.fixture
async def received_plan(checkpoint_case):  # noqa: F811
    c = checkpoint_case
    c.provider.build_request = provider().build_request
    with patch(
        "app.services.motion_construction.validate_declarations",
        side_effect=AuthError("MOTION_STAGING_TRANSITION_INVALID", 409),
    ):
        with pytest.raises(AuthError, match="TRANSITION_INVALID"):
            await c.runner.run(c.event)
    async with c.database.transaction(c.tenant, c.actor) as s:
        c.row = dict(await c.requests.row(s, c.tenant, c.business, c.requested.id))
        c.model = await c.checkpoints.effect(s, c.row, uuid5(c.body.operation_id, "generate:plan:0"))
    output = await c.checkpoints.payloads.open(c.row, c.model["response_ciphertext"])
    c.plan_sha = digest(output["construction_plan"])
    c.fresh = await c.inputs.prepare(c.requests.context.open(c.row["snapshot_ciphertext"]))
    c.recovery = MotionPlanningRecovery(c.checkpoints)
    c.recovery_args = (c.tenant, c.business, c.actor, c.requested.id, c.plan_sha, c.fresh, c.provider)
    return c


async def test_received_plan_is_reconciled_once_without_provider_or_render_replay(received_plan):
    c = received_plan
    sha = await c.recovery.reconcile(*c.recovery_args)
    assert await c.recovery.reconcile(*c.recovery_args) == sha
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()
    view = await c.checkpoints.present(c.tenant, c.business, c.actor, c.requested.id, "plan")
    assert view["decision"] is None and digest(view["packet"]["artifact"]) == c.plan_sha
    async with c.database.transaction(c.tenant, c.actor) as s:
        assert (
            await s.scalar(
                text("SELECT count(*) FROM outbox_events WHERE tenant_id=:t AND event_type='motion.failed'"),
                {"t": c.tenant},
            )
            == 1
        )
        assert (
            await s.scalar(
                text("SELECT count(*) FROM audit_events WHERE tenant_id=:t AND action='motion.plan_reconciled'"),
                {"t": c.tenant},
            )
            == 1
        )
    await decide(c, "plan", await decision(c, "plan"))
    assert await c.runner.run(event(c, "plan")) == "awaiting_render"
    assert c.provider.calls == ["plan", "implementation"]


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "uncertain",
        "wrong_failure",
        "foreign",
        "owner",
        "missing",
        "signed",
        "input",
        "large",
        "race",
        "existing_hash",
        "audio",
    ],
)
async def test_reconciliation_refuses_unbound_or_unsafe_state(received_plan, admin, change, seeded):
    c = received_plan
    args = list(c.recovery_args)
    if change == "hash":
        args[4] = "0" * 64
    elif change == "foreign":
        args[0] = uuid4()
    elif change == "owner":
        async with admin.begin() as s:
            await s.execute(
                text("UPDATE motion_requests SET actor_id=:a WHERE id=:r"), {"a": seeded["a2"], "r": c.requested.id}
            )
    elif change in {"uncertain", "wrong_failure", "missing", "signed"}:
        async with admin.begin() as s:
            if change == "uncertain":
                await s.execute(
                    text("UPDATE motion_effects SET state='submitted' WHERE operation_id=:o"),
                    {"o": c.model["operation_id"]},
                )
            elif change == "wrong_failure":
                await s.execute(
                    text("UPDATE motion_requests SET failure_code='OTHER' WHERE id=:r"), {"r": c.requested.id}
                )
            elif change == "missing":
                await s.execute(
                    text("DELETE FROM motion_effects WHERE operation_id=:o"), {"o": c.model["operation_id"]}
                )
            else:
                await s.execute(
                    text("UPDATE motion_effects SET request_hash=:h WHERE operation_id=:o"),
                    {"h": "0" * 64, "o": c.model["operation_id"]},
                )
    elif change == "input":
        original = c.provider.build_request
        c.provider.build_request = lambda job: {**original(job), "max_output_tokens": 1}
    elif change == "existing_hash":
        await c.recovery.reconcile(*args)
        args[4] = "0" * 64
    elif change == "large":
        original = c.requests.context.seal
        c.requests.context.seal = lambda value: (
            "x" * (1024 * 1024 + 1)
            if isinstance(value, dict) and value.get("version") == "motion-checkpoint-v1"
            else original(value)
        )
    elif change == "race":
        original = c.recovery.snapshot
        calls = 0

        async def raced(*a):
            nonlocal calls
            calls += 1
            row, effects, existing = await original(*a)
            if calls == 2:
                row = {**row, "failure_code": "changed"}
            return row, effects, existing

        c.recovery.snapshot = raced
    else:
        from dataclasses import replace

        args[5] = replace(c.fresh, audio={**c.fresh.audio, "volume": 0.2})
    with pytest.raises(AuthError):
        await c.recovery.reconcile(*args)
    assert c.provider.calls == ["plan"]
