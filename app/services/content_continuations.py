"""Conversation linkage for the productive WhatsApp candidate workflow."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from app.services.auth import AuthError
from app.services.creative_continuation import continued_instruction
from app.services.motion_context import MotionContext
from app.services.whatsapp_materials import WhatsAppMaterialsService


async def record_continuation(session, settings, database, delivery, source: UUID, note: str):
    """Called under the delivery lock; paid effects remain in the candidate workflow."""
    tenant, business, actor = delivery["tenant_id"], delivery["business_id"], delivery["actor_id"]
    await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
    existing = (
        (
            await session.execute(
                text("SELECT * FROM content_source_continuations WHERE parent_delivery_id=:id"), {"id": delivery["id"]}
            )
        )
        .mappings()
        .one_or_none()
    )
    cipher = MotionContext(settings)
    if existing:
        if existing["source_event_id"] != source or cipher.open(existing["note_ciphertext"])["note"] != note:
            raise AuthError("CONTENT_CONTINUATION_CONFLICT", 409)
        return
    inbound = await session.scalar(
        text("""SELECT 1 FROM whatsapp_material_events WHERE id=:source
      AND tenant_id=:tenant AND business_id=:business AND sender_hash=:sender AND kind='text'
      AND state IN ('processing','processed') AND created_at>=:created
      AND (expires_at IS NULL OR expires_at>now())"""),
        {
            "source": source,
            "tenant": tenant,
            "business": business,
            "sender": delivery["recipient_hash"],
            "created": delivery["created_at"],
        },
    )
    if not inbound or delivery["delivery_state"] != "delivered" or delivery["expires_at"] <= datetime.now(UTC):
        raise AuthError("CONTENT_CONTINUATION_SOURCE_INVALID", 409)
    from app.services.editorial_briefings import EditorialBriefingService

    original = await EditorialBriefingService(settings, database)._source(
        session, tenant, business, actor, delivery["source_event_id"]
    )
    if not original:
        raise AuthError("CONTENT_CONTINUATION_SOURCE_INVALID", 409)
    questions = [delivery["message_body"]] if delivery["kind"] == "clarification" else None
    continued_instruction(original, note, questions=questions)  # bound before persisting
    await session.execute(
        text("""INSERT INTO content_source_continuations
      (source_event_id,parent_delivery_id,parent_source_id,tenant_id,business_id,actor_id,kind,note_ciphertext)
      VALUES(:source,:delivery,:parent,:tenant,:business,:actor,:kind,:note)"""),
        {
            "source": source,
            "delivery": delivery["id"],
            "parent": delivery["source_event_id"],
            "tenant": tenant,
            "business": business,
            "actor": actor,
            "kind": "reply" if questions else "adjustment",
            "note": cipher.seal({"note": note, "questions": questions}),
        },
    )
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(:tenant,:actor,:operation,'content.continuation_recorded',:business) ON CONFLICT DO NOTHING"""),
        {"tenant": tenant, "actor": actor, "operation": source, "business": business},
    )


async def apply_clarification_reply(settings, app_database, worker_database, event, message) -> bool:
    """A quoted question identifies the turn; no guess from unrelated new messages."""
    reference = message.get("context", {}).get("id") if isinstance(message.get("context"), dict) else None
    note = message.get("text", {}).get("body") if isinstance(message.get("text"), dict) else None
    if not isinstance(reference, str) or not isinstance(note, str) or not note.strip():
        return False
    async with worker_database.sessions() as session, session.begin():
        target = (
            (
                await session.execute(
                    text("""SELECT id,actor_id FROM content_deliveries WHERE provider_message_id=:reference
          AND tenant_id=:tenant AND business_id=:business AND recipient_hash=:sender AND kind='clarification'
          AND delivery_state='delivered' AND expires_at>now()"""),
                    {
                        "reference": reference,
                        "tenant": event["tenant_id"],
                        "business": event["business_id"],
                        "sender": event["sender_hash"],
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
    if target is None:
        return False
    async with app_database.transaction(event["tenant_id"], target["actor_id"]) as session:
        delivery = (
            (
                await session.execute(
                    text("SELECT * FROM content_deliveries WHERE id=:id FOR UPDATE"), {"id": target["id"]}
                )
            )
            .mappings()
            .one_or_none()
        )
        if delivery is None:
            raise AuthError("CONTENT_CONTINUATION_SOURCE_INVALID", 409)
        await record_continuation(session, settings, app_database, delivery, event["id"], note.strip())
    return True
