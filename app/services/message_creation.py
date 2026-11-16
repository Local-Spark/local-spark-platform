"""One message-to-piece coordinator for both transports.

The legacy creation_lab_* storage names are retained for existing histories;
origin is immutable and authorization/funding/delivery are transport adapters.
"""

from contextlib import asynccontextmanager
from dataclasses import asdict, replace
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text

from app.adapters.jev_intent_ai import JevIntentProvider
from app.schemas.creation_lab import LabStart
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.creation_lab_drafts import ZERO, CreationLabDrafts
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_motion_requests import LabMotionRequests
from app.services.creative_catalog_resolution import CatalogIntent, resolve_catalog_context
from app.services.motion_context import MotionContext, digest

MESSAGE_FORMATS = ("photo", "story", "reel")


def message_text(cipher, row):
    return cipher.open(row.get("normalized_message_ciphertext") or row["instruction_ciphertext"])["instruction"]


class MessageCreation:
    def __init__(self, settings, database, run):
        self.settings, self.database, self.run = settings, database, run
        self.execution = CreationLabExecution(self.settings, database)
        self.cipher = MotionContext(self.settings)

    async def authorize(self, session, row):
        await session.execute(
            text("SELECT set_config('app.tenant_id',:tenant,true),set_config('app.creation_lab_run_id',:run,true)"),
            {"tenant": str(row["tenant_id"]), "run": str(self.run)},
        )
        if row["origin"] == "whatsapp":
            from app.services.editorial_proposals import _access_sql
            from app.services.whatsapp_materials import WhatsAppMaterialsService

            await WhatsAppMaterialsService._require_owner(
                session, row["tenant_id"], row["business_id"], row["actor_id"]
            )
            if not await session.scalar(
                text(_access_sql()), {"tenant": row["tenant_id"], "live": self.settings.environment == "production"}
            ):
                raise AuthError("PLAN_REQUIRED", 403)
            if not await session.scalar(
                text("""SELECT 1 FROM whatsapp_material_events e
                JOIN whatsapp_material_assets a ON a.id=e.id
                JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id AND l.business_id=e.business_id AND l.sender_hash=e.sender_hash
                WHERE e.id=:source AND e.tenant_id=:tenant AND e.business_id=:business AND e.state='processed'
                  AND l.active AND l.actor_id=:actor AND a.delete_requested_at IS NULL
                  AND (e.expires_at IS NULL OR e.expires_at>now()) AND (a.expires_at IS NULL OR a.expires_at>now())"""),
                {
                    "source": row["source_event_id"],
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "actor": row["actor_id"],
                },
            ):
                raise AuthError("MESSAGE_SOURCE_UNAVAILABLE", 409)
            invalid = await session.scalar(
                text("""SELECT 1 FROM creation_lab_attachments m WHERE m.run_id=:run
                AND NOT EXISTS(SELECT 1 FROM whatsapp_material_assets a WHERE a.tenant_id=:tenant AND a.business_id=:business
                  AND a.object_key=m.object_key AND a.sha256=m.sha256 AND a.delete_requested_at IS NULL
                  AND (a.expires_at IS NULL OR a.expires_at>now())) LIMIT 1"""),
                {"run": self.run, "tenant": row["tenant_id"], "business": row["business_id"]},
            )
            if invalid:
                raise AuthError("MESSAGE_MATERIAL_UNAVAILABLE", 409)
        from app.services.service_agreement_scope import accepted_agreement_sql

        if not await session.scalar(
            text(f"SELECT {accepted_agreement_sql()}"), {"tenant": row["tenant_id"], "business": row["business_id"]}
        ):
            raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
        if row["origin"] == "lab":
            from app.services.creation_lab_settings import lab_settings

            self.settings = lab_settings(self.settings)
            self.execution.settings = self.settings
            if not self.settings.creation_lab_execution_enabled:
                raise AuthError("CREATION_LAB_EXECUTION_DISABLED", 409)
        if (
            not self.settings.typesafe_api_key
            or self.settings.intent_ai_mode != "jev"
            or self.settings.intent_ai_input_rate_usd_micros <= 0
        ):
            raise AuthError("MESSAGE_CREATION_NOT_CONFIGURED", 409)

    async def materials(self, session):
        return [
            dict(x)
            for x in (
                await session.execute(
                    text("SELECT * FROM creation_lab_attachments WHERE run_id=:run AND active ORDER BY id"),
                    {"run": self.run},
                )
            ).mappings()
        ]

    async def start(self, actor, body):
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run, "creation.message.start")
            await self.authorize(session, row)
            fingerprint = digest(body.model_dump(mode="json"))
            if row["start_hash"]:
                if row["start_hash"] != fingerprint:
                    raise AuthError("CREATION_LAB_START_CONFLICT", 409)
                return CreationLabDrafts(self.settings, self.database).present(dict(row))
            if row["state"] != "draft":
                raise AuthError("CREATION_LAB_DRAFT_REQUIRED", 409)
            materials = await self.materials(session)
            if not materials and not message_text(self.cipher, row).strip():
                raise AuthError("MESSAGE_EMPTY", 422)
            if len(materials) > 1:
                raise AuthError("MESSAGE_ONE_ATTACHMENT_REQUIRED", 422)
            if any(x["state"] != "ready" for x in materials):
                raise AuthError("CREATION_LAB_UPLOAD_UNRESOLVED", 409)
            if body.source_attachment_id is not None and body.source_attachment_id not in {x["id"] for x in materials}:
                raise AuthError("MESSAGE_ATTACHMENT_UNAVAILABLE", 409)
            minimum = (64000 * self.settings.intent_ai_input_rate_usd_micros + 999999) // 1000000
            if row["budget_usd_micros"] < minimum:
                raise AuthError("CREATION_LAB_RUN_BUDGET_EXCEEDED", 409)
            await session.execute(
                text("UPDATE creation_lab_runs SET state='queued',start_hash=:hash WHERE id=:run"),
                {"hash": fingerprint, "run": self.run},
            )
            await self.execution.event(session, self.run, uuid5(self.run, "queued"), "run.queued")
            await _event(session, row["tenant_id"], row["business_id"], actor, self.run, "creation_lab.requested")
            result = dict(row) | {"state": "queued"}
        return CreationLabDrafts(self.settings, self.database).present(result)

    async def execute(self, event):
        from app.services.creation_lab_images import LabImageRequests, LabImageRunner

        actor = UUID(event.actor_id)
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.execution.guard(session, actor, self.run, "creation.message.execute")
            if (str(row["tenant_id"]), str(row["business_id"])) != (event.tenant_id, event.business_id):
                raise AuthError("CREATION_LAB_EVENT_MISMATCH", 409)
            if row["state"] != "queued":
                return "already_claimed"
            await self.authorize(session, row)
            token = uuid4()
            await session.execute(
                text(
                    "UPDATE creation_lab_runs SET state='running',execution_token=:token,execution_event_id=:event WHERE id=:run"
                ),
                {"token": token, "event": uuid5(self.run, "motion.requested"), "run": self.run},
            )
            row = dict(row) | {"state": "running", "execution_token": token}
            await self.execution.event(session, self.run, uuid5(self.run, "interpreting"), "run.interpreting")
            materials = await self.materials(session)
        image_requests = LabImageRequests(self.settings, self.database, self.run, administrative=row["origin"] == "lab")
        image_runner = LabImageRunner(image_requests)

        async def authorize(session):
            fresh = await self.execution.guard(session, actor, self.run, "creation.message.effect")
            self.execution.fence(fresh, token)
            await self.authorize(session, fresh)
            if await self.materials(session) != materials:
                raise AuthError("CREATION_LAB_CONTEXT_CHANGED", 409)

        outer = self

        class ScopedCatalog:
            @asynccontextmanager
            async def transaction(self, tenant, owner):
                async with outer.database.transaction(tenant, owner) as session:
                    await authorize(session)
                    yield session

        class Interpreter:
            async def interpret(self, message, candidates):
                provider = JevIntentProvider(outer.settings.typesafe_api_key, outer.settings.intent_ai_model)
                operation = uuid5(outer.run, "message-intent")
                payload = provider.prepare(message, candidates, list(MESSAGE_FORMATS))[0]
                reserve = (64000 * outer.settings.intent_ai_input_rate_usd_micros + 999999) // 1000000
                await outer.execution.claim(
                    actor,
                    outer.run,
                    token,
                    operation,
                    "catalog",
                    payload,
                    reserve=reserve,
                    provider="jev",
                    model=outer.settings.intent_ai_model,
                    authorize=authorize,
                )
                await outer.execution.submitted(actor, outer.run, token, operation)
                answer = await provider.interpret(
                    message,
                    candidates,
                    list(MESSAGE_FORMATS),
                    operation,
                    response_observer=image_runner.observer(row, token, operation),
                )
                await outer.execution.received(
                    actor,
                    outer.run,
                    token,
                    operation,
                    asdict(answer),
                    (answer.input_tokens * outer.settings.intent_ai_input_rate_usd_micros + 999999) // 1000000,
                )
                return CatalogIntent(
                    answer.decision,
                    answer.offering_id,
                    answer.intent,
                    "short_video" if answer.format == "reel" else answer.format,
                )

        try:
            message = message_text(self.cipher, row)
            if materials and materials[0]["kind"] == "audio" and not row.get("normalized_message_ciphertext"):
                from app.services.message_creation_audio import transcribe_message

                transcript = await transcribe_message(self, row, token, materials[0], authorize)
                message = (message + "\n" + transcript).strip()
                if len(message) > 4000:
                    raise AuthError("MESSAGE_TOO_LONG", 422)
                async with self.database.transaction(ZERO, actor) as session:
                    await authorize(session)
                    encoded = self.cipher.seal({"instruction": message})
                    await session.execute(
                        text("UPDATE creation_lab_runs SET normalized_message_ciphertext=:value WHERE id=:run"),
                        {"value": encoded, "run": self.run},
                    )
                    row["normalized_message_ciphertext"] = encoded
            resolution = await resolve_catalog_context(
                ScopedCatalog(),
                row["tenant_id"],
                row["business_id"],
                actor,
                message,
                Interpreter(),
                interpret_unmatched=True,
                execution_run=self.run,
            )
            await self.execution.evidence(
                actor, self.run, token, uuid5(self.run, "intent-resolution"), "catalog", asdict(resolution)
            )
            if resolution.status not in {"resolved", "none"} or resolution.intent != "content_request":
                if resolution.status in {
                    "invalid_decision",
                    "interpreter_unavailable",
                    "budget_blocked",
                    "context_changed",
                }:
                    raise AuthError("MESSAGE_INTENT_" + resolution.status.upper(), 409)
                await image_runner.pause(
                    row,
                    token,
                    "catalog",
                    {
                        "questions": [
                            "O que você quer divulgar e em qual formato? Confirme os detalhes necessários para criar a peça."
                        ]
                    },
                )
                return "awaiting_reply"
            catalog = resolution.snapshot
            kind = materials[0]["kind"] if materials else "text"
            from app.services.message_creation_format import message_format

            fmt = message_format(message, resolution.format, kind)
            if fmt not in MESSAGE_FORMATS:
                await image_runner.pause(
                    row, token, "catalog", {"questions": ["Você quer um post no feed, um story estático ou um reel?"]}
                )
                return "awaiting_reply"
            if fmt == "reel" and kind != "video":
                await image_runner.pause(
                    row, token, "catalog", {"questions": ["Envie o vídeo que deseja usar para criar o reel."]}
                )
                return "awaiting_reply"
            if fmt != "reel" and kind == "video":
                await image_runner.pause(
                    row,
                    token,
                    "catalog",
                    {
                        "questions": [
                            "Para a peça estática, envie uma foto ou confirme que deseja criar um reel com esse vídeo."
                        ]
                    },
                )
                return "awaiting_reply"
            requests = (
                LabMotionRequests(self.settings, self.database, self.run, administrative=row["origin"] == "lab")
                if fmt == "reel"
                else image_requests
            )
            body = LabStart(operation_id=self.run, source_attachment_id=materials[0]["id"] if kind == "video" else None)
            async with self.database.transaction(ZERO, actor) as session:
                await authorize(session)
                row["format"] = fmt
                await session.execute(
                    text("UPDATE creation_lab_runs SET format=:format WHERE id=:run"), {"format": fmt, "run": self.run}
                )
                await requests._admission(session, row["tenant_id"], row["business_id"])
                snapshot = await requests.build_snapshot(session, row, body)
                snapshot["execution"]["request_budget"] = row["budget_usd_micros"]
                trace = uuid5(self.run, "snapshot")
                await session.execute(
                    text(
                        "INSERT INTO creation_lab_trace(id,run_id,stage,slot,payload_ciphertext) VALUES(:id,:run,'context','evidence',:value)"
                    ),
                    {"id": trace, "run": self.run, "value": self.cipher.seal({"value": snapshot})},
                )
                fingerprint = self.cipher.fingerprint(snapshot)
                await session.execute(
                    text(
                        "UPDATE creation_lab_runs SET snapshot_trace_id=:trace,source_fingerprint=:hash WHERE id=:run"
                    ),
                    {"trace": trace, "hash": fingerprint, "run": self.run},
                )
                row.update(
                    snapshot_trace_id=trace,
                    source_fingerprint=fingerprint,
                    snapshot_ciphertext=self.cipher.seal(snapshot),
                    operation_id=self.run,
                )
                await self.execution.event(
                    session, self.run, uuid5(self.run, "context-ready"), "run.context_ready", trace
                )
                if fmt == "reel":
                    await session.execute(
                        text("UPDATE creation_lab_runs SET state='queued',execution_token=NULL WHERE id=:run"),
                        {"run": self.run},
                    )
            translated = replace(event, event_id=str(uuid5(self.run, "motion.requested")))
            if fmt == "reel":
                from app.services.creation_lab_motion_output import LabMotionOrchestrator
                from app.services.motion_runtime import build_motion_runner

                productive = build_motion_runner(
                    self.settings,
                    self.database,
                    self.database,
                    requests=requests,
                    administrative=row["origin"] == "lab",
                )
                return await LabMotionOrchestrator(productive, self.run).run(translated)
            # There is no administrative catalog/editorial approval in message creation.
            return await image_runner.run(translated, "catalog_approved", prepared=(row, token, {"catalog": catalog}))
        except BaseException as exc:
            code = getattr(exc, "code", "MESSAGE_CREATION_FAILED")
            # The motion runner owns its new fence after dispatch.
            async with self.database.transaction(ZERO, actor) as session:
                fresh = await self.execution.guard(session, actor, self.run, "creation.message.fail")
                if fresh["state"] == "running" and fresh["execution_token"] == token:
                    await self.execution.finish_locked(session, fresh, "failed", code)
            raise
