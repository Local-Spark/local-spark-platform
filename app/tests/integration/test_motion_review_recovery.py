"""Received MP4 resumes only unsubmitted critique; no repeat of render or generation."""

from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.motion_review_recovery import MotionReviewRecovery, review_recovery_event
from app.tests.integration.test_motion_checkpoints import checkpoint_case  # noqa: F401
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.integration.test_motion_render_recovery import IMAGE, failed_render  # noqa: F401

pytestmark = pytest.mark.integration


@pytest.fixture
async def unreviewed_video(failed_render):  # noqa: F811
    c = failed_render
    await c.recovery.request(*c.args)
    c.renderer.render.side_effect = AsyncMock(
        return_value=replace(c.rendered, diagnostics={**c.rendered.diagnostics, "executor_image": IMAGE})
    )
    original = c.runner.produce

    async def interrupted(row, token, prepared, composition):
        await c.runner.render(row, token, prepared, 0, composition)
        raise AuthError("MOTION_EXECUTION_FAILED", 409)

    c.runner.produce = interrupted
    with pytest.raises(AuthError, match="EXECUTION_FAILED"):
        await c.runner.run(c.resume)
    c.runner.produce = original
    async with c.database.transaction(c.tenant, c.actor) as s:
        c.version = dict(
            (
                await s.execute(
                    text("SELECT * FROM motion_render_versions WHERE tenant_id=:t AND request_id=:r"),
                    {"t": c.tenant, "r": c.requested.id},
                )
            )
            .mappings()
            .one()
        )
    c.review_recovery = MotionReviewRecovery(c.runner)
    c.review_args = (c.tenant, c.business, c.actor, c.requested.id, c.version["sha256"])
    c.review_event = replace(c.event, event_id=str(review_recovery_event(c.body.operation_id)))
    return c


async def test_received_version_reaches_critique_without_render_or_generation(unreviewed_video):
    c = unreviewed_video
    eid = await c.review_recovery.request(*c.review_args)
    assert await c.review_recovery.request(*c.review_args) == eid
    renders = c.renderer.render.await_count
    c.runner.produce = AsyncMock(return_value="completed")
    assert await c.runner.run(c.review_event) == "completed"
    assert await c.runner.run(c.review_event) == "already_claimed"
    candidate = c.runner.produce.await_args.kwargs["initial_candidate"]
    assert candidate.rendered.mp4 == c.rendered.mp4 and candidate.artifact.sha256 == c.version["sha256"]
    assert c.renderer.render.await_count == renders and c.provider.calls == ["plan", "implementation"]


@pytest.mark.parametrize("change", ["hash", "owner", "state", "pending", "review_started", "budget", "conflict"])
async def test_review_continuation_requires_exact_closed_effects(unreviewed_video, admin, seeded, change):
    c = unreviewed_video
    args = list(c.review_args)
    if change == "hash":
        args[-1] = "0" * 64
    elif change == "conflict":
        await c.review_recovery.request(*args)
        args[-1] = "0" * 64
    else:
        async with admin.begin() as s:
            if change == "owner":
                await s.execute(
                    text("UPDATE motion_requests SET actor_id=:a WHERE id=:r"), {"a": seeded["a2"], "r": c.requested.id}
                )
            elif change == "state":
                await s.execute(text("UPDATE motion_requests SET state='uncertain' WHERE id=:r"), {"r": c.requested.id})
            elif change == "pending":
                await s.execute(
                    text("UPDATE motion_effects SET state='submitted' WHERE operation_id=:o"),
                    {"o": uuid5(c.body.operation_id, "generate:0")},
                )
            elif change == "review_started":
                await s.execute(
                    text(
                        """INSERT INTO motion_effects(tenant_id,business_id,request_id,operation_id,kind,state,
                        request_hash,request_ciphertext) VALUES(:t,:b,:r,:o,'review','received',:h,'x')"""
                    ),
                    {
                        "t": c.tenant,
                        "b": c.business,
                        "r": c.requested.id,
                        "o": uuid5(c.body.operation_id, "review:0"),
                        "h": "0" * 64,
                    },
                )
            else:
                await s.execute(
                    text("UPDATE motion_requests SET budget_usd_micros=1 WHERE id=:r"), {"r": c.requested.id}
                )
    with pytest.raises(AuthError):
        await c.review_recovery.request(*args)


@pytest.mark.parametrize(
    "change",
    [
        "event",
        "missing",
        "changed",
        "namespace",
        "media",
        "composition",
        "frame",
        "empty",
        "quarantine",
        "original_namespace",
    ],
)
async def test_resume_rechecks_artifact_and_preserves_failed_continuation(unreviewed_video, admin, change):
    c = unreviewed_video
    if change != "missing":
        await c.review_recovery.request(*c.review_args)
    if change == "event":
        with pytest.raises(AuthError):
            await c.review_recovery.run(replace(c.review_event, event_id=str(uuid4())))
        return
    if change in ("changed", "namespace", "original_namespace", "composition"):
        async with admin.begin() as s:
            if change == "changed":
                await s.execute(text("UPDATE motion_requests SET state='uncertain' WHERE id=:r"), {"r": c.requested.id})
            elif change == "composition":
                await s.execute(
                    text("UPDATE motion_render_versions SET composition_ciphertext=:p WHERE request_id=:r"),
                    {"p": c.requests.context.seal({}), "r": c.requested.id},
                )
            else:
                await s.execute(
                    text("UPDATE motion_render_versions SET operation_id=:o WHERE request_id=:r"),
                    {
                        "o": uuid5(c.body.operation_id, "render:0") if change == "original_namespace" else uuid4(),
                        "r": c.requested.id,
                    },
                )
    elif change == "media":
        c.store.objects[c.version["object_key"]] = b"changed"
    elif change == "frame":
        c.review_recovery.checks.payloads.open = AsyncMock(
            return_value={"frames": [{"png": "eA==", "sha256": "0" * 64}]}
        )
    elif change == "empty":
        c.review_recovery.checks.payloads.open = AsyncMock(return_value={"frames": []})
    elif change == "quarantine":
        c.runner.inputs.prepare = AsyncMock(side_effect=AuthError("MOTION_CONTEXT_CHANGED", 409))
        c.runner.fail = AsyncMock(side_effect=RuntimeError("database unavailable"))
        c.runner.effects.quarantine = AsyncMock()
    if change == "original_namespace":
        c.runner.produce = AsyncMock(return_value="completed")
        assert await c.review_recovery.run(c.review_event) == "completed"
        return
    # Direct service call retains the altered evidence reader in frame/empty cases.
    with pytest.raises(AuthError):
        await c.review_recovery.run(c.review_event)
