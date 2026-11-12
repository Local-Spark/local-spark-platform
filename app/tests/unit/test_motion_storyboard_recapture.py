"""Synthetic recovery guards: no paid retry, altered pixels or unrelated failed request."""

import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.adapters.motion_html_renderer import RenderBundle
from app.adapters.motion_inputs import PreparedMotionInput
from app.services.auth import AuthError
from app.services.motion_context import digest
from app.services.motion_elements import elements_hash
from app.services.motion_movement import movement_hash
from app.services.motion_storyboard_frames import storyboard_moments
from app.services.motion_storyboard_recapture import EVENT, MotionStoryboardRecapture, VerifiedRecaptureRenderer
from app.services.motion_temporal import POLICY_V3
from app.tests.unit.test_motion_plan import context
from app.tests.unit.test_motion_storyboards import board_case, board_output, boarded  # noqa: F401
from app.workflows.contracts import BusinessEvent


@pytest.fixture
def recapture_case(board_case, monkeypatch):  # noqa: F811
    c = board_case
    c.row.update(
        state="failed",
        failure_code="MOTION_EFFECT_ALREADY_CLAIMED",
        piece_id=None,
        budget_usd_micros=6250000,
        snapshot_ciphertext="snapshot",
    )
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V3
    ctx.update(
        request={"evolution": {"confirmed": True}},
        evolution={"synthetic": True},
        source={},
        kit={},
        authorized_audio={"mode": "silent", "tracks": []},
    )
    composition = boarded()
    pixels = board_output(composition, ctx)
    op = c.row["operation_id"]
    version = uuid5(op, "storyboard:0")
    receipts, effects = {}, {}

    def record(key, kind, response, request=None):
        a, b = str(key) + "-request", str(key) + "-response"
        receipts[a], receipts[b] = request, response
        effects[key] = dict(
            operation_id=key,
            kind=kind,
            state="received",
            request_hash=digest(request),
            request_ciphertext=a,
            response_ciphertext=b,
            reserved_usd_micros=0,
            estimated_usd_micros=0,
        )

    signed = dict(
        purpose="storyboard",
        composition=composition.model_dump(mode="json"),
        moments=storyboard_moments(composition, ctx),
        assets=[],
        movement_runtime_sha256=movement_hash(ctx),
        element_runtime_sha256=elements_hash(ctx),
    )
    expected = [{"ms": f.ms, "sha256": f.sha256} for f in pixels.evidence]
    record(version, "render", {"frames": expected}, signed)
    public = {k: v for k, v in ctx.items() if k != "evolution"}
    record(
        uuid5(op, "generate:0"),
        "generate",
        {"composition": signed["composition"]},
        {"payload": {"input": [{"content": [{"text": json.dumps({"authorized_context": public})}]}]}},
    )
    planned = composition.model_dump(mode="json", exclude={"html", "scene_init"})
    planned.setdefault("illustrations", [])
    record(uuid5(op, "generate:plan:0"), "generate", {"construction_plan": planned})
    runner = SimpleNamespace(
        requests=c.requests,
        store=c.store,
        inputs=SimpleNamespace(
            prepare=AsyncMock(return_value=PreparedMotionInput(ctx, (), (), 1000, ctx["authorized_audio"]))
        ),
        renderer=SimpleNamespace(),
        effects=SimpleNamespace(model=AsyncMock()),
        fail=AsyncMock(),
    )
    recovery = MotionStoryboardRecapture(runner)
    recovery.boards.payloads.open = AsyncMock(side_effect=lambda row, key: deepcopy(receipts[key]))
    monkeypatch.setattr("app.services.motion_storyboard_recapture._event", c.events)
    c.session.scalar.return_value = False
    c.session.execute.return_value = SimpleNamespace(
        mappings=lambda: SimpleNamespace(all=lambda: list(effects.values()))
    )
    return SimpleNamespace(
        c=c,
        service=recovery,
        runner=runner,
        effects=effects,
        receipts=receipts,
        ctx=ctx,
        signed=signed,
        expected=expected,
        pixels=pixels,
    )


async def test_evidence_requires_real_collision_and_matching_received_composition(recapture_case):
    v = recapture_case
    result = await v.service.evidence(v.c.row, v.effects)
    assert result[0] == boarded()
    version = uuid5(v.c.row["operation_id"], "storyboard:0")
    key = v.effects[version]["request_ciphertext"]
    v.receipts[key]["composition"]["html"] = "changed"
    with pytest.raises(AuthError, match="EVIDENCE_CHANGED"):
        await v.service.evidence(v.c.row, v.effects)
    with pytest.raises(AuthError, match="INELIGIBLE"):
        await v.service.evidence(v.c.row, {})


@pytest.mark.parametrize("change", ["actor", "state", "failure", "piece", "board", "unreceived", "unpriced", "budget"])
async def test_enqueue_rejects_unrelated_or_uncertain_work(recapture_case, change):
    v = recapture_case
    row = v.c.row
    args = (row["tenant_id"], row["business_id"], row["actor_id"], row["id"])
    if change == "actor":
        row["actor_id"] = uuid4()
    elif change == "state":
        row["state"] = "completed"
    elif change == "failure":
        row["failure_code"] = "OTHER"
    elif change == "piece":
        row["piece_id"] = uuid4()
    elif change == "board":
        v.c.session.scalar.return_value = True
    else:
        e = next(iter(v.effects.values()))
        if change == "unreceived":
            e["state"] = "submitted"
        elif change == "unpriced":
            e.update(reserved_usd_micros=1, estimated_usd_micros=None)
        else:
            e.update(reserved_usd_micros=7000000)
    with pytest.raises(AuthError, match="INELIGIBLE"):
        await v.service.enqueue(*args)
    v.c.events.assert_not_awaited()
    v.runner.effects.model.assert_not_awaited()


async def test_enqueue_is_audited_and_requires_unchanged_snapshot(recapture_case):
    v = recapture_case
    row = v.c.row
    args = (row["tenant_id"], row["business_id"], row["actor_id"], row["id"])
    result = await v.service.enqueue(*args)
    assert result["event_id"] == str(uuid5(row["operation_id"], EVENT))
    assert v.c.events.await_args.args[-1] == EVENT
    assert "state='queued'" in str(v.c.session.execute.await_args.args[0])
    v.service.snapshot = AsyncMock(side_effect=[(row, v.effects), ({**row, "failure_code": "changed"}, v.effects)])
    with pytest.raises(AuthError, match="FENCED"):
        await v.service.enqueue(*args)


@pytest.mark.parametrize("change", [None, "input", "pixels", "event"])
async def test_temporal_recovery_never_calls_provider_or_approves_board(recapture_case, change):
    v = recapture_case
    row = v.c.row
    event = BusinessEvent(
        str(uuid5(row["operation_id"], EVENT)),
        str(row["tenant_id"]),
        str(row["business_id"]),
        str(row["actor_id"]),
        str(row["operation_id"]),
    )
    v.service.snapshot = AsyncMock(return_value=(row, v.effects))
    v.c.session.scalar.return_value = change != "event"
    v.service.boards.capture = AsyncMock()
    if change == "input":
        v.runner.inputs.prepare.return_value = replace(
            v.runner.inputs.prepare.return_value, context={**v.ctx, "kit": {"changed": True}}
        )
    if change == "pixels":
        v.service.boards.capture.side_effect = AuthError("MOTION_RECAPTURE_PIXELS_CHANGED", 409)
    if change:
        with pytest.raises(AuthError):
            await v.service.run(event)
        if change != "event":
            v.runner.fail.assert_awaited_once()
    else:
        assert await v.service.run(event) == "awaiting_storyboard"
        assert v.service.boards.capture.await_args.kwargs["capture_id"] == uuid5(
            row["operation_id"], "storyboard:recapture:1"
        )
    v.runner.effects.model.assert_not_awaited()
    assert all(call.args[-1] != "motion.storyboard_approved" for call in v.c.events.await_args_list)


async def test_recapture_rejects_changed_pixels_and_any_mp4(recapture_case):
    v = recapture_case
    renderer = SimpleNamespace(render=AsyncMock(return_value=v.pixels))
    checked = VerifiedRecaptureRenderer(renderer, v.expected)
    bundle = RenderBundle("<html/>", "", (), {"mode": "silent", "tracks": []}, 64, 64, 30, 1000, frames_only=True)
    assert await checked.render(bundle, operation_id=uuid4()) == v.pixels
    with pytest.raises(AuthError, match="FRAMES_ONLY"):
        await checked.render(replace(bundle, frames_only=False), operation_id=uuid4())
    renderer.render.return_value = replace(v.pixels, mp4=b"not allowed")
    with pytest.raises(AuthError, match="PIXELS_CHANGED"):
        await checked.render(bundle, operation_id=uuid4())
    checked.expected = []
    renderer.render.return_value = v.pixels
    with pytest.raises(AuthError, match="PIXELS_CHANGED"):
        await checked.render(bundle, operation_id=uuid4())
