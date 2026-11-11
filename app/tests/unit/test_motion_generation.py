"""No paid IO: compact construction restores only the authoritative supplied direction."""

import json
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest

from app.adapters.motion_ai import MotionAIError
from app.schemas.motion_production import MotionRequest, MotionReview
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_generation import (
    GENERATION_CONTRACT,
    LEGACY_GENERATION_CONTRACT,
    STAGED_GENERATION_CONTRACT,
    decode_provided_output,
    generation_wire_model,
    provided_output_enabled,
)
from app.services.motion_plan import validate_motion_plan
from app.tests.unit.test_motion_ai import frame, provider, request, response_data, review_data
from app.tests.unit.test_motion_plan import direction_data, planned
from app.tests.unit.test_motion_visual_direction import provided_context


def compact_context():
    return {**provided_context(), "generation_contract": deepcopy(LEGACY_GENERATION_CONTRACT)}


def wire_data():
    return {**planned().model_dump(mode="json", exclude={"scene_direction"}), "illustrations": []}


@pytest.mark.parametrize("kind", ["generate", "correct"])
async def test_provided_direction_is_restored_without_echo_and_preserved_on_correction(kind):
    ctx = compact_context()
    original = deepcopy(ctx)
    client = provider(lambda _: httpx.Response(200, json=response_data(wire_data())))
    job = replace(
        request(kind, composition=planned(), review=MotionReview.model_validate(review_data(revise=True))), context=ctx
    )
    payload = client.build_request(job)
    assert "scene_direction" not in payload["text"]["format"]["schema"]["properties"]
    assert "não devolva scene_direction" in payload["instructions"]
    result = await client.submit(job, payload)
    assert result.composition.scene_direction.model_dump(mode="json") == original["request"]["scene_direction"]
    assert ctx == original
    validate_motion_plan(result.composition, ctx, duration_ms=1000, asset_ids=set())
    assert result.composition.html == planned().html
    assert result.composition.scene_init == planned().scene_init


async def test_no_model_supplied_direction_can_override_server_input():
    data = wire_data()
    data["scene_direction"] = direction_data()
    client = provider(lambda _: httpx.Response(200, json=response_data(data)))
    job = replace(request(), context=compact_context())
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID"):
        await client.submit(job, client.build_request(job))


@pytest.mark.parametrize("change", ["unknown", "missing_direction", "wrong_mode"])
def test_contract_fails_closed_before_any_provider_io(change):
    ctx = compact_context()
    if change == "unknown":
        ctx["generation_contract"]["version"] = "unknown"
    elif change == "missing_direction":
        ctx["request"].pop("scene_direction")
    else:
        ctx["creative_contract"]["version"] = "reel-creative-v4"
    with pytest.raises(AuthError):
        provider().build_request(replace(request(), context=ctx))


def test_new_capture_compacts_provided_only_and_recapture_preserves_old_wire():
    body = MotionRequest(
        operation_id=uuid4(),
        source_asset_id=uuid4(),
        instruction="Synthetic direction",
        scene_direction=direction_data(),
    )
    current = capture_motion_guidance(body)
    assert provided_output_enabled(current)
    assert "Devolva scene_direction" not in current["creative_contract"]["scene_direction_rules"]
    assert "generation_contract" not in capture_motion_guidance(body.model_copy(update={"scene_direction": None}))
    historical = capture_motion_guidance(body, previous={**current, "generation_contract": None})
    assert "generation_contract" not in historical
    assert (
        "scene_direction"
        in provider().build_request(replace(request(), context=historical))["text"]["format"]["schema"]["properties"]
    )
    assert capture_motion_guidance(body, previous=current)["generation_contract"] == current["generation_contract"]
    assert not provided_output_enabled(provided_context())
    with pytest.raises(AuthError, match="CONTRACT_REQUIRED"):
        decode_provided_output(json.dumps(wire_data()), provided_context())


def test_compact_contract_requires_provided_direction_and_keeps_review_full():
    ctx = compact_context()
    ctx["creative_contract"]["version"] = "reel-creative-v4"
    ctx["request"].pop("scene_direction")
    with pytest.raises(AuthError, match="DIRECTION_REQUIRED"):
        provided_output_enabled(ctx)
    ctx = compact_context()
    payload = provider().build_request(
        replace(request("review", composition=planned(), frames=(frame(),)), context=ctx)
    )
    data = json.loads(payload["input"][0]["content"][0]["text"])
    assert data["current_composition"]["scene_direction"] == ctx["request"]["scene_direction"]
    assert payload["text"]["format"]["name"] == "MotionReview"


def compact_wire(data):
    data = deepcopy(data)
    aliases = {
        "phase": "p",
        "start_ms": "s",
        "end_ms": "e",
        "start_state": "a",
        "end_state": "z",
        "trajectory": "path",
        "curve": "c",
        "speech_cue_id": "cue",
    }
    for scene in data["motion_plan"]["scenes"]:
        scene.setdefault("keyframe_ms", None)
        for element in scene["elements"]:
            for i, beat in enumerate(element["beats"]):
                beat.setdefault("speech_cue_id", None)
                curve = beat["curve"]
                if curve["kind"] in {"linear", "ease_in", "ease_out", "ease_in_out"}:
                    beat["curve"] = curve["kind"]
                element["beats"][i] = {aliases[k]: v for k, v in beat.items()}
    return data


@pytest.mark.parametrize("kind", ["generate", "correct"])
@pytest.mark.parametrize(
    "curve",
    [
        {"kind": "ease_out", "parameters": []},
        {"kind": "cubic_bezier", "parameters": [0.2, 0.1, 0.8, 1]},
        {"kind": "spring", "parameters": [100, 20, 1]},
    ],
)
async def test_v2_wire_expands_losslessly_before_all_existing_checks(kind, curve):
    ctx = {**compact_context(), "generation_contract": deepcopy(GENERATION_CONTRACT)}
    data = wire_data()
    data["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]["curve"] = curve
    expected = decode_provided_output(json.dumps(data), compact_context())
    wire = compact_wire(data)
    original = deepcopy(wire)
    client = provider(lambda _: httpx.Response(200, json=response_data(wire)))
    job = replace(
        request(kind, composition=planned(), review=MotionReview.model_validate(review_data(revise=True))), context=ctx
    )
    payload = client.build_request(job)
    assert payload["text"]["format"]["name"] == "CompactProvidedDirectionOutput"
    result = await client.submit(job, payload)
    assert result.composition == expected
    assert wire == original
    validate_motion_plan(result.composition, ctx, duration_ms=1000, asset_ids=set())
    assert len(json.dumps(wire, separators=(",", ":"))) < len(json.dumps(data, separators=(",", ":")))


@pytest.mark.parametrize("change", ["overlap", "curve", "link", "alias", "cue"])
def test_v2_projection_does_not_bypass_plan_validation(change):
    from pydantic import ValidationError

    ctx = {**compact_context(), "generation_contract": deepcopy(GENERATION_CONTRACT)}
    wire = compact_wire(wire_data())
    element = wire["motion_plan"]["scenes"][0]["elements"][0]
    beat = element["beats"][0]
    if change == "overlap":
        element["beats"].append(deepcopy(beat))
    elif change == "curve":
        beat["c"] = {"kind": "cubic_bezier", "parameters": [2, 0, 1, 1]}
    elif change == "link":
        element["related_element_ids"] = ["missing"]
    elif change == "alias":
        beat["start_ms"] = beat.pop("s")
    else:
        beat["cue"] = "invalid cue"
    with pytest.raises(ValidationError):
        decode_provided_output(json.dumps(wire), ctx)


def test_v3_default_and_immutable_v1_v2_recapture():
    body = MotionRequest(
        operation_id=uuid4(), source_asset_id=uuid4(), instruction="Synthetic", scene_direction=direction_data()
    )
    current = capture_motion_guidance(body)
    assert current["generation_contract"] == STAGED_GENERATION_CONTRACT
    v2 = {**current, "generation_contract": deepcopy(GENERATION_CONTRACT)}
    assert capture_motion_guidance(body, previous=v2)["generation_contract"] == GENERATION_CONTRACT
    old = {**current, "generation_contract": deepcopy(LEGACY_GENERATION_CONTRACT)}
    assert capture_motion_guidance(body, previous=old)["generation_contract"] == LEGACY_GENERATION_CONTRACT
    with pytest.raises(AuthError, match="CONTRACT_REQUIRED"):
        generation_wire_model(provided_context())
