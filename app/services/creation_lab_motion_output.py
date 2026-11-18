"""Private output adapter for the unchanged productive motion render/review loop."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_motion_effects import LabMotionEffects
from app.services.motion_orchestrator import Candidate, MotionOrchestrator


class LabMotionOrchestrator(MotionOrchestrator):
    def __init__(self, productive: MotionOrchestrator, run: UUID) -> None:
        super().__init__(
            productive.requests,
            productive.effects.ledger.database,
            productive.provider,
            productive.renderer,
            productive.inputs,
            productive.store,
            illustration_provider=productive.illustration_provider,
            speech_recognizer=productive.speech_recognizer,
        )
        self.run_id = run
        self.effects = LabMotionEffects(self.requests, run)
        self.execution = CreationLabExecution(self.requests.settings, self.requests.database)

    async def prepare(self, row, token):
        from app.services.motion_checkpoints import input_manifest

        operation = uuid5(row["operation_id"], "prepare-inputs")
        await self.effects.claim(
            row, token, operation, "preparation", {"source_fingerprint": row["source_fingerprint"]}
        )
        prepared = await super().prepare(row, token)
        await self.effects.received(row, token, operation, input_manifest(prepared))
        return prepared

    def checkpoints(self):
        from app.services.creation_lab_checkpoints import LabMotionCheckpoints

        return LabMotionCheckpoints(self.requests, self.store)

    def storyboards(self):
        from app.services.creation_lab_checkpoints import LabMotionStoryboards

        return LabMotionStoryboards(self.requests, self.store)

    async def persist_render(
        self,
        row: dict[str, Any],
        token: UUID,
        number: int,
        render_operation: UUID,
        artifact: PieceArtifact,
        composition_ciphertext: str,
        evidence_ciphertext: str,
        diagnostics_ciphertext: str,
    ) -> None:
        if row["id"] != self.run_id:
            raise AuthError("CREATION_LAB_RUN_MISMATCH", 409)
        evidence = {
            "composition": self.requests.context.open(composition_ciphertext),
            "frames": self.requests.context.open(evidence_ciphertext),
            "diagnostics": self.requests.context.open(diagnostics_ciphertext),
        }
        # Serialize/encrypt the bounded evidence before taking the writer lock.
        # Frame evidence may approach 48 MiB; it is already bounded by persist_payload.
        sealed_evidence = {slot: self.execution.cipher.seal({"value": payload}) for slot, payload in evidence.items()}
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            current = await self.execution.guard(
                session, row["actor_id"], self.run_id, "admin.creation_lab.artifact.create"
            )
            self.execution.fence(current, token)
            await session.execute(
                text("""INSERT INTO creation_lab_versions
              (id,run_id,number,object_key,sha256,mime_type,size_bytes)
              VALUES(:id,:run,:number,:key,:sha,:mime,:size)"""),
                {
                    "id": artifact.id,
                    "run": self.run_id,
                    "number": number,
                    "key": artifact.object_key,
                    "sha": artifact.sha256,
                    "mime": artifact.mime_type,
                    "size": artifact.size_bytes,
                },
            )
            # Keep lock acquisition at 3s and ordinary statements at 10s. Only the
            # bounded diagnostic INSERTs get a larger, transaction-local deadline.
            await session.execute(text("SET LOCAL statement_timeout = '60s'"))
            try:
                for slot, payload in sealed_evidence.items():
                    await session.execute(
                        text("""INSERT INTO creation_lab_trace(id,run_id,effect_id,stage,slot,payload_ciphertext)
                      VALUES(:id,:run,:effect,:stage,'evidence',:payload)"""),
                        {
                            "id": uuid5(render_operation, f"render:{slot}"),
                            "run": self.run_id,
                            "effect": render_operation,
                            "stage": slot,
                            "payload": payload,
                        },
                    )
            except DBAPIError as exc:
                if getattr(exc.orig, "sqlstate", None) == "57014":
                    raise AuthError("CREATION_LAB_RENDER_EVIDENCE_TIMEOUT", 409) from None
                raise
            await session.execute(text("SET LOCAL statement_timeout = '10s'"))
            await self.execution.event(
                session,
                self.run_id,
                uuid5(artifact.id, "recorded"),
                "artifact.recorded",
                uuid5(render_operation, "render:composition"),
            )

    async def record_review(self, row: dict[str, Any], token: UUID, candidate: Candidate) -> None:
        if row["id"] != self.run_id or candidate.review is None:
            raise AuthError("CREATION_LAB_REVIEW_INVALID", 409)
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            current = await self.execution.guard(
                session, row["actor_id"], self.run_id, "admin.creation_lab.artifact.review"
            )
            self.execution.fence(current, token)
            changed = await session.scalar(
                text("""UPDATE creation_lab_versions SET review_verdict=:verdict
              WHERE run_id=:run AND id=:id AND review_verdict IS NULL RETURNING 1"""),
                {"run": self.run_id, "id": candidate.artifact.id, "verdict": candidate.review.verdict},
            )
            if not changed:
                raise AuthError("CREATION_LAB_REVIEW_ALREADY_RECORDED", 409)
            # The complete review is already retained by the shared model effect.
            await self.execution.event(
                session, self.run_id, uuid5(candidate.artifact.id, "reviewed"), "artifact.reviewed"
            )

    async def complete(
        self, row: dict[str, Any], token: UUID, candidates: list[Candidate], selected: Candidate
    ) -> None:
        if row["id"] != self.run_id or not any(candidate is selected for candidate in candidates):
            raise AuthError("CREATION_LAB_RESULT_INVALID", 409)
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            current = await self.execution.guard(
                session, row["actor_id"], self.run_id, "admin.creation_lab.artifact.select"
            )
            self.execution.fence(current, token)
            changed = await session.scalar(
                text("""UPDATE creation_lab_versions SET selected=true
              WHERE run_id=:run AND id=:id AND review_verdict='adequate' RETURNING 1"""),
                {"run": self.run_id, "id": selected.artifact.id},
            )
            if not changed:
                raise AuthError("CREATION_LAB_RESULT_INVALID", 409)
            await self.execution.event(
                session, self.run_id, uuid5(self.run_id, "artifact-selected"), "artifact.selected"
            )
            await self.execution.finish_locked(session, current, "completed")

    async def fail(self, row: dict[str, Any], token: UUID, code: str, *, failure_event_id: UUID | None = None) -> None:
        if row["id"] != self.run_id:
            raise AuthError("CREATION_LAB_RUN_MISMATCH", 409)
        safe_code = code if isinstance(code, str) and code.isupper() and len(code) <= 100 else "MOTION_EXECUTION_FAILED"
        await self.execution.finish(row["actor_id"], self.run_id, token, "failed", safe_code)
