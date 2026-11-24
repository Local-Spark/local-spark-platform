"""Dedicated _test PostgreSQL: pinned capture and renderer admission; providers are fake."""

import hashlib
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy import text

from app.adapters.motion_html_renderer import RenderAsset
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_protocols import MotionModelResult
from app.services.motion_video_reel import VIDEO_REEL_CONTRACT
from app.services.motion_video_scene_visibility import CONTRACT as SCENE_CONTRACT
from app.tests.integration.test_motion_production import create, motion_case  # noqa: F401
from app.tests.unit.test_motion_video_reel import CTX, artifact, video_case

pytestmark = pytest.mark.integration


async def test_video_capture_is_immutable_and_idempotent(motion_case, admin):  # noqa: F811
    c = motion_case
    requested = await create(c)
    assert (await create(c)).id == requested.id
    async with admin.connect() as conn:
        sealed = await conn.scalar(text("SELECT snapshot_ciphertext FROM motion_requests"))
        snapshot = c.requests.context.open(sealed)
        assert snapshot["video_reel_contract"] == VIDEO_REEL_CONTRACT
        assert snapshot["video_scene_visibility_contract"] == SCENE_CONTRACT
        assert snapshot["skill"]["id"] == "instagram-reel-video-v19"
        assert capture_motion_guidance(c.body, previous=snapshot)["video_reel_contract"] == VIDEO_REEL_CONTRACT
        assert await conn.scalar(text("SELECT count(*) FROM motion_requests")) == 1
        assert await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.requested'")) == 1
        assert await conn.scalar(text("SELECT count(*) FROM audit_events")) > 0
    assert c.provider.calls == []
    c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("valid", [True, False])
async def test_video_gate_precedes_render_and_pins_executed_bundle(motion_case, admin, valid):  # noqa: F811
    c = motion_case
    prepared = c.inputs.prepare.return_value
    logo = b"synthetic kit logo"
    c.inputs.prepare.return_value = replace(
        prepared,
        context={**prepared.context, **CTX, "video_scene_visibility_contract": SCENE_CONTRACT},
        duration_ms=3000,
        assets=(*prepared.assets, RenderAsset("assets/logo.png", "image/png", logo, hashlib.sha256(logo).hexdigest())),
    )
    data = video_case()
    if not valid:
        data["motion_plan"]["scenes"][0].pop("video_layout")
    c.provider.submit = AsyncMock(return_value=MotionModelResult(composition=artifact(data), estimated_usd_micros=0))
    await create(c)
    row, token = await c.requests.begin(c.tenant, c.business, c.actor, c.body.operation_id, UUID(c.event.event_id))
    # Use the real durable render path without claiming audiovisual acceptance.
    if valid:
        await c.runner.render(row, token, c.inputs.prepare.return_value, 0, artifact(data))
        bundle = c.renderer.render.await_args.args[0]
        assert bundle.scene_init.index("installVideoSceneVisibilityV1") < bundle.scene_init.index("installVideoReelV1")
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM motion_effects WHERE kind='render'")) == 1
    else:
        with pytest.raises(AuthError, match="MOTION_VIDEO_LAYOUT_REQUIRED"):
            await c.runner.render(row, token, c.inputs.prepare.return_value, 0, artifact(data))
        c.renderer.render.assert_not_awaited()
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM motion_effects WHERE kind='render'")) == 0
