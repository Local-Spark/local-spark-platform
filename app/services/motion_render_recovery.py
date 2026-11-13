"""One explicit local renderer replacement, with new effect identities and unchanged paid receipts."""

import re
from typing import TYPE_CHECKING
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_context import digest
from app.services.motion_storyboards import MotionStoryboards
from app.workflows.contracts import BusinessEvent

if TYPE_CHECKING:
    from app.services.motion_orchestrator import MotionOrchestrator


def recovery_operation(operation: UUID) -> UUID:
    return uuid5(operation, "renderer-recovery:1")


def recovery_event(operation: UUID) -> UUID:
    return uuid5(recovery_operation(operation), "motion.storyboard_approved")


class MotionRenderRecovery:
    def __init__(self, runner: "MotionOrchestrator"):
        self.runner, self.requests = runner, runner.requests
        self.boards = MotionStoryboards(runner.requests, runner.store)

    async def request(
        self, tenant: UUID, business: UUID, actor: UUID, request: UUID, board_sha: str, executor_image: str
    ) -> UUID:
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", executor_image):
            raise AuthError("MOTION_RENDER_RECOVERY_IMAGE_INVALID", 409)
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            row = dict(await self.requests.row(session, tenant, business, request))
            if row["actor_id"] != actor:
                raise AuthError("MOTION_OWNER_CHANGED", 409)
            operation = recovery_operation(row["operation_id"])
            event = recovery_event(row["operation_id"])
            payload = {
                "version": "motion-render-recovery-v1",
                "board_sha256": board_sha,
                "executor_image": executor_image,
                "failed_operation_id": str(uuid5(row["operation_id"], "render:0")),
            }
            from app.services.motion_checkpoints import MotionCheckpoints

            checks = MotionCheckpoints(self.requests, self.runner.store)
            existing = await checks.effect(session, row, operation)
            if existing is not None:
                if existing["request_hash"] != digest(payload):
                    raise AuthError("MOTION_RENDER_RECOVERY_CONFLICT", 409)
                return event
            board = dict(await self.boards.board(session, tenant, business, request))
            effects = [
                dict(e)
                for e in (
                    await session.execute(
                        text("""SELECT * FROM motion_effects
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request"""),
                        {"tenant": tenant, "business": business, "request": request},
                    )
                ).mappings()
            ]
            failed = uuid5(row["operation_id"], "render:0")
            pending = [e for e in effects if e["state"] != "received"]
            original_image = self.requests.context.open(row["snapshot_ciphertext"])["execution"]["renderer_image"]
            if (
                row["state"] != "failed"
                or row["failure_code"] != "MOTION_RENDER_EXECUTION_FAILED"
                or row["piece_id"]
                or board["state"] != "rendering"
                or board["content_sha256"] != board_sha
                or executor_image == original_image
                or len(pending) != 1
                or pending[0]["operation_id"] != failed
                or pending[0]["kind"] != "render"
                or pending[0]["state"] != "claimed"
                or any(e["reserved_usd_micros"] and e["estimated_usd_micros"] is None for e in effects)
                or sum(max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects)
                > row["budget_usd_micros"]
                or await session.scalar(
                    text(
                        "SELECT 1 FROM motion_render_versions WHERE tenant_id=:tenant AND request_id=:request LIMIT 1"
                    ),
                    {"tenant": tenant, "request": request},
                )
            ):
                raise AuthError("MOTION_RENDER_RECOVERY_INELIGIBLE", 409)
            await self.requests._admission(session, tenant, business)
            await self.requests.current(session, row)
            params = {
                "tenant": tenant,
                "business": business,
                "request": request,
                "operation": operation,
                "actor": actor,
            }
            await session.execute(
                text("""INSERT INTO motion_effects
                (tenant_id,business_id,request_id,operation_id,kind,state,request_hash,request_ciphertext)
                VALUES(:tenant,:business,:request,:operation,'review','claimed',:hash,:payload)"""),
                {**params, "hash": digest(payload), "payload": self.requests.context.seal(payload)},
            )
            await session.execute(
                text("""UPDATE motion_effects SET state='received',response_ciphertext=:response,
                estimated_usd_micros=0,finished_at=clock_timestamp()
                WHERE tenant_id=:tenant AND operation_id=:failed"""),
                {
                    **params,
                    "failed": failed,
                    "response": self.requests.context.seal(
                        {
                            "status": "failed",
                            "failure_code": row["failure_code"],
                            "continuation_operation_id": str(operation),
                        }
                    ),
                },
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                VALUES(:tenant,:actor,:operation,'motion.renderer_recovery_requested',:business)"""),
                params,
            )
            await _event(
                session, tenant, business, actor, row["operation_id"], "motion.storyboard_approved", event_id=event
            )
        return event

    async def run(self, event: BusinessEvent) -> str:
        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        if UUID(event.event_id) != recovery_event(operation):
            raise AuthError("MOTION_EVENT_MISMATCH", 409)
        request = uuid5(operation, f"motion-request:{tenant}:{business}")
        from app.services.motion_checkpoints import MotionCheckpoints

        checks = MotionCheckpoints(self.requests, self.runner.store)
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            row = dict(await self.requests.row(session, tenant, business, request))
            marker = await checks.effect(session, row, recovery_operation(operation))
            valid = await session.scalar(
                text("""SELECT 1 FROM outbox_events WHERE tenant_id=:tenant AND id=:event
                AND event_type='motion.storyboard_approved' AND payload->>'operation_id'=:operation
                AND payload->>'business_id'=:business AND payload->>'actor_id'=:actor"""),
                {
                    "tenant": tenant,
                    "event": UUID(event.event_id),
                    "operation": str(operation),
                    "business": str(business),
                    "actor": str(actor),
                },
            )
            if marker is None or not valid or row["actor_id"] != actor:
                raise AuthError("MOTION_EVENT_MISMATCH", 409)
            if marker["state"] == "received":
                return "already_claimed"
            payload = self.requests.context.open(marker["request_ciphertext"])
            board = dict(await self.boards.board(session, tenant, business, request))
            if (
                row["state"] != "failed"
                or row["failure_code"] != "MOTION_RENDER_EXECUTION_FAILED"
                or marker["state"] != "claimed"
                or marker["request_hash"] != digest(payload)
                or board["state"] != "rendering"
                or board["content_sha256"] != payload["board_sha256"]
                or getattr(self.runner.renderer, "image", None) != payload["executor_image"]
            ):
                raise AuthError("MOTION_RENDER_RECOVERY_CHANGED", 409)
            await self.requests._admission(session, tenant, business)
            await self.requests.current(session, row)
            token = uuid4()
            await session.execute(
                text("""UPDATE motion_requests SET state='running',execution_token=:token,
                failure_code=NULL,finished_at=NULL
                WHERE tenant_id=:tenant AND business_id=:business AND id=:request"""),
                {"tenant": tenant, "business": business, "request": request, "token": token},
            )
            await session.execute(
                text("""UPDATE motion_effects SET state='received',response_ciphertext=:response,
                estimated_usd_micros=0,finished_at=clock_timestamp()
                WHERE tenant_id=:tenant AND operation_id=:operation"""),
                {
                    "tenant": tenant,
                    "operation": recovery_operation(operation),
                    "response": self.requests.context.seal(
                        {"started": True, "executor_image": payload["executor_image"]}
                    ),
                },
            )
        row["render_namespace"] = recovery_operation(operation)
        try:
            prepared = await self.runner.inputs.prepare(self.requests.context.open(row["snapshot_ciphertext"]))
            prepared, composition = await self.boards.restore(row, board, prepared)
            return await self.runner.produce(row, token, prepared, composition)
        except BaseException as exc:
            failure = uuid5(UUID(event.event_id), "motion.failed")
            try:
                await self.runner.fail(
                    row, token, getattr(exc, "code", "MOTION_EXECUTION_FAILED"), failure_event_id=failure
                )
            except Exception:
                await self.runner.effects.quarantine(row, token, failure_event_id=failure)
            raise
