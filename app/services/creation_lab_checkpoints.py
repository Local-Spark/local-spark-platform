"""Exact-byte administrative decisions and private adapters for productive checkpoints."""

import base64
import hashlib
from typing import Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.adapters.material_media import MaterialStore
from app.schemas.motion_preparation import MotionCheckpointDecision
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_motion_requests import LabMotionRequests
from app.services.motion_checkpoints import MotionCheckpoints, Stage, checkpoint_id
from app.services.motion_context import digest
from app.services.motion_storyboards import MotionStoryboards
from app.workflows.contracts import BusinessEvent

STAGES = {"plan", "render", "storyboard", "editorial", "catalog"}


class LabCheckpoints:
    def __init__(self, requests: LabMotionRequests):
        self.requests, self.execution = requests, requests.execution
        self.run_id = requests.run_id

    async def pause(self, session: Any, row: Any, token: UUID, stage: str, trace: UUID, payload: Any) -> None:
        self.execution.fence(
            await self.execution.guard(session, row["actor_id"], self.run_id, "admin.creation_lab.checkpoint.pause"),
            token,
        )
        await session.execute(
            text("""INSERT INTO creation_lab_checkpoints(run_id,stage,trace_id,content_sha256)
          VALUES(:run,:stage,:trace,:sha)"""),
            {"run": self.run_id, "stage": stage, "trace": trace, "sha": digest(payload)},
        )
        await session.execute(
            text("UPDATE creation_lab_runs SET state='awaiting_approval',execution_token=NULL WHERE id=:run"),
            {"run": self.run_id},
        )
        await self.execution.event(
            session, self.run_id, uuid5(self.run_id, f"{stage}:ready"), f"checkpoint.{stage}_ready", trace
        )

    async def list(self, actor: UUID) -> list[dict[str, Any]]:
        async with self.requests.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, self.run_id, "admin.creation_lab.checkpoint.read")
            rows = (
                (
                    await session.execute(
                        text("""SELECT c.*,t.payload_ciphertext,
              r.trace_expires_at IS NOT NULL AND r.trace_expires_at<=clock_timestamp() AS expired
              FROM creation_lab_checkpoints c JOIN creation_lab_trace t ON t.id=c.trace_id
              JOIN creation_lab_runs r ON r.id=c.run_id WHERE c.run_id=:run ORDER BY c.created_at"""),
                        {"run": self.run_id},
                    )
                )
                .mappings()
                .all()
            )
            result = []
            for row in rows:
                payload = (
                    None
                    if row["expired"] or not row["payload_ciphertext"]
                    else self.requests.context.open(row["payload_ciphertext"])["value"]
                )
                if payload is not None:
                    # Do not put executable HTML or base64 assets into the UI. Full payload remains in authenticated trace.
                    payload = {
                        k: v
                        for k, v in payload.items()
                        if k not in {"resolved_images", "illustrations", "baseline_evidence"}
                    }
                    for key in ("artifact", "composition"):
                        if key in payload and isinstance(payload[key], dict):
                            payload[key] = {k: v for k, v in payload[key].items() if k not in {"html", "scene_init"}}
                    if "frames" in payload:
                        payload["frames"] = [
                            {k: v for k, v in frame.items() if k not in {"object_key", "data"}}
                            for frame in payload["frames"]
                        ]
                result.append(
                    {
                        "stage": row["stage"],
                        "content_sha256": row["content_sha256"],
                        "decision": row["decision"],
                        "consumed": row["consumed"],
                        "trace_id": row["trace_id"],
                        "payload": payload,
                    }
                )
            return result

    async def decide(self, actor: UUID, stage: str, body: MotionCheckpointDecision) -> dict[str, str]:
        if stage not in STAGES:
            raise AuthError("CREATION_LAB_CHECKPOINT_NOT_FOUND", 404)
        async with self.requests.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run_id, "admin.creation_lab.checkpoint.decide")
            checkpoint = (
                (
                    await session.execute(
                        text("SELECT * FROM creation_lab_checkpoints WHERE run_id=:run AND stage=:stage"),
                        {"run": self.run_id, "stage": stage},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if checkpoint is None or checkpoint["content_sha256"] != body.content_sha256:
                raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
            fingerprint = digest(body.model_dump(mode="json"))
            if checkpoint["decision"]:
                if checkpoint["decision_hash"] != fingerprint:
                    raise AuthError("MOTION_CHECKPOINT_DECISION_CONFLICT", 409)
                return {"decision": body.decision, "stage": stage}
            if row["state"] != "awaiting_approval":
                raise AuthError("MOTION_CHECKPOINT_NOT_WAITING", 409)
            if body.decision == "approve":
                value = await session.scalar(
                    text("SELECT payload_ciphertext FROM creation_lab_trace WHERE id=:id AND run_id=:run"),
                    {"id": checkpoint["trace_id"], "run": self.run_id},
                )
                if not value or self.requests.context.open(value)["value"].get("questions"):
                    raise AuthError("CREATION_LAB_REPLY_REQUIRED", 409)
                await self.requests.current(session, await self.requests.normalized(session, row))
            trace = uuid5(self.run_id, f"decision:{stage}")
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,:stage,'evidence',:payload)"""),
                {
                    "id": trace,
                    "run": self.run_id,
                    "stage": stage,
                    "payload": self.requests.context.seal({"value": body.model_dump(mode="json")}),
                },
            )
            await session.execute(
                text("""UPDATE creation_lab_checkpoints SET decision=:decision,
              decision_hash=:hash,decision_trace_id=:trace WHERE run_id=:run AND stage=:stage"""),
                {"decision": body.decision, "hash": fingerprint, "trace": trace, "run": self.run_id, "stage": stage},
            )
            await self.execution.event(
                session, self.run_id, uuid5(self.run_id, f"{stage}:decision"), f"checkpoint.{body.decision}", trace
            )
            await self.requests.scope(session, row)
            if body.decision == "approve":
                await _event(
                    session, row["tenant_id"], row["business_id"], actor, self.run_id, f"creation_lab.{stage}_approved"
                )
            else:
                await self.execution.finish_locked(session, row, "cancelled", "CREATION_LAB_CHECKPOINT_REJECTED")
            return {"decision": body.decision, "stage": stage}

    async def begin(self, event: BusinessEvent, stage: str) -> tuple[dict[str, Any], UUID, dict[str, Any]] | None:
        actor = UUID(event.actor_id)
        if UUID(event.operation_id) != self.run_id or UUID(event.event_id) != uuid5(
            self.run_id, f"motion.{stage}_approved"
        ):
            raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
        async with self.requests.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run_id, "admin.creation_lab.checkpoint.resume")
            if str(row["tenant_id"]) != event.tenant_id or str(row["business_id"]) != event.business_id:
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            cp = (
                (
                    await session.execute(
                        text("""SELECT c.*,t.payload_ciphertext FROM creation_lab_checkpoints c
              JOIN creation_lab_trace t ON t.id=c.trace_id WHERE c.run_id=:run AND c.stage=:stage"""),
                        {"run": self.run_id, "stage": stage},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if cp is None or cp["decision"] != "approve":
                raise AuthError("MOTION_CHECKPOINT_NOT_APPROVED", 409)
            if cp["consumed"]:
                return None
            if row["state"] != "awaiting_approval":
                raise AuthError("MOTION_CHECKPOINT_NOT_WAITING", 409)
            normalized = await self.requests.normalized(session, row)
            await self.requests.current(session, normalized)
            payload = self.requests.context.open(cp["payload_ciphertext"])["value"]
            if digest(payload) != cp["content_sha256"]:
                raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
            token = uuid4()
            await session.execute(
                text("UPDATE creation_lab_checkpoints SET consumed=true WHERE run_id=:run AND stage=:stage"),
                {"run": self.run_id, "stage": stage},
            )
            await session.execute(
                text(
                    "UPDATE creation_lab_runs SET state='running',execution_token=:token,execution_event_id=:event WHERE id=:run"
                ),
                {"run": self.run_id, "token": token, "event": UUID(event.event_id)},
            )
            await self.execution.event(
                session, self.run_id, uuid5(self.run_id, f"{stage}:resumed"), f"checkpoint.{stage}_resumed"
            )
            return normalized, token, payload


class LabMotionCheckpoints(MotionCheckpoints):
    def __init__(self, requests: LabMotionRequests, store: MaterialStore):
        super().__init__(requests, store)
        self.lab = LabCheckpoints(requests)

    async def is_recovery(self, event: BusinessEvent) -> bool:
        return False

    async def effect(self, session: Any, row: dict[str, Any], operation: UUID) -> dict[str, Any] | None:
        effect = (
            (
                await session.execute(
                    text("SELECT * FROM creation_lab_effects WHERE id=:id AND run_id=:run"),
                    {"id": operation, "run": row["id"]},
                )
            )
            .mappings()
            .one_or_none()
        )
        if effect is None:
            return None
        result = dict(effect)
        for slot in ("request", "response"):
            value = await session.scalar(
                text(
                    "SELECT payload_ciphertext FROM creation_lab_trace WHERE run_id=:run AND effect_id=:id AND slot=:slot"
                ),
                {"run": row["id"], "id": operation, "slot": slot},
            )
            result[f"{slot}_ciphertext"] = (
                self.requests.context.seal(self.requests.context.open(value)["value"]) if value else None
            )
        return result

    async def pause(self, row: dict[str, Any], token: UUID, stage: Stage) -> None:
        trace = uuid5(checkpoint_id(row["operation_id"], stage), "request")
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            value = await session.scalar(
                text("SELECT payload_ciphertext FROM creation_lab_trace WHERE id=:id AND run_id=:run"),
                {"id": trace, "run": row["id"]},
            )
            await self.lab.pause(session, row, token, stage, trace, self.requests.context.open(value)["value"])

    async def begin(self, event: BusinessEvent, stage: Stage) -> tuple[dict[str, Any], UUID, dict[str, Any]] | None:
        return await self.lab.begin(event, stage)


class LabMotionStoryboards(MotionStoryboards):
    def __init__(self, requests: LabMotionRequests, store: MaterialStore):
        super().__init__(requests, store)
        self.lab = LabCheckpoints(requests)

    async def persist_frame(self, row, token, operation, manifest, data, effects):
        # Frames are diagnostic evidence, not retained customer assets. Keep their
        # bytes in the expiring encrypted board instead of orphaning S3 objects.
        return {k: v for k, v in manifest.items() if k != "object_key"} | {"data": base64.b64encode(data).decode()}

    async def read_png(self, manifest):
        if "data" not in manifest:
            return await super().read_png(manifest)
        data = base64.b64decode(manifest["data"], validate=True)
        if len(data) != manifest["size_bytes"] or hashlib.sha256(data).hexdigest() != manifest["sha256"]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        return data

    async def persist_board(self, row: dict[str, Any], token: UUID, operation: UUID, sha: str, ciphertext: str) -> None:
        payload = self.requests.context.open(ciphertext)
        if digest(payload) != sha:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        trace = uuid5(operation, "board")
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,'storyboard','evidence',:payload)"""),
                {"id": trace, "run": row["id"], "payload": self.requests.context.seal({"value": payload})},
            )
            await self.lab.pause(session, row, token, "storyboard", trace, payload)

    async def begin_resume(self, event: BusinessEvent) -> tuple[dict[str, Any], UUID, dict[str, Any]] | None:
        started = await self.lab.begin(event, "storyboard")
        if started is None:
            return None
        row, token, payload = started
        return (
            row,
            token,
            {"payload_ciphertext": self.requests.context.seal(payload), "content_sha256": digest(payload)},
        )


async def storyboard_frame(requests: LabMotionRequests, actor: UUID, index: int) -> bytes:
    async def manifest():
        async with requests.database.transaction(ZERO, actor) as session:
            await requests.execution.guard(session, actor, requests.run_id, "admin.creation_lab.storyboard.read")
            row = (
                (
                    await session.execute(
                        text("""SELECT t.payload_ciphertext,
              r.trace_expires_at IS NOT NULL AND r.trace_expires_at<=clock_timestamp() AS expired
              FROM creation_lab_checkpoints c JOIN creation_lab_trace t ON t.id=c.trace_id
              JOIN creation_lab_runs r ON r.id=c.run_id WHERE c.run_id=:run AND c.stage='storyboard'"""),
                        {"run": requests.run_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_CHECKPOINT_NOT_FOUND", 404)
            if row["expired"] or not row["payload_ciphertext"]:
                raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
            frames = requests.context.open(row["payload_ciphertext"])["value"]["frames"]
            if not 0 <= index < len(frames):
                raise AuthError("CREATION_LAB_FRAME_NOT_FOUND", 404)
            return frames[index]

    expected = await manifest()
    data = await LabMotionStoryboards(requests, MaterialStore(requests.settings)).read_png(expected)
    if expected != await manifest():
        raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
    return data
