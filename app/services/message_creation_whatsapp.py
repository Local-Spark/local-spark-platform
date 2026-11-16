"""Authenticated WhatsApp input adapter for the common creation coordinator."""

import json
from uuid import UUID, uuid5

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.schemas.creation_lab import LabContinuation, LabStart
from app.services.auth import AuthError
from app.services.creation_lab_continuations import CreationLabContinuations
from app.services.creation_lab_execution import CreationLabExecution
from app.services.message_creation import MessageCreation
from app.services.motion_context import MotionContext, digest


async def enqueue_message(settings, database, worker_database, source_id: str) -> str:
    source = UUID(source_id)
    async with worker_database.sessions() as session, session.begin():
        material = (
            (
                await session.execute(
                    text("""SELECT a.*, e.ciphertext AS envelope,l.actor_id
          FROM whatsapp_material_events e JOIN whatsapp_material_assets a ON a.id=e.id
          JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id AND l.business_id=e.business_id
            AND l.sender_hash=e.sender_hash AND l.active
          WHERE e.id=:source AND e.state='processed' AND (e.expires_at IS NULL OR e.expires_at>now())
            AND a.delete_requested_at IS NULL AND (a.expires_at IS NULL OR a.expires_at>now())"""),
                    {"source": source},
                )
            )
            .mappings()
            .one_or_none()
        )
    if material is None:
        return "skipped"
    material = dict(material)
    actor, tenant, business = material["actor_id"], material["tenant_id"], material["business_id"]
    cipher = MotionContext(settings)
    transport = Fernet(settings.meta_encryption_key.get_secret_value().encode())
    instruction = transport.decrypt(material["ciphertext"].encode()).decode()
    envelope = json.loads(transport.decrypt(material["envelope"].encode()))
    reference = envelope.get("context", {}).get("id") if isinstance(envelope.get("context"), dict) else None
    operation = uuid5(source, "message-creation")
    run = uuid5(actor, f"creation-lab:{operation}")
    execution = CreationLabExecution(settings, database)
    # The durable source ID identifies retries. No second request or spend occurs.
    async with database.transaction(tenant, actor) as session:
        await session.execute(text("SELECT set_config('app.creation_lab_run_id',:run,true)"), {"run": str(run)})
        exists = await session.scalar(text("SELECT 1 FROM creation_lab_runs WHERE id=:run"), {"run": run})
        target = None
        if reference and not exists:
            target = (
                (
                    await session.execute(
                        text("""SELECT d.* FROM message_creation_deliveries d
              JOIN whatsapp_channel_links l ON l.tenant_id=d.tenant_id AND l.business_id=d.business_id
              WHERE d.provider_message_id=:reference AND d.tenant_id=:tenant AND d.business_id=:business
                AND d.actor_id=:actor AND d.recipient_hash=l.sender_hash AND l.active AND d.expires_at>now()"""),
                        {"reference": reference, "tenant": tenant, "business": business, "actor": actor},
                    )
                )
                .mappings()
                .one_or_none()
            )
    command = instruction.strip().casefold()
    if not exists and not target:
        async with database.transaction(tenant, actor) as session:
            legacy = await session.scalar(
                text("SELECT 1 FROM content_source_continuations WHERE source_event_id=:source"), {"source": source}
            )
        if legacy:
            return "legacy_continuation"
    if command in {"aprovar", "confirmar", "descartar", "pedir ajustes"}:
        # Output decisions require exact-version visual confirmation in the
        # existing review service; they never become a fresh paid creation.
        return "review_required" if target else "skipped"
    if command.startswith("pedir ajustes:") and not target and not exists:
        return "skipped"
    if target:
        if not instruction.strip():
            instruction = "Use o material desta resposta para continuar o pedido."
        await CreationLabContinuations(settings, database).create(
            actor,
            target["run_id"],
            LabContinuation(
                operation_id=operation, note=instruction, stage=target["stage"], content_sha256=target["content_sha256"]
            ),
            source_event_id=source,
            replacement_material=material if material["kind"] != "text" else None,
        )
    elif not exists:
        if reference:
            # Unrecognized quoted context must never be guessed as a new paid job.
            return "unrecognized_reply"
        if len(instruction) > 4000:
            raise AuthError("MESSAGE_TOO_LONG", 422)
        async with database.transaction(tenant, actor) as session:
            await session.execute(text("SELECT set_config('app.creation_lab_run_id',:run,true)"), {"run": str(run)})
            await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)})
            row = {
                "id": run,
                "actor_id": actor,
                "tenant_id": tenant,
                "business_id": business,
                "origin": "whatsapp",
                "source_event_id": source,
            }
            await MessageCreation(settings, database, run).authorize(session, row)
            budget = settings.visual_ai_monthly_budget_usd_micros
            if budget <= 0:
                raise AuthError("VISUAL_BUDGET_DISABLED", 409)
            inserted = await session.scalar(
                text("""INSERT INTO creation_lab_runs
              (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,instruction_ciphertext,budget_usd_micros,origin,flow_version,source_event_id)
              VALUES(:id,:actor,:tenant,:business,:operation,:hash,'auto','automatic',:instruction,:budget,'whatsapp',2,:source)
              ON CONFLICT(id) DO NOTHING RETURNING id"""),
                {
                    "id": run,
                    "actor": actor,
                    "tenant": tenant,
                    "business": business,
                    "operation": operation,
                    "hash": digest({"source": str(source)}),
                    "instruction": cipher.seal({"instruction": instruction}),
                    "budget": budget,
                    "source": source,
                },
            )
            if inserted:
                if (
                    material["kind"] == "audio"
                    and material.get("transcription_state") == "completed"
                    and material.get("transcript_ciphertext")
                ):
                    transcript = transport.decrypt(material["transcript_ciphertext"].encode()).decode()
                    normalized = (instruction + "\n" + transcript).strip()
                    if len(normalized) > 4000:
                        raise AuthError("MESSAGE_TOO_LONG", 422)
                    await session.execute(
                        text("UPDATE creation_lab_runs SET normalized_message_ciphertext=:value WHERE id=:run"),
                        {"value": cipher.seal({"instruction": normalized}), "run": run},
                    )
                if material["kind"] != "text":
                    await copy_material(session, cipher, run, material)
                await execution.event(session, run, uuid5(run, "draft.created"), "draft.created")
    await MessageCreation(settings, database, run).start(actor, LabStart(operation_id=operation))
    return "queued"


async def copy_material(session, cipher, run, material):
    identifier = uuid5(run, f"material:{material['id']}")
    await session.execute(
        text("""INSERT INTO creation_lab_attachments
      (id,run_id,operation_id,request_hash,name_ciphertext,object_key,kind,mime_type,sha256,byte_size,rights_confirmed,state)
      VALUES(:id,:run,:id,:hash,:name,:key,:kind,:mime,:sha,:size,true,'ready')"""),
        {
            "id": identifier,
            "run": run,
            "hash": digest({"source": str(material["id"]), "sha256": material["sha256"]}),
            "name": cipher.seal({"name": "Material da mensagem"}),
            "key": material["object_key"],
            "kind": material["kind"],
            "mime": material["mime_type"],
            "sha": material["sha256"],
            "size": material["size_bytes"],
        },
    )
