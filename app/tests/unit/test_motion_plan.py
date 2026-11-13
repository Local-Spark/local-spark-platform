"""Temporal direction is grounded in the request and cannot bypass render admission."""

from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_fixture import FixtureMotionProvider
from app.schemas.motion_plan import MotionCurve, MotionPlan
from app.schemas.motion_production import HTMLMotionComposition, MotionReview
from app.services.auth import AuthError
from app.services.motion_creative import motion_creative_contract
from app.services.motion_plan import requires_motion_plan, validate_motion_plan
from app.tests.unit.test_motion_ai import composition, provider, request, response_data, review_data


def plan_data():
    def element(identifier, start, end, related):
        return {
            "id": identifier,
            "role": "text",
            "asset_id": None,
            "purpose": "Reveal the message",
            "related_element_ids": related,
            "coordination": "Hand attention to the next message",
            "beats": [
                {
                    "phase": "enter",
                    "start_ms": start,
                    "end_ms": end,
                    "start_state": "y=40px, opacity=0",
                    "end_state": "y=0px, opacity=1",
                    "trajectory": "Vertical, then hold",
                    "curve": {"kind": "ease_out", "parameters": []},
                }
            ],
        }

    return {
        "version": "motion-plan-v1",
        "identity_source": "business_kit",
        "duration_ms": 1000,
        "style_id": "editorial",
        "scenes": [
            {
                "id": "hook",
                "start_ms": 0,
                "end_ms": 600,
                "message": "Question",
                "transition_to_next": "Overlapping handoff",
                "elements": [element("title", 0, 300, ["answer"])],
            },
            {
                "id": "close",
                "start_ms": 500,
                "end_ms": 1000,
                "message": "Answer",
                "transition_to_next": "End",
                "elements": [element("answer", 500, 800, [])],
            },
        ],
    }


def context():
    return {
        "creative_contract": motion_creative_contract(),
        "styles": [{"id": "editorial"}],
        "kit": {"overrides": {"brand_name": "Business identity"}},
        "skill": {"id": "authorized-skill", "instructions": "Use the business kit"},
        "output": {"duration_ms": 1000},
        "authorized_audio": {"mode": "silent", "tracks": []},
    }


def planned(data=None):
    data = data or plan_data()
    return HTMLMotionComposition.model_validate(
        {**composition().model_dump(), "motion_plan": data, "scene_direction": direction_data(data)}
    )


def direction_data(plan=None):
    return {
        "version": "scene-direction-v1",
        "scenes": [
            {
                "scene_id": scene["id"],
                "brief_basis": "Synthetic request for an editorial question and answer.",
                "visual_representation": "Typographic question unfolding into an answer.",
                "composition": "Primary text at top left, room for the next statement.",
                "narrative_action": "Reveal the answer as the question yields attention.",
                "attention_order": [e["id"] for e in scene["elements"]],
                "elements": [
                    {
                        "element_id": e["id"],
                        "depicts": "The authorized message",
                        "appearance": "Business kit typography and colors",
                        "construction": "authorized_asset" if e["asset_id"] else "code",
                    }
                    for e in scene["elements"]
                ],
            }
            for scene in (plan or plan_data())["scenes"]
        ],
    }


def test_overlapping_scenes_and_legacy_documents_are_supported():
    validate_motion_plan(planned(), context(), duration_ms=1000, asset_ids=set())
    for old in ({}, {"creative_contract": {"version": "reel-creative-v1"}}):
        assert not requires_motion_plan(old)
        validate_motion_plan(composition(), old, duration_ms=1000, asset_ids=set())
    data = plan_data()
    data["scenes"][0]["end_ms"] = 1000
    assert MotionPlan.model_validate(data).duration_ms == 1000


@pytest.mark.parametrize(
    "change",
    [
        "gap",
        "end",
        "duplicate_scene",
        "duplicate_element",
        "self_link",
        "unknown_link",
        "duplicate_link",
        "beat_outside",
        "beat_overlap",
        "zero_beat",
        "missing_asset",
        "extra_asset",
        "identity",
    ],
)
def test_malformed_temporal_plans_are_rejected(change):
    data = plan_data()
    scene, last = data["scenes"]
    element = scene["elements"][0]
    beat = element["beats"][0]
    if change == "gap":
        last["start_ms"] = 700
    elif change == "end":
        data["duration_ms"] = 1100
    elif change == "duplicate_scene":
        last["id"] = scene["id"]
    elif change == "duplicate_element":
        last["elements"][0]["id"] = element["id"]
    elif change == "self_link":
        element["related_element_ids"] = ["title"]
    elif change == "unknown_link":
        element["related_element_ids"] = ["absent"]
    elif change == "duplicate_link":
        element["related_element_ids"] = ["answer", "answer"]
    elif change == "beat_outside":
        beat["end_ms"] = 700
    elif change == "beat_overlap":
        element["beats"].append(deepcopy(beat))
    elif change == "zero_beat":
        beat["end_ms"] = 0
    elif change == "missing_asset":
        element["role"] = "video"
    elif change == "extra_asset":
        element["asset_id"] = "assets/source.mp4"
    else:
        data["identity_source"] = "reference"
    with pytest.raises(ValidationError):
        MotionPlan.model_validate(data)


@pytest.mark.parametrize(
    "kind,params",
    [
        ("linear", [1]),
        ("cubic_bezier", [0, 0, 1]),
        ("cubic_bezier", [-1, 0, 1, 1]),
        ("spring", [100, 0, 1]),
        ("spring", [100, 10]),
        ("spring", [100, 10, float("inf")]),
        ("cubic_bezier", [0, float("nan"), 1, 1]),
    ],
)
def test_invalid_curves_cannot_reach_renderer(kind, params):
    with pytest.raises(ValidationError):
        MotionCurve(kind=kind, parameters=params)


def test_overshooting_curves_and_positive_springs_are_allowed():
    assert MotionCurve(kind="cubic_bezier", parameters=[0.2, -0.5, 0.5, 1.5]).parameters[1] == -0.5
    assert MotionCurve(kind="spring", parameters=[100, 10, 1]).parameters == (100, 10, 1)


@pytest.mark.parametrize(
    "problem,code",
    [
        ("missing", "REQUIRED"),
        ("duration", "DURATION_CHANGED"),
        ("style", "STYLE_UNAVAILABLE"),
        ("asset", "ASSET_UNAVAILABLE"),
    ],
)
def test_plans_cannot_change_authorized_duration_style_or_material(problem, code):
    data = plan_data()
    ctx = context()
    if problem == "style":
        ctx["styles"] = []
    if problem == "asset":
        data["scenes"][0]["elements"][0].update(role="video", asset_id="assets/foreign.mp4")
    with pytest.raises(AuthError, match=f"MOTION_PLAN_{code}"):
        validate_motion_plan(
            composition() if problem == "missing" else planned(data),
            ctx,
            duration_ms=2000 if problem == "duration" else 1000,
            asset_ids={"assets/source.mp4"},
        )


def test_unknown_contract_is_not_silently_downgraded():
    with pytest.raises(AuthError, match="CONTRACT_UNKNOWN"):
        requires_motion_plan({"creative_contract": {"version": "future"}})


@pytest.mark.parametrize("kind", ["generate", "correct"])
async def test_model_requires_plan_in_same_call_and_preserves_context(kind):
    seen = []

    def handler(sent):
        seen.append(sent)
        return httpx.Response(200, json=response_data(planned().model_dump(mode="json")))

    client = provider(handler)
    job = replace(
        request(kind, composition=planned(), review=MotionReview.model_validate(review_data(revise=True))),
        context=context(),
    )
    payload = client.build_request(job)
    schema = payload["text"]["format"]["schema"]
    assert "motion_plan" in schema["required"]
    assert schema["properties"]["motion_plan"] == {"$ref": "#/$defs/MotionPlan"}
    result = await client.submit(job, payload)
    assert result.composition.motion_plan == planned().motion_plan
    assert len(seen) == 1
    import json

    sent_context = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert sent_context == context()


async def test_model_missing_plan_fails_without_retry():
    calls = []

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=response_data())

    client = provider(handler)
    job = replace(request(), context=context())
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID"):
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1


async def test_local_synthetic_provider_remains_usable_with_new_contract():
    client = FixtureMotionProvider()
    job = replace(request(), context=context())
    result = await client.submit(job, client.build_request(job))
    validate_motion_plan(result.composition, context(), duration_ms=1000, asset_ids={"assets/source.mp4"})
    assert result.estimated_usd_micros == 0


def test_scene_end_cannot_exceed_the_declared_output_duration():
    data = plan_data()
    data["duration_ms"] = data["scenes"][-1]["end_ms"] - 1
    with pytest.raises(ValidationError, match="Scene outside output timeline"):
        planned(data)


def test_structural_floor_rejects_a_thin_plan_only_when_selected():
    from uuid import uuid4

    from app.schemas.motion_production import MotionRequest
    from app.services.motion_context import capture_motion_guidance

    validate_motion_plan(planned(), context(), duration_ms=1000, asset_ids=set())
    selected = context()
    selected["structural_floor"] = "motion-production-quality-v3"
    with pytest.raises(AuthError, match="MOTION_STRUCTURAL_FLOOR_REJECTED"):
        validate_motion_plan(planned(), selected, duration_ms=1000, asset_ids=set())
    body = MotionRequest(
        operation_id=uuid4(),
        source_asset_id=uuid4(),
        instruction="Café",
        structural_floor="motion-production-quality-v3",
    )
    captured = capture_motion_guidance(body)
    assert captured["structural_floor"] == "motion-production-quality-v3"
    assert "Piso estrutural v3" in captured["creative_contract"]["motion_plan_rules"]
    plain = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Café")
    assert "structural_floor" not in plain.model_dump(mode="json")


def test_direction_cannot_claim_an_undeclared_generated_material():
    from app.services.motion_plan import validate_scene_direction
    from app.tests.unit.test_motion_illustrations import composition_with_art

    composition = composition_with_art().model_copy(update={"illustrations": ()})
    with pytest.raises(AuthError, match="ILLUSTRATION_UNDECLARED"):
        validate_scene_direction(composition, context())
