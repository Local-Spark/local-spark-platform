"""A resumed checkpoint must reuse exactly the reviewed input, without another generation."""

import base64
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.adapters.motion_html_renderer import RenderAsset
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_checkpoint_execution import restore_input
from app.services.motion_checkpoints import APPROVED, input_manifest
from app.services.motion_materials import prepare_implementation_materials
from app.services.outbox import ClaimedEvent, _start_workflow
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_illustrations import composition_with_art, image_result
from app.workflows.contracts import BusinessEvent


def prepared():
    return PreparedMotionInput(
        {"source": {"sha256": "a" * 64}, "request": {"review_checkpoints": True}},
        (),
        (frame(100),),
        1000,
        {"mode": "silent", "tracks": []},
    )


@pytest.mark.parametrize(
    "changed",
    [
        None,
        "source",
        "kit",
        "request",
        "authorized_audio",
        "output",
        "creative_contract",
        "preparation_contract",
        "audio_analysis_contract",
        "audio_assessment",
        "frames",
    ],
)
def test_plan_resume_reuses_captured_transcript_and_checks_every_input(changed):
    fresh = prepared()
    context = {**fresh.context, "speech_timing": {"words": ["preserved"]}}
    packet = {"stage": "plan", "context": context, "inputs": input_manifest(fresh)}
    if changed == "frames":
        fresh = replace(fresh, source_frames=(frame(300),))
    elif changed:
        fresh = replace(fresh, context={**fresh.context, changed: "changed"})
    if changed:
        with pytest.raises(AuthError, match="INPUT_CHANGED"):
            restore_input(fresh, packet)
    else:
        result = restore_input(fresh, packet)
        assert result.context["speech_timing"] == context["speech_timing"]
        assert result.assets == fresh.assets and result.source_frames == fresh.source_frames


@pytest.mark.parametrize("changed", [None, "missing", "duplicate", "type", "hash", "bytes", "preview"])
def test_render_resume_restores_verified_generated_material_without_generator(changed):
    fresh = prepared()
    composition = composition_with_art()
    image = image_result()
    asset = RenderAsset(composition.illustrations[0].asset_id, "image/png", image.content, image.sha256)
    plan = MotionConstructionPlan.model_validate(composition.model_dump(mode="json", exclude={"html", "scene_init"}))
    resolved = prepare_implementation_materials(plan, replace(fresh, assets=(asset,)))
    item = {
        "id": asset.id,
        "mime_type": asset.mime_type,
        "sha256": asset.sha256,
        "data": base64.b64encode(asset.data).decode(),
    }
    packet = {
        "stage": "render",
        "artifact": composition.model_dump(mode="json"),
        "context": resolved.context,
        "inputs": input_manifest(resolved),
        "resolved_images": [item],
    }
    if changed == "missing":
        packet["resolved_images"] = []
    elif changed == "duplicate":
        packet["resolved_images"].append(deepcopy(item))
    elif changed == "type":
        item["mime_type"] = "image/jpeg"
    elif changed == "hash":
        item["sha256"] = "0" * 64
    elif changed == "bytes":
        item["data"] = base64.b64encode(b"changed").decode()
    elif changed == "preview":
        packet["inputs"]["previews"][0]["sha256"] = "0" * 64
    if changed:
        with pytest.raises(AuthError, match="INPUT_CHANGED"):
            restore_input(fresh, packet)
    else:
        assert restore_input(fresh, packet) == resolved


@pytest.mark.parametrize("stage", ["plan", "render"])
async def test_each_approval_dispatches_to_existing_temporal_with_distinct_identity(stage):
    operation = uuid4()
    event = BusinessEvent(
        str(uuid5(operation, APPROVED[stage])), str(uuid4()), str(uuid4()), str(uuid4()), str(operation)
    )
    client = SimpleNamespace(start_workflow=AsyncMock())
    await _start_workflow(
        client, SimpleNamespace(temporal_task_queue="synthetic"), ClaimedEvent(event, 1, APPROVED[stage])
    )
    assert client.start_workflow.await_args.args == ("MotionProductionWorkflow", event)
    assert client.start_workflow.await_args.kwargs["id"].startswith(f"motion-{stage}-approved/")
