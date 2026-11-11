"""A separately supplied scene brief is binding input, never an approval claim."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import HTMLMotionComposition, MotionRequest, MotionReview
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.services.auth import AuthError
from app.services.motion_creative import motion_creative_contract, provided_direction_contract
from app.services.motion_illustrations import MotionIllustrations
from app.services.motion_plan import requires_motion_plan, requires_scene_direction, validate_motion_plan
from app.services.motion_visual_direction import supplied_direction
from app.tests.unit.test_motion_ai import frame, provider, request, review_data
from app.tests.unit.test_motion_plan import context, direction_data, planned


def provided_context():
    return {
        **context(),
        "creative_contract": provided_direction_contract(),
        "request": {"scene_direction": direction_data()},
    }


@pytest.mark.parametrize("kind", ["generate", "review", "correct"])
@pytest.mark.parametrize("provided", [True, False])
def test_builder_distinguishes_provided_and_proposed_without_inventing_approval(kind, provided):
    ctx = provided_context() if provided else context()
    before = deepcopy(ctx)
    job = replace(
        request(
            kind, composition=planned(), frames=(frame(),), review=MotionReview.model_validate(review_data(revise=True))
        ),
        context=ctx,
    )
    payload = provider().build_request(job)
    data = json.loads(payload["input"][0]["content"][0]["text"])
    descriptor = data["visual_direction_input"]
    assert data["authorized_context"] == before == ctx
    assert descriptor["human_approval"] == "not_asserted"
    assert descriptor["mode"] == ("provided" if provided else "model_proposed")
    assert descriptor["source"] == ("request.scene_direction" if provided else "model_response")
    if provided:
        encoded = json.dumps(direction_data(), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        assert descriptor["sha256"] == hashlib.sha256(encoded).hexdigest()
        assert requires_motion_plan(ctx) and requires_scene_direction(ctx)
        assert "A direção visual foi fornecida" in ctx["creative_contract"]["scene_direction_rules"]
        assert "Antes de escrever a animação, desenvolva a direção" not in json.dumps(data)
    else:
        assert descriptor["sha256"] is None
    if kind == "review":
        assert "Devolva a direção" not in descriptor["rules"]
        assert "evidências disponíveis" in payload["instructions"]
    elif provided:
        assert "Devolva a direção sem alterações" in payload["instructions"]
    else:
        assert "Sem direção visual fornecida" in payload["instructions"]


async def test_provided_direction_is_part_of_the_exact_counted_payload():
    calls = []

    def transport(sent):
        calls.append(json.loads(sent.content))
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 7000})

    model = provider(transport)
    job = replace(request(), context=provided_context())
    payload = model.build_request(job)
    assert await model.count_input_tokens(job, payload) == 7000
    assert calls == [{key: payload[key] for key in ("model", "input", "instructions", "text", "reasoning")}]
    assert "scene_direction" in payload["text"]["format"]["schema"]["required"]


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "REQUIRED"),
        ("contract", "CONTRACT_REQUIRED"),
        ("schema", "INVALID"),
        ("scenes", "SCENES_INVALID"),
        ("duplicate_element", "ELEMENTS_INVALID"),
        ("global_element", "ELEMENTS_INVALID"),
        ("attention", "ATTENTION_INVALID"),
        ("duplicate_attention", "ATTENTION_INVALID"),
    ],
)
def test_unusable_direction_is_rejected_before_provider_preflight(change, code):
    ctx = provided_context()
    design = ctx["request"]["scene_direction"]
    first = design["scenes"][0]
    if change == "missing":
        ctx["request"].clear()
    elif change == "contract":
        ctx["creative_contract"] = {"version": "reel-creative-v2"}
    elif change == "schema":
        first["composition"] = ""
    elif change == "scenes":
        design["scenes"][1]["scene_id"] = first["scene_id"]
    elif change == "duplicate_element":
        first["elements"].append(deepcopy(first["elements"][0]))
    elif change == "global_element":
        design["scenes"][1]["elements"][0]["element_id"] = first["elements"][0]["element_id"]
    elif change == "attention":
        first["attention_order"] = ["foreign"]
    else:
        first["attention_order"] *= 2
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_" + code):
        provider().build_request(replace(request(), context=ctx))


@pytest.mark.parametrize(
    "change", ["missing_library", "unknown_component", "unexpected_component", "generation_disabled"]
)
def test_direction_cannot_enable_unavailable_resources(change):
    ctx = provided_context()
    element = ctx["request"]["scene_direction"]["scenes"][0]["elements"][0]
    if change in {"missing_library", "unknown_component"}:
        element.update(construction="component", component_id="cup")
        if change == "missing_library":
            ctx["creative_contract"].pop("element_library")
        else:
            element["component_id"] = "unknown"
    elif change == "unexpected_component":
        element["component_id"] = "cup"
    else:
        element["construction"] = "generated_asset"
    with pytest.raises(AuthError, match="MOTION_SCENE_COMPONENT_|MOTION_VISUAL_DIRECTION_ILLUSTRATION_UNAVAILABLE"):
        supplied_direction(ctx)


def test_available_components_and_authorized_generation_remain_options():
    ctx = provided_context()
    ctx["request"]["scene_direction"]["scenes"][0]["elements"][0].update(construction="component", component_id="cup")
    ctx["request"]["scene_direction"]["scenes"][1]["elements"][0]["construction"] = "generated_asset"
    ctx["illustration_generation"] = {
        "enabled": True
    }  # Actual budget policy is enforced by the existing image service.
    assert supplied_direction(ctx) is not None


@pytest.mark.parametrize("change", ["representation", "composition", "action", "missing"])
def test_generated_direction_cannot_replace_supplied_decisions(change):
    data = planned().model_dump(mode="json")
    if change == "missing":
        data.pop("scene_direction")
    else:
        key = {"representation": "visual_representation", "composition": "composition", "action": "narrative_action"}[
            change
        ]
        data["scene_direction"]["scenes"][0][key] = "Outra direção"
    value = HTMLMotionComposition.model_validate(data)
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_CHANGED"):
        validate_motion_plan(value, provided_context(), duration_ms=1000, asset_ids=set())


def test_timing_and_code_can_change_within_supplied_direction_and_legacy_still_works():
    data = planned().model_dump(mode="json")
    data["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]["end_ms"] = 250
    data["scene_init"] = "window.seek=async(ms)=>{};"
    value = HTMLMotionComposition.model_validate(data)
    validate_motion_plan(value, provided_context(), duration_ms=1000, asset_ids=set())
    # A model-proposed direction retains the previous flexibility.
    data["scene_direction"]["scenes"][0]["composition"] = "Outra proposta"
    validate_motion_plan(HTMLMotionComposition.model_validate(data), context(), duration_ms=1000, asset_ids=set())
    assert supplied_direction({}) is None
    assert motion_creative_contract()["version"] == "reel-creative-v4"


async def test_changed_direction_stops_before_any_image_effect_or_budget_reservation():
    ctx = provided_context()
    ctx["request"]["scene_direction"]["scenes"][0]["composition"] = "Direção fornecida distinta"
    prepared = PreparedMotionInput(ctx, (), (), 1000, {"mode": "silent", "tracks": []})
    effects, store, model = AsyncMock(), AsyncMock(), AsyncMock()
    service = MotionIllustrations(effects, store, model)
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_CHANGED"):
        await service.prepare({}, uuid4(), prepared, planned())
    assert effects.mock_calls == store.mock_calls == model.mock_calls == []


def test_reviewable_cafe_brief_uses_the_product_schema_without_adding_a_timeline():
    path = Path(__file__).resolve().parents[3] / "docs/evals/direcao-cafe-pausa-2026-11-10.json"
    design = MotionSceneDirection.model_validate_json(path.read_text())
    assert [scene.scene_id for scene in design.scenes] == ["preparo", "convite"]
    assert "start_ms" not in design.model_dump_json()
    data = {"operation_id": uuid4(), "source_asset_id": uuid4(), "instruction": "Fictício"}
    legacy = MotionRequest(**data)
    assert "scene_direction" not in legacy.model_dump(mode="json")
    selected = MotionRequest(**data, scene_direction=design)
    assert (
        supplied_direction(
            {"creative_contract": provided_direction_contract(), "request": selected.model_dump(mode="json")}
        )
        == design
    )
