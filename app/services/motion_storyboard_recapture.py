"""Explicit one-time repair of v3 frame identity collisions; never repeats a model call."""

import json
from dataclasses import replace
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.adapters.motion_html_renderer import RenderBundle, RenderedMotion
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_context import digest
from app.services.motion_elements import elements_hash
from app.services.motion_movement import movement_hash
from app.services.motion_protocols import MotionRenderer
from app.services.motion_storyboard_frames import storyboard_moments, storyboard_upload_name
from app.services.motion_storyboards import MotionStoryboards
from app.services.motion_temporal import POLICY_V3
from app.workflows.contracts import BusinessEvent

if TYPE_CHECKING:
    from app.services.motion_orchestrator import MotionOrchestrator

EVENT = "motion.storyboard_recapture_requested"


class VerifiedRecaptureRenderer:
    def __init__(self, renderer: MotionRenderer, expected: list[dict[str, Any]]):
        self.renderer, self.expected = renderer, expected

    async def render(self, bundle: RenderBundle, *, operation_id: UUID) -> RenderedMotion:
        if not bundle.frames_only:
            raise AuthError("MOTION_RECAPTURE_FRAMES_ONLY", 409)
        result = await self.renderer.render(bundle, operation_id=operation_id)
        if result.mp4 or [{"ms": f.ms, "sha256": f.sha256} for f in result.evidence] != self.expected:
            raise AuthError("MOTION_RECAPTURE_PIXELS_CHANGED", 409)
        return result


class MotionStoryboardRecapture:
    def __init__(self, runner: "MotionOrchestrator"):
        self.runner = runner
        self.boards = MotionStoryboards(runner.requests, runner.store)

    async def snapshot(
        self, session: Any, tenant: UUID, business: UUID, actor: UUID, request: UUID, state: str
    ) -> tuple[dict[str, Any], dict[UUID, dict[str, Any]]]:
        requests = self.runner.requests
        await requests.gate._lock(session, tenant, business, actor)
        row = dict(await requests.row(session, tenant, business, request))
        if (
            row["actor_id"] != actor
            or row["state"] != state
            or row["piece_id"]
            or (state == "failed" and row["failure_code"] != "MOTION_EFFECT_ALREADY_CLAIMED")
        ):
            raise AuthError("MOTION_RECAPTURE_INELIGIBLE", 409)
        await requests._admission(session, tenant, business)
        await requests.current(session, row)
        if await session.scalar(
            text("""SELECT EXISTS(SELECT 1 FROM motion_storyboards
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id) OR EXISTS(
            SELECT 1 FROM motion_render_versions
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id)"""),
            {"tenant": tenant, "business": business, "id": request},
        ):
            raise AuthError("MOTION_RECAPTURE_INELIGIBLE", 409)
        effects = (
            (
                await session.execute(
                    text("""SELECT * FROM motion_effects
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id ORDER BY operation_id"""),
                    {"tenant": tenant, "business": business, "id": request},
                )
            )
            .mappings()
            .all()
        )
        if (
            not effects
            or any(e["state"] != "received" for e in effects)
            or any(e["reserved_usd_micros"] and e["estimated_usd_micros"] is None for e in effects)
            or sum(max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects)
            > row["budget_usd_micros"]
        ):
            raise AuthError("MOTION_RECAPTURE_INELIGIBLE", 409)
        return row, {e["operation_id"]: dict(e) for e in effects}

    async def evidence(self, row: dict[str, Any], effects: dict[UUID, dict[str, Any]]) -> tuple[Any, ...]:
        operation = row["operation_id"]
        version = uuid5(operation, "storyboard:0")
        if {key for key, value in effects.items() if value["kind"] == "render"} != {version}:
            raise AuthError("MOTION_RECAPTURE_INELIGIBLE", 409)

        async def read(key: UUID, kind: str, field: str = "response_ciphertext") -> dict[str, Any]:
            effect = effects.get(key)
            if effect is None or effect["kind"] != kind or not effect.get(field):
                raise AuthError("MOTION_RECAPTURE_EVIDENCE_REQUIRED", 409)
            value = await self.boards.payloads.open(row, effect[field])
            if field == "request_ciphertext" and digest(value) != effect["request_hash"]:
                raise AuthError("MOTION_RECAPTURE_EVIDENCE_CHANGED", 409)
            return value

        signed = await read(version, "render", "request_ciphertext")
        rendered = await read(version, "render")
        generated = await read(uuid5(operation, "generate:0"), "generate")
        planned = await read(uuid5(operation, "generate:plan:0"), "generate")
        model_input = await read(uuid5(operation, "generate:0"), "generate", "request_ciphertext")
        ctx = json.loads(model_input["payload"]["input"][0]["content"][0]["text"])["authorized_context"]
        composition = HTMLMotionComposition.model_validate(signed["composition"])
        actual = composition.model_dump(mode="json", exclude={"html", "scene_init"})
        actual.setdefault("illustrations", [])
        moments = storyboard_moments(composition, ctx)
        legacy_names = [f"{m['scene_id']}:{m['frame_index']}" if "event_id" in m else m["scene_id"] for m in moments]
        if (
            signed.get("purpose") != "storyboard"
            or composition.illustrations
            or ctx.get("creative_contract", {}).get("temporal_review") != POLICY_V3
            or not ctx.get("request", {}).get("evolution")
            or generated.get("composition") != signed["composition"]
            or planned.get("construction_plan") != actual
            or digest(signed["moments"]) != digest(moments)
            or len(rendered["frames"]) != len(moments)
            or len(set(legacy_names)) == len(legacy_names)
            or len({storyboard_upload_name(m) for m in moments}) != len(moments)
        ):
            raise AuthError("MOTION_RECAPTURE_EVIDENCE_CHANGED", 409)
        return composition, ctx, signed, rendered

    async def enqueue(self, tenant: UUID, business: UUID, actor: UUID, request: UUID) -> dict[str, Any]:
        db = self.runner.requests.database
        async with db.transaction(tenant, actor) as session:
            row, effects = await self.snapshot(session, tenant, business, actor, request, "failed")
        await self.evidence(row, effects)  # Storage IO outside locks.
        async with db.transaction(tenant, actor) as session:
            current, latest = await self.snapshot(session, tenant, business, actor, request, "failed")
            if digest(row) != digest(current) or digest(list(effects.values())) != digest(list(latest.values())):
                raise AuthError("MOTION_EXECUTION_FENCED", 409)
            await session.execute(
                text("""UPDATE motion_requests SET state='queued',failure_code=NULL,
                finished_at=NULL,execution_token=NULL WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": request},
            )
            await _event(session, tenant, business, actor, row["operation_id"], EVENT)
        return {"state": "queued", "event_id": str(uuid5(row["operation_id"], EVENT))}

    async def run(self, event: BusinessEvent) -> str:
        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        if UUID(event.event_id) != uuid5(operation, EVENT):
            raise AuthError("MOTION_EVENT_MISMATCH", 409)
        request = uuid5(operation, f"motion-request:{tenant}:{business}")
        db = self.runner.requests.database
        async with db.transaction(tenant, actor) as session:
            valid = await session.scalar(
                text("""SELECT 1 FROM outbox_events WHERE tenant_id=:tenant AND id=:event
                AND event_type=:kind AND payload->>'business_id'=:business AND payload->>'actor_id'=:actor
                AND payload->>'operation_id'=:operation"""),
                {
                    "tenant": tenant,
                    "event": UUID(event.event_id),
                    "kind": EVENT,
                    "business": str(business),
                    "actor": str(actor),
                    "operation": str(operation),
                },
            )
            if not valid:
                raise AuthError("MOTION_EVENT_MISMATCH", 409)
            row, effects = await self.snapshot(session, tenant, business, actor, request, "queued")
            token = uuid4()
            await session.execute(
                text("""UPDATE motion_requests SET state='running',execution_token=:token
                WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": request, "token": token},
            )
            await _event(session, tenant, business, actor, operation, "motion.storyboard_recapture_started")
        row.update(state="running", execution_token=token)
        try:
            composition, ctx, signed, rendered = await self.evidence(row, effects)
            prepared = await self.runner.inputs.prepare(self.runner.requests.context.open(row["snapshot_ciphertext"]))
            if (
                any(ctx.get(k) != prepared.context.get(k) for k in ("source", "kit", "authorized_audio", "request"))
                or signed["assets"] != [{"id": a.id, "sha256": a.sha256} for a in prepared.assets]
                or signed["movement_runtime_sha256"] != movement_hash(prepared.context)
                or signed["element_runtime_sha256"] != elements_hash(prepared.context)
            ):
                raise AuthError("MOTION_RECAPTURE_INPUT_CHANGED", 409)
            prepared = replace(prepared, context={**ctx, "evolution": prepared.context["evolution"]})
            await self.boards.capture(
                row,
                token,
                prepared,
                composition,
                VerifiedRecaptureRenderer(self.runner.renderer, rendered["frames"]),
                self.runner.effects,
                capture_id=uuid5(operation, "storyboard:recapture:1"),
            )
            return "awaiting_storyboard"
        except BaseException as exc:
            await self.runner.fail(
                row,
                token,
                getattr(exc, "code", "MOTION_EXECUTION_FAILED"),
                failure_event_id=uuid5(UUID(event.event_id), "motion.failed"),
            )
            raise
