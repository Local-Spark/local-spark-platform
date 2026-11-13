"""Resume critique of a received MP4 only before any review submission, without regenerating it."""

import base64
import hashlib
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.adapters.motion_html_renderer import RenderedFrame, RenderedMotion
from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact, _event
from app.services.motion_checkpoints import MotionCheckpoints
from app.services.motion_context import digest
from app.services.motion_render_recovery import recovery_operation
from app.services.motion_storyboards import MotionStoryboards
from app.workflows.contracts import BusinessEvent

if TYPE_CHECKING:
    from app.services.motion_orchestrator import Candidate, MotionOrchestrator


def review_recovery_event(operation: UUID) -> UUID:
    return uuid5(uuid5(operation, "review-recovery:1"), "motion.storyboard_approved")


class MotionReviewRecovery:
    def __init__(self, runner: "MotionOrchestrator"):
        self.runner, self.requests = runner, runner.requests
        self.boards = MotionStoryboards(runner.requests, runner.store)
        self.checks = MotionCheckpoints(runner.requests, runner.store)

    async def snapshot(
        self, s: Any, tenant: UUID, business: UUID, actor: UUID, request: UUID
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        await self.requests.gate._lock(s, tenant, business, actor)
        row = dict(await self.requests.row(s, tenant, business, request))
        if row["actor_id"] != actor:
            raise AuthError("MOTION_OWNER_CHANGED", 409)
        versions = [
            dict(v)
            for v in (
                await s.execute(
                    text(
                        "SELECT * FROM motion_render_versions WHERE tenant_id=:t AND business_id=:b AND request_id=:r"
                    ),
                    {"t": tenant, "b": business, "r": request},
                )
            ).mappings()
        ]
        effects = [
            dict(e)
            for e in (
                await s.execute(
                    text("SELECT * FROM motion_effects WHERE tenant_id=:t AND business_id=:b AND request_id=:r"),
                    {"t": tenant, "b": business, "r": request},
                )
            ).mappings()
        ]
        return row, versions, effects

    async def request(self, tenant: UUID, business: UUID, actor: UUID, request: UUID, sha: str) -> UUID:
        async with self.requests.database.transaction(tenant, actor) as s:
            row, versions, effects = await self.snapshot(s, tenant, business, actor, request)
            op = uuid5(row["operation_id"], "review-recovery:1")
            eid = review_recovery_event(row["operation_id"])
            payload = {"version": "motion-received-review-v1", "mp4_sha256": sha}
            old = next((e for e in effects if e["operation_id"] == op), None)
            if old:
                if old["request_hash"] != digest(payload):
                    raise AuthError("MOTION_REVIEW_RECOVERY_CONFLICT", 409)
                return eid
            forbidden = {
                uuid5(row["operation_id"], "review:0"),
                uuid5(uuid5(row["operation_id"], "review:0"), "payload:request"),
            }
            used = sum(max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects)
            if (
                row["state"] != "failed"
                or row["failure_code"] != "MOTION_EXECUTION_FAILED"
                or row["piece_id"]
                or len(versions) != 1
                or versions[0]["number"] != 0
                or versions[0]["sha256"] != sha
                or versions[0]["review_ciphertext"]
                or any(e["state"] != "received" or e["operation_id"] in forbidden for e in effects)
                or any(e["reserved_usd_micros"] and e["estimated_usd_micros"] is None for e in effects)
                or row["budget_usd_micros"] - used < self.requests.settings.motion_ai_reservation_usd_micros
            ):
                raise AuthError("MOTION_REVIEW_RECOVERY_INELIGIBLE", 409)
            await self.requests._admission(s, tenant, business)
            await self.requests.current(s, row)
            params = {"t": tenant, "b": business, "r": request, "o": op, "a": actor}
            await s.execute(
                text("""INSERT INTO motion_effects(tenant_id,business_id,request_id,operation_id,kind,state,
                request_hash,request_ciphertext)
                VALUES(:t,:b,:r,:o,'review','claimed',:h,:p)"""),
                {**params, "h": digest(payload), "p": self.requests.context.seal(payload)},
            )
            await s.execute(
                text(
                    "INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id) "
                    "VALUES(:t,:a,:o,'motion.review_recovery_requested',:b)"
                ),
                params,
            )
            await _event(s, tenant, business, actor, row["operation_id"], "motion.storyboard_approved", event_id=eid)
            return eid

    async def candidate(self, row: dict[str, Any], version: dict[str, Any], composition: Any) -> "Candidate":
        from app.services.motion_orchestrator import Candidate

        if self.requests.context.open(version["composition_ciphertext"]) != composition.model_dump(mode="json"):
            raise AuthError("MOTION_REVIEW_RECOVERY_BYTES_CHANGED", 409)
        media = await self.runner.store.get_video(version["object_key"])
        diagnostics = self.requests.context.open(version["diagnostics_ciphertext"])
        evidence = await self.checks.payloads.open(row, version["evidence_ciphertext"])
        if (
            hashlib.sha256(media).hexdigest() != version["sha256"]
            or len(media) != version["size_bytes"]
            or diagnostics.get("executor_image") != getattr(self.runner.renderer, "image", None)
        ):
            raise AuthError("MOTION_REVIEW_RECOVERY_BYTES_CHANGED", 409)
        frames = []
        for f in evidence["frames"]:
            raw = base64.b64decode(f["png"], validate=True)
            if hashlib.sha256(raw).hexdigest() != f["sha256"]:
                raise AuthError("MOTION_REVIEW_RECOVERY_BYTES_CHANGED", 409)
            frames.append(RenderedFrame(f["ms"], raw, f["sha256"], f.get("frame_index"), f.get("pts_seconds")))
        if not frames:
            raise AuthError("MOTION_REVIEW_RECOVERY_BYTES_CHANGED", 409)
        rendered = RenderedMotion(media, version["sha256"], tuple(frames), diagnostics)
        artifact = PieceArtifact(
            uuid5(version["operation_id"], "artifact"),
            version["object_key"],
            version["sha256"],
            "video/mp4",
            len(media),
        )
        return Candidate(0, composition, rendered, artifact)

    async def run(self, event: BusinessEvent) -> str:
        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        if UUID(event.event_id) != review_recovery_event(operation):
            raise AuthError("MOTION_EVENT_MISMATCH", 409)
        request = uuid5(operation, f"motion-request:{tenant}:{business}")
        op = uuid5(operation, "review-recovery:1")
        async with self.requests.database.transaction(tenant, actor) as s:
            row, versions, effects = await self.snapshot(s, tenant, business, actor, request)
            marker = next((e for e in effects if e["operation_id"] == op), None)
            valid = await s.scalar(
                text(
                    "SELECT 1 FROM outbox_events WHERE tenant_id=:t AND id=:e AND "
                    "event_type='motion.storyboard_approved' AND payload->>'operation_id'=:o AND "
                    "payload->>'business_id'=:b AND payload->>'actor_id'=:a"
                ),
                {"t": tenant, "e": UUID(event.event_id), "o": str(operation), "b": str(business), "a": str(actor)},
            )
            if marker is None or not valid:
                raise AuthError("MOTION_EVENT_MISMATCH", 409)
            if marker["state"] == "received":
                return "already_claimed"
            payload = self.requests.context.open(marker["request_ciphertext"])
            if (
                row["state"] != "failed"
                or row["failure_code"] != "MOTION_EXECUTION_FAILED"
                or marker["state"] != "claimed"
                or marker["request_hash"] != digest(payload)
                or len(versions) != 1
                or versions[0]["sha256"] != payload["mp4_sha256"]
            ):
                raise AuthError("MOTION_REVIEW_RECOVERY_CHANGED", 409)
            version = versions[0]
            board = dict(await self.boards.board(s, tenant, business, request))
            await self.requests._admission(s, tenant, business)
            await self.requests.current(s, row)
            token = uuid4()
            await s.execute(
                text(
                    "UPDATE motion_requests SET "
                    "state='running',execution_token=:k,failure_code=NULL,finished_at=NULL WHERE "
                    "tenant_id=:t AND business_id=:b AND id=:r"
                ),
                {"t": tenant, "b": business, "r": request, "k": token},
            )
            await s.execute(
                text(
                    "UPDATE motion_effects SET "
                    "state='received',response_ciphertext=:p,estimated_usd_micros=0,finished_at=clock_timestamp() "
                    "WHERE tenant_id=:t AND operation_id=:o"
                ),
                {
                    "t": tenant,
                    "o": op,
                    "p": self.requests.context.seal({"started": True, "mp4_sha256": version["sha256"]}),
                },
            )
        try:
            namespace = recovery_operation(operation)
            if version["operation_id"] == uuid5(operation, "render:0"):
                namespace = operation
            if version["operation_id"] != uuid5(namespace, "render:0"):
                raise AuthError("MOTION_REVIEW_RECOVERY_BYTES_CHANGED", 409)
            row["render_namespace"] = namespace
            prepared = await self.runner.inputs.prepare(self.requests.context.open(row["snapshot_ciphertext"]))
            prepared, composition = await self.boards.restore(row, board, prepared)
            candidate = await self.candidate(row, version, composition)
            return await self.runner.produce(row, token, prepared, composition, initial_candidate=candidate)
        except BaseException as exc:
            failure = uuid5(UUID(event.event_id), "motion.failed")
            try:
                await self.runner.fail(
                    row, token, getattr(exc, "code", "MOTION_EXECUTION_FAILED"), failure_event_id=failure
                )
            except Exception:
                await self.runner.effects.quarantine(row, token, failure_event_id=failure)
            raise
