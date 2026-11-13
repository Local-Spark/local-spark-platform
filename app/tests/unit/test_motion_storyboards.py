"""Exact board decision, representative frames and reuse without paid regeneration."""

import hashlib
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.adapters.motion_html_renderer import MotionRenderError, RenderedMotion, _decode, _prepare
from app.schemas.motion_production import HTMLMotionComposition, MotionRequest
from app.schemas.motion_storyboards import StoryboardDecision
from app.services.auth import AuthError
from app.services.motion_context import digest
from app.services.motion_storyboard_frames import storyboard_moments
from app.services.motion_storyboards import MotionStoryboards
from app.services.motion_temporal import POLICY_V2, POLICY_V3
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_html_renderer import bundle, output, packed
from app.tests.unit.test_motion_plan import context, planned


def boarded():
    data = planned().model_dump(mode="json")
    for scene in data["motion_plan"]["scenes"]:
        scene["keyframe_ms"] = (scene["start_ms"] + scene["end_ms"]) // 2
    return HTMLMotionComposition.model_validate(data)


def board_output(value, ctx=None):
    frames = []
    for moment in storyboard_moments(value, ctx):
        index = moment["frame_index"]
        raw = frame(round(index * 1000 / 30))
        frames.append(replace(raw, frame_index=index, pts_seconds=f"{index / 30:.6f}"))
    return RenderedMotion(b"", hashlib.sha256(b"").hexdigest(), tuple(frames), {"evidence_source": "browser_keyframes"})


def test_history_does_not_acquire_an_approval_gate():
    request = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Fictício")
    assert not request.storyboard and "storyboard" not in request.model_dump()
    assert "keyframe_ms" not in planned().motion_plan.scenes[0].model_dump()


@pytest.mark.parametrize("change", ["missing", "outside", "duplicate", "quantized_outside"])
def test_no_missing_or_ambiguous_scene_moment(change):
    data = boarded().model_dump(mode="json")
    scenes = data["motion_plan"]["scenes"]
    if change == "missing":
        scenes[0]["keyframe_ms"] = None
    elif change == "outside":
        scenes[0]["keyframe_ms"] = 600
    elif change == "duplicate":
        scenes[0]["keyframe_ms"] = scenes[1]["keyframe_ms"] = 550
    else:
        scenes[1]["start_ms"] = 501
        scenes[1]["elements"][0]["beats"][0]["start_ms"] = 501
        scenes[1]["keyframe_ms"] = 501
    with pytest.raises(AuthError, match="MOTION_STORYBOARD_"):
        storyboard_moments(HTMLMotionComposition.model_validate(data))


def test_frames_only_output_cannot_be_confused_with_decoded_video(tmp_path):
    cfg = _prepare(bundle(frames_only=True), tmp_path / "board")
    assert cfg["version"] == 2
    header, raw = output(cfg)
    with pytest.raises(MotionRenderError):
        _decode(packed(header, raw), cfg)
    video_size = header["video"]["size"]
    header["version"] = 2
    header["video"] = {"size": 0, "sha256": hashlib.sha256(b"").hexdigest()}
    header["diagnostics"]["evidence_source"] = "browser_keyframes"
    restored = _decode(packed(header, raw[video_size:]), cfg)
    assert restored.mp4 == b"" and len(restored.evidence) == 3
    with pytest.raises(MotionRenderError):
        _prepare(bundle(frames_only=True, sample_times_ms=()), tmp_path / "empty")


@pytest.fixture
def board_case(monkeypatch):
    row = {key: uuid4() for key in ("tenant_id", "business_id", "actor_id", "id", "operation_id", "execution_token")}
    row.update(state="running", source_fingerprint="source-fingerprint")
    board = {
        "version_id": uuid4(),
        "content_sha256": "a" * 64,
        "state": "awaiting_approval",
        "decision_operation_id": None,
        "decision_hash": None,
        "payload_ciphertext": "private",
    }
    session = SimpleNamespace(execute=AsyncMock(), scalar=AsyncMock(return_value=True))
    active = []

    @asynccontextmanager
    async def transaction(*args):
        active.append(True)
        try:
            yield session
        finally:
            active.pop()

    requests = SimpleNamespace(
        database=SimpleNamespace(transaction=transaction),
        row=AsyncMock(return_value=row),
        gate=SimpleNamespace(
            _lock=AsyncMock(), _state=AsyncMock(return_value="active"), finish_withdrawal_if_idle=AsyncMock()
        ),
        context=SimpleNamespace(seal=lambda obj: "encrypted", open=lambda value: {}),
        _admission=AsyncMock(),
        current=AsyncMock(),
        locked_running=AsyncMock(),
        settings=SimpleNamespace(),
    )
    store = SimpleNamespace(single_attempt_put=True, put=AsyncMock(), get_image=AsyncMock())
    service = MotionStoryboards(requests, store)
    service.board = AsyncMock(return_value=board)
    events = AsyncMock()
    monkeypatch.setattr("app.services.motion_storyboards._event", events)
    monkeypatch.setattr("app.services.motion_storyboards.WhatsAppMaterialsService._require_owner", AsyncMock())
    monkeypatch.setattr("app.services.motion_storyboards.VisualPendingChanges.apply_pending_in_session", AsyncMock())
    monkeypatch.setattr("app.services.motion_storyboards.apply_pending_script_changes", AsyncMock())
    body = StoryboardDecision(
        operation_id=uuid4(), version_id=board["version_id"], content_sha256=board["content_sha256"], decision="approve"
    )
    return SimpleNamespace(
        row=row,
        board=board,
        session=session,
        requests=requests,
        store=store,
        service=service,
        events=events,
        body=body,
        active=active,
    )


@pytest.mark.parametrize("failure", [None, "version", "hash", "state", "actor", "context", "revoked"])
async def test_approval_requires_exact_live_owner_version(board_case, failure):
    c = board_case
    if failure == "version":
        c.board["version_id"] = uuid4()
    elif failure == "hash":
        c.board["content_sha256"] = "b" * 64
    elif failure == "state":
        c.board["state"] = "approved"
    elif failure == "actor":
        c.row["actor_id"] = uuid4()
    elif failure == "context":
        c.requests.current.side_effect = AuthError("MOTION_CONTEXT_CHANGED", 409)
    elif failure == "revoked":
        c.requests.gate._lock.side_effect = AuthError("OWNER_REQUIRED", 403)
    actor = c.row["actor_id"] if failure != "actor" else uuid4()
    args = c.row["tenant_id"], c.row["business_id"], actor, c.row["id"], c.body
    if failure:
        with pytest.raises(AuthError):
            await c.service.decide(*args)
        c.events.assert_not_awaited()
    else:
        assert await c.service.decide(*args) == {"state": "approved"}
        c.requests.current.assert_awaited_once()
        assert c.events.await_args_list[-1].args[-1] == "motion.storyboard_approved"
        assert c.events.await_args_list[-1].args[-2] == c.row["operation_id"]
        c.store.put.assert_not_awaited()


async def test_decision_replay_never_enqueues_a_second_execution(board_case):
    c = board_case
    c.board.update(
        state="rendering",
        decision_operation_id=c.body.operation_id,
        decision_hash=digest(c.body.model_dump(mode="json")),
    )
    args = c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"]
    assert await c.service.decide(*args, c.body) == {"state": "rendering"}
    c.events.assert_not_awaited()
    with pytest.raises(AuthError, match="OPERATION_CONFLICT"):
        await c.service.decide(*args, c.body.model_copy(update={"decision": "reject"}))


async def test_rejection_records_feedback_without_render_or_new_model_call(board_case):
    c = board_case
    result = await c.service.decide(
        c.row["tenant_id"],
        c.row["business_id"],
        c.row["actor_id"],
        c.row["id"],
        c.body.model_copy(update={"decision": "reject", "feedback": "Texto pequeno"}),
    )
    assert result == {"state": "rejected"}
    c.requests.current.assert_not_awaited()
    assert not any(call.args[-1] == "motion.storyboard_approved" for call in c.events.await_args_list)
    assert any("MOTION_STORYBOARD_REJECTED" in str(call.args[0]) for call in c.session.execute.await_args_list)


async def test_gallery_uses_verified_pixels_and_escapes_model_text(board_case):
    c = board_case
    png = frame().png
    payload = {
        "frames": [
            {
                "scene_id": "scene",
                "message": "<script>bad</script>",
                "at_ms": 300,
                "sha256": hashlib.sha256(png).hexdigest(),
                "size_bytes": len(png),
                "object_key": "private/frame",
            }
        ]
    }
    c.service.load = AsyncMock(return_value=(c.row, c.board, payload))
    c.store.get_image.return_value = png
    page = await c.service.gallery(c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"])
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "data:image/png;base64," in page and "private/frame" not in page
    c.store.get_image.return_value = b"changed"
    with pytest.raises(AuthError, match="BYTES_CHANGED"):
        await c.service.gallery(c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"])


@pytest.mark.parametrize("mode", ["plain", "art", "audio", "store"])
async def test_capture_persists_every_scene_and_provenance_without_mp4(board_case, mode):
    from app.adapters.motion_html_renderer import RenderAsset
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.tests.unit.test_motion_illustrations import composition_with_art, image_result

    c = board_case
    composition = boarded()
    assets = ()
    if mode == "art":
        data = composition_with_art().model_dump(mode="json")
        for scene in data["motion_plan"]["scenes"]:
            scene["keyframe_ms"] = (scene["start_ms"] + scene["end_ms"]) // 2
        composition = HTMLMotionComposition.model_validate(data)
        art = image_result()
        assets = (RenderAsset(composition.illustrations[0].asset_id, "image/png", art.content, art.sha256),)
    pixels = board_output(composition)
    renderer = SimpleNamespace(render=AsyncMock(return_value=pixels))
    saved = []

    async def persist(*args):
        saved.append(args[-1])
        return "encrypted board"

    effects = SimpleNamespace(claim=AsyncMock(), received=AsyncMock(), persist_payload=AsyncMock(side_effect=persist))

    async def put(key, media):
        assert not c.active
        c.store.get_image.return_value = media.data

    c.store.put.side_effect = put
    prepared = PreparedMotionInput(context(), assets, (), 1000, {"mode": "silent", "tracks": []})
    if mode in {"audio", "store"}:
        if mode == "audio":
            prepared = replace(prepared, audio={"mode": "mix", "tracks": []})
        else:
            c.store.single_attempt_put = False
        with pytest.raises(AuthError, match="(ORIGINAL_AUDIO_CHANGED|STORAGE_SINGLE_ATTEMPT_REQUIRED)"):
            await c.service.capture(c.row, c.row["execution_token"], prepared, composition, renderer, effects)
        c.store.put.assert_not_awaited()
        return
    await c.service.capture(c.row, c.row["execution_token"], prepared, composition, renderer, effects)
    assert renderer.render.await_args.args[0].frames_only is True
    assert len(saved[0]["frames"]) == 2 and saved[0]["composition"] == composition.model_dump(mode="json")
    assert bool(saved[0]["illustrations"]) == (mode == "art")
    assert c.store.put.await_count == 2
    assert c.events.await_args.args[-1] == "motion.storyboard_ready"
    assert "awaiting_approval" in str(c.session.execute.await_args.args[0])


@pytest.mark.parametrize("policy", [POLICY_V2, POLICY_V3])
async def test_v2_preview_keeps_sequences_and_unique_durable_frame_ids(board_case, policy):
    from app.adapters.motion_inputs import PreparedMotionInput

    c = board_case
    composition = boarded()
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = policy
    pixels = board_output(composition, ctx)
    renderer = SimpleNamespace(render=AsyncMock(return_value=pixels))
    saved = []

    async def persist(*args):
        saved.append(args[-1])
        return "encrypted board"

    effects = SimpleNamespace(claim=AsyncMock(), received=AsyncMock(), persist_payload=AsyncMock(side_effect=persist))

    async def put(key, media):
        assert not c.active
        c.store.get_image.return_value = media.data

    c.store.put.side_effect = put
    prepared = PreparedMotionInput(ctx, (), (), 1000, {"mode": "silent", "tracks": []})
    await c.service.capture(c.row, c.row["execution_token"], prepared, composition, renderer, effects)
    payload = saved[0]
    assert len(payload["frames"]) > 2 and len(payload["frames"]) <= 20
    assert len({item["object_key"] for item in payload["frames"]}) == len(payload["frames"])
    assert any(item.get("kind") == "transition" for item in payload["frames"])
    assert payload["temporal_preview"]["policy"] == policy
    assert not payload["temporal_preview"]["incomplete_events"]
    assert payload["asset_hashes"] == []
    c.service.load = AsyncMock(return_value=(c.row, c.board, payload))
    png = pixels.evidence[0].png
    c.service.read_png = AsyncMock(return_value=png)
    page = await c.service.gallery(c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"])
    assert "Prévia amostrada" in page and "passagens não selecionados" in page
    assert "transition-" in page and "não demonstram movimento contínuo" in page


@pytest.mark.parametrize(
    "state,valid", [("approved", True), ("rendering", True), ("awaiting_approval", True), ("approved", False)]
)
async def test_resume_needs_real_outbox_approval_and_fences_redelivery(board_case, state, valid):
    from app.workflows.contracts import BusinessEvent

    c = board_case
    c.board["state"] = state
    operation = c.row["operation_id"]
    c.session.scalar.return_value = valid
    event = BusinessEvent(
        str(uuid5(operation, "motion.storyboard_approved")),
        str(c.row["tenant_id"]),
        str(c.row["business_id"]),
        str(c.row["actor_id"]),
        str(operation),
    )
    if not valid:
        with pytest.raises(AuthError, match="EVENT_MISMATCH"):
            await c.service.begin_resume(event)
    else:
        result = await c.service.begin_resume(event)
        assert (result is not None) == (state == "approved")
        if result:
            assert result[1] == c.row["execution_token"]
            assert "state='rendering'" in str(c.session.execute.await_args.args[0])
    c.store.put.assert_not_awaited()


async def test_restore_approved_art_uses_private_bytes_and_never_calls_a_provider(board_case):
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.services.motion_elements import elements_hash
    from app.services.motion_movement import movement_hash
    from app.tests.unit.test_motion_illustrations import composition_with_art, image_result

    c = board_case
    composition = composition_with_art()
    art = image_result()
    payload = {
        "composition": composition.model_dump(mode="json"),
        "context": context(),
        "source_fingerprint": c.row["source_fingerprint"],
        "asset_hashes": [{"id": composition.illustrations[0].asset_id, "sha256": art.sha256}],
        "runtime_hashes": [movement_hash(context()), elements_hash(context())],
        "illustrations": [
            {
                "asset_id": composition.illustrations[0].asset_id,
                "object_key": "private/art",
                "sha256": art.sha256,
                "size_bytes": len(art.content),
            }
        ],
    }
    c.board["content_sha256"] = digest(payload)
    c.service.payloads.open = AsyncMock(return_value=payload)
    c.store.get_image.return_value = art.content
    prepared = PreparedMotionInput(context(), (), (), 1000, {"mode": "silent", "tracks": []})
    restored, value = await c.service.restore(c.row, c.board, prepared)
    assert value == composition and restored.assets[0].data == art.content
    assert restored.asset_previews[0][0] == composition.illustrations[0].asset_id
    c.store.put.assert_not_awaited()
    c.board["content_sha256"] = "f" * 64
    with pytest.raises(AuthError, match="BYTES_CHANGED"):
        await c.service.restore(c.row, c.board, prepared)


@pytest.mark.parametrize("change", [None, "asset", "direction", "composition"])
async def test_v2_resume_binds_approved_material_and_direction(board_case, change):
    from app.adapters.motion_html_renderer import RenderAsset
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.services.motion_elements import elements_hash
    from app.services.motion_movement import movement_hash

    c = board_case
    ctx = context()
    ctx["request"] = {"scene_direction": {"version": "original"}}
    data = b"synthetic"
    asset = RenderAsset("assets/source.mp4", "video/mp4", data, hashlib.sha256(data).hexdigest())
    payload = {
        "composition": boarded().model_dump(mode="json"),
        "context": deepcopy(ctx),
        "source_fingerprint": c.row["source_fingerprint"],
        "illustrations": [],
        "asset_hashes": [{"id": asset.id, "sha256": asset.sha256}],
        "runtime_hashes": [movement_hash(ctx), elements_hash(ctx)],
    }
    c.board["content_sha256"] = digest(payload)
    if change == "asset":
        asset = replace(asset, data=b"modified")
    elif change == "direction":
        ctx["request"]["scene_direction"]["version"] = "changed"
    elif change == "composition":
        payload["composition"]["html"] = "changed"
    c.service.payloads.open = AsyncMock(return_value=payload)
    prepared = PreparedMotionInput(ctx, (asset,), (), 1000, {"mode": "silent", "tracks": []})
    if change:
        with pytest.raises(AuthError, match="BYTES_CHANGED"):
            await c.service.restore(c.row, c.board, prepared)
    else:
        _, composition = await c.service.restore(c.row, c.board, prepared)
        assert composition == boarded()


async def test_relay_resumes_through_temporal_with_separate_durable_workflow_identity():
    from app.services.outbox import ClaimedEvent, _start_workflow
    from app.workflows.contracts import BusinessEvent

    operation = uuid4()
    event = BusinessEvent(
        str(uuid5(operation, "motion.storyboard_approved")), str(uuid4()), str(uuid4()), str(uuid4()), str(operation)
    )
    client = SimpleNamespace(start_workflow=AsyncMock())
    await _start_workflow(
        client, SimpleNamespace(temporal_task_queue="synthetic"), ClaimedEvent(event, 1, "motion.storyboard_approved")
    )
    assert client.start_workflow.await_args.args == ("MotionProductionWorkflow", event)
    assert client.start_workflow.await_args.kwargs["id"].startswith("motion-storyboard-approved/")


async def test_storyboard_routes_return_private_gallery_and_exact_decision(board_case, monkeypatch):
    from fastapi import Response

    from app.api.v1 import motion_requests as routes

    c = board_case
    payload = {"frames": [{"scene_id": "scene", "message": "Convite", "at_ms": 300, "sha256": "a" * 64}]}
    c.service.load = AsyncMock(return_value=(c.row, c.board, payload))
    c.service.gallery = AsyncMock(return_value="<html>Quadros completos</html>")
    c.service.decide = AsyncMock(return_value={"state": "approved"})
    monkeypatch.setattr(routes, "boards", lambda _: c.service)
    ids = (c.row["tenant_id"], c.row["business_id"], c.row["id"])
    response = Response()
    result = await routes.read_storyboard(*ids, object(), response, c.row["actor_id"])
    assert result.version_id == c.board["version_id"] and response.headers["cache-control"] == "no-store"
    gallery = await routes.storyboard_gallery(*ids, object(), c.row["actor_id"])
    assert (
        gallery.headers["cache-control"] == "no-store"
        and "frame-ancestors" in gallery.headers["content-security-policy"]
    )
    assert await routes.decide_storyboard(*ids, c.body, object(), response, c.row["actor_id"]) == {"state": "approved"}


def test_storyboard_frame_guard_rejects_mp4_and_unbound_frame_identity():
    comp = boarded()
    moments, rendered = storyboard_moments(comp), board_output(comp)
    for invalid in (
        replace(rendered, mp4=b"video"),
        replace(rendered, evidence=()),
        replace(rendered, evidence=(replace(rendered.evidence[0], sha256="f" * 64), *rendered.evidence[1:])),
    ):
        with pytest.raises(AuthError, match="FRAMES_INVALID"):
            MotionStoryboards.validate_frames(invalid, moments)


def test_structural_storyboard_rejects_an_unproven_beat():
    rendered = board_output(boarded())
    png = b"\x89PNG\r\n\x1a\n" + b"x" * 16
    frame = replace(rendered.evidence[0], png=png, sha256=hashlib.sha256(png).hexdigest(), frame_index=0, ms=0)
    with pytest.raises(AuthError, match="MOTION_STRUCTURAL_FLOOR_REJECTED"):
        MotionStoryboards.validate_frames(
            replace(rendered, evidence=(frame,)),
            ({"scene_id": "s", "kind": "structural_start", "frame_index": 0},),
        )


async def test_storyboard_lookup_load_and_approval_fail_closed_on_missing_or_changed_state(board_case):
    c = board_case
    c.session.execute.return_value = SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))
    with pytest.raises(AuthError, match="STORYBOARD_NOT_FOUND"):
        await MotionStoryboards.board(c.session, c.row["tenant_id"], c.row["business_id"], c.row["id"])
    c.service.payloads.open = AsyncMock(return_value={"changed": True})
    args = (c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"])
    with pytest.raises(AuthError, match="BYTES_CHANGED"):
        await c.service.load(*args)
    c.row["state"] = "failed"
    with pytest.raises(AuthError, match="EXECUTION_FENCED"):
        await c.service.decide(*args, c.body)
    c.events.assert_not_awaited()


async def test_gallery_labels_real_baseline_pixels_and_rejects_tampering(board_case):
    import base64

    c, raster = board_case, frame(100)
    payload = {
        "frames": [],
        "baseline_evidence": [{"ms": 100, "sha256": raster.sha256, "png": base64.b64encode(raster.png).decode()}],
    }
    c.service.load = AsyncMock(return_value=(c.row, c.board, payload))
    args = (c.row["tenant_id"], c.row["business_id"], c.row["actor_id"], c.row["id"])
    assert "Peça de referência" in await c.service.gallery(*args)
    payload["baseline_evidence"][0]["sha256"] = "f" * 64
    with pytest.raises(AuthError, match="EVOLUTION_EVIDENCE_INVALID"):
        await c.service.gallery(*args)


async def test_resume_recompiles_planned_sound_and_refuses_a_different_captured_mix(board_case):
    from app.tests.unit.test_motion_audiovisual import natural_plan, natural_prepared

    c, prepared = board_case, natural_prepared()
    composition = HTMLMotionComposition(
        **natural_plan().model_dump(), html="<div></div>", scene_init="window.seek=()=>{}"
    )
    payload = {
        "composition": composition.model_dump(mode="json"),
        "context": {**prepared.context, "authorized_soundtrack": {"unapproved_mix": True}},
        "source_fingerprint": c.row["source_fingerprint"],
        "illustrations": [],
    }
    c.board["content_sha256"] = digest(payload)
    c.service.payloads.open = AsyncMock(return_value=payload)
    with pytest.raises(AuthError, match="STORYBOARD_BYTES_CHANGED"):
        await c.service.restore(c.row, c.board, prepared)
