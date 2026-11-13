"""The planner's content/material decisions must actually reach construction and inspection."""

import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_construction import implement_motion
from app.services.motion_context import capture_motion_guidance
from app.services.motion_generation import construction_plan_hash, decode_construction_plan
from app.services.motion_repertoire import load_repertoire_images
from app.services.motion_staging import require_staging_materials, staging_enabled, staging_input, validate_staging
from app.services.motion_temporal import POLICY_V4, events, evidence_manifest, sample_times
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_audiovisual import (
    audiovisual_wire,
    natural_body,
    natural_context,
    natural_plan,
    natural_prepared,
)


def staged_context():
    return {
        **natural_context(),
        **capture_motion_guidance(natural_body(repertoire_id="business-reel-v5")),
        "styles": [{"id": "editorial"}],
    }


def staging_data():
    return {
        "version": "motion-staging-v1",
        "unavailable_materials": [],
        "moments": [
            {
                "scene_id": "hook",
                "contribution": "Establish the question",
                "protagonist_id": "title",
                "media_relation": "graphic",
                "material_element_ids": [],
                "development": "Question unfolds",
                "sustained_value": "Read the question",
                "inspect_start_ms": 0,
                "inspect_end_ms": 300,
                "transition": {
                    "next_scene_id": "close",
                    "start_ms": 400,
                    "end_ms": 700,
                    "element_ids": ["title", "answer"],
                    "origin": "Question",
                    "crossing": "Handoff",
                    "destination": "Answer",
                },
            },
            {
                "scene_id": "close",
                "contribution": "Resolve the question",
                "protagonist_id": "answer",
                "media_relation": "graphic",
                "material_element_ids": [],
                "development": "Answer revealed",
                "sustained_value": "Read the answer",
                "inspect_start_ms": 700,
                "inspect_end_ms": 1000,
                "transition": None,
            },
        ],
    }


def staged_plan():
    return MotionConstructionPlan.model_validate({**natural_plan().model_dump(mode="json"), "staging": staging_data()})


def staged_composition():
    return HTMLMotionComposition.model_validate(
        {**staged_plan().model_dump(mode="json"), "html": "<div></div>", "scene_init": "window.seek=()=>{}"}
    )


def staged_job():
    p = natural_prepared()
    ctx = staged_context()
    return replace(
        request(),
        context=ctx,
        assets=p.assets,
        source_frames=p.source_frames,
        reference_images=load_repertoire_images(ctx),
    )


def test_real_builder_supplies_qualified_mechanisms_inventory_and_required_staging_schema():
    job = staged_job()
    payload = provider().build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert payload["text"]["format"]["name"] == "MotionStagedPlanningOutput"
    assert "staging" in payload["text"]["format"]["schema"]["required"]
    assert len(job.reference_images) == 2 and len(sent["material_inventory"]["source_samples"]) == 2
    assert all(r.sha256 not in {a.sha256 for a in job.assets} for r in job.reference_images)
    assert sent["authorized_context"]["request"]["instruction"] == natural_body().instruction
    assert job.baseline_frames == () and sent["material_inventory"]["image_generation"] is None
    assert (
        decode_construction_plan(json.dumps({**audiovisual_wire(), "staging": staging_data()}), job.context)
        == staged_plan()
    )
    validate_staging(staged_plan(), job.context)
    require_staging_materials(staged_plan(), job.context)


def test_new_default_and_recapture_preserve_versions_and_old_plan_hash():
    old = natural_plan()
    assert "staging" not in old.model_dump(mode="json")
    before = construction_plan_hash(old)
    body = natural_body(repertoire_id=None)
    new = capture_motion_guidance(body)
    assert staging_enabled(new) and new["repertoire"]["id"] == "business-reel-v5"
    assert capture_motion_guidance(body, previous=new) == new
    legacy = capture_motion_guidance(natural_body())
    assert not staging_enabled(legacy)
    assert capture_motion_guidance(natural_body(), previous=legacy)["repertoire"] == legacy["repertoire"]
    assert before == construction_plan_hash(old)
    validate_staging(old, legacy)
    assert staging_input(replace(staged_job(), context=legacy)) is None


def test_transition_can_span_overlapping_scene_handoff_from_incoming_start():
    data = staged_plan().model_dump(mode="json")
    first, following = data["motion_plan"]["scenes"]
    first["end_ms"] = 650
    transition = data["staging"]["moments"][0]["transition"]
    transition.update(start_ms=following["start_ms"], end_ms=650)
    validate_staging(MotionConstructionPlan.model_validate(data), staged_context())
    transition["end_ms"] = 620
    with pytest.raises(AuthError, match="TRANSITION_INVALID"):
        validate_staging(MotionConstructionPlan.model_validate(data), staged_context())


@pytest.mark.parametrize(
    "change",
    [
        "contract",
        "missing",
        "plan",
        "unexpected",
        "scenes",
        "protagonist",
        "material",
        "duplicate",
        "interval",
        "relation",
        "transition",
        "next",
        "target",
        "duplicate_target",
        "boundary",
        "last",
    ],
)
def test_invalid_planning_links_cannot_be_approved_as_executable(change):
    ctx, data = staged_context(), staged_plan().model_dump(mode="json")
    moment = data["staging"]["moments"][0]
    if change == "contract":
        ctx["staging_contract"] = {"version": "invented"}
    elif change == "missing":
        data.pop("staging")
    elif change == "plan":
        data["motion_plan"] = None
    elif change == "unexpected":
        ctx.pop("staging_contract")
    elif change == "scenes":
        moment["scene_id"] = "missing"
    elif change == "protagonist":
        moment["protagonist_id"] = "missing"
    elif change == "material":
        moment["material_element_ids"] = ["title"]
    elif change == "duplicate":
        moment["material_element_ids"] = ["title", "title"]
    elif change == "interval":
        moment["inspect_end_ms"] = 900
    elif change == "relation":
        moment["media_relation"] = "recording_dominant"
    elif change == "transition":
        moment["transition"] = None
    elif change == "next":
        moment["transition"]["next_scene_id"] = "missing"
    elif change == "target":
        moment["transition"]["element_ids"] = ["missing"]
    elif change == "duplicate_target":
        moment["transition"]["element_ids"] = ["title", "title"]
    elif change == "boundary":
        moment["transition"]["start_ms"] = 600
    else:
        data["staging"]["moments"][-1]["transition"] = deepcopy(moment["transition"])
    artifact = HTMLMotionComposition.model_validate({**data, "html": "x", "scene_init": "x"})
    with pytest.raises(AuthError, match="MOTION_STAGING"):
        validate_staging(artifact, ctx)


async def test_missing_material_stops_before_reservation_generation_or_substitution():
    plan = staged_plan()
    plan = plan.model_copy(
        update={
            "staging": plan.staging.model_copy(
                update={"unavailable_materials": ("Required product macro not supplied",)}
            )
        }
    )
    prepared = replace(natural_prepared(), context=staged_context())
    effects = SimpleNamespace(capacity=AsyncMock(), model=AsyncMock())
    with pytest.raises(AuthError, match="REQUIRES_PLAN_REVISION"):
        await implement_motion(effects, provider(), {"operation_id": uuid4()}, uuid4(), prepared, plan, None)
    effects.capacity.assert_not_awaited()
    effects.model.assert_not_awaited()


def test_temporal_sampling_consumes_declared_intervals_and_accounts_for_missing_frames():
    comp, ctx = staged_composition(), staged_context()
    selected, count = events(comp, POLICY_V4)
    assert count == 3 and {e.kind for e in selected} == {"transition", "staging"}
    times = sample_times(comp, ctx)
    frames = tuple(frame(round(t * 30 // 1000 * 1000 / 30)) for t in times)
    report = evidence_manifest(comp, frames, "current", POLICY_V4)
    assert report["coverage_complete"] and report["omitted_event_ids"] == []
    assert not evidence_manifest(comp, (), "current", POLICY_V4)["coverage_complete"]
    assert len(times) <= 48
    with pytest.raises(AuthError, match="STAGING_REQUIRED"):
        events(comp.model_copy(update={"staging": None}), POLICY_V4)


def test_more_events_are_bounded_and_omissions_are_named_not_certified():
    comp = staged_composition()
    # Stress the selector with separated intervals, using the maximum legal scene count.
    base = comp.staging.moments[0]
    moments = tuple(
        base.model_copy(
            update={
                "scene_id": f"s{i}",
                "inspect_start_ms": i * 5000,
                "inspect_end_ms": i * 5000 + 2000,
                "transition": base.transition.model_copy(
                    update={"next_scene_id": f"s{i + 1}", "start_ms": i * 5000 + 3000, "end_ms": i * 5000 + 4000}
                )
                if i < 11
                else None,
            }
        )
        for i in range(12)
    )
    comp = comp.model_copy(
        update={
            "staging": comp.staging.model_copy(update={"moments": moments}),
            "motion_plan": comp.motion_plan.model_copy(update={"duration_ms": 60000}),
        }
    )
    selected, count = events(comp, POLICY_V4)
    assert count == 23 and len(selected) <= 16
    report = evidence_manifest(comp, (), "current", POLICY_V4)
    assert len(report["omitted_event_ids"]) == count - len(selected) and not report["coverage_complete"]
    assert len(sample_times(comp, staged_context())) <= 48


def test_temporal_pass_requires_actual_complete_sequences_and_storyboard_requires_plan():
    from app.schemas.motion_production import MotionReview
    from app.services.motion_review import MotionReviewError, validate_temporal_review
    from app.services.motion_storyboard_frames import storyboard_moments
    from app.services.motion_temporal import temporal_payload
    from app.tests.unit.test_motion_temporal import temporal_case

    comp, ctx = staged_composition(), staged_context()
    job = replace(staged_job(), composition=comp)
    _, data, _ = temporal_case()
    with pytest.raises(MotionReviewError, match="COVERAGE_REQUIRED"):
        validate_temporal_review(job, MotionReview.model_validate(data))
    frames = tuple(frame(round(t * 30 // 1000 * 1000 / 30)) for t in sample_times(comp, ctx))
    report = evidence_manifest(comp, frames, "current", POLICY_V4)
    for check in data["temporal_checks"]:
        check["event_ids"] = [event["id"] for event in report["events"]]
        check["evidence"] = [{"version": "current", "at_ms": f.ms, "sha256": f.sha256} for f in frames]
    validate_temporal_review(replace(job, frames=frames), MotionReview.model_validate(data))
    with pytest.raises(AuthError, match="TEMPORAL_PLAN_REQUIRED"):
        temporal_payload(ctx, None, (), None, ())
    for update in ({"motion_plan": None}, {"scene_direction": None}):
        with pytest.raises(AuthError, match="STORYBOARD_PLAN_REQUIRED"):
            storyboard_moments(comp.model_copy(update=update), ctx)


def test_storyboard_respects_raster_budget_when_scene_cards_compete_with_transition_evidence():
    from app.services.motion_storyboard_frames import storyboard_moments

    comp = staged_composition()
    moments, scenes = [], []
    for i in range(12):
        base = comp.staging.moments[0]
        moments.append(
            base.model_copy(
                update={
                    "scene_id": f"s{i}",
                    "inspect_start_ms": i * 5000,
                    "inspect_end_ms": i * 5000 + 2000,
                    "transition": base.transition.model_copy(
                        update={"next_scene_id": f"s{i + 1}", "start_ms": i * 5000 + 3000, "end_ms": i * 5000 + 6000}
                    )
                    if i < 11
                    else None,
                }
            )
        )
        scenes.append(
            comp.motion_plan.scenes[0].model_copy(
                update={"id": f"s{i}", "start_ms": i * 5000, "end_ms": (i + 1) * 5000, "keyframe_ms": i * 5000 + 4800}
            )
        )
    comp = comp.model_copy(
        update={
            "staging": comp.staging.model_copy(update={"moments": tuple(moments)}),
            "motion_plan": comp.motion_plan.model_copy(update={"scenes": tuple(scenes), "duration_ms": 60000}),
        }
    )
    result = storyboard_moments(comp, staged_context())
    assert len(result) <= 48 and len({r["frame_index"] for r in result}) == len(result)
    assert any(r.get("kind") == "transition" for r in result)
    assert not evidence_manifest(comp, (), "current", POLICY_V4)["coverage_complete"]


def test_legacy_graphic_hold_does_not_invent_an_action_event():
    from app.services.motion_temporal import POLICY

    comp = staged_composition()
    scene = comp.motion_plan.scenes[0]
    element = scene.elements[0]
    held = element.model_copy(
        update={"role": "image", "beats": tuple(b.model_copy(update={"phase": "hold"}) for b in element.beats)}
    )
    comp = comp.model_copy(
        update={
            "motion_plan": comp.motion_plan.model_copy(
                update={"scenes": (scene.model_copy(update={"elements": (held,)}),)}
            )
        }
    )
    selected, total = events(comp, POLICY)
    assert not selected and total == 0
