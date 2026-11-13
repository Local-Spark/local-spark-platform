"""Two bounded, durable completions; never retries an incomplete or uncertain response."""

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid5

from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects
from app.services.motion_generation import asset_informed_enabled, staged_generation_enabled
from app.services.motion_illustrations import MotionIllustrations, validate_declarations
from app.services.motion_materials import prepare_implementation_materials
from app.services.motion_protocols import MotionModelProvider, MotionModelRequest
from app.services.motion_quality import require_quality_readiness
from app.services.motion_sound_library import apply_planned_sound


async def construct_motion(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
) -> HTMLMotionComposition:
    if asset_informed_enabled(prepared.context):
        raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_RESOLVER_REQUIRED", 409)
    _, composition = await _construct_motion(effects, provider, row, token, prepared, None)
    return composition


async def construct_motion_with_assets(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
    illustrations: MotionIllustrations,
) -> tuple[PreparedMotionInput, HTMLMotionComposition]:
    return await _construct_motion(effects, provider, row, token, prepared, illustrations)


async def _construct_motion(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
    illustrations: MotionIllustrations | None,
) -> tuple[PreparedMotionInput, HTMLMotionComposition]:
    operation = row["operation_id"]
    job = MotionModelRequest(
        operation_id=uuid5(operation, "generate:0"),
        kind="generate",
        context=prepared.context,
        assets=prepared.assets,
        source_frames=prepared.source_frames,
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
        baseline_frames=prepared.baseline_frames,
    )
    if staged_generation_enabled(prepared.context):
        plan = await plan_motion(effects, provider, row, token, prepared)
        return await implement_motion(effects, provider, row, token, prepared, plan, illustrations)
    generated = await effects.model(row, token, provider, job)
    if generated.composition is None:
        raise AuthError("MOTION_GENERATION_RESULT_INVALID", 409)
    return prepared, generated.composition


def construction_job(row: dict[str, Any], prepared: PreparedMotionInput) -> MotionModelRequest:
    return MotionModelRequest(
        operation_id=uuid5(row["operation_id"], "generate:0"),
        kind="generate",
        context=prepared.context,
        assets=prepared.assets,
        source_frames=prepared.source_frames,
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
        baseline_frames=prepared.baseline_frames,
    )


async def plan_motion(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
) -> MotionConstructionPlan:
    if not staged_generation_enabled(prepared.context):
        raise AuthError("MOTION_CHECKPOINT_STAGED_REQUIRED", 409)
    require_quality_readiness(prepared.context)
    reserve = effects.requests.settings.motion_ai_reservation_usd_micros
    required = reserve if prepared.context.get("request", {}).get("review_checkpoints") else 3 * reserve
    if not await effects.capacity(row, token, required):
        raise AuthError("MOTION_CONSTRUCTION_BUDGET_REQUIRED", 409)
    job = replace(construction_job(row, prepared), operation_id=uuid5(row["operation_id"], "generate:plan:0"))
    planned = await effects.model(row, token, provider, job)
    plan = planned.construction_plan
    if plan is None or planned.composition is not None:
        raise AuthError("MOTION_PLANNING_RESULT_INVALID", 409)
    validate_declarations(plan, prepared)
    if plan.audio.model_dump(mode="json") != prepared.audio:
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    return plan


async def implement_motion(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
    plan: MotionConstructionPlan,
    illustrations: MotionIllustrations | None,
) -> tuple[PreparedMotionInput, HTMLMotionComposition]:
    validate_declarations(plan, prepared)
    if plan.audio.model_dump(mode="json") != prepared.audio:
        raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
    prepared = apply_planned_sound(prepared, plan)
    reserve = effects.requests.settings.motion_ai_reservation_usd_micros
    image_reserve = (prepared.context.get("illustration_generation") or {}).get("reservation_usd_micros", 0)
    calls = 1 if prepared.context.get("request", {}).get("review_checkpoints") else 2
    if not await effects.capacity(row, token, calls * reserve + len(plan.illustrations) * image_reserve):
        raise AuthError("MOTION_CONSTRUCTION_BUDGET_REQUIRED", 409)
    if asset_informed_enabled(prepared.context):
        if illustrations is None:
            raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_RESOLVER_REQUIRED", 409)
        prepared = await illustrations.prepare(row, token, prepared, plan)
        prepared = prepare_implementation_materials(plan, prepared)
    job = replace(construction_job(row, prepared), construction_plan=plan)
    generated = await effects.model(row, token, provider, job)
    if generated.composition is None:
        raise AuthError("MOTION_GENERATION_RESULT_INVALID", 409)
    expected = plan.model_dump(mode="json")
    actual = generated.composition.model_dump(mode="json", exclude={"html", "scene_init"})
    actual.setdefault("illustrations", [])
    if actual != expected:
        raise AuthError("MOTION_CONSTRUCTION_PLAN_CHANGED", 409)
    return prepared, generated.composition
