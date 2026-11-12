"""Resume approved stages through Temporal; never repeat ASR/planning or render early."""

import base64
import hashlib
from dataclasses import replace
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid5

from app.adapters.motion_html_renderer import RenderAsset
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_checkpoints import MotionCheckpoints, Stage, input_manifest
from app.services.motion_construction import implement_motion
from app.services.motion_illustrations import MotionIllustrations
from app.services.motion_materials import prepare_implementation_materials
from app.services.motion_storyboards import MotionStoryboards
from app.workflows.contracts import BusinessEvent

if TYPE_CHECKING:
    from app.services.motion_orchestrator import MotionOrchestrator


def restore_input(prepared: PreparedMotionInput, packet: dict[str, Any]) -> PreparedMotionInput:
    context = packet["context"]
    for key in ("source", "kit", "request", "authorized_audio", "output", "creative_contract", "preparation_contract"):
        if prepared.context.get(key) != context.get(key):
            raise AuthError("MOTION_CHECKPOINT_INPUT_CHANGED", 409)
    assets = list(prepared.assets)
    if packet["stage"] == "render":
        composition = HTMLMotionComposition.model_validate(packet["artifact"])
        expected = {item.asset_id for item in composition.illustrations}
        images = packet["resolved_images"]
        if {item["id"] for item in images} != expected or len(images) != len(expected):
            raise AuthError("MOTION_CHECKPOINT_INPUT_CHANGED", 409)
        for item in images:
            data = base64.b64decode(item["data"], validate=True)
            if (
                item["mime_type"] != "image/png"
                or len(data) > 8 * 1024 * 1024
                or hashlib.sha256(data).hexdigest() != item["sha256"]
            ):
                raise AuthError("MOTION_CHECKPOINT_INPUT_CHANGED", 409)
            assets.append(RenderAsset(item["id"], item["mime_type"], data, item["sha256"]))
        prepared = replace(prepared, assets=tuple(assets), context=context)
        plan_data = composition.model_dump(mode="json", exclude={"html", "scene_init"})
        plan_data.setdefault("illustrations", [])
        prepared = prepare_implementation_materials(MotionConstructionPlan.model_validate(plan_data), prepared)
    else:
        prepared = replace(prepared, context=context)
    if input_manifest(prepared) != packet["inputs"]:
        raise AuthError("MOTION_CHECKPOINT_INPUT_CHANGED", 409)
    return prepared


async def resume_checkpoint(runner: "MotionOrchestrator", event: BusinessEvent, stage: Stage) -> str:
    checkpoints = MotionCheckpoints(runner.requests, runner.store)
    started = await checkpoints.begin(event, stage)
    if started is None:
        return "already_claimed"
    row, token, packet = started
    try:
        async with runner.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await runner.requests.locked_running(session, row, token)
            await runner.requests._admission(session, row["tenant_id"], row["business_id"])
        fresh = await runner.inputs.prepare(runner.requests.context.open(row["snapshot_ciphertext"]))
        prepared = restore_input(fresh, packet)
        if stage == "plan":
            plan = MotionConstructionPlan.model_validate(packet["artifact"])
            illustrations = MotionIllustrations(runner.effects, runner.store, runner.illustration_provider)
            prepared, composition = await implement_motion(
                runner.effects, runner.provider, row, token, prepared, plan, illustrations
            )
            await checkpoints.capture(row, token, "render", prepared, composition, runner.effects)
            return "awaiting_render"
        composition = HTMLMotionComposition.model_validate(packet["artifact"])
        await MotionStoryboards(runner.requests, runner.store).capture(
            row, token, prepared, composition, runner.renderer, runner.effects
        )
        return "awaiting_storyboard"
    except BaseException as exc:
        failure_event_id = uuid5(UUID(event.event_id), "motion.failed")
        try:
            await runner.fail(
                row, token, getattr(exc, "code", "MOTION_EXECUTION_FAILED"), failure_event_id=failure_event_id
            )
        except Exception:
            await runner.effects.quarantine(row, token, failure_event_id=failure_event_id)
        raise
