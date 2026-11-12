"""Intent provenance survives serialization and evidence cannot be claimed without attachments."""

import json
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters import motion_inputs
from app.adapters.motion_html_renderer import RenderAsset
from app.schemas.motion_preparation import MotionPreparation
from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_preparation import PREPARATION_RULES, additional_source_times, evidence_bindings
from app.services.motion_repertoire import capture_repertoire, load_repertoire_images
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_construction import staged_context
from app.tests.unit.test_motion_inputs import source_snapshot, video_info
from app.tests.unit.test_motion_plan import direction_data


def preparation_data():
    return {
        "client_message": "Preserve a voz. Talvez luz no fundo.",
        "decisions": [
            {
                "id": "voice",
                "kind": "requirement",
                "origin": "client",
                "source_excerpt": "Preserve a voz.",
                "interpretation": "Conservar a faixa original",
                "scope": "request",
            },
            {
                "id": "light",
                "kind": "example",
                "origin": "client",
                "source_excerpt": "Talvez luz no fundo.",
                "interpretation": "Possibilidade, sem obrigação de fundo escuro",
                "scope": "scene",
                "scene_ids": ["hook"],
            },
            {
                "id": "close",
                "kind": "hypothesis",
                "origin": "operator",
                "source_excerpt": "Proposta para comparar",
                "interpretation": "Preservar convite legível",
                "scope": "scene",
                "scene_ids": ["close"],
            },
        ],
        "evidence": [
            {
                "id": "gesture",
                "kind": "source",
                "at_ms": [100, 300],
                "scene_ids": ["hook"],
                "observation": "Dois estados do gesto",
                "intended_use": "Preparar antes do acento",
                "limitations": "Sem escuta ou curva medida",
            }
        ],
    }


def body(**updates):
    return MotionRequest(
        operation_id=uuid4(),
        source_asset_id=uuid4(),
        instruction="Convite",
        storyboard=True,
        scene_direction=direction_data(),
        preparation=preparation_data(),
        review_checkpoints=True,
        **updates,
    )


def prepared_context():
    return {**staged_context(), "request": body().model_dump(mode="json"), "preparation_contract": PREPARATION_RULES}


def test_provenance_and_rules_reach_real_builder_without_reclassifying_examples():
    value = body()
    guidance = capture_motion_guidance(value)
    assert guidance["preparation_contract"] == PREPARATION_RULES
    ctx = {**staged_context(), "request": value.model_dump(mode="json"), "preparation_contract": PREPARATION_RULES}
    job = replace(request(), context=ctx, source_frames=(frame(100), frame(300)))
    payload = provider().build_request(job)
    actual = json.loads(payload["input"][0]["content"][0]["text"])
    assert actual["authorized_context"]["request"]["preparation"]["client_message"] == value.preparation.client_message
    assert actual["authorized_context"]["request"]["preparation"]["decisions"][1]["kind"] == "example"
    assert actual["preparation_evidence"][0]["attachments"] == [
        {"at_ms": f.ms, "sha256": f.sha256} for f in job.source_frames
    ]
    assert [block["type"] for block in payload["input"][0]["content"]].count("input_image") == 2


@pytest.mark.parametrize(
    "change",
    [
        "forged_requirement",
        "missing_quote",
        "unknown_scene",
        "unbound_scene",
        "duplicate",
        "no_direction",
        "no_preparation",
        "no_storyboard",
        "invalid_scope",
    ],
)
def test_invalid_preparation_cannot_enter_the_product(change):
    data = body().model_dump(mode="json")
    if change == "forged_requirement":
        data["preparation"]["decisions"][2]["kind"] = "requirement"
    elif change == "missing_quote":
        data["preparation"]["decisions"][0]["source_excerpt"] = "Sempre use borda"
    elif change == "unknown_scene":
        data["preparation"]["evidence"][0]["scene_ids"] = ["unknown"]
    elif change == "unbound_scene":
        data["preparation"]["decisions"].pop()
    elif change == "duplicate":
        data["preparation"]["decisions"].append(data["preparation"]["decisions"][0])
    elif change == "no_direction":
        data.pop("scene_direction")
    elif change == "no_preparation":
        data.pop("preparation")
    elif change == "invalid_scope":
        data["preparation"]["decisions"][0]["scope"] = "scene"
    else:
        data["storyboard"] = False
    with pytest.raises(ValidationError):
        MotionRequest.model_validate(data)


@pytest.mark.parametrize("change", ["missing", "changed", "contract"])
def test_missing_evidence_stops_builder_before_any_io(change):
    ctx = prepared_context()
    frames = (frame(100), frame(300))
    if change == "missing":
        frames = frames[:1]
    elif change == "changed":
        frames = (replace(frames[0], sha256="0" * 64), frames[1])
    else:
        ctx.pop("preparation_contract")
    with pytest.raises(AuthError, match="MOTION_PREPARATION_"):
        provider().build_request(replace(request(), context=ctx, source_frames=frames))


@pytest.mark.parametrize("kind", ["baseline", "reference", "material"])
def test_every_evidence_kind_is_bound_to_real_bytes(kind):
    ctx = prepared_context()
    item = ctx["request"]["preparation"]["evidence"][0]
    item["kind"] = kind
    item["at_ms"] = []
    args = {}
    if kind == "baseline":
        item["at_ms"] = [100]
        args["baseline_frames"] = (frame(100),)
    elif kind == "reference":
        ctx["repertoire"] = capture_repertoire("business-reel-v3")
        args["reference_images"] = load_repertoire_images(ctx)
        item["reference_ids"] = ["maestros-space-041", "maestros-space-042", "maestros-space-043"]
    else:
        f = frame()
        item["asset_id"] = "assets/cup.png"
        args.update(
            assets=(RenderAsset(item["asset_id"], "image/png", f.png, f.sha256),),
            asset_previews=((item["asset_id"], f),),
        )
    job = replace(request(), context=ctx, **args)
    assert evidence_bindings(job)[0]["attachments"]
    for name in args:
        args[name] = ()
    with pytest.raises(AuthError, match="EVIDENCE_MISSING"):
        evidence_bindings(replace(job, **args))


def test_historical_requests_keep_their_serialized_shape():
    value = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Legacy")
    assert "preparation" not in value.model_dump() and "review_checkpoints" not in value.model_dump()
    assert evidence_bindings(request()) == [] and additional_source_times({}, 1000) == ()
    assert "preparation_contract" not in capture_motion_guidance(value)


async def test_selected_source_instants_are_actually_decoded_without_replacing_global_samples(monkeypatch):
    command = AsyncMock(return_value=frame().png)
    monkeypatch.setattr(motion_inputs, "_command", command)
    frames = await motion_inputs.source_frames(b"synthetic", 1000, extra_times=(100, 300))
    assert [f.ms for f in frames] == [0, 100, 200, 300, 400, 600, 800, 900]
    assert command.await_count == 8
    assert additional_source_times(prepared_context(), 1000) == (100, 300)
    with pytest.raises(AuthError, match="SOURCE_LIMIT"):
        additional_source_times(prepared_context(), 200)


async def test_loader_applies_selection_to_actual_source_sampling(monkeypatch):
    data = b"original recording"
    snapshot = source_snapshot(data)
    snapshot["request"] = body().model_dump(mode="json")
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    sampling = AsyncMock(return_value=(frame(100), frame(300)))
    monkeypatch.setattr(motion_inputs, "source_frames", sampling)
    from types import SimpleNamespace

    store = SimpleNamespace(get_video=AsyncMock(return_value=data))
    await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert sampling.await_args.kwargs == {"extra_times": (100, 300)}


@pytest.mark.parametrize("times", [[True], [-1], [60000], [1, 1]])
def test_evidence_instants_are_bounded_and_strict(times):
    data = preparation_data()
    data["evidence"][0]["at_ms"] = times
    with pytest.raises(ValidationError):
        MotionPreparation.model_validate(data)
