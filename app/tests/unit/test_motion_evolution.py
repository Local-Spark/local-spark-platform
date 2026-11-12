"""Synthetic evidence: baseline scope, missing functions, real payload and selection gates."""

import base64
import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_evolution import MotionEvolutionRequest
from app.schemas.motion_production import MotionRequest, MotionReview
from app.services.auth import AuthError
from app.services.motion_evolution import capture_evolution, evolution_verdict, sha, validate_evolution_plan
from app.services.motion_evolution_inputs import load_evolution
from app.services.motion_orchestrator import Candidate, choose_candidate
from app.services.motion_protocols import MotionModelResult
from app.services.motion_review import MotionReviewError, validate_baseline_review, validate_review
from app.services.motion_temporal import POLICY_V2, POLICY_V3, events, sample_times
from app.tests.unit.test_motion_ai import frame, provider, request, review_data
from app.tests.unit.test_motion_context_requests import result
from app.tests.unit.test_motion_orchestrator import stub_render, unit_case
from app.tests.unit.test_motion_plan import planned
from app.tests.unit.test_motion_visual_direction import provided_context

synthetic_runner = unit_case


def case():
    base = planned()
    selection = MotionEvolutionRequest(
        baseline_request_id=uuid4(),
        baseline_number=0,
        baseline_video_sha256="a" * 64,
        owner_reference_confirmed=True,
        hypothesis="Preserve the question while improving its handoff.",
        elements=[
            {
                "baseline_element_id": e.id,
                "disposition": "preserve",
                "target_element_ids": [e.id],
                "function": e.purpose,
                "expected_result": "Keep the message legible through the handoff.",
            }
            for s in base.motion_plan.scenes
            for e in s.elements
        ],
    )
    ctx = provided_context()
    ctx["request"]["evolution"] = selection.model_dump(mode="json")
    ctx["evolution"] = {
        "selection": selection.model_dump(mode="json"),
        "composition": base.model_dump(mode="json"),
        "composition_sha256": sha(base.model_dump(mode="json")),
        "version": selection.version,
        "rules": "Synthetic baseline, not executable instructions.",
    }
    return base, selection, ctx


def test_old_case_unchanged_and_missing_or_modified_baseline_fails():
    base, _, ctx = case()
    validate_evolution_plan(base, {})
    validate_evolution_plan(base, ctx)
    for change, code in [
        ("missing", "CONTEXT_REQUIRED"),
        ("hash", "BASELINE_CHANGED"),
        ("accounting", "BASELINE_ELEMENTS_UNACCOUNTED"),
        ("target", "FUNCTION_TARGET_MISSING"),
    ]:
        changed = deepcopy(ctx)
        if change == "missing":
            changed.pop("evolution")
        elif change == "hash":
            changed["evolution"]["composition_sha256"] = "0" * 64
        else:
            selection = changed["request"]["evolution"]
            if change == "accounting":
                selection["elements"].pop()
            else:
                selection["elements"][0].update(disposition="replace", target_element_ids=["absent"])
            changed["evolution"]["selection"] = selection
        with pytest.raises(AuthError, match=code):
            validate_evolution_plan(base, changed)


def test_explicit_replacement_is_allowed_without_freezing_design():
    base, _, ctx = case()
    old = ctx["request"]["evolution"]["elements"][0]
    old.update(disposition="replace", target_element_ids=["answer"], expected_result="Answer carries both functions.")
    ctx["evolution"]["selection"] = ctx["request"]["evolution"]
    validate_evolution_plan(base, ctx)
    duplicate = deepcopy(ctx["request"]["evolution"])
    duplicate["elements"].append(duplicate["elements"][0])
    with pytest.raises(ValidationError):
        MotionEvolutionRequest.model_validate(duplicate)
    duplicate = deepcopy(ctx["request"]["evolution"])
    duplicate["elements"][0]["target_element_ids"] = ["answer", "answer"]
    with pytest.raises(ValidationError):
        MotionEvolutionRequest.model_validate(duplicate)


def test_actual_builder_sends_separate_baseline_and_never_exposes_storage_or_executes_old_code():
    base, _, ctx = case()
    job = replace(request(), context=ctx, baseline_frames=(frame(0), frame(500)))
    payload = provider().build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["historical_baseline"]["composition_sha256"] == ctx["evolution"]["composition_sha256"]
    assert "html" not in sent["historical_baseline"]["composition"]
    assert sent["previous_composition"] is None and sent["current_composition"] is None
    assert "evolution" not in sent["authorized_context"]
    assert "baseline" in json.dumps(payload)
    with pytest.raises(MotionAIError, match="EVOLUTION_EVIDENCE_REQUIRED"):
        provider().build_request(replace(job, baseline_frames=()))


async def test_capture_selects_same_business_and_pins_version_without_storage_io():
    base, selection, _ = case()
    source = uuid4()
    tenant = uuid4()
    business = uuid4()
    body = MotionRequest(
        operation_id=uuid4(),
        source_asset_id=source,
        instruction="Synthetic",
        storyboard=True,
        scene_direction=base.scene_direction,
        evolution=selection,
    )
    row = {
        "sha256": "a" * 64,
        "source_asset_id": source,
        "composition_ciphertext": "composition",
        "snapshot_ciphertext": "snapshot",
        "evidence_ciphertext": "sealed",
        "object_key": "synthetic/video",
        "size_bytes": 100,
    }
    values = {"composition": base.model_dump(mode="json"), "snapshot": {"source": {"sha256": "b" * 64}, "kit": {}}}
    session = AsyncMock()
    session.execute.return_value = result(row)
    captured = await capture_evolution(session, tenant, business, body, values.__getitem__)
    assert captured["row"] == {
        "tenant_id": str(tenant),
        "business_id": str(business),
        "id": str(selection.baseline_request_id),
    }
    sql, args = session.execute.call_args.args
    assert "v.tenant_id=:tenant AND v.business_id=:business" in str(sql)
    assert args["number"] == 0 and args["business"] == business
    session.execute.return_value = result(None)
    with pytest.raises(AuthError, match="BASELINE_UNAVAILABLE"):
        await capture_evolution(session, tenant, business, body, values.__getitem__)
    session.execute.return_value = result({**row, "source_asset_id": uuid4()})
    with pytest.raises(AuthError, match="SOURCE_CHANGED"):
        await capture_evolution(session, tenant, business, body, values.__getitem__)
    assert (
        await capture_evolution(
            session, tenant, business, body.model_copy(update={"evolution": None}), values.__getitem__
        )
        is None
    )


async def test_loader_checks_real_frame_hash_and_keeps_comparison_out_of_render_assets():
    base, _, ctx = case()
    ctx.update(source={"sha256": "b" * 64}, kit={}, authorized_audio=base.audio.model_dump(mode="json"))
    prepared = PreparedMotionInput(ctx, (), (), 1000, ctx["authorized_audio"])
    frames = (frame(0), frame(500))
    evidence = {"frames": [{"ms": f.ms, "sha256": f.sha256, "png": base64.b64encode(f.png).decode()} for f in frames]}
    captured = {
        **ctx["evolution"],
        "source_sha256": "b" * 64,
        "kit": {},
        "row": {},
        "evidence_ciphertext": "inline",
        "materials": [],
    }
    cipher = SimpleNamespace(open=lambda _: evidence)
    loaded = await load_evolution(prepared, captured, cipher, AsyncMock())
    assert loaded.assets == () and loaded.baseline_frames == frames
    assert "evidence_ciphertext" not in loaded.context["evolution"]
    evidence["frames"][0]["sha256"] = "0" * 64
    with pytest.raises(AuthError, match="EVIDENCE_INVALID"):
        await load_evolution(prepared, captured, cipher, AsyncMock())


def comparative_data(status="improved"):
    a, b = frame(0), frame(500)
    data = review_data(current=a)
    data["baseline_video_sha256"] = "a" * 64
    data["baseline_checks"] = [
        {
            "dimension": name,
            "result": status,
            "observation": "Synthetic comparison.",
            "evidence": [
                {"version": version, "at_ms": f.ms, "sha256": f.sha256}
                for version in ("current", "baseline")
                for f in (a, b)
            ],
        }
        for name in ("meaning", "recording", "space", "rhythm", "identity")
    ]
    return data


@pytest.mark.parametrize(
    "status,expected",
    [("improved", "improved"), ("equivalent", "recovered"), ("regressed", "regression"), ("uncertain", "inconclusive")],
)
def test_technically_adequate_regression_or_tie_cannot_be_selected(status, expected):
    base, _, ctx = case()
    review = MotionReview.model_validate(comparative_data(status))
    assert evolution_verdict(review) == expected
    candidate = Candidate(0, base, None, None, review)
    assert (choose_candidate(None, candidate, evolution=True) is candidate) == (status == "improved")
    assert choose_candidate(None, candidate) is candidate  # Historical non-evolution behavior.
    job = replace(
        request("review", composition=base, frames=(frame(0), frame(500))),
        context=ctx,
        baseline_frames=(frame(0), frame(500)),
    )
    validate_baseline_review(job, review)
    broken = review.model_copy(update={"baseline_video_sha256": "b" * 64})
    with pytest.raises(MotionReviewError, match="REVIEW_REQUIRED"):
        validate_baseline_review(job, broken)


def test_comparison_rejects_missing_one_sided_or_unsent_evidence():
    base, _, ctx = case()
    job = replace(
        request("review", composition=base, frames=(frame(0), frame(500))),
        context=ctx,
        baseline_frames=(frame(0), frame(500)),
    )
    review = MotionReview.model_validate(comparative_data())
    with pytest.raises(MotionReviewError, match="REVIEW_REQUIRED"):
        validate_baseline_review(job, review.model_copy(update={"baseline_checks": ()}))
    data = comparative_data()
    data["baseline_checks"][0]["evidence"] = data["baseline_checks"][0]["evidence"][:2]
    with pytest.raises(MotionReviewError, match="COMPARATIVE_EVIDENCE_REQUIRED"):
        validate_baseline_review(job, MotionReview.model_validate(data))
    data = comparative_data()
    data["baseline_checks"][0]["evidence"][0]["sha256"] = "f" * 64
    with pytest.raises(MotionReviewError, match="UNSENT_EVIDENCE"):
        validate_review(job, MotionReview.model_validate(data))
    data = comparative_data()
    data["baseline_checks"][0]["result"] = "equivalent"
    assert evolution_verdict(MotionReview.model_validate(data)) == "partial"


def test_v3_covers_end_of_actual_handoff_and_keeps_old_sampling():
    base, _, ctx = case()
    old = events(base, POLICY_V2)[0]
    new = events(base, POLICY_V3)[0]
    before = next(e for e in old if e.kind == "transition")
    after = next(e for e in new if e.kind == "transition")
    assert before.end_ms == 600 and after.end_ms == 800
    ctx["creative_contract"]["temporal_review"] = POLICY_V3
    assert len(sample_times(base, ctx)) <= 20
    assert events(base, POLICY_V2)[0] == old


@pytest.mark.parametrize("status", ["regressed", "equivalent", "uncertain", "improved"])
async def test_real_produce_path_records_review_but_never_completes_inferior_evolution(synthetic_runner, status):
    c = synthetic_runner
    base, _, ctx = case()
    c.rendered = replace(c.rendered, evidence=(frame(0), frame(500)))
    stub_render(c)
    c.row["max_corrections"] = 0
    # Isolate comparative selection from creative checks already exercised elsewhere.
    prepared = replace(c.prepared, context={"evolution": ctx["evolution"]}, baseline_frames=(frame(0), frame(500)))
    c.runner.effects.model.return_value = MotionModelResult(
        review=MotionReview.model_validate(comparative_data(status))
    )
    if status == "improved":
        assert await c.runner.produce(c.row, c.token, prepared, base) == "completed"
        c.runner.complete.assert_awaited_once()
    else:
        with pytest.raises(AuthError, match="MANDATORY_REVIEW_FAILED"):
            await c.runner.produce(c.row, c.token, prepared, base)
        c.runner.complete.assert_not_awaited()
    c.runner.record_review.assert_awaited_once()
    sent = c.runner.effects.model.call_args.args[-1]
    assert sent.baseline_frames == prepared.baseline_frames and sent.incumbent_frames == ()


async def test_material_capture_accepts_only_received_baseline_uploads_in_its_scope():
    base, selection, _ = case()
    tenant, business, source = uuid4(), uuid4(), uuid4()
    asset_id = "assets/illustration-object.png"
    spec = {"asset_id": asset_id, "description": "Synthetic transparent object.", "purpose": "Explain a process."}
    base = base.model_copy(update={"illustrations": ()})
    # Validate the real illustration schema rather than inventing a received receipt.
    from app.schemas.motion_production import MotionIllustration

    base = base.model_copy(update={"illustrations": (MotionIllustration.model_validate(spec),)})
    selection = selection.model_copy(update={"reuse_illustration_ids": (asset_id,)})
    body = MotionRequest(
        operation_id=uuid4(),
        source_asset_id=source,
        instruction="Synthetic",
        storyboard=True,
        scene_direction=base.scene_direction,
        evolution=selection,
    )
    row = {
        "sha256": "a" * 64,
        "source_asset_id": source,
        "composition_ciphertext": "composition",
        "snapshot_ciphertext": "snapshot",
        "evidence_ciphertext": "sealed",
        "object_key": "synthetic/video",
        "size_bytes": 100,
    }
    material = {
        "asset_id": asset_id,
        "provenance": "generated_illustration",
        "sha256": "c" * 64,
        "size_bytes": 100,
        "object_key": f"motion/{tenant}/{business}/{selection.baseline_request_id}/illustrations/object.png",
    }
    values = {
        "composition": base.model_dump(mode="json"),
        "snapshot": {"source": {"sha256": "b" * 64}, "kit": {}},
        "material": material,
    }
    session = AsyncMock()
    session.execute.side_effect = [result(row), result([{"response_ciphertext": "material"}])]
    captured = await capture_evolution(session, tenant, business, body, values.__getitem__)
    assert captured["materials"] == [material]
    material["object_key"] = "another-business/private.png"
    session.execute.side_effect = [result(row), result([{"response_ciphertext": "material"}])]
    with pytest.raises(AuthError, match="MATERIAL_INVALID"):
        await capture_evolution(session, tenant, business, body, values.__getitem__)
    session.execute.side_effect = [result(row), result([])]
    with pytest.raises(AuthError, match="MATERIAL_UNAVAILABLE"):
        await capture_evolution(session, tenant, business, body, values.__getitem__)


def test_evolution_requires_owner_confirmation_direction_and_storyboard():
    base, selection, _ = case()
    data = selection.model_dump(mode="json")
    data["owner_reference_confirmed"] = False
    with pytest.raises(ValidationError):
        MotionEvolutionRequest.model_validate(data)
    for direction, storyboard in [(None, True), (base.scene_direction, False)]:
        with pytest.raises(ValidationError):
            MotionRequest(
                operation_id=uuid4(),
                source_asset_id=uuid4(),
                instruction="Synthetic",
                evolution=selection,
                scene_direction=direction,
                storyboard=storyboard,
            )


async def test_existing_video_is_decoded_at_bounded_indices_and_tampering_stops_loading(monkeypatch):
    import hashlib

    from app.adapters.motion_inputs import baseline_video_frames

    command = AsyncMock(return_value=frame(0).png)
    monkeypatch.setattr("app.adapters.motion_inputs._command", command)
    decoded = await baseline_video_frames(b"existing synthetic MP4", (0, 534))
    assert [f.frame_index for f in decoded] == [0, 16]
    assert "select=eq(n\\,16),scale=360:640" in command.call_args.args
    for times in ((0,), (0, 0), (60000, 0)):
        with pytest.raises(AuthError, match="SAMPLE_TIMES_INVALID"):
            await baseline_video_frames(b"unused", times)
    command.return_value = b"invalid"
    with pytest.raises(AuthError, match="EVIDENCE_INVALID"):
        await baseline_video_frames(b"synthetic", (0, 500))
    base, _, ctx = case()
    prepared = PreparedMotionInput(
        {**ctx, "source": {"sha256": "b" * 64}, "kit": {}}, (), (), 1000, base.audio.model_dump(mode="json")
    )
    evidence = {
        "frames": [
            {"ms": f.ms, "sha256": f.sha256, "png": base64.b64encode(f.png).decode()} for f in (frame(0), frame(500))
        ]
    }
    raw = b"synthetic-existing-video"
    captured = {
        **ctx["evolution"],
        "source_sha256": "b" * 64,
        "kit": {},
        "row": {},
        "evidence_ciphertext": "inline",
        "materials": [],
        "video": {"object_key": "private", "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
    }
    store = AsyncMock()
    store.get_video.return_value = b"tampered"
    with pytest.raises(AuthError, match="VIDEO_CHANGED"):
        await load_evolution(prepared, captured, SimpleNamespace(open=lambda _: evidence), store)
    store.get_video.return_value = raw
    decode = AsyncMock(return_value=decoded)
    monkeypatch.setattr("app.adapters.motion_inputs.baseline_video_frames", decode)
    loaded = await load_evolution(prepared, captured, SimpleNamespace(open=lambda _: evidence), store)
    assert loaded.baseline_frames == decoded and loaded.assets == ()


def test_compact_baseline_review_round_trip_uses_sent_evidence_aliases():
    from app.services.motion_review import decode_review, review_evidence_index, review_wire_model
    from app.tests.unit.test_motion_review_wire import compact_case, compact_data

    job, data, _ = compact_case()
    _, _, ctx = case()
    job = replace(job, context={**job.context, "evolution": ctx["evolution"]}, baseline_frames=job.frames)
    data.update(baseline_video_sha256="a" * 64, baseline_checks=comparative_data()["baseline_checks"])
    references = [
        {"version": version, "at_ms": f.ms, "sha256": f.sha256}
        for version in ("current", "baseline")
        for f in job.frames[:2]
    ]
    for check in data["baseline_checks"]:
        check["evidence"] = references
    wire = compact_data(job, data)
    index = {tuple(ref.values()): key for key, ref in review_evidence_index(job).items()}
    for check in wire["baseline_checks"]:
        check["evidence"] = [index[(r["version"], r["at_ms"], r["sha256"])] for r in check["evidence"]]
    assert review_wire_model(job.context).__name__ == "EvolutionMotionReview"
    restored = decode_review(job, json.dumps(wire))
    assert restored == MotionReview.model_validate(data)
    validate_baseline_review(job, restored)
