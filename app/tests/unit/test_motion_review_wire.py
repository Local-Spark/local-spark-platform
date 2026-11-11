"""Compact critique preserves grounding and stop conditions without a live provider."""

import json
from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError, request_bytes
from app.schemas.motion_production import MotionReview
from app.schemas.motion_review_wire import CompactMotionReview
from app.services.motion_creative import provided_direction_contract
from app.services.motion_orchestrator import needs_correction
from app.services.motion_repertoire import capture_repertoire, load_repertoire_images
from app.services.motion_review import (
    MotionReviewError,
    compact_review_enabled,
    decode_review,
    review_contract,
    review_evidence_index,
    validate_review,
)
from app.tests.unit.test_motion_ai import provider, response_data
from app.tests.unit.test_motion_creative import creative_case
from app.tests.unit.test_motion_temporal import temporal_case


def compact_case():
    job, data, _ = temporal_case()
    job = replace(job, context={**job.context, "review_contract": review_contract()})
    return job, data, compact_data(job, data)


def compact_data(job, data):
    ids = {tuple(ref.values()): id for id, ref in review_evidence_index(job).items()}
    wire = MotionReview.model_validate(data).model_dump(mode="json")

    def aliases(refs):
        return list(dict.fromkeys(ids[(r["version"], r["at_ms"], r["sha256"])] for r in refs))

    for group in ("criteria", "creative_checks", "temporal_checks"):
        for item in wire[group]:
            item["evidence"] = aliases(item["evidence"])
    wire["preference_evidence"] = aliases(wire["preference_evidence"])
    for issue in wire["issues"]:
        issue["evidence_id"] = ids[("current", issue.pop("at_ms"), issue.pop("evidence_sha256"))]
    if job.context.get("review_contract", {}).get("version") == "motion-review-v3":
        for check in wire["creative_checks"]:
            check["issue_indices"] = []
    return wire


async def test_compact_response_restores_identical_durable_review_without_relaxing_evidence():
    job, data, wire = compact_case()
    model = provider(lambda _: httpx.Response(200, json=response_data(wire)))
    result = await model.submit(job, model.build_request(job))
    assert result.review == MotionReview.model_validate(data)
    validate_review(job, result.review)
    assert not needs_correction(result.review)
    assert len(request_bytes(wire)) < len(request_bytes(data)) * 0.5
    assert "sha256" not in json.dumps(wire)
    assert "sha256" in result.review.model_dump_json()


@pytest.mark.parametrize("kind", ["generate", "review", "correct"])
async def test_same_targets_references_and_direction_reach_counted_payload_with_explicit_review_projection(kind):
    job, _, _ = compact_case()
    ctx = {
        **job.context,
        "creative_contract": provided_direction_contract(),
        "request": {"scene_direction": job.composition.scene_direction.model_dump(mode="json")},
        "repertoire": capture_repertoire("business-reel-v1"),
    }
    from app.tests.unit.test_motion_ai import review_data

    job = replace(
        job,
        kind=kind,
        context=ctx,
        incumbent_composition=job.composition,
        incumbent_frames=job.frames,
        source_frames=job.frames[:1],
        reference_images=load_repertoire_images(ctx),
        review=MotionReview.model_validate(review_data(revise=True)),
    )
    original = deepcopy(job)
    calls = []

    def transport(sent):
        calls.append(json.loads(sent.content))
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 12000})

    model = provider(transport)
    payload = model.build_request(job)
    content = json.loads(payload["input"][0]["content"][0]["text"])
    assert content["authorized_context"] == ctx
    assert "alvos de acabamento" in payload["instructions"]
    assert content["visual_direction_input"]["mode"] == "provided"
    if kind == "review":
        assert payload["text"]["format"]["name"] == "LinkedMotionReview"
        assert payload["max_output_tokens"] == 8000
        for key in ("current_composition", "previous_composition"):
            assert "html" not in content[key] and "scene_init" not in content[key]
            assert content[key]["motion_plan"] == job.composition.motion_plan.model_dump(mode="json")
        index = content["review_evidence_index"]
        assert {ref["version"] for ref in index.values()} == {"source", "current", "previous"}
        assert all(not key.startswith("finish") for key in index)
        assert not {ref["sha256"] for ref in index.values()} & {r.sha256 for r in job.reference_images}
        assert content["input_projection"] == "review-composition-without-code-v1"
    else:
        assert "review_evidence_index" not in content
        assert content["current_composition"]["html"] == job.composition.html
        assert content["previous_composition"]["scene_init"] == job.composition.scene_init
    assert await model.count_input_tokens(job, payload) == 12000
    assert calls == [{key: payload[key] for key in ("model", "input", "instructions", "text", "reasoning")}]
    assert job == original


@pytest.mark.parametrize("change", ["unknown", "duplicate", "reference", "prose", "issue_limit", "unheard", "missing"])
def test_compact_wire_cannot_invent_evidence_or_relax_existing_requirements(change):
    job, _, wire = compact_case()
    if change == "unknown":
        wire["criteria"][0]["evidence"] = ["current-99"]
    elif change == "duplicate":
        wire["criteria"][0]["evidence"] *= 2
    elif change == "reference":
        wire["criteria"][0]["evidence"] = ["finish_reference-0"]
    elif change == "prose":
        wire["criteria"][0]["observation"] = "x" * 241
    elif change == "issue_limit":
        wire["issues"] = [{}] * 7
    elif change == "unheard":
        next(item for item in wire["criteria"] if item["name"] == "audio")["status"] = "pass"
    else:
        wire["creative_checks"] = []
    with pytest.raises((MotionReviewError, ValidationError)):
        validate_review(job, decode_review(job, json.dumps(wire)))


@pytest.mark.parametrize("version", ["current", "source", "previous"])
def test_issue_alias_must_resolve_to_current_artifact(version):
    job, data, _ = compact_case()
    job = replace(job, source_frames=job.frames, incumbent_frames=job.frames, incumbent_composition=job.composition)
    data["verdict"] = "needs_revision"
    data["preferred"] = "undetermined"
    next(item for item in data["criteria"] if item["name"] == "legibility")["status"] = "fail"
    data["issues"] = [
        {
            "criterion": "legibility",
            "severity": "major",
            "actionable": True,
            "at_ms": job.frames[0].ms,
            "evidence_sha256": job.frames[0].sha256,
            "problem": "Cena s1: título cortado no estado de leitura.",
            "correction": "Aumentar a margem interna do título preservando kit e direção.",
        }
    ]
    wire = compact_data(job, data)
    wire["issues"][0]["evidence_id"] = f"{version}-0"
    if version != "current":
        with pytest.raises(MotionReviewError, match="ISSUE_VERSION_INVALID"):
            decode_review(job, json.dumps(wire))
    else:
        review = decode_review(job, json.dumps(wire))
        validate_review(job, review)
        assert review == MotionReview.model_validate(data)
        assert needs_correction(review)


@pytest.mark.parametrize("evidence", ["matching", "other_time", "other_version", "other_hash"])
def test_creative_correction_must_be_located_in_the_check_evidence(evidence):
    job, data = creative_case()
    job = replace(job, context={**job.context, "review_contract": review_contract()})
    data["verdict"] = "needs_revision"
    data["creative_checks"][0]["status"] = "not_met"
    data["creative_checks"][0]["evidence"] = data["creative_checks"][0]["evidence"][:1]
    next(item for item in data["criteria"] if item["name"] == "composition")["status"] = "fail"
    issue_frame = job.frames[0 if evidence == "matching" else 1]
    if evidence == "other_version":
        job = replace(job, source_frames=job.frames)
        data["creative_checks"][0]["evidence"].append(
            {"version": "source", "at_ms": issue_frame.ms, "sha256": issue_frame.sha256}
        )
    if evidence == "other_hash":
        from app.tests.unit.test_motion_ai import frame

        other = frame(issue_frame.ms, "green")
        job = replace(job, frames=(*job.frames, other))
        data["creative_checks"][0]["evidence"].append({"version": "current", "at_ms": other.ms, "sha256": other.sha256})
    data["issues"] = [
        {
            "criterion": "composition",
            "severity": "major",
            "actionable": True,
            "at_ms": issue_frame.ms,
            "evidence_sha256": issue_frame.sha256,
            "problem": "Cena s1: a camada cobre a ação real.",
            "correction": "Reposicionar a camada atrás da gravação.",
        }
    ]
    review = MotionReview.model_validate(data)
    if evidence == "matching":
        validate_review(job, review)
    else:
        with pytest.raises(MotionReviewError, match="CREATIVE_CORRECTION_UNGROUNDED"):
            validate_review(job, review)


def test_uncertainty_does_not_create_correction_and_historical_schema_still_works():
    job, data, _ = compact_case()
    data["verdict"] = "insufficient_evidence"
    for group in ("creative_checks", "temporal_checks"):
        for item in data[group]:
            item.update(status="uncertain", evidence=[])
    wire = compact_data(job, data)
    review = decode_review(job, json.dumps(wire))
    validate_review(job, review)
    assert not needs_correction(review)
    old = replace(job, context={k: v for k, v in job.context.items() if k != "review_contract"})
    assert decode_review(old, json.dumps(data)) == review
    payload = provider().build_request(old)
    assert payload["text"]["format"]["name"] == "MotionReview"
    assert "html" in json.loads(payload["input"][0]["content"][0]["text"])["current_composition"]


@pytest.mark.parametrize("policy", [{"version": "unknown"}, {**review_contract(), "wire_format": "changed"}])
def test_policy_is_versioned_and_rejected_before_dispatch(policy):
    job, _, _ = compact_case()
    job = replace(job, context={**job.context, "review_contract": policy})
    with pytest.raises(MotionReviewError, match="CONTRACT_UNKNOWN"):
        provider().build_request(job)
    policy = review_contract()
    policy["targets"].clear()
    assert compact_review_enabled({"review_contract": review_contract()})


@pytest.mark.parametrize("incomplete", [True, False])
async def test_truncated_or_broken_review_never_becomes_a_partial_verdict_or_retry(incomplete):
    job, _, _ = compact_case()
    body = response_data(
        status="incomplete" if incomplete else "completed",
        incomplete_details={"reason": "max_output_tokens"},
        usage={"input_tokens": 12000, "output_tokens": 8000},
        output=[{"content": [{"type": "output_text", "text": '{"verdict":"adequate"'}]}],
    )
    calls = []

    def transport(sent):
        calls.append(sent)
        return httpx.Response(200, json=body, headers={"x-request-id": "truncated-review"})

    model = provider(transport)
    with pytest.raises(MotionAIError, match="OUTPUT_LIMIT" if incomplete else "RESPONSE_INVALID") as caught:
        await model.submit(job, model.build_request(job))
    assert len(calls) == 1
    assert caught.value.raw_response is not None
    if incomplete:
        assert caught.value.usage == {"input_tokens": 12000, "output_tokens": 8000}
        assert caught.value.provider_request_id == "truncated-review"
        assert caught.value.estimated_usd_micros is not None


def test_wire_schema_keeps_seven_criteria_and_does_not_ask_for_generated_code():
    schema = CompactMotionReview.model_json_schema()
    assert schema["properties"]["criteria"]["minItems"] == schema["properties"]["criteria"]["maxItems"] == 7
    assert schema["properties"]["issues"]["maxItems"] == 6
    assert "html" not in schema["properties"]


def linked_failure_case():
    job, data = creative_case()
    job = replace(job, context={**job.context, "review_contract": review_contract()})
    data["verdict"] = "needs_revision"
    data["creative_checks"][0]["status"] = "not_met"
    data["creative_checks"][0]["evidence"] = data["creative_checks"][0]["evidence"][:1]
    next(c for c in data["criteria"] if c["name"] == "composition")["status"] = "fail"
    data["issues"] = [
        {
            "criterion": "composition",
            "severity": "major",
            "actionable": True,
            "at_ms": job.frames[1].ms,
            "evidence_sha256": job.frames[1].sha256,
            "problem": "Video wrapper clips its translated child.",
            "correction": "Remove unintended mask.",
        }
    ]
    wire = compact_data(job, data)
    wire["creative_checks"][0]["issue_indices"] = [0]
    return job, data, wire


def test_explicit_issue_link_supplies_real_evidence_without_guessing_same_defect():
    job, data, wire = linked_failure_case()
    review = decode_review(job, json.dumps(wire))
    validate_review(job, review)
    assert len(review.creative_checks[0].evidence) == 2
    assert review.creative_checks[0].evidence[-1].sha256 == job.frames[1].sha256
    assert needs_correction(review)
    # Model can cite the same frame directly as well; expansion is idempotent.
    wire["creative_checks"][0]["evidence"].append(wire["issues"][0]["evidence_id"])
    assert decode_review(job, json.dumps(wire)) == review
    from app.services.motion_review import REVIEW_CONTRACT

    historical = replace(job, context={**job.context, "review_contract": REVIEW_CONTRACT})
    for check in wire["creative_checks"]:
        check.pop("issue_indices")
    assert decode_review(historical, json.dumps(wire)) == review
    assert provider().build_request(historical)["text"]["format"]["name"] == "CompactMotionReview"


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "duplicate",
        "out_of_range",
        "wrong_criterion",
        "met",
        "uncertain",
        "minor",
        "not_actionable",
        "source",
        "unknown_frame",
        "boolean",
    ],
)
def test_explicit_links_do_not_bypass_grounding(case):
    job, _, wire = linked_failure_case()
    check = wire["creative_checks"][0]
    issue = wire["issues"][0]
    if case == "missing":
        check["issue_indices"] = []
    elif case == "duplicate":
        check["issue_indices"] = [0, 0]
    elif case == "out_of_range":
        check["issue_indices"] = [1]
    elif case == "wrong_criterion":
        issue["criterion"] = "motion"
    elif case in {"met", "uncertain"}:
        check["status"] = case
    elif case == "minor":
        issue["severity"] = "minor"
    elif case == "not_actionable":
        issue["actionable"] = False
    elif case == "source":
        job = replace(job, source_frames=job.frames)
        issue["evidence_id"] = "source-0"
    elif case == "boolean":
        check["issue_indices"] = [True]
    else:
        issue["evidence_id"] = "current-99"
    with pytest.raises((MotionReviewError, ValidationError)):
        validate_review(job, decode_review(job, json.dumps(wire)))
