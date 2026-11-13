"""Stop conditions and invalid IO boundaries, independently of a model/vendor."""

import hashlib
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.adapters.motion_html_renderer import RenderedMotion
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import MotionAudio, MotionReview
from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.motion_orchestrator import Candidate, MotionOrchestrator
from app.services.motion_protocols import MotionModelResult
from app.services.motion_review import MotionReviewError
from app.tests.unit.test_motion_ai import composition, frame, review_data
from app.workflows.contracts import BusinessEvent


@pytest.fixture
def unit_case(settings):
    row = {key: uuid4() for key in ("tenant_id", "business_id", "actor_id", "operation_id", "id")}
    row.update(max_corrections=2, snapshot_ciphertext="private", format="reel")
    token = uuid4()
    session = AsyncMock()
    session.scalar.return_value = 1

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    requests = SimpleNamespace(
        begin=AsyncMock(return_value=(row, token)),
        context=SimpleNamespace(open=lambda _: {}, seal=lambda _: "ciphertext"),
        database=SimpleNamespace(transaction=transaction),
        settings=settings,
        locked_running=AsyncMock(),
        row=AsyncMock(return_value={"state": "running", "execution_token": token}),
        gate=SimpleNamespace(
            _lock=AsyncMock(), _state=AsyncMock(return_value="active"), finish_withdrawal_if_idle=AsyncMock()
        ),
    )
    rendered = RenderedMotion(b"synthetic", hashlib.sha256(b"synthetic").hexdigest(), (frame(),), {})
    prepared = PreparedMotionInput({}, (), (frame(),), 1000, {"mode": "silent", "tracks": []})
    store = SimpleNamespace(single_attempt_put=True, put=AsyncMock(), get_video=AsyncMock(return_value=rendered.mp4))
    runner = MotionOrchestrator(
        requests,
        object(),
        SimpleNamespace(provider="fake"),
        SimpleNamespace(render=AsyncMock(return_value=rendered)),
        SimpleNamespace(prepare=AsyncMock(return_value=prepared)),
        store,
    )
    runner.effects = SimpleNamespace(
        model=AsyncMock(),
        persist_payload=AsyncMock(return_value="ciphertext"),
        claim=AsyncMock(),
        received=AsyncMock(),
        capacity_for_correction=AsyncMock(return_value=True),
        quarantine=AsyncMock(),
    )
    event = BusinessEvent(
        str(uuid5(row["operation_id"], "motion.requested")),
        str(row["tenant_id"]),
        str(row["business_id"]),
        str(row["actor_id"]),
        str(row["operation_id"]),
    )
    return SimpleNamespace(
        runner=runner, row=row, token=token, session=session, rendered=rendered, prepared=prepared, event=event
    )


def review(*, revise=False, previous=False, **updates):
    data = review_data(revise=revise, previous=frame() if previous else None)
    data.update(updates)
    return MotionModelResult(review=MotionReview.model_validate(data))


def stub_render(case):
    async def render(_row, _token, _prepared, number, value):
        return Candidate(
            number, value, case.rendered, PieceArtifact(uuid4(), "private", case.rendered.sha256, "video/mp4", 9)
        )

    case.runner.render = AsyncMock(side_effect=render)
    case.runner.record_review = AsyncMock()
    case.runner.complete = AsyncMock()
    case.runner.fail = AsyncMock()


@pytest.mark.parametrize("number", [0, 1])
async def test_missing_direction_blocks_generation_and_correction_before_render_claim(unit_case, number):
    from app.services.motion_creative import motion_creative_contract

    c = unit_case
    prepared = replace(c.prepared, context={"creative_contract": motion_creative_contract()})
    with pytest.raises(AuthError, match="MOTION_PLAN_REQUIRED"):
        await c.runner.render(c.row, c.token, prepared, number, composition())
    c.runner.effects.claim.assert_not_awaited()
    c.runner.renderer.render.assert_not_awaited()
    c.runner.store.put.assert_not_awaited()


async def test_movement_runtime_is_bound_to_effect_and_render_bundle(unit_case):
    from app.services.motion_creative import motion_creative_contract
    from app.tests.unit.test_motion_plan import planned

    c = unit_case
    contract = motion_creative_contract()
    prepared = replace(c.prepared, context={"creative_contract": contract, "styles": [{"id": "editorial"}]})
    await c.runner.render(c.row, c.token, prepared, 0, planned())
    expected = contract["movement_runtime"]["sha256"]
    assert c.runner.renderer.render.call_args.args[0].movement_runtime_sha256 == expected
    assert c.runner.effects.claim.call_args_list[0].args[-1]["movement_runtime_sha256"] == expected


@pytest.mark.parametrize("number", [0, 1])
async def test_missing_scene_direction_stops_before_render_cost_and_storage(unit_case, number):
    from app.services.motion_creative import motion_creative_contract
    from app.tests.unit.test_motion_plan import planned

    c = unit_case
    prepared = replace(c.prepared, context={"creative_contract": motion_creative_contract()})
    value = planned().model_copy(update={"scene_direction": None})
    with pytest.raises(AuthError, match="MOTION_SCENE_DIRECTION_REQUIRED"):
        await c.runner.render(c.row, c.token, prepared, number, value)
    c.runner.effects.claim.assert_not_awaited()
    c.runner.renderer.render.assert_not_awaited()
    c.runner.store.put.assert_not_awaited()


@pytest.mark.parametrize("number", [0, 1])
async def test_provided_direction_cannot_be_replaced_at_render_admission(unit_case, number):
    from app.tests.unit.test_motion_plan import planned
    from app.tests.unit.test_motion_visual_direction import provided_context

    c = unit_case
    ctx = provided_context()
    ctx["request"]["scene_direction"]["scenes"][0]["composition"] = "Composição fornecida distinta"
    prepared = replace(c.prepared, context=ctx)
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_CHANGED"):
        await c.runner.render(c.row, c.token, prepared, number, planned())
    c.runner.effects.claim.assert_not_awaited()
    c.runner.renderer.render.assert_not_awaited()
    c.runner.store.put.assert_not_awaited()


async def test_generator_cannot_replace_direction_and_continue_to_assets_or_render(unit_case):
    from app.tests.unit.test_motion_plan import planned
    from app.tests.unit.test_motion_visual_direction import provided_context

    c = unit_case
    ctx = provided_context()
    ctx["request"]["scene_direction"]["scenes"][0]["composition"] = "Composição fornecida distinta"
    c.runner.inputs.prepare.return_value = replace(c.prepared, context=ctx)
    c.runner.effects.model.return_value = MotionModelResult(composition=planned())
    c.runner.fail = AsyncMock()
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_CHANGED"):
        await c.runner.run(c.event)
    c.runner.effects.model.assert_awaited_once()
    c.runner.renderer.render.assert_not_awaited()
    c.runner.effects.claim.assert_not_awaited()


async def test_unavailable_runtime_stops_before_paid_generation(unit_case):
    c = unit_case
    c.runner.inputs.prepare.return_value = replace(
        c.prepared, context={"creative_contract": {"movement_runtime": {"version": "future", "sha256": "f" * 64}}}
    )
    c.runner.fail = AsyncMock()
    with pytest.raises(AuthError, match="MOVEMENT_VERSION_UNAVAILABLE"):
        await c.runner.run(c.event)
    c.runner.effects.model.assert_not_awaited()
    c.runner.renderer.render.assert_not_awaited()


async def test_temporal_sampling_flows_through_render_review_and_durable_evidence(unit_case):
    from app.services.motion_temporal import sample_times
    from app.tests.unit.test_motion_temporal import temporal_case

    c = unit_case
    job, data, manifest = temporal_case()
    c.runner.inputs.prepare.return_value = replace(c.prepared, context=job.context)
    c.runner.renderer.render.return_value = replace(c.rendered, evidence=job.frames)
    c.runner.effects.model.side_effect = [
        MotionModelResult(composition=job.composition),
        MotionModelResult(review=MotionReview.model_validate(data)),
    ]
    c.runner.record_review = AsyncMock()
    c.runner.complete = AsyncMock()
    assert await c.runner.run(c.event) == "completed"
    assert c.runner.effects.model.await_count == 2
    samples = sample_times(job.composition, job.context)
    assert c.runner.renderer.render.call_args.args[0].sample_times_ms == samples
    assert c.runner.effects.claim.call_args_list[0].args[-1]["sample_times_ms"] == list(samples)
    assert c.runner.effects.persist_payload.call_args.args[-1]["temporal_sampling"] == manifest


@pytest.mark.parametrize("stage", ["generate", "review", "correct"])
async def test_missing_provider_result_stops_before_another_effect(unit_case, stage):
    c = unit_case
    stub_render(c)
    valid = MotionModelResult(composition=composition())
    outputs = {
        "generate": [MotionModelResult()],
        "review": [valid, MotionModelResult()],
        "correct": [valid, review(revise=True), MotionModelResult()],
    }
    c.runner.effects.model.side_effect = outputs[stage]
    label = {"generate": "GENERATION", "correct": "CORRECTION", "review": "REVIEW"}[stage]
    with pytest.raises(AuthError, match=f"MOTION_{label}_RESULT_INVALID"):
        await c.runner.run(c.event)
    c.runner.complete.assert_not_awaited()
    assert c.runner.effects.model.await_count == len(outputs[stage])


async def test_second_correction_requires_first_gain_and_remaining_actionable_issue(unit_case):
    c = unit_case
    stub_render(c)
    source = frame(150, "blue")
    c.runner.inputs.prepare.return_value = replace(c.prepared, source_frames=(source,))
    valid = MotionModelResult(composition=composition())
    c.runner.effects.model.side_effect = [
        valid,
        review(revise=True),
        valid,
        review(revise=True, previous=True),
        valid,
        review(previous=True),
    ]
    assert await c.runner.run(c.event) == "completed"
    assert c.runner.effects.model.await_count == 6
    chosen = c.runner.complete.call_args.args[-1]
    assert chosen.number == 2
    assert [v.number for v in c.runner.complete.call_args.args[-2]] == [0, 1, 2]
    requests = [call.args[-1] for call in c.runner.effects.model.call_args_list]
    assert all(request.source_frames == (source,) for request in requests)
    assert requests[0].frames == ()
    assert all(request.frames == c.rendered.evidence for request in requests[1:])


async def test_selected_references_survive_generation_review_and_correction(unit_case):
    from app.services.motion_repertoire import load_repertoire_images
    from app.tests.unit.test_motion_repertoire import context

    c = unit_case
    stub_render(c)
    ctx = context()
    images = load_repertoire_images(ctx)
    # This test isolates orchestration; runtime/plan compatibility is checked by loader tests.
    prepared = replace(c.prepared, context={"repertoire": ctx["repertoire"]}, reference_images=images)
    c.runner.inputs.prepare.return_value = prepared
    valid = MotionModelResult(composition=composition())
    c.runner.effects.model.side_effect = [valid, review(revise=True), valid, review(previous=True)]
    assert await c.runner.run(c.event) == "completed"
    jobs = [call.args[-1] for call in c.runner.effects.model.call_args_list]
    assert [job.kind for job in jobs] == ["generate", "review", "correct", "review"]
    assert all(job.reference_images == images for job in jobs)
    assert all(job.assets == prepared.assets for job in jobs)


async def test_service_rejects_unsent_critic_evidence_from_any_provider(unit_case):
    c = unit_case
    stub_render(c)
    data = review_data()
    data["criteria"][0]["evidence"][0]["sha256"] = "f" * 64
    c.runner.effects.model.side_effect = [
        MotionModelResult(composition=composition()),
        MotionModelResult(review=MotionReview.model_validate(data)),
    ]
    with pytest.raises(MotionReviewError, match="MOTION_REVIEW_UNSENT_EVIDENCE"):
        await c.runner.run(c.event)
    c.runner.record_review.assert_not_awaited()
    c.runner.complete.assert_not_awaited()


async def test_duplicate_activity_and_failed_owner_cleanup_cannot_repeat(unit_case):
    c = unit_case
    c.runner.requests.begin.return_value = None
    assert await c.runner.run(c.event) == "already_claimed"
    c.runner.effects.model.assert_not_awaited()
    c.runner.requests.begin.return_value = (c.row, c.token)
    c.runner.inputs.prepare.side_effect = RuntimeError("private input")
    c.runner.fail = AsyncMock(side_effect=AuthError("BUSINESS_OWNER_REQUIRED", 403))
    with pytest.raises(RuntimeError, match="private input"):
        await c.runner.run(c.event)
    c.runner.effects.quarantine.assert_awaited_once_with(c.row, c.token)


@pytest.mark.parametrize("kind", ["audio", "hash", "no_evidence", "empty", "large", "unsafe_store", "storage_hash"])
async def test_invalid_render_or_storage_never_enters_review(unit_case, kind):
    c = unit_case
    value = composition()
    if kind == "audio":
        value = value.model_copy(
            update={
                "audio": MotionAudio(
                    mode="mix",
                    tracks=(
                        {
                            "asset_id": "assets/source.mp4",
                            "offset_ms": 0,
                            "trim_start_ms": 0,
                            "trim_end_ms": 10,
                            "volume": 1,
                        },
                    ),
                )
            }
        )
    elif kind == "hash":
        c.runner.renderer.render.return_value = replace(c.rendered, sha256="a" * 64)
    elif kind == "no_evidence":
        c.runner.renderer.render.return_value = replace(c.rendered, evidence=())
    elif kind in {"empty", "large"}:

        class LargeBytes(bytes):
            def __len__(self):
                return 50 * 1024 * 1024 + 1

        data = b"" if kind == "empty" else LargeBytes(b"large")
        c.runner.renderer.render.return_value = replace(c.rendered, mp4=data, sha256=hashlib.sha256(data).hexdigest())
    elif kind == "unsafe_store":
        c.runner.store.single_attempt_put = False
    else:
        c.runner.store.get_video.return_value = b"different"
    with pytest.raises(AuthError):
        await c.runner.render(c.row, c.token, c.prepared, 0, value)
    c.session.execute.assert_not_awaited()


async def test_review_is_compare_and_swap_and_cannot_be_overwritten(unit_case):
    c = unit_case
    item = Candidate(
        0, composition(), c.rendered, PieceArtifact(uuid4(), "key", c.rendered.sha256, "video/mp4", 9), review().review
    )
    await c.runner.record_review(c.row, c.token, item)
    c.session.scalar.return_value = None
    with pytest.raises(AuthError, match="MOTION_REVIEW_ALREADY_RECORDED"):
        await c.runner.record_review(c.row, c.token, item)


async def test_failure_preserves_completed_request_and_sanitizes_error_code(unit_case, monkeypatch):
    c = unit_case
    c.runner.requests.row.return_value = {"state": "completed", "execution_token": c.token}
    await c.runner.fail(c.row, c.token, "PRIVATE secret")
    c.session.execute.assert_not_awaited()
    c.runner.requests.row.return_value = {"state": "running", "execution_token": c.token}
    c.session.scalar.return_value = None
    c.runner.release = AsyncMock()
    await c.runner.fail(c.row, c.token, "private secret")
    params = c.session.execute.call_args_list[0].args[1]
    assert params["state"] == "failed" and params["code"] == "MOTION_EXECUTION_FAILED"
    c.runner.release.assert_awaited_once()


async def test_successful_render_commits_only_after_verified_private_upload(unit_case):
    c = unit_case
    candidate = await c.runner.render(c.row, c.token, c.prepared, 0, composition())
    assert candidate.artifact.sha256 == c.rendered.sha256
    assert candidate.artifact.object_key.startswith(
        f"motion/{c.row['tenant_id']}/{c.row['business_id']}/{c.row['id']}/0/"
    )
    assert c.runner.effects.claim.await_count == 2 and c.runner.effects.received.await_count == 2
    assert c.session.execute.await_count == 1
    assert "INSERT INTO motion_render_versions" in str(c.session.execute.call_args.args[0])
    args = c.runner.renderer.render.call_args.args[0]
    assert (args.width, args.height, args.fps, args.duration_ms) == (720, 1280, 30, 1000)


async def test_completion_preserves_rejected_versions_without_selecting_latest(unit_case, monkeypatch):
    from app.services import motion_orchestrator as module

    c = unit_case
    pieces = [
        Candidate(
            i,
            composition(),
            c.rendered,
            PieceArtifact(uuid4(), f"private/{i}", c.rendered.sha256, "video/mp4", 9),
            review().review,
        )
        for i in range(3)
    ]
    versions = [uuid4(), uuid4(), uuid4()]
    writer = AsyncMock(side_effect=versions)
    monkeypatch.setattr(module, "write_version", writer)
    pending = AsyncMock()
    scripts = AsyncMock()
    monkeypatch.setattr(module.VisualPendingChanges, "apply_pending_in_session", pending)
    monkeypatch.setattr(module, "apply_pending_script_changes", scripts)
    await c.runner.complete(c.row, c.token, pieces, pieces[1])
    assert [call.kwargs["select_current"] for call in writer.call_args_list] == [True, True, False]
    assert [call.kwargs["parent_id"] for call in writer.call_args_list] == [None, versions[0], versions[1]]
    assert all(call.kwargs["simulated"] for call in writer.call_args_list)
    pending.assert_awaited_once()
    scripts.assert_awaited_once()


@pytest.mark.parametrize("stop", ["budget", "no_gain", "maximum"])
async def test_revision_stops_without_spending_on_an_unjustified_round(unit_case, stop):
    c = unit_case
    stub_render(c)
    value = MotionModelResult(composition=composition())
    c.runner.effects.model.side_effect = [value, review(revise=True)]
    if stop == "budget":
        c.runner.effects.capacity_for_correction.return_value = False
    elif stop == "maximum":
        c.row["max_corrections"] = 0
    else:
        c.runner.effects.model.side_effect = [
            value,
            review(revise=True),
            value,
            review(revise=True, previous=True, preferred="previous"),
        ]
    with pytest.raises(AuthError, match="MOTION_MANDATORY_REVIEW_FAILED"):
        await c.runner.run(c.event)
    assert c.runner.effects.model.await_count == (4 if stop == "no_gain" else 2)
    c.runner.complete.assert_not_awaited()


async def test_unknown_failure_keeps_active_guard_until_reconciliation(unit_case):
    c = unit_case
    c.session.scalar.return_value = 1
    c.runner.release = AsyncMock()
    await c.runner.fail(c.row, c.token, "MOTION_OUTCOME_UNCERTAIN")
    assert c.session.execute.call_args_list[0].args[1]["state"] == "uncertain"
    c.runner.release.assert_not_awaited()


@pytest.mark.parametrize("changed", [False, True])
async def test_images_are_created_once_then_reused_by_review_and_correction(unit_case, settings, changed):
    from app.services.motion_illustration_policy import illustration_policy
    from app.tests.unit.test_motion_illustrations import art_settings, composition_with_art, image_result
    from app.tests.unit.test_motion_plan import context

    c = unit_case
    stub_render(c)
    cfg = art_settings(settings)
    ctx = context()
    ctx["illustration_generation"] = illustration_policy(cfg)
    c.runner.inputs.prepare.return_value = replace(c.prepared, context=ctx)
    result = image_result()
    c.runner.illustration_provider = SimpleNamespace(generate=AsyncMock(return_value=result))
    c.runner.store.get_image = AsyncMock(return_value=result.content)
    c.runner.effects.requests = SimpleNamespace(settings=cfg)
    c.runner.effects.capacity = AsyncMock(return_value=True)
    c.runner.effects.reserve_submission = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    c.runner.effects.ledger = SimpleNamespace(finish=AsyncMock())
    from app.services.motion_temporal import evidence_manifest, sample_times
    from app.tests.unit.test_motion_temporal import temporal_case

    original = composition_with_art()
    _, review_template, _ = temporal_case()
    frames = tuple(frame(round(ms * 30 // 1000 * 1000 / 30), "blue") for ms in sample_times(original, ctx))
    c.rendered = replace(c.rendered, evidence=frames)
    manifest = evidence_manifest(original, frames, "current")
    refs = [{"version": "current", "at_ms": f.ms, "sha256": f.sha256} for f in frames]
    for check in review_template["creative_checks"]:
        check["evidence"] = refs
    for check in review_template["temporal_checks"]:
        check["evidence"] = refs
        check["event_ids"] = [event["id"] for event in manifest["events"]]

    def art_review(revise=False, previous=False):
        data = review_data(current=frames[0], previous=frames[0] if previous else None, revise=revise)
        data["creative_checks"] = review_template["creative_checks"]
        data["temporal_checks"] = review_template["temporal_checks"]
        if previous:
            data["preference_evidence"] = refs + [{**ref, "version": "previous"} for ref in refs]
        return MotionModelResult(review=MotionReview.model_validate(data))

    corrected = original
    if changed:
        corrected = original.model_copy(
            update={"illustrations": (original.illustrations[0].model_copy(update={"description": "Outra arte"}),)}
        )
    c.runner.effects.model.side_effect = [
        MotionModelResult(composition=original),
        art_review(revise=True),
        MotionModelResult(composition=corrected),
        art_review(previous=True),
    ]
    if changed:
        with pytest.raises(AuthError, match="ILLUSTRATION_CORRECTION_CHANGED"):
            await c.runner.run(c.event)
        assert c.runner.render.await_count == 1
    else:
        assert await c.runner.run(c.event) == "completed"
        assert c.runner.render.await_count == 2
        assert c.runner.render.await_args_list[0].args[2].assets == c.runner.render.await_args_list[1].args[2].assets
    c.runner.illustration_provider.generate.assert_awaited_once()
    for call in c.runner.effects.model.await_args_list[1:]:
        assert call.args[3].asset_previews[0][0] == "assets/illustration-cup.png"


async def test_requested_storyboard_pauses_before_video_and_paid_review(unit_case, monkeypatch):
    from app.services.motion_storyboards import MotionStoryboards
    from app.tests.unit.test_motion_plan import context
    from app.tests.unit.test_motion_storyboards import boarded

    c = unit_case
    prepared = replace(c.prepared, context={**context(), "request": {"storyboard": True}})
    c.runner.inputs.prepare.return_value = prepared
    c.runner.effects.model.return_value = MotionModelResult(composition=boarded())
    capture = AsyncMock()
    monkeypatch.setattr(MotionStoryboards, "capture", capture)
    assert await c.runner.run(c.event) == "awaiting_storyboard"
    assert c.runner.effects.model.await_count == 1
    capture.assert_awaited_once()
    c.runner.renderer.render.assert_not_awaited()


async def test_approved_board_resumes_without_generation_or_illustration_calls(unit_case, monkeypatch):
    from uuid import uuid5

    from app.services.motion_storyboards import MotionStoryboards
    from app.tests.unit.test_motion_storyboards import boarded

    c = unit_case
    c.runner.requests._admission = AsyncMock()
    monkeypatch.setattr(MotionStoryboards, "begin_resume", AsyncMock(return_value=(c.row, c.token, {})))
    monkeypatch.setattr(MotionStoryboards, "restore", AsyncMock(return_value=(c.prepared, boarded())))
    c.runner.produce = AsyncMock(return_value="completed")
    event = replace(c.event, event_id=str(uuid5(c.row["operation_id"], "motion.storyboard_approved")))
    assert await c.runner.run(event) == "completed"
    c.runner.produce.assert_awaited_once()
    c.runner.effects.model.assert_not_awaited()
    c.runner.requests.begin.assert_not_awaited()


@pytest.mark.parametrize("fallback", [False, True])
async def test_resumed_failure_has_its_own_durable_event(unit_case, monkeypatch, fallback):
    from uuid import UUID, uuid5

    from app.services.motion_storyboards import MotionStoryboards
    from app.tests.unit.test_motion_storyboards import boarded

    c = unit_case
    c.runner.requests._admission = AsyncMock()
    monkeypatch.setattr(MotionStoryboards, "begin_resume", AsyncMock(return_value=(c.row, c.token, {})))
    monkeypatch.setattr(MotionStoryboards, "restore", AsyncMock(return_value=(c.prepared, boarded())))
    c.runner.produce = AsyncMock(side_effect=AuthError("MOTION_AI_OUTPUT_LIMIT", 409))
    c.runner.fail = AsyncMock(side_effect=RuntimeError("database unavailable") if fallback else None)
    event = replace(c.event, event_id=str(uuid5(c.row["operation_id"], "motion.storyboard_approved")))
    expected = uuid5(UUID(event.event_id), "motion.failed")
    with pytest.raises(AuthError, match="OUTPUT_LIMIT"):
        await c.runner.run(event)
    c.runner.fail.assert_awaited_once_with(c.row, c.token, "MOTION_AI_OUTPUT_LIMIT", failure_event_id=expected)
    if fallback:
        c.runner.effects.quarantine.assert_awaited_once_with(c.row, c.token, failure_event_id=expected)
    else:
        c.runner.effects.quarantine.assert_not_awaited()


async def test_incomplete_review_stops_before_correction_or_approval(unit_case):
    from app.adapters.motion_ai import MotionAIError

    c = unit_case
    stub_render(c)
    c.runner.effects.model.side_effect = MotionAIError("MOTION_AI_OUTPUT_LIMIT")
    with pytest.raises(MotionAIError, match="OUTPUT_LIMIT"):
        await c.runner.produce(c.row, c.token, c.prepared, composition())
    c.runner.render.assert_awaited_once()
    c.runner.effects.model.assert_awaited_once()
    assert c.runner.effects.model.await_args.args[3].kind == "review"
    c.runner.record_review.assert_not_awaited()
    c.runner.effects.capacity_for_correction.assert_not_awaited()
    c.runner.complete.assert_not_awaited()


async def test_speech_is_prepared_before_generation_and_reused_for_render(unit_case, monkeypatch):
    from app.services.motion_speech_recognition import MotionSpeechRecognition

    c = unit_case
    stub_render(c)
    annotated = replace(c.prepared, context={"transcript": {"synthetic": True}})
    prepare = AsyncMock(return_value=annotated)
    monkeypatch.setattr(MotionSpeechRecognition, "prepare", prepare)
    c.runner.effects.model.side_effect = [MotionModelResult(composition=composition()), review()]
    await c.runner.run(c.event)
    prepare.assert_awaited_once_with(c.row, c.token, c.prepared)
    assert c.runner.effects.model.await_args_list[0].args[3].context == annotated.context
    assert c.runner.render.await_args.args[2] is annotated
