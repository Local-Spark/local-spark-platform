"""Reconcile a fully received plan after local validation repair; never regenerate or approve it."""

import json
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_checkpoint_execution import restore_input
from app.services.motion_checkpoints import MotionCheckpoints, checkpoint_id, input_manifest
from app.services.motion_construction import construction_job
from app.services.motion_context import digest
from app.services.motion_illustrations import validate_declarations
from app.services.motion_protocols import MotionModelProvider


def semantic_payload(payload: dict[str, Any]) -> str:
    value = json.loads(json.dumps(payload))
    for message in value["input"]:
        for block in message["content"]:
            if block["type"] == "input_text":
                block["text"] = json.loads(block["text"])
    return digest(value)


class MotionPlanningRecovery:
    def __init__(self, checkpoints: MotionCheckpoints):
        self.checkpoints, self.requests = checkpoints, checkpoints.requests

    async def snapshot(
        self, session: Any, tenant: UUID, business: UUID, actor: UUID, request: UUID
    ) -> tuple[dict[str, Any], dict[UUID, dict[str, Any]], dict[str, Any] | None]:
        await self.requests.gate._lock(session, tenant, business, actor)
        row = dict(await self.requests.row(session, tenant, business, request))
        if row["actor_id"] != actor:
            raise AuthError("MOTION_OWNER_CHANGED", 409)
        effects = [
            dict(e)
            for e in (
                await session.execute(
                    text("""SELECT * FROM motion_effects
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request ORDER BY operation_id"""),
                    {"tenant": tenant, "business": business, "request": request},
                )
            ).mappings()
        ]
        by_id = {e["operation_id"]: e for e in effects}
        existing = by_id.get(checkpoint_id(row["operation_id"], "plan"))
        if existing is None:
            allowed = {uuid5(row["operation_id"], stage) for stage in ("generate:plan:0", "speech:0")}
            if (
                row["state"] != "failed"
                or row["failure_code"] != "MOTION_STAGING_TRANSITION_INVALID"
                or row["piece_id"]
                or any(e["state"] != "received" for e in effects)
                or any(e["kind"] != "upload" and e["operation_id"] not in allowed for e in effects)
                or any(e["reserved_usd_micros"] and e["estimated_usd_micros"] is None for e in effects)
                or sum(max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects)
                > row["budget_usd_micros"]
            ):
                raise AuthError("MOTION_PLANNING_RECOVERY_INELIGIBLE", 409)
            await self.requests._admission(session, tenant, business)
            await self.requests.current(session, row)
        return row, by_id, existing

    async def reconcile(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        request: UUID,
        expected_plan_sha: str,
        fresh: PreparedMotionInput,
        provider: MotionModelProvider,
    ) -> str:
        async with self.requests.database.transaction(tenant, actor) as session:
            row, effects, existing = await self.snapshot(session, tenant, business, actor, request)
        if existing is not None:
            return await self.existing(row, existing, expected_plan_sha)
        operation = uuid5(row["operation_id"], "generate:plan:0")
        model = effects.get(operation)
        if model is None or model["kind"] != "generate":
            raise AuthError("MOTION_PLANNING_RECEIPT_REQUIRED", 409)
        signed = await self.checkpoints.payloads.open(row, model["request_ciphertext"])
        output = await self.checkpoints.payloads.open(row, model["response_ciphertext"])
        if digest(signed) != model["request_hash"] or digest(output.get("construction_plan")) != expected_plan_sha:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        plan = MotionConstructionPlan.model_validate(output["construction_plan"])
        context = json.loads(signed["payload"]["input"][0]["content"][0]["text"])["authorized_context"]
        packet = {
            "version": "motion-checkpoint-v1",
            "stage": "plan",
            "context": context,
            "artifact": plan.model_dump(mode="json"),
            "inputs": input_manifest(fresh),
            "source_fingerprint": row["source_fingerprint"],
            "model_operation_id": str(operation),
            "model_request_hash": model["request_hash"],
            "model_wire_sha256": signed["wire_sha256"],
            "resolved_images": [],
            "limitations": ["Reconciled received plan; no approval, render or new provider call."],
        }
        prepared = restore_input(fresh, packet)
        rebuilt = provider.build_request(construction_job(row, prepared))
        if semantic_payload(rebuilt) != semantic_payload(signed["payload"]):
            raise AuthError("MOTION_CHECKPOINT_INPUT_CHANGED", 409)
        validate_declarations(plan, prepared)
        if plan.audio.model_dump(mode="json") != prepared.audio:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
        ciphertext = self.requests.context.seal(packet)
        # Reconciliation writes only bounded SQL metadata, never another external effect.
        if len(ciphertext) > 1024 * 1024:
            raise AuthError("MOTION_PLANNING_RECOVERY_TOO_LARGE", 409)
        sha = digest(packet)
        async with self.requests.database.transaction(tenant, actor) as session:
            current, latest, existing = await self.snapshot(session, tenant, business, actor, request)
            if (
                existing is not None
                or digest(current) != digest(row)
                or digest(list(latest.values())) != digest(list(effects.values()))
            ):
                raise AuthError("MOTION_EXECUTION_FENCED", 409)
            params = {"tenant": tenant, "business": business, "request": request}
            await session.execute(
                text("""INSERT INTO motion_effects
                (tenant_id,business_id,request_id,operation_id,kind,state,request_hash,request_ciphertext,
                 response_ciphertext,estimated_usd_micros,finished_at)
                VALUES(:tenant,:business,:request,:operation,'review','received',:sha,:payload,:response,0,clock_timestamp())"""),
                {
                    **params,
                    "operation": checkpoint_id(row["operation_id"], "plan"),
                    "sha": sha,
                    "payload": ciphertext,
                    "response": self.requests.context.seal({"content_sha256": sha}),
                },
            )
            await session.execute(
                text("""UPDATE motion_requests SET state='running',execution_token=NULL,
                failure_code=NULL,finished_at=NULL
                WHERE tenant_id=:tenant AND business_id=:business AND id=:request"""),
                params,
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                VALUES(:tenant,:actor,:operation,'motion.plan_reconciled',:business)"""),
                {**params, "actor": actor, "operation": row["operation_id"]},
            )
            await _event(session, tenant, business, actor, row["operation_id"], "motion.plan_ready")
        return sha

    async def existing(self, row: dict[str, Any], effect: dict[str, Any], expected_sha: str) -> str:
        packet = await self.checkpoints.payloads.open(row, effect["request_ciphertext"])
        if (
            effect["state"] != "received"
            or digest(packet) != effect["request_hash"]
            or digest(packet["artifact"]) != expected_sha
        ):
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        return str(effect["request_hash"])
