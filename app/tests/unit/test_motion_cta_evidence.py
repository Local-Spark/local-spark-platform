"""CTA evidence is sampled, versioned and never an automatic approval."""

from copy import deepcopy
from dataclasses import replace

import pytest

from app.schemas.motion_production import MotionReview
from app.services.motion_context import capture_motion_guidance
from app.services.motion_review import MotionReviewError, validate_temporal_review
from app.services.motion_storyboard_frames import storyboard_moments
from app.services.motion_temporal import POLICY_V4, POLICY_V5, events, evidence_manifest, sample_times
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_photo_hard import artifact
from app.tests.unit.test_motion_photo_planning import photo_case
from app.tests.unit.test_motion_photo_polish import case
from app.tests.unit.test_motion_staging import staged_composition
from app.tests.unit.test_motion_temporal import temporal_case


def cta_case(start=13400):
    data, _ = case()
    data["motion_plan"]["scenes"][-1]["elements"][-1]["beats"][0]["end_ms"] = start
    base = data["staging"]["moments"][0]
    moments = []
    scenes = data["motion_plan"]["scenes"]
    for i, scene in enumerate(scenes):
        moment = deepcopy(base)
        moment.update(
            scene_id=scene["id"],
            protagonist_id=scene["elements"][0]["id"],
            inspect_start_ms=scene["start_ms"],
            inspect_end_ms=scene["end_ms"],
        )
        if i < len(scenes) - 1:
            moment["transition"].update(
                next_scene_id=scenes[i + 1]["id"],
                start_ms=scene["end_ms"] - 100,
                end_ms=scene["end_ms"] + 100,
            )
        else:
            moment["transition"] = None
        moments.append(moment)
    moments[-1]["inspect_start_ms"] = 12534
    data["staging"]["moments"] = moments
    return artifact(data)


def ctx(policy=POLICY_V5):
    return {"creative_contract": {"temporal_review": policy}}


@pytest.mark.parametrize("start", [13400, 13500, 13401])
def test_cta_entry_is_sampled_despite_late_staging_window(start):
    comp = cta_case(start)
    times = sample_times(comp, ctx())
    indices = {t * 30 // 1000 for t in times}
    assert start * 30 // 1000 - 1 in indices
    assert (start * 30 + 999) // 1000 in indices
    assert max(indices) == 449 and len(times) <= 48
    frames = tuple(frame(round(i * 1000 / 30)) for i in sorted(indices))
    report = evidence_manifest(comp, frames, "current", POLICY_V5)
    window = next(e for e in report["events"] if e["kind"] == "reading")
    assert window["start_ms"] == start and window["end_ms"] == 15000
    assert window["last_frame_end_ms"] == 15000
    assert window["minimum_reading_ms"] == 1500
    assert window["complete"] and report["coverage_complete"]
    old = evidence_manifest(comp, (), "current", POLICY_V4)
    old_close = next(e for e in old["events"] if e["id"] == "moment-scene2")
    assert old_close["expected_times_ms"] == [12533, 13767, 14967]
    assert old_close["expected_times_ms"][-1] - old_close["expected_times_ms"][-2] == 1200

    missing = tuple(f for f in frames if f.ms not in window["expected_times_ms"][:2])
    assert not evidence_manifest(comp, missing, "current", POLICY_V5)["coverage_complete"]


def test_no_photo_closing_no_invented_cta_and_v4_unchanged():
    comp = staged_composition()
    assert events(comp, POLICY_V5) == events(comp, POLICY_V4)
    photo = cta_case()
    assert not any(e.kind == "reading" for e in events(photo, POLICY_V4)[0])
    body, prepared, _ = photo_case()
    old = deepcopy(prepared.context)
    old["creative_contract"]["temporal_review"] = POLICY_V4
    assert capture_motion_guidance(body, previous=old)["creative_contract"]["temporal_review"] == POLICY_V4
    assert capture_motion_guidance(body)["creative_contract"]["temporal_review"] == POLICY_V5


def test_manifest_missing_cta_cannot_pass_and_wire_explains_real_last_frame():
    base, data, _ = temporal_case()
    comp = cta_case()
    times = sample_times(comp, ctx())
    frames = tuple(frame(round(t * 30 // 1000 * 1000 / 30)) for t in times)
    report = evidence_manifest(comp, frames, "current", POLICY_V5)
    refs = [ref for e in report["events"] for ref in e["evidence"]]
    refs = list({(r["at_ms"], r["sha256"]): r for r in refs}.values())
    for check in data["temporal_checks"]:
        check.update(event_ids=[e["id"] for e in report["events"]], evidence=refs)
    job = replace(base, composition=comp, frames=frames, context=ctx())
    review = MotionReview.model_validate(data)
    validate_temporal_review(job, review)
    reading = next(e for e in report["events"] if e["kind"] == "reading")
    missing = tuple(f for f in frames if f.ms != reading["expected_times_ms"][0])
    with pytest.raises(MotionReviewError, match="COVERAGE_REQUIRED"):
        validate_temporal_review(replace(job, frames=missing), review)
    wire_context = {
        **base.context,
        "creative_contract": {**base.context["creative_contract"], "temporal_review": POLICY_V5},
    }
    wire = provider().build_request(replace(request("review", composition=comp, frames=frames), context=wire_context))
    assert "não existe frame em 15000ms" in wire["instructions"]


def test_storyboard_and_review_share_cta_frame_indices():
    _, prepared, plan = photo_case()
    comp = artifact(plan.model_dump(mode="json"))
    # The real shared plan includes scene directions needed by storyboard.
    moments = storyboard_moments(comp, prepared.context)
    expected = {t * 30 // 1000 for t in sample_times(comp, prepared.context)}
    assert expected <= {m["frame_index"] for m in moments}
    assert len(moments) <= 48


def test_legacy_selection_keeps_duplicate_start_and_hold_fallback_behavior():
    from app.services.motion_temporal import POLICY_V2

    comp = cta_case()
    selected, total = events(comp, POLICY_V2)
    assert len(selected) == 3 and total > 3
    scene = comp.motion_plan.scenes[0]
    element = scene.elements[0]
    beat = element.beats[0]
    element = element.model_copy(
        update={
            "role": "text",
            "beats": tuple(
                beat.model_copy(update={"phase": "hold", "start_ms": a, "end_ms": b})
                for a, b in [(0, 1000), (1500, 2500), (3000, 4000)]
            ),
        }
    )
    scene = scene.model_copy(update={"elements": (element,)})
    comp = comp.model_copy(update={"motion_plan": comp.motion_plan.model_copy(update={"scenes": (scene,)})})
    assert len(events(comp, POLICY_V2)[0]) == 3
