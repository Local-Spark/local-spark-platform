"""Explicit failed-render continuation uses new identities and preserves paid submissions."""

from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from sqlalchemy import text

from app.adapters.motion_html_renderer import MotionRenderError
from app.schemas.motion_storyboards import StoryboardDecision
from app.services.auth import AuthError
from app.services.motion_render_recovery import MotionRenderRecovery, recovery_event, recovery_operation
from app.services.motion_storyboards import MotionStoryboards
from app.tests.integration.test_motion_checkpoints import checkpoint_case, decide, decision, event  # noqa: F401
from app.tests.integration.test_motion_production import motion_case  # noqa: F401

pytestmark = pytest.mark.integration
IMAGE = "sha256:" + "f" * 64


@pytest.fixture
async def failed_render(checkpoint_case):  # noqa: F811
    c = checkpoint_case
    assert await c.runner.run(c.event) == "awaiting_plan"
    await decide(c, "plan", await decision(c, "plan"))
    assert await c.runner.run(event(c, "plan")) == "awaiting_render"
    await decide(c, "render", await decision(c, "render"))
    assert await c.runner.run(event(c, "render")) == "awaiting_storyboard"
    c.boards = MotionStoryboards(c.requests, c.store)
    _, board, _ = await c.boards.load(c.tenant, c.business, c.actor, c.requested.id)
    c.sha = board["content_sha256"]
    await c.boards.decide(
        c.tenant,
        c.business,
        c.actor,
        c.requested.id,
        StoryboardDecision(
            operation_id=uuid4(), version_id=board["version_id"], content_sha256=c.sha, decision="approve"
        ),
    )
    c.renderer.render.side_effect = MotionRenderError("MOTION_RENDER_EXECUTION_FAILED")
    e = replace(c.event, event_id=str(uuid5(c.body.operation_id, "motion.storyboard_approved")))
    with pytest.raises(MotionRenderError):
        await c.runner.run(e)
    c.recovery = MotionRenderRecovery(c.runner)
    c.args = (c.tenant, c.business, c.actor, c.requested.id, c.sha, IMAGE)
    c.renderer.image = IMAGE
    c.resume = replace(c.event, event_id=str(recovery_event(c.body.operation_id)))
    return c


async def test_recovery_uses_new_render_identity_without_repeating_plan_or_code(failed_render):
    c = failed_render
    eid = await c.recovery.request(*c.args)
    assert await c.recovery.request(*c.args) == eid
    c.renderer.render.side_effect = AsyncMock(return_value=c.rendered)
    # Reach the native renderer with restored composition; model output is irrelevant to this assertion.
    original = c.runner.render

    async def produce(row, token, prepared, composition):
        await original(row, token, prepared, 0, composition)
        return "rendered"

    c.runner.produce = produce
    assert await c.runner.run(c.resume) == "rendered"
    assert await c.runner.run(c.resume) == "already_claimed"
    assert c.provider.calls == ["plan", "implementation"]
    actual = c.renderer.render.call_args.kwargs["operation_id"]
    assert actual == uuid5(recovery_operation(c.body.operation_id), "render:0")
    async with c.database.transaction(c.tenant, c.actor) as s:
        row = await c.requests.row(s, c.tenant, c.business, c.requested.id)
        old = await c.checkpoints.effect(s, row, uuid5(c.body.operation_id, "render:0"))
        assert c.requests.context.open(old["response_ciphertext"])["status"] == "failed"
        assert (
            await s.scalar(
                text("SELECT count(*) FROM motion_render_versions WHERE tenant_id=:t AND request_id=:r"),
                {"t": c.tenant, "r": c.requested.id},
            )
            == 1
        )


@pytest.mark.parametrize(
    "change", ["image", "same", "hash", "state", "owner", "pending", "missing", "unknown_cost", "budget", "version"]
)
async def test_request_refuses_unsafe_render_recovery(failed_render, admin, seeded, change):
    c = failed_render
    args = list(c.args)
    if change == "image":
        args[-1] = "unbound:latest"
    elif change == "same":
        async with c.database.transaction(c.tenant, c.actor) as s:
            row = await c.requests.row(s, c.tenant, c.business, c.requested.id)
        args[-1] = c.requests.context.open(row["snapshot_ciphertext"])["execution"]["renderer_image"]
    elif change == "hash":
        args[-2] = "0" * 64
    else:
        async with admin.begin() as s:
            if change == "state":
                await s.execute(text("UPDATE motion_requests SET state='uncertain' WHERE id=:r"), {"r": c.requested.id})
            elif change == "owner":
                await s.execute(
                    text("UPDATE motion_requests SET actor_id=:a WHERE id=:r"), {"a": seeded["a2"], "r": c.requested.id}
                )
            elif change == "pending":
                await s.execute(
                    text("UPDATE motion_effects SET state='submitted' WHERE operation_id=:o"),
                    {"o": uuid5(c.body.operation_id, "generate:0")},
                )
            elif change == "missing":
                await s.execute(
                    text("DELETE FROM motion_effects WHERE operation_id=:o"),
                    {"o": uuid5(c.body.operation_id, "render:0")},
                )
            elif change == "unknown_cost":
                await s.execute(
                    text("UPDATE motion_effects SET estimated_usd_micros=NULL WHERE operation_id=:o"),
                    {"o": uuid5(c.body.operation_id, "generate:0")},
                )
            elif change == "budget":
                await s.execute(
                    text("UPDATE motion_requests SET budget_usd_micros=1 WHERE id=:r"), {"r": c.requested.id}
                )
            else:
                await s.execute(
                    text(
                        """INSERT INTO motion_render_versions(tenant_id,business_id,request_id,number,operation_id,
                        composition_ciphertext,object_key,sha256,size_bytes,evidence_ciphertext,diagnostics_ciphertext)
                        VALUES(:t,:b,:r,0,:o,'x','x',:h,1,'x','x')"""
                    ),
                    {"t": c.tenant, "b": c.business, "r": c.requested.id, "o": uuid4(), "h": "0" * 64},
                )
    with pytest.raises(AuthError):
        await c.recovery.request(*args)


@pytest.mark.parametrize(
    "change", ["conflict", "event", "missing", "executor", "context", "failed_again", "persist_failure"]
)
async def test_resume_is_fenced_and_failure_remains_durable(failed_render, change):
    c = failed_render
    if change != "missing":
        await c.recovery.request(*c.args)
    if change == "conflict":
        with pytest.raises(AuthError, match="CONFLICT"):
            await c.recovery.request(*c.args[:-1], "sha256:" + "e" * 64)
        return
    if change == "event":
        with pytest.raises(AuthError, match="EVENT_MISMATCH"):
            await c.recovery.run(replace(c.resume, event_id=str(uuid4())))
        return
    if change == "executor":
        c.renderer.image = "sha256:" + "e" * 64
    elif change == "context":
        c.runner.inputs.prepare = AsyncMock(side_effect=AuthError("MOTION_CONTEXT_CHANGED", 409))
    elif change == "persist_failure":
        c.runner.inputs.prepare = AsyncMock(side_effect=AuthError("MOTION_CONTEXT_CHANGED", 409))
        c.runner.fail = AsyncMock(side_effect=RuntimeError("database unavailable"))
        c.runner.effects.quarantine = AsyncMock()
    elif change == "failed_again":
        c.runner.produce = AsyncMock(side_effect=AuthError("MOTION_RENDER_EXECUTION_FAILED", 409))
    with pytest.raises(AuthError):
        await c.runner.run(c.resume)
