"""Scene direction must bind to the timed plan without changing legacy requests."""

import json
from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.schemas.motion_production import HTMLMotionComposition, MotionReview
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.services.auth import AuthError
from app.services.motion_plan import requires_motion_plan, requires_scene_direction, validate_motion_plan
from app.tests.unit.test_motion_ai import composition, provider, request, response_data, review_data
from app.tests.unit.test_motion_plan import context, direction_data, planned


def validate(value, ctx=None):
    validate_motion_plan(value, context() if ctx is None else ctx, duration_ms=1000, asset_ids=set())


@pytest.mark.parametrize("version", [None, "reel-creative-v1", "reel-creative-v2"])
def test_history_does_not_acquire_new_direction_requirements(version):
    ctx = context()
    ctx["creative_contract"] = {"version": version} if version else None
    old = planned().model_copy(update={"scene_direction": None})
    validate(old, ctx)
    assert "scene_direction" not in old.model_dump(mode="json")
    assert not requires_scene_direction(ctx)
    assert requires_motion_plan(ctx) == (version == "reel-creative-v2")
    if version == "reel-creative-v2":
        with pytest.raises(AuthError, match="MOTION_PLAN_REQUIRED"):
            validate(composition(), ctx)


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "REQUIRED"),
        ("missing_scene", "SCENES_INVALID"),
        ("duplicate_scene", "SCENES_INVALID"),
        ("reordered_scene", "SCENES_INVALID"),
        ("missing_element", "ELEMENTS_INVALID"),
        ("duplicate_element", "ELEMENTS_INVALID"),
        ("foreign_element", "ELEMENTS_INVALID"),
        ("foreign_attention", "ATTENTION_INVALID"),
        ("duplicate_attention", "ATTENTION_INVALID"),
        ("asset_invented", "SOURCE_INVALID"),
    ],
)
def test_incomplete_or_unbound_direction_cannot_reach_renderer(change, code):
    data = planned().model_dump(mode="json")
    scenes = data["scene_direction"]["scenes"]
    first = scenes[0]
    if change == "missing":
        data["scene_direction"] = None
    elif change == "missing_scene":
        scenes.pop()
    elif change == "duplicate_scene":
        scenes[1] = deepcopy(first)
    elif change == "reordered_scene":
        scenes.reverse()
    elif change == "missing_element":
        # Plan has two elements, direction only one; no empty schema bypass.
        extra = deepcopy(data["motion_plan"]["scenes"][0]["elements"][0])
        extra.update(id="graphic", related_element_ids=[])
        data["motion_plan"]["scenes"][0]["elements"].append(extra)
    elif change == "duplicate_element":
        first["elements"].append(deepcopy(first["elements"][0]))
    elif change == "foreign_element":
        first["elements"][0]["element_id"] = "answer"
    elif change == "foreign_attention":
        first["attention_order"] = ["answer"]
    elif change == "duplicate_attention":
        first["attention_order"] *= 2
    else:
        first["elements"][0]["construction"] = "authorized_asset"
    with pytest.raises(AuthError, match=f"MOTION_SCENE_DIRECTION_{code}"):
        validate(HTMLMotionComposition.model_validate(data))


def test_direction_cannot_exist_without_timed_plan_even_in_legacy_document():
    value = planned().model_copy(update={"motion_plan": None})
    with pytest.raises(AuthError, match="MOTION_SCENE_DIRECTION_PLAN_REQUIRED"):
        validate(value, {})


@pytest.mark.parametrize("change", ["blank", "unknown_version", "empty_attention", "unavailable_tool"])
def test_no_blank_direction_or_invented_asset_generation(change):
    data = direction_data()
    scene = data["scenes"][0]
    if change == "blank":
        scene["visual_representation"] = "  \n "
    elif change == "unknown_version":
        data["version"] = "future"
    elif change == "empty_attention":
        scene["attention_order"] = []
    else:
        scene["elements"][0]["construction"] = "generate_image"
    with pytest.raises(ValidationError):
        MotionSceneDirection.model_validate(data)


def test_direction_survives_private_composition_serialization_without_a_second_timeline():
    original = planned()
    restored = HTMLMotionComposition.model_validate_json(original.model_dump_json())
    assert restored == original
    validate(restored)
    assert "start_ms" not in restored.scene_direction.model_dump_json()
    # No arbitrary icon/effect-count requirement for a deliberately restrained design.
    assert len(restored.scene_direction.scenes[0].elements) == 1


def test_figurative_code_art_needs_no_external_asset_or_fixed_template():
    data = planned().model_dump(mode="json")
    scene = data["motion_plan"]["scenes"][0]
    scene["elements"][0]["role"] = "graphic"
    design = data["scene_direction"]["scenes"][0]
    design.update(
        visual_representation="A pausa aparece como vapor de uma xícara formando um relógio.",
        composition="Xícara em primeiro plano; vapor acima, afastado da área de leitura.",
        narrative_action="O vapor se transforma em relógio, conectando preparo e tempo de pausa.",
    )
    design["elements"][0].update(
        depicts="Xícara, vapor e relógio ilustrativos",
        appearance="Contornos vetoriais nas cores do kit; alça, corpo e vapor em partes desenhadas.",
        construction="code",
    )
    validate(HTMLMotionComposition.model_validate(data))
    # An authorized image must stay an asset; code cannot disguise a missing file.
    scene["elements"][0].update(role="image", asset_id="assets/product.png")
    with pytest.raises(AuthError, match="MOTION_SCENE_DIRECTION_SOURCE_INVALID"):
        validate(HTMLMotionComposition.model_validate(data))


@pytest.mark.parametrize("kind", ["generate", "correct"])
@pytest.mark.parametrize("missing", [False, True])
async def test_new_direction_is_required_in_paid_response_schema_without_extra_call(kind, missing):
    calls = []
    value = planned().model_dump(mode="json")
    if missing:
        value.pop("scene_direction")

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=response_data(value))

    client = provider(handler)
    job = replace(
        request(kind, composition=planned(), review=MotionReview.model_validate(review_data(revise=True))),
        context=context(),
    )
    payload = client.build_request(job)
    schema = payload["text"]["format"]["schema"]
    assert schema["properties"]["scene_direction"] == {"$ref": "#/$defs/MotionSceneDirection"}
    assert "scene_direction" in schema["required"]
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["authorized_context"] == job.context
    assert sent["current_composition"]["scene_direction"] == planned().scene_direction.model_dump(mode="json")
    if missing:
        with pytest.raises(MotionAIError, match="MOTION_AI_RESPONSE_INVALID"):
            await client.submit(job, payload)
    else:
        result = await client.submit(job, payload)
        validate(result.composition)
    assert len(calls) == 1
