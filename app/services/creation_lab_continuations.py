"""Explicit replies and revisions as linked, budget-preserving private attempts."""

from uuid import UUID, uuid5

from sqlalchemy import text

from app.schemas.creation_lab import LabContinuation
from app.services.auth import AuthError
from app.services.creation_lab_drafts import ZERO, CreationLabDrafts
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creative_continuation import continued_instruction


class CreationLabContinuations:
    def __init__(self, settings, database):
        self.settings, self.database = settings, database
        self.execution = CreationLabExecution(settings, database)
        self.drafts = CreationLabDrafts(settings, database)

    async def create(self, actor: UUID, run: UUID, body: LabContinuation):
        fingerprint = self.drafts.cipher.fingerprint(body.model_dump(mode="json"))
        async with self.database.transaction(ZERO, actor) as session:
            parent = await self.execution.guard(session, actor, run, "admin.creation_lab.continue")
            existing = (
                (await session.execute(text("SELECT * FROM creation_lab_runs WHERE parent_run_id=:run"), {"run": run}))
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["continuation_hash"] != fingerprint:
                    raise AuthError("CREATION_LAB_CONTINUATION_CONFLICT", 409)
                return self.drafts.present(dict(existing))
            if parent["attempt_number"] >= 10:
                raise AuthError("CREATION_LAB_CONTINUATION_LIMIT", 409)
            questions = []
            if body.stage is not None:
                checkpoint = (
                    (
                        await session.execute(
                            text("""SELECT c.*,t.payload_ciphertext FROM creation_lab_checkpoints c
                  JOIN creation_lab_trace t ON t.id=c.trace_id WHERE c.run_id=:run AND c.stage=:stage"""),
                            {"run": run, "stage": body.stage},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    parent["state"] != "awaiting_approval"
                    or checkpoint is None
                    or checkpoint["decision"]
                    or checkpoint["content_sha256"] != body.content_sha256
                ):
                    raise AuthError("MOTION_CHECKPOINT_CHANGED", 409)
                payload = self.drafts.cipher.open(checkpoint["payload_ciphertext"])["value"]
                questions = payload.get("questions", [])
            else:
                if parent["state"] != "completed" or not await session.scalar(
                    text("""SELECT 1 FROM creation_lab_versions
                  WHERE run_id=:run AND sha256=:sha"""),
                    {"run": run, "sha": body.content_sha256},
                ):
                    raise AuthError("CREATION_LAB_RESULT_CHANGED", 409)
            if await session.scalar(
                text("SELECT 1 FROM creation_lab_effects WHERE run_id=:run AND state<>'received' LIMIT 1"), {"run": run}
            ):
                raise AuthError("CREATION_LAB_CONTINUATION_UNRESOLVED", 409)
            if await session.scalar(
                text("SELECT 1 FROM creation_lab_attachments WHERE run_id=:run AND state<>'ready' LIMIT 1"),
                {"run": run},
            ):
                raise AuthError("CREATION_LAB_UPLOAD_UNRESOLVED", 409)
            remaining = parent["budget_usd_micros"] - parent["committed_usd_micros"]
            if remaining <= 0:
                raise AuthError("CREATION_LAB_RUN_BUDGET_EXCEEDED", 409)
            original = self.drafts.cipher.open(parent["instruction_ciphertext"])["instruction"]
            instruction = continued_instruction(original, body.note, questions=questions)
            child = uuid5(actor, f"creation-lab:{body.operation_id}")
            if await session.scalar(text("SELECT 1 FROM creation_lab_runs WHERE id=:id"), {"id": child}):
                raise AuthError("CREATION_LAB_OPERATION_CONFLICT", 409)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO creation_lab_runs
              (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,instruction_ciphertext,
               budget_usd_micros,parent_run_id,rehearsal_id,continuation_hash,attempt_number)
              VALUES(:id,:actor,:tenant,:business,:operation,:hash,:format,:mode,:instruction,:budget,
                     :parent,:root,:hash,:number) RETURNING *"""),
                        {
                            "id": child,
                            "actor": actor,
                            "tenant": parent["tenant_id"],
                            "business": parent["business_id"],
                            "operation": body.operation_id,
                            "hash": fingerprint,
                            "format": parent["format"],
                            "mode": parent["mode"],
                            "instruction": self.drafts.cipher.seal({"instruction": instruction}),
                            "budget": remaining,
                            "parent": run,
                            "root": parent["rehearsal_id"] or run,
                            "number": parent["attempt_number"] + 1,
                        },
                    )
                )
                .mappings()
                .one()
            )
            materials = (
                (
                    await session.execute(
                        text("SELECT * FROM creation_lab_attachments WHERE run_id=:run ORDER BY id"), {"run": run}
                    )
                )
                .mappings()
                .all()
            )
            for material in materials:
                await session.execute(
                    text("""INSERT INTO creation_lab_attachments
                  (id,run_id,operation_id,request_hash,name_ciphertext,object_key,kind,mime_type,sha256,byte_size,rights_confirmed,state)
                  VALUES(:id,:run,:operation,:hash,:name,:key,:kind,:mime,:sha,:size,true,'ready')"""),
                    {
                        "id": uuid5(child, f"material:{material['id']}"),
                        "run": child,
                        "operation": uuid5(child, f"material:{material['id']}"),
                        "hash": material["request_hash"],
                        "name": material["name_ciphertext"],
                        "key": material["object_key"],
                        "kind": material["kind"],
                        "mime": material["mime_type"],
                        "sha": material["sha256"],
                        "size": material["byte_size"],
                    },
                )
            await session.execute(
                text("""INSERT INTO creation_lab_collection_choices(run_id,selection_ciphertext)
              SELECT :child,selection_ciphertext FROM creation_lab_collection_choices WHERE run_id=:run"""),
                {"child": child, "run": run},
            )
            await self.execution.event(session, child, uuid5(child, "draft.created"), "draft.created")
            trace = uuid5(child, "continuation")
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,'continuation','evidence',:payload)"""),
                {
                    "id": trace,
                    "run": child,
                    "payload": self.drafts.cipher.seal(
                        {"value": {"parent_run_id": str(run), "questions": questions, **body.model_dump(mode="json")}}
                    ),
                },
            )
            await self.execution.event(session, child, uuid5(child, "continuation.recorded"), "trace.recorded", trace)
            if parent["state"] == "awaiting_approval":
                await self.execution.finish_locked(session, parent, "cancelled", "CREATION_LAB_CONTINUED")
            return self.drafts.present(dict(row))
