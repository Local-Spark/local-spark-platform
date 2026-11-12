"""A temporal critique cannot pass from isolated, invented or one-sided evidence."""

import json
from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_fixture import FixtureMotionProvider
from app.schemas.motion_production import MotionReview
from app.services.auth import AuthError
from app.services.motion_orchestrator import needs_correction
from app.services.motion_review import MotionReviewError, validate_review, validate_temporal_review
from app.services.motion_temporal import (
    POLICY_V2,
    TEMPORAL_CRITERIA,
    events,
    evidence_manifest,
    sample_times,
    temporal_enabled,
)
from app.tests.unit.test_motion_ai import composition, frame, provider, request, response_data, review_data
from app.tests.unit.test_motion_creative import creative_case
from app.tests.unit.test_motion_plan import context, planned


def temporal_case():
    comp, ctx = planned(), context()
    frames = tuple(frame(round((ms * 30 // 1000) * 1000 / 30), "blue") for ms in sample_times(comp, ctx))
    manifest = evidence_manifest(comp, frames, "current")
    job = replace(request("review", composition=comp, frames=frames), context=ctx)
    data = review_data(current=frames[0])
    data["creative_checks"] = creative_case()[1]["creative_checks"]
    refs = [{"version": "current", "at_ms": f.ms, "sha256": f.sha256} for f in frames]
    for check in data["creative_checks"]:
        check["evidence"] = refs
    data["temporal_checks"] = [
        {
            "name": name,
            "status": "pass",
            "observation": "Synthetic observed sequence only.",
            "event_ids": [e["id"] for e in manifest["events"]],
            "evidence": refs,
            "issue_indices": [],
        }
        for name in TEMPORAL_CRITERIA
    ]
    return job, data, manifest


def test_sample_cap_coverage_and_exact_frame_roundtrip():
    job, data, manifest = temporal_case()
    times = sample_times(job.composition, job.context)
    assert 3 <= len(times) <= 20 and list(times) == sorted(set(times))
    assert all(0 <= t < 1000 for t in times)
    assert len(manifest["events"]) == 3 and manifest["omitted_events"] > 0
    assert all(e["complete"] for e in manifest["events"])
    assert any(e["kind"] == "transition" for e in manifest["events"])
    validate_review(job, MotionReview.model_validate(data))
    assert sample_times(composition(), {}) == ()
    assert not temporal_enabled({})


@pytest.mark.parametrize("duration", [1, 2, 34, 67, 1000, 60000])
def test_short_outputs_and_frame_boundaries_are_bounded(duration):
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    data["scenes"] = data["scenes"][:1]
    scene = data["scenes"][0]
    scene["end_ms"] = data["duration_ms"] = duration
    element = scene["elements"][0]
    element["related_element_ids"] = []
    element["beats"][0]["end_ms"] = duration
    comp = planned(data)
    times = sample_times(comp, context())
    assert 1 <= len(times) <= 20 and all(0 <= t < duration for t in times)
    frames = tuple(frame(round(t * 30 // 1000 * 1000 / 30)) for t in times)
    if duration <= 34:
        assert not evidence_manifest(comp, frames, "current")["events"][0]["complete"]


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "unknown_event", "duplicate_event", "two_frames", "coverage", "unsent", "source"]
)
def test_temporal_verdict_needs_complete_current_sequences(change):
    job, data, _ = temporal_case()
    check = data["temporal_checks"][0]
    if change == "missing":
        data.pop("temporal_checks")
    elif change == "duplicate":
        data["temporal_checks"][1] = deepcopy(check)
    elif change == "unknown_event":
        check["event_ids"] = ["made-up"]
    elif change == "duplicate_event":
        check["event_ids"] = [check["event_ids"][0]] * 2
    elif change == "two_frames":
        check["evidence"] = check["evidence"][:2]
    elif change == "coverage":
        check["event_ids"] = check["event_ids"][:1]
    elif change == "unsent":
        check["evidence"] = [{**check["evidence"][0], "sha256": "f" * 64}]
    else:
        job = replace(job, source_frames=job.frames)
        check["evidence"] = [{**ref, "version": "source"} for ref in check["evidence"]]
    with pytest.raises(MotionReviewError):
        validate_review(job, MotionReview.model_validate(data))


def test_missing_decoded_frame_cannot_be_replaced_by_plan_or_claimed_diagnostics():
    job, data, manifest = temporal_case()
    removed = manifest["events"][0]["evidence"][0]["at_ms"]
    job = replace(
        job,
        frames=tuple(f for f in job.frames if f.ms != removed),
        context={**job.context, "render_diagnostics": {"temporal_sampling": manifest}},
    )
    for key in ("creative_checks", "temporal_checks"):
        for check in data[key]:
            check["evidence"] = [r for r in check["evidence"] if r["at_ms"] != removed]
    data["preference_evidence"] = [{"version": "current", "at_ms": job.frames[0].ms, "sha256": job.frames[0].sha256}]
    for criterion in data["criteria"]:
        if criterion["evidence"]:
            criterion["evidence"] = data["preference_evidence"]
    with pytest.raises(MotionReviewError, match="SEQUENCE_REQUIRED"):
        validate_review(job, MotionReview.model_validate(data))


def test_uncertainty_cannot_claim_adequacy_or_trigger_correction():
    job, data, _ = temporal_case()
    for check in data["temporal_checks"]:
        check.update(status="uncertain", evidence=[])
    with pytest.raises(ValidationError, match="temporal"):
        MotionReview.model_validate(data)
    data["verdict"] = "insufficient_evidence"
    review = MotionReview.model_validate(data)
    validate_review(job, review)
    assert not needs_correction(review)


def test_generic_motion_issue_cannot_bypass_uncertain_temporal_checks():
    job, data, _ = temporal_case()
    data["verdict"] = "needs_revision"
    data["issues"] = review_data(current=job.frames[0], revise=True)["issues"]
    data["issues"][0]["criterion"] = "motion"
    next(c for c in data["criteria"] if c["name"] == "motion")["status"] = "fail"
    for check in data["temporal_checks"]:
        check.update(status="uncertain", evidence=[])
    with pytest.raises(MotionReviewError, match="CORRECTION_UNGROUNDED"):
        validate_review(job, MotionReview.model_validate(data))


@pytest.mark.parametrize("invalid", [None, "index", "criterion", "unlinked", "uncertain"])
def test_correction_is_linked_to_demonstrated_temporal_failure(invalid):
    job, data, manifest = temporal_case()
    data["verdict"] = "needs_revision"
    data["issues"] = review_data(current=job.frames[0], revise=True)["issues"]
    next(c for c in data["criteria"] if c["name"] == "legibility")["status"] = "fail"
    check = next(c for c in data["temporal_checks"] if c["name"] == "reading_time")
    check.update(status="fail", issue_indices=[0])
    if invalid == "index":
        check["issue_indices"] = [-1]
    elif invalid == "criterion":
        check["name"] = "overlap"
        data["temporal_checks"][1]["name"] = "reading_time"
    elif invalid == "unlinked":
        check["issue_indices"] = []
    elif invalid == "uncertain":
        check["status"] = "uncertain"
    if invalid:
        with pytest.raises(MotionReviewError, match="CORRECTION_UNGROUNDED"):
            validate_review(job, MotionReview.model_validate(data))
    else:
        review = MotionReview.model_validate(data)
        validate_review(job, review)
        assert needs_correction(review)


def test_preference_needs_sequences_of_both_rendered_versions():
    job, data, manifest = temporal_case()
    previous = tuple(frame(f.ms, "red") for f in job.frames)
    job = replace(job, incumbent_composition=job.composition, incumbent_frames=previous)
    prev_manifest = evidence_manifest(job.composition, previous, "previous")
    data["preference_evidence"] = [manifest["events"][0]["evidence"][0], prev_manifest["events"][0]["evidence"][0]]
    with pytest.raises(MotionReviewError, match="COMPARISON_REQUIRED"):
        validate_review(job, MotionReview.model_validate(data))
    data["preference_evidence"] = manifest["events"][0]["evidence"] + prev_manifest["events"][0]["evidence"]
    validate_review(job, MotionReview.model_validate(data))


async def test_manifest_and_all_frames_are_in_one_counted_payload_without_extra_call():
    job, data, manifest = temporal_case()
    calls = []

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=response_data(data))

    client = provider(handler)
    payload = client.build_request(job)
    content = payload["input"][0]["content"]
    assert json.loads(content[0]["text"])["temporal_evidence"]["current"] == manifest
    assert sum(i["type"] == "input_image" for i in content) == len(job.frames) <= 20
    result = await client.submit(job, payload)
    assert len(calls) == 1 and len(result.review.temporal_checks) == 4
    with pytest.raises(MotionAIError, match="EVIDENCE_TOO_LARGE"):
        client.build_request(replace(job, frames=(job.frames * 21)[:21]))
    fixture = FixtureMotionProvider()
    synthetic = await fixture.submit(job, fixture.build_request(job))
    validate_review(job, synthetic.review)


def test_policy_and_plan_cannot_silently_downgrade():
    with pytest.raises(AuthError, match="POLICY_UNAVAILABLE"):
        temporal_enabled({"creative_contract": {"temporal_review": {"version": "future"}}})
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        events(composition())
    job, data, _ = temporal_case()
    with pytest.raises(MotionReviewError, match="CONTRACT_REQUIRED"):
        validate_review(replace(job, context={}), MotionReview.model_validate(data))


def test_review_prioritizes_linked_speech_events_with_the_existing_frame_limit():
    from app.tests.unit.test_motion_speech import speech_case

    ctx, composition = speech_case()
    selected, total = events(composition)
    assert total > len(selected)
    assert [event.kind for event in selected[:2]] == ["speech", "speech"]
    assert [event.start_ms for event in selected[:2]] == [0, 500]
    times = sample_times(composition, ctx)
    assert len(times) <= 20
    assert 0 in times and 500 in times


def synthetic_three_scene_plan():
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    prototype = data["scenes"][0]
    element = prototype["elements"][0]
    scenes = []
    for index, (start, end) in enumerate(((0, 4200), (3600, 9000), (8400, 11200))):
        scene = deepcopy(prototype)
        scene.update(id=f"scene-{index}", start_ms=start, end_ms=end, keyframe_ms=(start + end) // 2)
        item = deepcopy(element)
        item.update(id=f"item-{index}", related_element_ids=[])
        item["beats"][0].update(start_ms=start + 100, end_ms=start + 500, speech_cue_id="same-cue")
        scene["elements"] = [item]
        if index == 0:
            for number in range(3):
                duplicate = deepcopy(item)
                duplicate["id"] = f"duplicate-{number}"
                scene["elements"].append(duplicate)
        if index == 1:
            item.update(role="image", asset_id="assets/object.png")
            item["beats"][0].update(start_ms=6800, end_ms=7400, speech_cue_id="object-cue")
        scenes.append(scene)
    data.update(duration_ms=11200, scenes=scenes)
    return planned(data)


def test_v2_distributes_transitions_and_object_without_speech_crowding():
    comp = synthetic_three_scene_plan()
    old, total = events(comp)
    selected, new_total = events(comp, POLICY_V2)
    assert total == new_total and len({event.start_ms for event in old}) == 1
    assert [(event.id, event.start_ms, event.end_ms) for event in selected] == [
        ("transition-scene-1", 3500, 4200),
        ("beat-item-1-0", 6800, 7400),
        ("transition-scene-2", 8300, 9000),
    ]
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    times = sample_times(comp, ctx)
    assert len(times) <= 20 and times == tuple(sorted(set(times)))
    frames = tuple(frame(round((ms * 30 // 1000) * 1000 / 30)) for ms in times)
    manifest = evidence_manifest(comp, frames, "current", POLICY_V2)
    assert manifest["omitted_events"] == total - 3
    assert manifest["covered_scene_ids"] == ["scene-0", "scene-1", "scene-2"]
    assert not manifest["uncovered_scene_ids"] and not manifest["omitted_transitions"]
    assert all(event["complete"] for event in manifest["events"])
    missing_time = manifest["events"][0]["expected_times_ms"][0]
    missing = evidence_manifest(comp, tuple(item for item in frames if item.ms != missing_time), "current", POLICY_V2)
    assert missing["incomplete_events"] > 0


def test_v2_short_piece_discloses_incomplete_windows():
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    data["scenes"] = data["scenes"][:1]
    data["duration_ms"] = data["scenes"][0]["end_ms"] = 2
    item = data["scenes"][0]["elements"][0]
    item["related_element_ids"] = []
    item["beats"][0]["end_ms"] = 2
    comp = planned(data)
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    times = sample_times(comp, ctx)
    frames = tuple(frame(round(ms * 30 // 1000 * 1000 / 30)) for ms in times)
    manifest = evidence_manifest(comp, frames, "current", POLICY_V2)
    assert len(times) == 1 and manifest["incomplete_events"] == 1


def test_v2_storyboard_does_not_request_frame_at_duration_boundary():
    from app.services.motion_storyboard_frames import storyboard_moments
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    data["scenes"] = data["scenes"][:1]
    scene = data["scenes"][0]
    data["duration_ms"] = scene["end_ms"] = 34
    scene["keyframe_ms"] = 0
    item = scene["elements"][0]
    item["related_element_ids"] = []
    item["beats"][0]["end_ms"] = 34
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    moments = storyboard_moments(planned(data), ctx)
    assert [moment["requested_ms"] for moment in moments] == [0]


@pytest.mark.parametrize("duration", [34, 67, 1000, 60000])
def test_v2_sample_bounds_at_short_and_long_durations(duration):
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    data["scenes"] = data["scenes"][:1]
    data["duration_ms"] = data["scenes"][0]["end_ms"] = duration
    item = data["scenes"][0]["elements"][0]
    item["related_element_ids"] = []
    item["beats"][0]["end_ms"] = duration
    comp = planned(data)
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    times = sample_times(comp, ctx)
    assert 1 <= len(times) <= 20 and times == tuple(sorted(set(times)))
    assert all(0 <= instant < duration for instant in times)


def test_v2_manifest_and_coverage_rules_reach_real_request_builder():
    comp = synthetic_three_scene_plan()
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    frames = tuple(frame(round((ms * 30 // 1000) * 1000 / 30)) for ms in sample_times(comp, ctx))
    job = replace(request("review", composition=comp, frames=frames), context=ctx)
    payload = provider(lambda _: pytest.fail("Network must not be called")).build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])["temporal_evidence"]["current"]
    assert sent == evidence_manifest(comp, frames, "current", POLICY_V2)
    assert "passagens omitidas" in payload["instructions"]
    assert sum(block["type"] == "input_image" for block in payload["input"][0]["content"]) == len(frames)


def test_v2_reports_omitted_transitions_and_does_not_allow_temporal_pass():
    from app.tests.unit.test_motion_plan import plan_data

    data = plan_data()
    prototype = data["scenes"][0]
    scenes = []
    for index in range(5):
        scene = deepcopy(prototype)
        scene.update(id=f"scene-{index}", start_ms=index * 1000, end_ms=(index + 1) * 1000)
        item = scene["elements"][0]
        item.update(id=f"item-{index}", related_element_ids=[])
        item["beats"][0].update(start_ms=index * 1000, end_ms=index * 1000 + 400)
        scenes.append(scene)
    data.update(duration_ms=5000, scenes=scenes)
    comp = planned(data)
    ctx = context()
    ctx["creative_contract"]["temporal_review"] = POLICY_V2
    frames = tuple(frame(round((ms * 30 // 1000) * 1000 / 30)) for ms in sample_times(comp, ctx))
    manifest = evidence_manifest(comp, frames, "current", POLICY_V2)
    assert manifest["omitted_transitions"] == 2
    assert len(frames) <= 20
    job, review_data_value, _ = temporal_case()
    refs = [{"version": "current", "at_ms": item.ms, "sha256": item.sha256} for item in frames]
    for check in review_data_value["temporal_checks"]:
        check["event_ids"] = [event["id"] for event in manifest["events"]]
        check["evidence"] = refs
    review = MotionReview.model_validate(review_data_value)
    with pytest.raises(MotionReviewError, match="COVERAGE_REQUIRED"):
        validate_temporal_review(replace(job, context=ctx, composition=comp, frames=frames), review)
