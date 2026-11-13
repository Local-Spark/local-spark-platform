"""Real restricted PostgreSQL admission/decisions; synthetic model/media, never paid IO or render."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy import text

from app.schemas.motion_preparation import MotionCheckpointDecision
from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_checkpoints import APPROVED, MotionCheckpoints, checkpoint_id
from app.services.motion_protocols import MotionModelResult
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_preparation import body
from app.tests.unit.test_motion_storyboards import board_output, boarded
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


@pytest.fixture
async def checkpoint_case(motion_case, request):  # noqa: F811
    c = motion_case
    c.cfg = c.cfg.model_copy(update={"motion_storyboard_enabled": True})
    c.requests.settings = c.requests.context.settings = c.cfg
    c.body = body().model_copy(update={"operation_id": c.body.operation_id, "source_asset_id": c.source})
    if getattr(request, "param", None) == "unresolved":
        c.body = c.body.model_copy(
            update={"preparation": c.body.preparation.model_copy(update={"unresolved": ("Confirmar intenção",)})}
        )
    composition = boarded()
    composition = composition.model_copy(
        update={"motion_plan": composition.motion_plan.model_copy(update={"style_id": None})}
    )
    data = composition.model_dump(mode="json", exclude={"html", "scene_init"})
    data.setdefault("illustrations", [])
    plan = MotionConstructionPlan.model_validate(data)
    prior = c.inputs.prepare.return_value

    async def prepare(snapshot):
        context = {
            k: v
            for k, v in snapshot.items()
            if k not in {"tenant_id", "business_id", "source", "logo", "execution", "references"}
        }
        context.update(
            source={"asset_id": "assets/source.mp4", "sha256": prior.assets[0].sha256, "duration_ms": 1000},
            output={"width": 720, "height": 1280, "fps": 30, "duration_ms": 1000},
            authorized_audio=prior.audio,
        )
        c.renderer.render.return_value = board_output(composition, context)
        return replace(prior, context=context, source_frames=(frame(100), frame(300)))

    async def submit(job, _payload):
        c.provider.calls.append("plan" if job.construction_plan is None else "implementation")
        if job.construction_plan is None:
            return MotionModelResult(construction_plan=plan, estimated_usd_micros=0)
        return MotionModelResult(composition=composition, estimated_usd_micros=0)

    c.inputs.prepare.side_effect = prepare
    c.provider.submit = submit
    c.store.get_image = c.store.get_video
    c.checkpoints = MotionCheckpoints(c.requests, c.store)
    c.requested = await c.requests.create(c.tenant, c.business, c.actor, c.body)
    return c


def event(c, stage):
    return BusinessEvent(
        str(uuid5(c.body.operation_id, APPROVED[stage])),
        str(c.tenant),
        str(c.business),
        str(c.actor),
        str(c.body.operation_id),
    )


async def inspect(c, stage):
    return await c.checkpoints.present(c.tenant, c.business, c.actor, c.requested.id, stage)


async def decision(c, stage, value="approve"):
    view = await inspect(c, stage)
    return MotionCheckpointDecision(
        operation_id=uuid4(),
        content_sha256=view["content_sha256"],
        decision=value,
        note="Conferência sintética do artefato exato",
    )


async def decide(c, stage, value):
    return await c.checkpoints.decide(c.tenant, c.business, c.actor, c.requested.id, stage, value)


async def test_persisted_plan_then_code_then_explicit_render_without_repeating_calls(checkpoint_case, admin):
    c = checkpoint_case
    assert await c.runner.run(c.event) == "awaiting_plan"
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()
    view = await inspect(c, "plan")
    assert not view["rendered"] and view["decision"] is None
    assert "html" not in view["packet"]["artifact"]
    assert view["packet"]["context"]["request"]["preparation"]["client_message"] == c.body.preparation.client_message
    async with c.database.transaction(c.tenant, c.actor) as session:
        row = await c.requests.row(session, c.tenant, c.business, c.requested.id)
        assert row["state"] == "running" and row["execution_token"] is None
    async with c.worker.transaction(c.tenant, c.actor) as session:
        assert await session.scalar(text("SELECT motion_asset_in_use(:source)"), {"source": c.source})
    with pytest.raises(AuthError, match="APPROVAL_REQUIRED"):
        await c.runner.run(event(c, "plan"))
    first = await decision(c, "plan")
    with pytest.raises(AuthError, match="CHANGED"):
        await decide(c, "plan", first.model_copy(update={"content_sha256": "0" * 64}))
    # Concurrent identical approvals enqueue only one event and do not execute work in the API.
    await asyncio.gather(decide(c, "plan", first), decide(c, "plan", first))
    assert c.provider.calls == ["plan"]
    with pytest.raises(AuthError, match="CONFLICT"):
        await decide(c, "plan", first.model_copy(update={"note": "different"}))
    assert await c.runner.run(event(c, "plan")) == "awaiting_render"
    assert c.provider.calls == ["plan", "implementation"]
    c.renderer.render.assert_not_awaited()
    assert await c.runner.run(event(c, "plan")) == "already_claimed"
    assert await c.runner.run(c.event) == "already_claimed"
    rendered = await inspect(c, "render")
    assert rendered["packet"]["artifact"]["html"] and not rendered["rendered"]
    assert rendered["model_input"]["kind"] == "generate"
    async with admin.connect() as conn:
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM motion_effects WHERE request_id=:id AND kind='render'"),
                {"id": c.requested.id},
            )
            == 0
        )
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM outbox_events WHERE id=:id"),
                {"id": uuid5(c.body.operation_id, APPROVED["plan"])},
            )
            == 1
        )
    final = await decision(c, "render")
    await decide(c, "render", final)
    assert await c.runner.run(event(c, "render")) == "awaiting_storyboard"
    c.renderer.render.assert_awaited_once()
    assert c.renderer.render.await_args.args[0].frames_only
    assert c.provider.calls == ["plan", "implementation"]
    assert await c.runner.run(event(c, "render")) == "already_claimed"
    async with admin.connect() as conn:
        assert (
            await conn.scalar(text("SELECT state FROM motion_storyboards WHERE request_id=:id"), {"id": c.requested.id})
            == "awaiting_approval"
        )
        assert (
            await conn.scalar(text("SELECT piece_id FROM motion_requests WHERE id=:id"), {"id": c.requested.id}) is None
        )


@pytest.mark.parametrize("stage", ["plan", "render"])
async def test_rejection_is_terminal_and_never_authorizes_next_stage(checkpoint_case, stage):
    c = checkpoint_case
    await c.runner.run(c.event)
    if stage == "render":
        await decide(c, "plan", await decision(c, "plan"))
        await c.runner.run(event(c, "plan"))
    reject = await decision(c, stage, "reject")
    await decide(c, stage, reject)
    assert await decide(c, stage, reject) == {"decision": "reject", "stage": stage}
    row = await c.requests.get(c.tenant, c.business, c.actor, c.requested.id)
    assert row.state == "failed" and row.failure_code == "MOTION_CHECKPOINT_REJECTED"
    with pytest.raises(AuthError, match="APPROVAL_REQUIRED"):
        await c.runner.run(event(c, stage))
    c.renderer.render.assert_not_awaited()


async def test_checkpoint_scope_and_changed_source_are_checked_before_implementation(checkpoint_case, seeded, admin):
    c = checkpoint_case
    await c.runner.run(c.event)
    with pytest.raises(AuthError):
        await c.checkpoints.present(seeded["t2"], c.business, seeded["a2"], c.requested.id, "plan")
    approval = await decision(c, "plan")
    await decide(c, "plan", approval)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE whatsapp_material_assets SET sha256=:sha WHERE id=:id"), {"id": c.source, "sha": "b" * 64}
        )
    with pytest.raises(AuthError, match="CONTEXT_CHANGED"):
        await c.runner.run(event(c, "plan"))
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()
    assert (await c.requests.get(c.tenant, c.business, c.actor, c.requested.id)).state == "failed"
    assert await c.runner.run(event(c, "plan")) == "already_claimed"


@pytest.mark.parametrize("checkpoint_case", ["unresolved"], indirect=True)
async def test_unresolved_preparation_cannot_be_approved_but_can_be_rejected(checkpoint_case):
    c = checkpoint_case
    await c.runner.run(c.event)
    with pytest.raises(AuthError, match="PREPARATION_UNRESOLVED"):
        await decide(c, "plan", await decision(c, "plan"))
    await decide(c, "plan", await decision(c, "plan", "reject"))
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("changed", ["input", "implementation", "renderer", "record_failure"])
async def test_resume_failure_is_terminal_and_does_not_repeat_effects(checkpoint_case, changed):
    c = checkpoint_case
    await c.runner.run(c.event)
    await decide(c, "plan", await decision(c, "plan"))
    stage = "plan"
    if changed in {"input", "record_failure"}:
        if changed == "record_failure":
            c.runner.fail = AsyncMock(side_effect=RuntimeError("Synthetic write failure"))
        prepare = c.inputs.prepare.side_effect

        async def different(snapshot):
            return replace(await prepare(snapshot), source_frames=(frame(400),))

        c.inputs.prepare.side_effect = different
    elif changed == "implementation":
        c.provider.submit = AsyncMock(side_effect=AuthError("MODEL_FAILED", 409))
    else:
        await c.runner.run(event(c, "plan"))
        await decide(c, "render", await decision(c, "render"))
        c.renderer.render.side_effect = AuthError("RENDER_FAILED", 409)
        stage = "render"
    with pytest.raises(AuthError):
        await c.runner.run(event(c, stage))
    state = (await c.requests.get(c.tenant, c.business, c.actor, c.requested.id)).state
    assert state == ("uncertain" if changed in {"implementation", "record_failure"} else "failed")
    assert await c.runner.run(event(c, stage)) == "already_claimed"
    if changed != "renderer":
        c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("changed", ["checkpoint", "model", "output", "decision"])
async def test_changed_evidence_never_authorizes_implementation(checkpoint_case, admin, changed):
    c = checkpoint_case
    await c.runner.run(c.event)
    approval = await decision(c, "plan")
    model = uuid5(c.body.operation_id, "generate:plan:0")
    checkpoint = checkpoint_id(c.body.operation_id, "plan")
    if changed == "decision":
        await decide(c, "plan", approval)
    operation = (
        checkpoint if changed == "checkpoint" else uuid5(checkpoint, "decision") if changed == "decision" else model
    )
    async with admin.begin() as conn:
        if changed == "output":
            await conn.execute(
                text("UPDATE motion_effects SET response_ciphertext=:payload WHERE operation_id=:op"),
                {"op": operation, "payload": c.requests.context.seal({"construction_plan": {}})},
            )
        else:
            await conn.execute(
                text("UPDATE motion_effects SET request_hash=:hash WHERE operation_id=:op"),
                {"op": operation, "hash": "0" * 64},
            )
    with pytest.raises(AuthError):
        if changed == "decision":
            await c.runner.run(event(c, "plan"))
        else:
            await inspect(c, "plan")
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


async def test_private_api_returns_exact_model_io_and_queues_only_decision(
    checkpoint_case, api, headers, monkeypatch, seeded
):
    from app.api.v1 import motion_requests as routes

    c = checkpoint_case
    monkeypatch.setattr(routes, "boards", lambda _: SimpleNamespace(requests=c.requests, store=c.store))
    await c.runner.run(c.event)
    path = f"/api/v1/organizations/{c.tenant}/businesses/{c.business}/motion-requests/{c.requested.id}/checkpoints"
    response = await api.get(path + "/plan", headers=headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["model_output"]["construction_plan"] == payload["packet"]["artifact"]
    assert (
        payload["model_input"]["context"]["request"]["preparation"]["client_message"]
        == c.body.preparation.client_message
    )
    assert (await api.get(path + "/render", headers=headers)).status_code == 409
    assert (await api.get(path + "/unknown", headers=headers)).status_code == 422
    assert (await api.get(path.replace(str(c.tenant), str(seeded["t2"])) + "/plan", headers=headers)).status_code != 200
    approval = await decision(c, "plan")
    response = await api.post(path + "/plan/decisions", headers=headers, json=approval.model_dump(mode="json"))
    assert response.status_code == 200 and response.json() == {"decision": "approve", "stage": "plan"}
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("changed", ["owner", "decide_while_executing", "resume_while_executing", "event"])
async def test_checkpoint_fences_owner_event_and_execution_lease(checkpoint_case, admin, seeded, changed):
    c = checkpoint_case
    await c.runner.run(c.event)
    approval = await decision(c, "plan")
    if changed == "resume_while_executing":
        await decide(c, "plan", approval)
    if changed != "event":
        async with admin.begin() as conn:
            if changed == "owner":
                await conn.execute(
                    text("UPDATE motion_requests SET actor_id=:actor WHERE id=:id"),
                    {"actor": seeded["a2"], "id": c.requested.id},
                )
            else:
                await conn.execute(
                    text("UPDATE motion_requests SET execution_token=:token WHERE id=:id"),
                    {"token": uuid4(), "id": c.requested.id},
                )
    with pytest.raises(AuthError, match="OWNER_CHANGED|NOT_WAITING|EVENT_MISMATCH"):
        if changed == "owner":
            await inspect(c, "plan")
        elif changed == "decide_while_executing":
            await decide(c, "plan", approval)
        else:
            value = event(c, "plan")
            if changed == "event":
                value = replace(value, event_id=str(uuid4()))
            await c.checkpoints.begin(value, "plan")
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


async def test_relay_claims_approvals_but_not_unapproved_ready_notifications(checkpoint_case, relay_database):
    from app.services.outbox import claim_events

    c = checkpoint_case
    await c.runner.run(c.event)
    await decide(c, "plan", await decision(c, "plan"))
    await c.runner.run(event(c, "plan"))
    await decide(c, "render", await decision(c, "render"))
    assert not await claim_events(relay_database, uuid4())
    claimed = await claim_events(relay_database, uuid4(), include_motion=True)
    assert {item.event_type for item in claimed} == {
        "motion.requested",
        "motion.plan_approved",
        "motion.render_approved",
    }
    c.renderer.render.assert_not_awaited()


async def failed_before_code(c):
    await c.runner.run(c.event)
    await decide(c, "plan", await decision(c, "plan"))
    build = c.provider.build_request

    def preflight_failure(job):
        if job.construction_plan is not None:
            raise RuntimeError("Synthetic local preflight failure before claim")
        return build(job)

    c.provider.build_request = preflight_failure
    with pytest.raises(RuntimeError):
        await c.runner.run(event(c, "plan"))
    c.provider.build_request = build
    assert (await c.requests.get(c.tenant, c.business, c.actor, c.requested.id)).state == "failed"
    assert c.provider.calls == ["plan"]
    return await decision(c, "plan")


async def test_explicit_pre_submission_recovery_preserves_approval_and_runs_only_code_once(checkpoint_case):
    c = checkpoint_case
    approval = await failed_before_code(c)
    args = (c.tenant, c.business, c.actor, c.requested.id, approval)
    first, second = await asyncio.gather(
        c.checkpoints.recover_before_submission(*args), c.checkpoints.recover_before_submission(*args)
    )
    assert first == second
    with pytest.raises(AuthError, match="RECOVERY_CONFLICT"):
        await c.checkpoints.recover_before_submission(*args[:-1], approval.model_copy(update={"note": "Changed"}))
    assert await c.runner.run(event(c, "plan")) == "already_claimed"
    recovered = replace(event(c, "plan"), event_id=first["event_id"])
    assert await c.runner.run(recovered) == "awaiting_render"
    assert await c.runner.run(recovered) == "already_claimed"
    assert c.provider.calls == ["plan", "implementation"]
    c.renderer.render.assert_not_awaited()
    assert (await inspect(c, "plan"))["decision"]["decision"] == "approve"
    assert (await inspect(c, "render"))["decision"] is None
    with pytest.raises(AuthError, match="EVENT_MISMATCH"):
        await c.checkpoints.begin(recovered, "render")


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "reject",
        "state",
        "approval_missing",
        "approval_unconsumed",
        "approval_hash",
        "approval_rejected",
        "code_claim",
        "payload_upload",
        "source",
        "illustrations",
    ],
)
async def test_recovery_refuses_uncertain_or_started_work_and_changed_inputs(checkpoint_case, admin, change):
    from app.services.motion_context import digest

    c = checkpoint_case
    approval = await failed_before_code(c)
    op = uuid5(checkpoint_id(c.body.operation_id, "plan"), "decision")
    if change == "hash":
        approval = approval.model_copy(update={"content_sha256": "0" * 64})
    elif change == "reject":
        approval = approval.model_copy(update={"decision": "reject"})
    elif change == "illustrations":
        original = c.checkpoints.load

        async def with_images(*args):
            row, checkpoint, decision_row, packet = await original(*args)
            packet["artifact"]["illustrations"] = ["Synthetic declared image"]
            return row, checkpoint, decision_row, packet

        c.checkpoints.load = with_images
    else:
        async with admin.begin() as conn:
            if change == "state":
                await conn.execute(
                    text("UPDATE motion_requests SET state='uncertain' WHERE id=:id"), {"id": c.requested.id}
                )
            elif change == "approval_missing":
                await conn.execute(text("DELETE FROM motion_effects WHERE operation_id=:op"), {"op": op})
            elif change == "approval_unconsumed":
                await conn.execute(text("UPDATE motion_effects SET state='claimed' WHERE operation_id=:op"), {"op": op})
            elif change == "approval_hash":
                await conn.execute(
                    text("UPDATE motion_effects SET request_hash=:hash WHERE operation_id=:op"),
                    {"op": op, "hash": "0" * 64},
                )
            elif change == "approval_rejected":
                view = await inspect(c, "plan")
                value = {**view["decision"], "decision": "reject"}
                await conn.execute(
                    text(
                        "UPDATE motion_effects SET request_hash=:hash,request_ciphertext=:payload "
                        "WHERE operation_id=:op"
                    ),
                    {"op": op, "hash": digest(value), "payload": c.requests.context.seal(value)},
                )
            elif change == "source":
                await conn.execute(
                    text("UPDATE whatsapp_material_assets SET sha256=:sha WHERE id=:source"),
                    {"source": c.source, "sha": "b" * 64},
                )
            else:
                code = uuid5(c.body.operation_id, "generate:0")
                operation = code if change == "code_claim" else uuid5(code, "payload:request")
                await conn.execute(
                    text("""INSERT INTO motion_effects(tenant_id,business_id,request_id,operation_id,
                    kind,state,request_hash,request_ciphertext) VALUES(:tenant,:business,:request,:op,:kind,
                    'claimed',:hash,:payload)"""),
                    {
                        "tenant": c.tenant,
                        "business": c.business,
                        "request": c.requested.id,
                        "op": operation,
                        "kind": "generate" if change == "code_claim" else "upload",
                        "hash": "a" * 64,
                        "payload": c.requests.context.seal({"synthetic": True}),
                    },
                )
    with pytest.raises(AuthError, match="(RECOVERY_|CONTEXT_CHANGED)"):
        await c.checkpoints.recover_before_submission(c.tenant, c.business, c.actor, c.requested.id, approval)
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("change", ["marker_hash", "marker_version", "marker_state", "outbox_missing"])
async def test_recovery_event_requires_its_bound_receipt_and_outbox(checkpoint_case, admin, change):
    from app.services.motion_context import digest

    c = checkpoint_case
    approval = await failed_before_code(c)
    result = await c.checkpoints.recover_before_submission(c.tenant, c.business, c.actor, c.requested.id, approval)
    recovered = replace(event(c, "plan"), event_id=result["event_id"])
    recovery_id = uuid5(UUID(result["event_id"]), "checkpoint-recovery")
    async with admin.begin() as conn:
        if change == "outbox_missing":
            await conn.execute(text("DELETE FROM outbox_events WHERE id=:id"), {"id": UUID(result["event_id"])})
        elif change == "marker_hash":
            await conn.execute(
                text("UPDATE motion_effects SET request_hash=:hash WHERE operation_id=:op"),
                {"op": recovery_id, "hash": "0" * 64},
            )
        elif change == "marker_state":
            await conn.execute(
                text("UPDATE motion_effects SET state='submitted' WHERE operation_id=:op"), {"op": recovery_id}
            )
        else:
            ciphertext = await conn.scalar(
                text("SELECT request_ciphertext FROM motion_effects WHERE operation_id=:op"), {"op": recovery_id}
            )
            value = c.requests.context.open(ciphertext)
            value["version"] = "forged"
            await conn.execute(
                text("UPDATE motion_effects SET request_hash=:hash,request_ciphertext=:payload WHERE operation_id=:op"),
                {"op": recovery_id, "hash": digest(value), "payload": c.requests.context.seal(value)},
            )
    with pytest.raises(AuthError, match="(RECOVERY_INVALID|APPROVAL_REQUIRED)"):
        await c.runner.run(recovered)
    assert c.provider.calls == ["plan"]
    c.renderer.render.assert_not_awaited()


@pytest.mark.parametrize("change", ["missing", "not_received", "input_payload"])
async def test_present_never_exposes_checkpoint_without_its_model_receipt(checkpoint_case, admin, change):
    c = checkpoint_case
    await c.runner.run(c.event)
    operation = uuid5(c.body.operation_id, "generate:plan:0")
    async with admin.begin() as conn:
        if change == "missing":
            await conn.execute(text("DELETE FROM motion_effects WHERE operation_id=:op"), {"op": operation})
        elif change == "not_received":
            await conn.execute(
                text("UPDATE motion_effects SET state='claimed' WHERE operation_id=:op"), {"op": operation}
            )
        else:
            await conn.execute(
                text("UPDATE motion_effects SET request_ciphertext=:payload WHERE operation_id=:op"),
                {"op": operation, "payload": c.requests.context.seal({"tampered": "synthetic input"})},
            )
    with pytest.raises(AuthError, match="MOTION_CHECKPOINT_CHANGED"):
        await inspect(c, "plan")
