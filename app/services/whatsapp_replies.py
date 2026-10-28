"""Claim and submit editorial replies once; uncertain calls require manual reconciliation."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import httpx
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.adapters.meta_whatsapp_send import send_text
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.editorial_conversation import EditorialConversationService

logger = logging.getLogger("meu_braco_direito.whatsapp_replies")


@dataclass(frozen=True)
class ClaimedReply:
    id: UUID
    recipient_ciphertext: str
    body: str
    ack: bool = False


async def _audit_reply(session: Any, reply_id: UUID, action: str) -> None:
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          SELECT d.tenant_id,d.actor_id,d.id,:action,d.business_id
          FROM editorial_conversation_decisions d WHERE d.id=:id
          ON CONFLICT DO NOTHING"""),
        {"id": reply_id, "action": action},
    )


async def _within_daily_limit(session: Any, tenant_id: UUID, limit: int) -> bool:
    """Serialize reservations per tenant and UTC day before the paid API call."""
    await session.execute(
        text("""SELECT pg_advisory_xact_lock(hashtextextended(
          'meta-outbound:' || CAST(:tenant AS text) || ':' ||
          CAST((now() AT TIME ZONE 'UTC')::date AS text),0))"""),
        {"tenant": str(tenant_id)},
    )
    used = await session.scalar(
        text("""SELECT
          (SELECT count(*) FROM editorial_whatsapp_replies
            WHERE tenant_id=:tenant AND attempted_at>=
              date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC') +
          (SELECT count(*) FROM editorial_whatsapp_replies
            WHERE tenant_id=:tenant AND ack_attempted_at>=
              date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC')"""),
        {"tenant": tenant_id},
    )
    return cast(int, used) < limit


async def _defer_to_tomorrow(session: Any, reply_id: UUID, *, ack: bool) -> None:
    column = "ack_next_attempt_at" if ack else "next_attempt_at"
    await session.execute(
        text(f"""UPDATE editorial_whatsapp_replies SET {column}=
          (date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC') + interval '1 day'
          WHERE id=:id"""),
        {"id": reply_id},
    )


async def _defer_for_agreement(session: Any, reply_id: UUID, *, ack: bool) -> None:
    """Let another business progress while this business awaits its agreement."""
    column = "ack_next_attempt_at" if ack else "next_attempt_at"
    await session.execute(
        text(f"UPDATE editorial_whatsapp_replies SET {column}=now()+interval '1 minute' WHERE id=:id"),
        {"id": reply_id},
    )


async def claim_reply(database: Database, settings: Settings) -> ClaimedReply | None:
    async with database.sessions() as session, session.begin():
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies SET state='uncertain',error_code='META_RESULT_UNKNOWN'
              WHERE state='submitting' AND attempted_at<now()-interval '2 minutes'""")
        )
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies SET ack_state='uncertain',ack_error_code='META_RESULT_UNKNOWN'
              WHERE ack_state='submitting' AND ack_attempted_at<now()-interval '2 minutes'""")
        )
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies SET state='expired',error_code='WINDOW_EXPIRED'
              WHERE state='pending' AND expires_at<=now()""")
        )
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies SET ack_state='expired',ack_error_code='WINDOW_EXPIRED'
              WHERE ack_state='pending' AND expires_at<=now()""")
        )
        await session.execute(
            text("""DELETE FROM editorial_whatsapp_replies
              WHERE created_at<now()-interval '30 days' AND state IN ('accepted','uncertain','failed','expired')""")
        )
        row = (
            (
                await session.execute(
                    text("""SELECT r.id,r.tenant_id,r.business_id,r.recipient_ciphertext,d.reply
                      FROM editorial_whatsapp_replies r JOIN editorial_conversation_decisions d ON d.id=r.id
                      JOIN whatsapp_channel_links l ON l.tenant_id=r.tenant_id
                        AND l.business_id=r.business_id AND l.sender_hash=r.sender_hash
                      JOIN whatsapp_processing_consents c ON c.tenant_id=r.tenant_id
                        AND c.business_id=r.business_id
                      JOIN whatsapp_material_events e ON e.id=r.source_event_id
                      JOIN business_profiles p ON p.tenant_id=r.tenant_id AND p.business_id=r.business_id
                      JOIN memberships m ON m.tenant_id=r.tenant_id AND m.actor_id=l.actor_id
                      JOIN user_accounts u ON u.id=l.actor_id
                      WHERE r.state='pending' AND r.expires_at>now() AND r.next_attempt_at<=now()
                        AND d.state='awaiting_confirmation' AND l.active AND c.revoked_at IS NULL
                        AND l.linked_at<=e.created_at AND p.phone_verified
                        AND m.role='owner' AND m.active AND u.active
                        AND (EXISTS(SELECT 1 FROM billing_sponsorships s
                          WHERE s.tenant_id=r.tenant_id AND s.revoked_at IS NULL
                            AND s.starts_at<=now() AND s.ends_at>now())
                        OR EXISTS(SELECT 1 FROM billing_accounts b
                          WHERE b.tenant_id=r.tenant_id AND b.livemode=:live
                            AND b.status='active' AND NOT b.blocked AND b.paid_until>now()))
                      ORDER BY r.created_at,r.id LIMIT 1 FOR UPDATE OF r SKIP LOCKED"""),
                    {"live": settings.environment == "production"},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if settings.service_agreement_required or settings.environment == "production":
            from app.services.service_agreement import service_agreement_allowed

            if not await service_agreement_allowed(
                session, settings, row["tenant_id"], row["business_id"], worker=True
            ):
                await _defer_for_agreement(session, row["id"], ack=False)
                return None
        if not await _within_daily_limit(session, row["tenant_id"], settings.meta_daily_message_limit):
            await _defer_to_tomorrow(session, row["id"], ack=False)
            await _audit_reply(session, row["id"], "whatsapp.reply_budget_deferred")
            return None
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies
              SET state='submitting',attempted_at=now() WHERE id=:id"""),
            {"id": row["id"]},
        )
        await _audit_reply(session, row["id"], "whatsapp.reply_submitting")
        return ClaimedReply(row["id"], row["recipient_ciphertext"], row["reply"])


async def claim_ack(database: Database, settings: Settings) -> ClaimedReply | None:
    async with database.sessions() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("""SELECT r.id,r.tenant_id,r.business_id,r.recipient_ciphertext,d.reply
                      FROM editorial_whatsapp_replies r JOIN editorial_conversation_decisions d ON d.id=r.id
                      JOIN whatsapp_channel_links l ON l.tenant_id=r.tenant_id
                        AND l.business_id=r.business_id AND l.sender_hash=r.sender_hash
                      JOIN whatsapp_processing_consents c ON c.tenant_id=r.tenant_id
                        AND c.business_id=r.business_id
                      JOIN business_profiles p ON p.tenant_id=r.tenant_id AND p.business_id=r.business_id
                      JOIN memberships m ON m.tenant_id=r.tenant_id AND m.actor_id=l.actor_id
                      JOIN user_accounts u ON u.id=l.actor_id
                      WHERE r.ack_state='pending' AND r.ack_next_attempt_at<=now()
                        AND r.expires_at>now() AND r.state='accepted' AND r.delivery_state<>'failed'
                        AND d.state IN ('confirmed','discarded') AND d.actor_id=l.actor_id
                        AND l.active AND c.revoked_at IS NULL
                        AND p.phone_verified AND m.role='owner' AND m.active AND u.active
                        AND (EXISTS(SELECT 1 FROM billing_sponsorships s
                          WHERE s.tenant_id=r.tenant_id AND s.revoked_at IS NULL
                            AND s.starts_at<=now() AND s.ends_at>now())
                        OR EXISTS(SELECT 1 FROM billing_accounts b
                          WHERE b.tenant_id=r.tenant_id AND b.livemode=:live
                            AND b.status='active' AND NOT b.blocked AND b.paid_until>now()))
                      ORDER BY r.created_at,r.id LIMIT 1 FOR UPDATE OF r SKIP LOCKED"""),
                    {"live": settings.environment == "production"},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if settings.service_agreement_required or settings.environment == "production":
            from app.services.service_agreement import service_agreement_allowed

            if not await service_agreement_allowed(
                session, settings, row["tenant_id"], row["business_id"], worker=True
            ):
                await _defer_for_agreement(session, row["id"], ack=True)
                return None
        if not await _within_daily_limit(session, row["tenant_id"], settings.meta_daily_message_limit):
            await _defer_to_tomorrow(session, row["id"], ack=True)
            await _audit_reply(session, row["id"], "whatsapp.ack_budget_deferred")
            return None
        await session.execute(
            text("""UPDATE editorial_whatsapp_replies SET ack_state='submitting',ack_attempted_at=now()
              WHERE id=:id"""),
            {"id": row["id"]},
        )
        await _audit_reply(session, row["id"], "whatsapp.ack_submitting")
        return ClaimedReply(row["id"], row["recipient_ciphertext"], row["reply"], ack=True)


async def finish_reply(database: Database, reply: ClaimedReply, state: str, message_id: str | None = None) -> None:
    async with database.sessions() as session, session.begin():
        prefix = "ack_" if reply.ack else ""
        finished = await session.scalar(
            text(f"""UPDATE editorial_whatsapp_replies SET {prefix}state=:state,
              {prefix}provider_message_id=:message_id,
              {prefix}error_code=CASE WHEN :state='failed' THEN 'META_REJECTED'
                WHEN :state='uncertain' THEN 'META_RESULT_UNKNOWN' ELSE NULL END,
              {prefix}accepted_at=CASE WHEN :state='accepted' THEN now() ELSE NULL END
              WHERE id=:id AND {prefix}state='submitting' RETURNING id"""),
            {"id": reply.id, "state": state, "message_id": message_id},
        )
        if finished is not None:
            kind = "ack" if reply.ack else "reply"
            await _audit_reply(session, reply.id, f"whatsapp.{kind}_{state}")


async def dispatch_reply(database: Database, settings: Settings, client: httpx.AsyncClient) -> bool:
    if (
        not settings.meta_reply_enabled
        or not settings.meta_access_token
        or not settings.meta_graph_version
        or not settings.meta_phone_number_id
        or not settings.meta_encryption_key
    ):
        return False
    reply = await claim_reply(database, settings) or await claim_ack(database, settings)
    if reply is None:
        return False
    state, message_id = "uncertain", None
    try:
        recipient = (
            Fernet(settings.meta_encryption_key.get_secret_value().encode())
            .decrypt(reply.recipient_ciphertext.encode())
            .decode()
        )
        message_id = await send_text(settings, recipient, reply.body, client)
        state = "accepted"
    except httpx.HTTPStatusError as error:
        state = "failed" if 400 <= error.response.status_code < 500 else "uncertain"
        logger.warning(
            "whatsapp.reply_http_error", extra={"reply_id": str(reply.id), "status": error.response.status_code}
        )
    except Exception:
        logger.warning("whatsapp.reply_uncertain", extra={"reply_id": str(reply.id)})
    await finish_reply(database, reply, state, message_id)
    return True


async def apply_inbound_command(
    settings: Settings, database: Database, row: Mapping[Any, Any], message: dict[str, Any]
) -> bool:
    """Apply only an explicit reply to a known prompt from this sender and business."""
    body = message.get("text", {}).get("body", "")
    command = body.strip().casefold() if isinstance(body, str) else ""
    if command not in {"confirmar", "descartar"}:
        return False
    context = message.get("context")
    reference = context.get("id") if isinstance(context, dict) else None
    async with database.sessions() as session, session.begin():
        if isinstance(reference, str) and reference:
            matched = (
                (
                    await session.execute(
                        text("""SELECT r.id,d.actor_id FROM editorial_whatsapp_replies r
                      JOIN editorial_conversation_decisions d ON d.id=r.id
                      WHERE r.provider_message_id=:reference AND r.state='accepted'
                        AND r.delivery_state<>'failed'
                        AND r.tenant_id=:tenant AND r.business_id=:business
                        AND r.sender_hash=:sender AND d.state='awaiting_confirmation'"""),
                        {
                            "reference": reference,
                            "tenant": row["tenant_id"],
                            "business": row["business_id"],
                            "sender": row["sender_hash"],
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
        else:
            candidates = (
                (
                    await session.execute(
                        text("""SELECT r.id,d.actor_id FROM editorial_whatsapp_replies r
                          JOIN editorial_conversation_decisions d ON d.id=r.id
                          WHERE r.state='accepted' AND r.delivery_state<>'failed'
                            AND r.accepted_at>now()-interval '30 minutes'
                            AND r.tenant_id=:tenant AND r.business_id=:business
                            AND r.sender_hash=:sender AND d.state='awaiting_confirmation'
                          ORDER BY r.accepted_at DESC LIMIT 2"""),
                        {"tenant": row["tenant_id"], "business": row["business_id"], "sender": row["sender_hash"]},
                    )
                )
                .mappings()
                .all()
            )
            matched = candidates[0] if len(candidates) == 1 else None
    if matched is None:
        return True
    owner_db = Database(settings)
    try:
        try:
            await EditorialConversationService(settings, owner_db).decide(
                row["tenant_id"], row["business_id"], matched["actor_id"], matched["id"], command == "confirmar"
            )
        except AuthError as error:
            logger.warning("whatsapp.command_rejected", extra={"event_id": str(row["id"]), "error_code": error.code})
    finally:
        await owner_db.close()
    return True
