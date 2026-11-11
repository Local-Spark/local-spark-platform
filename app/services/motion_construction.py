"""Two bounded, durable completions; never retries an incomplete or uncertain response."""

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid5

from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects
from app.services.motion_generation import staged_generation_enabled
from app.services.motion_illustrations import validate_declarations
from app.services.motion_protocols import MotionModelProvider, MotionModelRequest


async def construct_motion(
    effects: MotionEffects,
    provider: MotionModelProvider,
    row: dict[str, Any],
    token: UUID,
    prepared: PreparedMotionInput,
) -> HTMLMotionComposition:
    operation = row["operation_id"]
    job = MotionModelRequest(
        operation_id=uuid5(operation, "generate:0"),
        kind="generate",
        context=prepared.context,
        assets=prepared.assets,
        source_frames=prepared.source_frames,
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
    )
    if staged_generation_enabled(prepared.context):
        reserve = effects.requests.settings.motion_ai_reservation_usd_micros
        # Account for planning, implementation AND review before paying for the first.
        if not await effects.capacity(row, token, 3 * reserve):
            raise AuthError("MOTION_CONSTRUCTION_BUDGET_REQUIRED", 409)
        planned = await effects.model(
            row, token, provider, replace(job, operation_id=uuid5(operation, "generate:plan:0"))
        )
        plan = planned.construction_plan
        if plan is None or planned.composition is not None:
            raise AuthError("MOTION_PLANNING_RESULT_INVALID", 409)
        validate_declarations(plan, prepared)
        if plan.audio.model_dump(mode="json") != prepared.audio:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
        image_reserve = (prepared.context.get("illustration_generation") or {}).get("reservation_usd_micros", 0)
        if not await effects.capacity(row, token, 2 * reserve + len(plan.illustrations) * image_reserve):
            raise AuthError("MOTION_CONSTRUCTION_BUDGET_REQUIRED", 409)
        job = replace(job, construction_plan=plan)
    generated = await effects.model(row, token, provider, job)
    if generated.composition is None:
        raise AuthError("MOTION_GENERATION_RESULT_INVALID", 409)
    if job.construction_plan is not None:
        # Provider-independent integrity check, also applied to replacement adapters.
        expected = job.construction_plan.model_dump(mode="json")
        actual = generated.composition.model_dump(mode="json", exclude={"html", "scene_init"})
        actual.setdefault("illustrations", [])
        if actual != expected:
            raise AuthError("MOTION_CONSTRUCTION_PLAN_CHANGED", 409)
    return generated.composition
