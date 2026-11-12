"""A local synthetic defect can change only an explicit temporal window."""

import hashlib
import io
import json
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_html_renderer import MotionRenderError, RenderedMotion, _decode, _prepare
from app.schemas.motion_correction import MotionCorrectionRegion
from app.schemas.motion_production import MotionRequest, MotionReview
from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.motion_context import capture_motion_guidance
from app.services.motion_corrections import (
    CORRECTION_POLICY,
    compare_frames,
    correction_enabled,
    correction_scope,
    fingerprint,
    review_diagnostics,
    validate_candidate,
    validate_location,
)
from app.services.motion_orchestrator import Candidate
from app.services.motion_protocols import MotionModelResult
from app.services.motion_review import (
    MotionReviewError,
    decode_review,
    review_contract,
    review_wire_model,
    validate_review,
)
from app.tests.unit.test_motion_ai import frame, provider, request, response_data, review_data
from app.tests.unit.test_motion_html_renderer import bundle, output, packed
from app.tests.unit.test_motion_orchestrator import unit_case  # noqa: F401
from app.tests.unit.test_motion_plan import planned
from app.tests.unit.test_motion_review_wire import compact_data


def region(**changes):
    return {"scene_id": "hook", "element_ids": ["title"], "start_ms": 200, "end_ms": 400,
            "margin_before_ms": 33, "margin_after_ms": 33, **changes}


def critique():
    data = review_data(current=frame(300), revise=True)
    data["issues"][0]["localization"] = region()
    return MotionReview.model_validate(data)


def rasters(*, fixed=False, leak=None):
    """Deterministic raster fixture, not a browser render or a customer asset."""
    hashes = []
    for i in range(30):
        image = Image.new("RGB", (64, 64), "white")
        # A clipped synthetic title only during the specified central interval.
        x = 2 if fixed or i not in range(6, 12) else -3
        ImageDraw.Draw(image).rectangle((x, 2, x + 8, 10), fill="black")
        if i == leak:
            image.putpixel((63, 63), (255, 0, 0))
        out = io.BytesIO()
        image.save(out, "JPEG", quality=95)
        hashes.append(hashlib.sha256(out.getvalue()).hexdigest())
    return RenderedMotion(b"synthetic", fingerprint("synthetic"), (frame(300),), {
        "frame_count": 30, "width": 64, "height": 64, "fps": 30, "duration_ms": 1000,
        "executor_image": "sha256:" + "1" * 64, "fingerprint_environment": fingerprint("synthetic-pillow"),
        "frame_fingerprints": hashes,
    })


def test_scope_is_grounded_and_all_noncode_metadata_stays_immutable():
    base = planned()
    scope = correction_scope(base, critique())
    assert scope["region"] == region() and scope["expected_result"] == "Reposicionar título"
    assert scope["base_composition_sha256"] == fingerprint(base.model_dump(mode="json"))
    validate_candidate(base, base.model_copy(update={"scene_init": "window.seek=()=>{}; // fixed"}))
    for change in ({"concept": "Changed"}, {"motion_plan": None}, {"scene_direction": None},
                   {"source_usage": "Changed"}, {"audio": base.audio.model_copy(update={"mode": "mix"})}):
        with pytest.raises(AuthError, match="PROTECTED_PLAN_CHANGED"):
            validate_candidate(base, base.model_copy(update=change))
    for change in ({"scene_id": "missing"}, {"element_ids": ["answer"]}, {"start_ms": 301},
                   {"end_ms": 601}, {"margin_after_ms": 700}):
        issue = critique().issues[0].model_copy(update={"localization": MotionCorrectionRegion(**region(**change))})
        with pytest.raises(AuthError, match="LOCATION_INVALID"):
            validate_location(base, issue)
    with pytest.raises(AuthError, match="LOCATION_REQUIRED"):
        validate_location(base, critique().issues[0].model_copy(update={"localization": None}))
    for change in ({"start_ms": 400}, {"element_ids": ["title", "title"]},
                   {"margin_before_ms": 201}, {"margin_after_ms": 1001}, {"start_ms": True}):
        with pytest.raises(ValidationError):
            MotionCorrectionRegion(**region(**change))


def test_local_fixture_is_corrected_but_every_protected_frame_including_neighbors_rejects_regression():
    scope = correction_scope(planned(), critique())
    base, fixed = rasters(), rasters(fixed=True)
    result = compare_frames(base, fixed, scope)
    assert result["accepted"] and result["changed_frame_indices"] == list(range(6, 12))
    assert result["protected_frames"] == 23 and not result["quality_validated"]
    assert not compare_frames(base, base, scope)["accepted"]
    for index in [*range(6), *range(13, 30)]:
        result = compare_frames(base, rasters(fixed=True, leak=index), scope)
        assert not result["accepted"] and result["regression_frame_indices"] == [index]
    assert compare_frames(base, rasters(fixed=True, leak=12), scope)["accepted"]
    for key, value in (("executor_image", "sha256:" + "2" * 64), ("width", 128),
                       ("fingerprint_environment", "f" * 64), ("fps", 25)):
        changed = replace(fixed, diagnostics={**fixed.diagnostics, key: value})
        with pytest.raises(AuthError, match="ENVIRONMENT_CHANGED"):
            compare_frames(base, changed, scope)
    with pytest.raises(AuthError, match="EVIDENCE_INCOMPLETE"):
        compare_frames(base, replace(fixed, diagnostics={**fixed.diagnostics, "frame_fingerprints": []}), scope)
    assert "frame_fingerprints" not in review_diagnostics(base.diagnostics)
    assert "frame_fingerprints_sha256" in review_diagnostics(base.diagnostics)


def test_real_assembler_versions_new_policy_and_keeps_historical_snapshot():
    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Synthetic")
    fresh = capture_motion_guidance(body)
    assert fresh["correction_contract"] == CORRECTION_POLICY
    historical = {k: v for k, v in fresh.items() if k != "correction_contract"}
    assert "correction_contract" not in capture_motion_guidance(body, previous=historical)
    assert correction_enabled(fresh) and not correction_enabled(historical)
    with pytest.raises(AuthError, match="CONTRACT_UNKNOWN"):
        correction_enabled({"correction_contract": {"version": "future"}})


def test_localized_review_and_correction_reach_real_payload_builder():
    value, review = planned(), critique()
    ctx = {"correction_contract": CORRECTION_POLICY, "review_contract": review_contract()}
    job = replace(request("review", composition=value, frames=(frame(300),)), context=ctx)
    wire = compact_data(job, review.model_dump(mode="json"))
    assert "localization" in review_wire_model(ctx).model_json_schema()["$defs"]["LocalizedIssue"]["properties"]
    decoded = decode_review(job, json.dumps(wire))
    validate_review(job, decoded)
    assert decoded == review
    absent = review.model_copy(update={"issues": (review.issues[0].model_copy(update={"localization": None}),)})
    with pytest.raises(MotionReviewError, match="LOCATION_REQUIRED"):
        validate_review(job, absent)
    ctx = {**ctx, "correction_scope": correction_scope(value, review)}
    corrected = replace(job, kind="correct", context=ctx, review=review)
    payload = provider().build_request(corrected)
    assert "correction_scope" in payload["input"][0]["content"][0]["text"]
    assert "Preserve concept literalmente" in payload["instructions"]
    assert "deferred_issue_indices" in payload["instructions"]
    with pytest.raises(MotionAIError, match="SCOPE_CHANGED"):
        provider().build_request(replace(corrected, context={**ctx, "correction_scope": {}}))


async def test_invalid_review_localization_retains_received_response_and_cost_evidence():
    ctx = {"correction_contract": CORRECTION_POLICY, "review_contract": review_contract()}
    job = replace(request("review", composition=planned(), frames=(frame(300),)), context=ctx)
    wire = compact_data(job, critique().model_dump(mode="json"))
    wire["issues"][0]["localization"] = None
    client = provider(lambda _: httpx.Response(200, json=response_data(wire)))
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID") as exc:
        await client.submit(job, client.build_request(job))
    assert exc.value.raw_response and exc.value.estimated_usd_micros == 400


def test_renderer_protocol_requires_complete_fingerprints_when_requested(tmp_path):
    config = _prepare(replace(bundle(), fingerprint_frames=True), tmp_path / "fingerprints")
    header, data = output(config)
    with pytest.raises(MotionRenderError, match="INVALID_OUTPUT"):
        _decode(packed(header, data), config)
    header["diagnostics"].update(frame_fingerprints=["a" * 64] * 30, fingerprint_environment="b" * 64)
    assert len(_decode(packed(header, data), config).diagnostics["frame_fingerprints"]) == 30
    header["diagnostics"]["frame_fingerprints"].pop()
    with pytest.raises(MotionRenderError, match="INVALID_OUTPUT"):
        _decode(packed(header, data), config)


async def test_fingerprint_capture_is_bound_to_the_existing_render_identity(unit_case):  # noqa: F811
    c = unit_case
    prepared = replace(c.prepared, context={"correction_contract": CORRECTION_POLICY, "styles": [{"id": "editorial"}]})
    await c.runner.render(c.row, c.token, prepared, 0, planned())
    payload = c.runner.effects.claim.await_args_list[0].args[-1]
    assert payload["fingerprint_frames"] is True
    assert payload["assets"] == [] and payload["composition"] == planned().model_dump(mode="json")
    assert c.runner.renderer.render.await_args.args[0].fingerprint_frames is True
    assert c.runner.renderer.render.await_args.args[0].audio == prepared.audio


def test_full_minute_fingerprint_protocol_has_bounded_header_capacity(tmp_path):
    config = _prepare(replace(bundle(duration_ms=60000), fingerprint_frames=True), tmp_path / "full-minute")
    header, data = output(config)
    header["diagnostics"].update(
        frame_count=1800, frame_fingerprints=["a" * 64] * 1800, fingerprint_environment="b" * 64,
    )
    assert 65536 < len(json.dumps(header).encode()) < 262144
    assert len(_decode(packed(header, data), config).diagnostics["frame_fingerprints"]) == 1800


@pytest.mark.parametrize("failure", [None, "plan", "outside", "environment"])
async def test_orchestrator_records_local_gate_and_never_reviews_or_selects_rejected_candidate(unit_case, failure):  # noqa: F811
    c = unit_case
    value = planned()
    fixed = value.model_copy(update={"scene_init": "window.seek=()=>{}; // localized correction"})
    if failure == "plan":
        fixed = fixed.model_copy(update={"concept": "Unauthorized change"})
    base, corrected = rasters(), rasters(fixed=True, leak=29 if failure == "outside" else None)
    if failure == "environment":
        corrected = replace(corrected, diagnostics={**corrected.diagnostics, "fingerprint_environment": "f" * 64})
    rendered = [base, corrected]

    async def render(_row, _token, _prepared, number, composition):
        item = rendered[number]
        return Candidate(number, composition, item, PieceArtifact(uuid4(), "private", item.sha256, "video/mp4", 9))

    c.runner.render = AsyncMock(side_effect=render)
    c.runner.record_review = AsyncMock()
    c.runner.complete = AsyncMock()
    prepared = replace(c.prepared, context={"correction_contract": CORRECTION_POLICY})
    c.runner.effects.model.side_effect = [
        MotionModelResult(review=critique()), MotionModelResult(composition=fixed),
        MotionModelResult(review=MotionReview.model_validate(review_data(current=frame(300), previous=frame(300)))),
    ]
    if failure:
        with pytest.raises(AuthError, match="MANDATORY_REVIEW_FAILED"):
            await c.runner.produce(c.row, c.token, prepared, value)
        c.runner.complete.assert_not_awaited()
        assert c.runner.effects.model.await_count == 2
    else:
        assert await c.runner.produce(c.row, c.token, prepared, value) == "completed"
        assert c.runner.complete.await_args.args[-1].number == 1
    check = c.runner.effects.received.await_args.args[-1]
    assert check["accepted"] is (failure is None)
    claim = c.runner.effects.claim.await_args.args[-1]
    assert claim["kind"] == "local_correction_guard" and claim["scope"]["region"] == region()
    assert c.runner.render.await_count == (1 if failure == "plan" else 2)
    assert value == planned()
