"""Owner review before code and before any render, using existing durable effects."""

import base64
from typing import Any, Literal
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.adapters.material_media import MaterialStore
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_preparation import MotionCheckpointDecision
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_context import digest
from app.services.motion_effects import MotionEffects
from app.services.motion_payloads import MotionPayloads
from app.services.motion_requests import MotionRequestService
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.visual_pending_scripts import apply_pending_script_changes
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.workflows.contracts import BusinessEvent

Stage = Literal["plan", "render"]
APPROVED: dict[Stage, str] = {"plan": "motion.plan_approved", "render": "motion.render_approved"}
RECOVERY_SCHEMA = "motion-checkpoint-before-implementation-v1"


def checkpoint_id(operation: UUID, stage: Stage) -> UUID:
    return uuid5(operation, f"checkpoint:{stage}")


def input_manifest(prepared: PreparedMotionInput) -> dict[str, Any]:
    return {
        "assets": [{"id": a.id, "sha256": a.sha256} for a in prepared.assets],
        "source": [{"ms": f.ms, "sha256": f.sha256} for f in prepared.source_frames],
        "baseline": [{"ms": f.ms, "sha256": f.sha256} for f in prepared.baseline_frames],
        "references": [{"id": f.id, "sha256": f.sha256} for f in prepared.reference_images],
        "previews": [{"id": key, "sha256": f.sha256} for key, f in prepared.asset_previews],
    }


class MotionCheckpoints:
    def __init__(self, requests: MotionRequestService, store: MaterialStore):
        self.requests = requests
        self.payloads = MotionPayloads(requests.context, store)

    async def effect(self, session: Any, row: dict[str, Any], operation: UUID) -> dict[str, Any] | None:
        value = (
            (
                await session.execute(
                    text("""SELECT * FROM motion_effects
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id AND operation_id=:operation"""),
                    {
                        "tenant": row["tenant_id"],
                        "business": row["business_id"],
                        "id": row["id"],
                        "operation": operation,
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(value) if value is not None else None

    async def capture(
        self,
        row: dict[str, Any],
        token: UUID,
        stage: Stage,
        prepared: PreparedMotionInput,
        artifact: MotionConstructionPlan | HTMLMotionComposition,
        effects: MotionEffects,
    ) -> None:
        if not prepared.context.get("request", {}).get("review_checkpoints"):
            raise AuthError("MOTION_CHECKPOINT_NOT_REQUESTED", 409)
        model_operation = uuid5(row["operation_id"], "generate:plan:0" if stage == "plan" else "generate:0")
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            model = await self.effect(session, row, model_operation)
        if model is None or model["kind"] != "generate" or model["state"] != "received":
            raise AuthError("MOTION_CHECKPOINT_MODEL_RECEIPT_REQUIRED", 409)
        signed = await self.payloads.open(row, model["request_ciphertext"])
        if digest(signed) != model["request_hash"]:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        output = await self.payloads.open(row, model["response_ciphertext"])
        if output.get("construction_plan" if stage == "plan" else "composition") != artifact.model_dump(mode="json"):
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        generated_ids = {item.asset_id for item in artifact.illustrations} if stage == "render" else set()
        packet = {
            "version": "motion-checkpoint-v1",
            "stage": stage,
            "context": prepared.context,
            "artifact": artifact.model_dump(mode="json"),
            "inputs": input_manifest(prepared),
            "source_fingerprint": row["source_fingerprint"],
            "model_operation_id": str(model_operation),
            "model_request_hash": model["request_hash"],
            "model_wire_sha256": signed["wire_sha256"],
            "resolved_images": [
                {"id": a.id, "mime_type": a.mime_type, "sha256": a.sha256, "data": base64.b64encode(a.data).decode()}
                for a in prepared.assets
                if a.id in generated_ids
            ],
            "limitations": [
                "No render or audiovisual quality approval at this checkpoint.",
                "Plan approval permits implementation; render approval permits storyboard capture only.",
            ],
        }
        operation = checkpoint_id(row["operation_id"], stage)
        await effects.claim(row, token, operation, "review", packet)
        await effects.received(row, token, operation, {"content_sha256": digest(packet)}, 0)
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            # The request remains active like a storyboard; no actor retains an execution lease.
            await session.execute(
                text("""UPDATE motion_requests SET execution_token=NULL
                WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": row["tenant_id"], "business": row["business_id"], "id": row["id"]},
            )
            await _event(
                session,
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                row["operation_id"],
                f"motion.{stage}_ready",
            )

    async def load(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        request: UUID,
        stage: Stage,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
        async with self.requests.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = dict(await self.requests.row(session, tenant, business, request))
            if row["actor_id"] != actor:
                raise AuthError("MOTION_OWNER_CHANGED", 409)
            operation = checkpoint_id(row["operation_id"], stage)
            checkpoint = await self.effect(session, row, operation)
            decision = await self.effect(session, row, uuid5(operation, "decision"))
        if checkpoint is None or checkpoint["kind"] != "review" or checkpoint["state"] != "received":
            raise AuthError("MOTION_CHECKPOINT_NOT_READY", 409)
        packet = await self.payloads.open(row, checkpoint["request_ciphertext"])
        result = await self.payloads.open(row, checkpoint["response_ciphertext"])
        if (
            digest(packet) != checkpoint["request_hash"]
            or result.get("content_sha256") != digest(packet)
            or packet["stage"] != stage
            or packet["source_fingerprint"] != row["source_fingerprint"]
        ):
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        return row, checkpoint, decision, packet

    async def present(self, tenant: UUID, business: UUID, actor: UUID, request: UUID, stage: Stage) -> dict[str, Any]:
        row, checkpoint, decision, packet = await self.load(tenant, business, actor, request, stage)
        async with self.requests.database.transaction(tenant, actor) as session:
            model = await self.effect(session, row, UUID(packet["model_operation_id"]))
        if model is None or model["state"] != "received" or model["request_hash"] != packet["model_request_hash"]:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        signed = await self.payloads.open(row, model["request_ciphertext"])
        if digest(signed) != model["request_hash"] or signed["wire_sha256"] != packet["model_wire_sha256"]:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        output = await self.payloads.open(row, model["response_ciphertext"])
        if output.get("construction_plan" if stage == "plan" else "composition") != packet["artifact"]:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        return {
            "stage": stage,
            "content_sha256": checkpoint["request_hash"],
            "request_state": row["state"],
            "decision": self.requests.context.open(decision["request_ciphertext"]) if decision else None,
            "decision_consumed": bool(decision and decision["state"] == "received"),
            "packet": {key: value for key, value in packet.items() if key != "resolved_images"},
            "model_input": signed["payload"],
            "model_output": output,
            "rendered": False,
        }

    async def decide(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        request: UUID,
        stage: Stage,
        body: MotionCheckpointDecision,
    ) -> dict[str, str]:
        row, checkpoint, _, packet = await self.load(tenant, business, actor, request, stage)
        if checkpoint["request_hash"] != body.content_sha256:
            raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
        operation = uuid5(checkpoint_id(row["operation_id"], stage), "decision")
        value = body.model_dump(mode="json")
        fingerprint = digest(value)
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            current = await self.requests.row(session, tenant, business, request)
            existing = await self.effect(session, row, operation)
            if existing:
                if existing["request_hash"] != fingerprint:
                    raise AuthError("MOTION_CHECKPOINT_DECISION_CONFLICT", 409)
                return {"decision": body.decision, "stage": stage}
            if current["state"] != "running" or current["execution_token"] is not None or current["actor_id"] != actor:
                raise AuthError("MOTION_CHECKPOINT_NOT_WAITING", 409)
            if body.decision == "approve":
                await self.requests._admission(session, tenant, business)
                await self.requests.current(session, current)
                if packet["context"]["request"]["preparation"]["unresolved"]:
                    raise AuthError("MOTION_PREPARATION_UNRESOLVED", 409)
            await session.execute(
                text("""INSERT INTO motion_effects
                (tenant_id,business_id,request_id,operation_id,kind,state,request_hash,request_ciphertext)
                VALUES(:tenant,:business,:id,:operation,'review','claimed',:hash,:payload)"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": request,
                    "operation": operation,
                    "hash": fingerprint,
                    "payload": self.requests.context.seal(value),
                },
            )
            if body.decision == "reject":
                await session.execute(
                    text("""UPDATE motion_requests SET state='failed',failure_code='MOTION_CHECKPOINT_REJECTED',
                    finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": request},
                )
                gate = self.requests.gate
                await gate.finish_withdrawal_if_idle(
                    session, tenant, business, actor, await gate._state(session, tenant, business)
                )
                await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
            await _event(
                session,
                tenant,
                business,
                actor,
                row["operation_id"],
                APPROVED[stage] if body.decision == "approve" else "motion.failed",
            )
        if body.decision == "reject":
            await apply_pending_script_changes(self.requests.settings, self.requests.database, tenant, business, actor)
        return {"decision": body.decision, "stage": stage}

    async def is_recovery(self, event: BusinessEvent) -> bool:
        async with self.requests.database.transaction(UUID(event.tenant_id), UUID(event.actor_id)) as session:
            return bool(
                await session.scalar(
                    text("""SELECT 1 FROM motion_effects
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request
                AND operation_id=:recovery AND kind='review'"""),
                    {
                        "tenant": UUID(event.tenant_id),
                        "business": UUID(event.business_id),
                        "request": uuid5(
                            UUID(event.operation_id), f"motion-request:{event.tenant_id}:{event.business_id}"
                        ),
                        "recovery": uuid5(UUID(event.event_id), "checkpoint-recovery"),
                    },
                )
            )

    async def recover_before_submission(
        self, tenant: UUID, business: UUID, actor: UUID, request: UUID, body: MotionCheckpointDecision
    ) -> dict[str, str]:
        """Explicitly resume an approved, failed stage only when no code effect ever started."""
        row, checkpoint, _, packet = await self.load(tenant, business, actor, request, "plan")
        if body.decision != "approve" or body.content_sha256 != checkpoint["request_hash"]:
            raise AuthError("MOTION_CHECKPOINT_RECOVERY_INVALID", 409)
        event_id = uuid5(body.operation_id, APPROVED["plan"])
        recovery_id = uuid5(event_id, "checkpoint-recovery")
        payload = {
            "version": RECOVERY_SCHEMA,
            "event_id": str(event_id),
            "parent_operation_id": str(row["operation_id"]),
            "checkpoint_sha256": body.content_sha256,
            "decision": body.model_dump(mode="json"),
        }
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            current = await self.requests.row(session, tenant, business, request)
            existing = await self.effect(session, row, recovery_id)
            if existing:
                if existing["request_hash"] != digest(payload):
                    raise AuthError("MOTION_CHECKPOINT_RECOVERY_CONFLICT", 409)
                return {"event_id": str(event_id), "stage": "plan"}
            approved = await self.effect(session, row, uuid5(checkpoint_id(row["operation_id"], "plan"), "decision"))
            approval = self.requests.context.open(approved["request_ciphertext"]) if approved else {}
            code = uuid5(row["operation_id"], "generate:0")
            started = await session.scalar(
                text("""SELECT 1 FROM motion_effects WHERE tenant_id=:tenant
                AND request_id=:request AND operation_id IN (:code,:upload) LIMIT 1"""),
                {"tenant": tenant, "request": request, "code": code, "upload": uuid5(code, "payload:request")},
            )
            if (
                current["state"] != "failed"
                or current["actor_id"] != actor
                or approved is None
                or approved["state"] != "received"
                or approved["request_hash"] != digest(approval)
                or approval.get("decision") != "approve"
                or approval.get("content_sha256") != body.content_sha256
                or packet["artifact"]["illustrations"]
                or started
            ):
                raise AuthError("MOTION_CHECKPOINT_RECOVERY_NOT_SAFE", 409)
            await self.requests._admission(session, tenant, business)
            await self.requests.current(session, current)
            await session.execute(
                text("""INSERT INTO motion_effects
                (tenant_id,business_id,request_id,operation_id,kind,state,request_hash,request_ciphertext)
                VALUES(:tenant,:business,:request,:recovery,'review','claimed',:hash,:payload)"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "request": request,
                    "recovery": recovery_id,
                    "hash": digest(payload),
                    "payload": self.requests.context.seal(payload),
                },
            )
            await session.execute(
                text("""UPDATE motion_requests SET state='running',execution_token=NULL,
                failure_code=NULL,finished_at=NULL
                WHERE tenant_id=:tenant AND business_id=:business AND id=:request"""),
                {"tenant": tenant, "business": business, "request": request},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                VALUES(:tenant,:actor,:operation,'motion.checkpoint_recovery_requested',:business)"""),
                {"tenant": tenant, "actor": actor, "operation": body.operation_id, "business": business},
            )
            await _event(session, tenant, business, actor, row["operation_id"], APPROVED["plan"], event_id=event_id)
        return {"event_id": str(event_id), "stage": "plan"}

    async def begin(self, event: BusinessEvent, stage: Stage) -> tuple[dict[str, Any], UUID, dict[str, Any]] | None:
        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        recovering = UUID(event.event_id) != uuid5(operation, APPROVED[stage])
        if recovering and (stage != "plan" or not await self.is_recovery(event)):
            raise AuthError("MOTION_EVENT_MISMATCH", 409)
        request = uuid5(operation, f"motion-request:{tenant}:{business}")
        row, _, decision, packet = await self.load(tenant, business, actor, request, stage)
        decision_id = uuid5(checkpoint_id(operation, stage), "decision")
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            current = await self.requests.row(session, tenant, business, request)
            decision = await self.effect(session, row, decision_id)
            recovery_id = uuid5(UUID(event.event_id), "checkpoint-recovery")
            recovery = await self.effect(session, row, recovery_id) if recovering else None
            valid = await session.scalar(
                text("""SELECT 1 FROM outbox_events WHERE tenant_id=:tenant AND id=:event
                AND event_type=:kind AND payload->>'business_id'=:business AND payload->>'actor_id'=:actor
                AND payload->>'operation_id'=:operation"""),
                {
                    "tenant": tenant,
                    "event": UUID(event.event_id),
                    "kind": APPROVED[stage],
                    "business": str(business),
                    "actor": str(actor),
                    "operation": str(operation),
                },
            )
            if not valid or decision is None:
                raise AuthError("MOTION_CHECKPOINT_APPROVAL_REQUIRED", 409)
            if recovering:
                assert recovery is not None
                value = self.requests.context.open(recovery["request_ciphertext"])
                if (
                    recovery["state"] not in {"claimed", "received"}
                    or digest(value) != recovery["request_hash"]
                    or value.get("version") != RECOVERY_SCHEMA
                    or value.get("parent_operation_id") != str(operation)
                    or value.get("event_id") != event.event_id
                    or value.get("checkpoint_sha256") != digest(packet)
                ):
                    raise AuthError("MOTION_CHECKPOINT_RECOVERY_INVALID", 409)
                if recovery["state"] == "received":
                    return None
            approved = self.requests.context.open(decision["request_ciphertext"])
            if (
                digest(approved) != decision["request_hash"]
                or decision["kind"] != "review"
                or decision["state"] not in {"claimed", "received"}
                or approved["decision"] != "approve"
                or approved["content_sha256"] != digest(packet)
            ):
                raise AuthError("MOTION_CHECKPOINT_APPROVAL_REQUIRED", 409)
            if decision["state"] == "received" and not recovering:
                return None
            if current["state"] != "running" or current["execution_token"] is not None:
                raise AuthError("MOTION_CHECKPOINT_NOT_WAITING", 409)
            # Claim the one-shot continuation before revalidation. The orchestrator
            # can then terminally record revoked/changed inputs with this token,
            # instead of leaving an approved request permanently active.
            token = uuid4()
            await session.execute(
                text("""UPDATE motion_requests SET execution_token=:token
                WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": request, "token": token},
            )
            await session.execute(
                text("""UPDATE motion_effects SET state='received',finished_at=clock_timestamp()
                WHERE tenant_id=:tenant AND operation_id=:operation"""),
                {"tenant": tenant, "operation": recovery_id if recovering else decision_id},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                VALUES(:tenant,:actor,:operation,'motion.checkpoint_resumed',:business)"""),
                {
                    "tenant": tenant,
                    "actor": actor,
                    "operation": recovery_id if recovering else decision_id,
                    "business": business,
                },
            )
        return row, token, packet
