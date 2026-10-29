"""Restricted dispatch never turns an ambiguous visual effect into a retry."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.services.media_dispatch import claim_previews, dispatch_previews, reconcile_stale_previews
from app.services.visual_effect_guard import visual_operation
from app.tests.integration.test_visual_effect_guard import guarded_case as guarded_case

pytestmark = pytest.mark.integration


async def _queue_real(admin, c):
    # Exercise dispatch in isolation. The source fixture supplies a completely
    # synthetic request; API/contract authorization is covered by the path test.
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE media_previews SET generation_mode='visual_ai',state='pending',
              attempts=0,dispatch_fence=0,dispatch_owner=NULL,dispatch_lease_until=NULL WHERE id=:id"""),
            {"id": c.preview.id},
        )


async def test_disabled_dispatch_leaves_real_request_queued_and_ambiguous_start_keeps_its_fence(admin, guarded_case):
    c = guarded_case
    await _queue_real(admin, c)
    client = AsyncMock()
    assert await dispatch_previews(c.worker, client, c.cfg, uuid4()) == 0
    client.start_workflow.assert_not_awaited()
    cfg = c.cfg.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "openai_api_key": SecretStr("synthetic-unused"),
            "service_agreement_required": True,
        }
    )
    client.start_workflow.side_effect = RuntimeError("synthetic lost acknowledgement")
    assert await dispatch_previews(c.worker, client, cfg, uuid4()) == 1
    assert client.start_workflow.await_args.args == ("VisualGenerationWorkflow",)
    assert client.start_workflow.await_args.kwargs["id"] == f"visual-preview/{c.preview.id}"
    assert client.start_workflow.await_args.kwargs["args"] == [str(c.preview.id), 1]
    assert await dispatch_previews(c.worker, client, cfg, uuid4()) == 0
    async with admin.connect() as connection:
        row = (
            (
                await connection.execute(
                    text("""SELECT state,dispatch_fence,attempts,
                  extract(epoch FROM dispatch_lease_until-now()) AS remaining
                  FROM media_previews WHERE id=:id"""),
                    {"id": c.preview.id},
                )
            )
            .mappings()
            .one()
        )
        assert row["state"] == "rendering" and row["dispatch_fence"] == 1 and row["attempts"] == 1
        assert 710 < row["remaining"] <= 720


@pytest.mark.parametrize("reserved", [False, True])
async def test_expired_real_lease_never_redispatches_or_releases_admission_or_money(
    admin, database, guarded_case, reserved
):
    c = guarded_case
    assert await c.guard.admit(c.scope)
    reservation = None
    if reserved:
        reservation = await c.ledger.reserve(
            c.tenant, c.business, c.actor, visual_operation(c.preview.id), "fake", "synthetic", "a" * 64, 70
        )
    await _queue_real(admin, c)
    claim = (await claim_previews(c.worker, uuid4(), visual_enabled=True))[0]
    assert claim.fence == c.scope.fence and claim.generation_mode == "visual_ai"
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE media_previews SET dispatch_lease_until=now()-interval '1 second' WHERE id=:id"),
            {"id": c.preview.id},
        )
    assert await claim_previews(c.worker, uuid4(), visual_enabled=True) == []
    assert await reconcile_stale_previews(c.worker) == 1
    assert await reconcile_stale_previews(c.worker) == 0
    assert await claim_previews(c.worker, uuid4(), visual_enabled=True) == []
    async with database.transaction(c.tenant, c.actor) as session:
        assert await session.scalar(text("SELECT state FROM visual_consent_runs")) == "in_flight"
    async with admin.connect() as connection:
        row = (
            (await connection.execute(text("SELECT * FROM media_previews WHERE id=:id"), {"id": c.preview.id}))
            .mappings()
            .one()
        )
        assert row["state"] == "failed" and row["error_code"] == "VISUAL_OUTCOME_UNCERTAIN"
        assert row["attempts"] == 1 and row["dispatch_fence"] == claim.fence
        if reservation is not None:
            assert (
                await connection.scalar(
                    text("SELECT state FROM visual_cost_reservations WHERE id=:id"), {"id": reservation.id}
                )
                == "submitted"
            )
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
