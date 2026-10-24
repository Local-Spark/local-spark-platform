"""Apply signed Meta delivery receipts from the encrypted inbox exactly once."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database

RANK = {"awaiting_receipt": 0, "sent": 1, "failed": 2, "delivered": 3, "read": 4}
STATUS = frozenset(RANK) - {"awaiting_receipt"}


def receipt(payload: Any) -> tuple[str, str, str | None] | None:
    if not isinstance(payload, dict):
        return None
    message_id, state = payload.get("id"), payload.get("status")
    if not isinstance(message_id, str) or not message_id or not isinstance(state, str) or state not in STATUS:
        return None
    errors = payload.get("errors")
    first = errors[0] if isinstance(errors, list) and errors else None
    code = first.get("code") if isinstance(first, dict) else None
    safe_code = str(code) if type(code) is int and 0 <= code < 10**12 else None
    return message_id, state, safe_code if state == "failed" else None


async def process_receipts(database: Database, settings: Settings, limit: int = 25) -> int:
    """Use receipt identity plus inbox row locking; never infer delivery from POST success."""
    cipher = Fernet(settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""SELECT id,ciphertext,received_at FROM whatsapp_inbox
                      WHERE event_kind='status' AND state='quarantined'
                        AND expires_at>now() ORDER BY received_at,id LIMIT :limit
                      FOR UPDATE SKIP LOCKED"""),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        processed = 0
        for row in rows:
            try:
                parsed = receipt(json.loads(cipher.decrypt(row["ciphertext"].encode())))
            except (InvalidToken, ValueError, UnicodeDecodeError):
                parsed = None
            if parsed is None:
                await session.execute(
                    text("UPDATE whatsapp_inbox SET state='discarded' WHERE id=:id"), {"id": row["id"]}
                )
                processed += 1
                continue
            provider_id, state, code = parsed
            matched = (
                (
                    await session.execute(
                        text("""SELECT id,tenant_id,business_id,provider_message_id,
                          delivery_state,ack_delivery_state FROM editorial_whatsapp_replies
                          WHERE (provider_message_id=:provider OR ack_provider_message_id=:provider)
                          FOR UPDATE"""),
                        {"provider": provider_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if matched is None:
                # A status can race the commit that stores the POST response.
                if row["received_at"] <= datetime.now(UTC) - timedelta(minutes=2):
                    await session.execute(
                        text("UPDATE whatsapp_inbox SET state='discarded' WHERE id=:id"), {"id": row["id"]}
                    )
                    processed += 1
                continue
            ack = matched["provider_message_id"] != provider_id
            column = "ack_delivery_state" if ack else "delivery_state"
            if RANK[state] > RANK[matched[column]]:
                prefix = "ack_" if ack else ""
                await session.execute(
                    text(f"""UPDATE editorial_whatsapp_replies
                      SET {prefix}delivery_state=:state,{prefix}delivery_at=:received,
                        {prefix}provider_error_code=:code WHERE id=:id"""),
                    {"state": state, "received": row["received_at"], "code": code, "id": matched["id"]},
                )
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      SELECT :tenant,d.actor_id,:receipt,:action,:business
                      FROM editorial_conversation_decisions d WHERE d.id=:decision"""),
                    {
                        "tenant": matched["tenant_id"],
                        "receipt": row["id"],
                        "action": "whatsapp.ack_" + state if ack else "whatsapp.reply_" + state,
                        "business": matched["business_id"],
                        "decision": matched["id"],
                    },
                )
            await session.execute(text("UPDATE whatsapp_inbox SET state='linked' WHERE id=:id"), {"id": row["id"]})
            processed += 1
        return processed
