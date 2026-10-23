"""Correlate encrypted messages to a proved business without exposing them to the API."""

import json
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database

MATERIAL_KINDS = frozenset({"text", "image", "audio", "video"})
GROUP_SECONDS = 600


def material_group(tenant: UUID, business: UUID, sender_hash: str, received_at: datetime) -> UUID:
    """A fixed ten-minute window makes group identity independent of worker order."""
    slot = int(received_at.timestamp()) // GROUP_SECONDS
    return uuid5(NAMESPACE_URL, f"whatsapp-material:v1:{tenant}:{business}:{sender_hash}:{slot}")


def material_kind(cipher: Fernet, ciphertext: str) -> str | None:
    """Treat malformed payloads and channel commands as non-material."""
    try:
        message = json.loads(cipher.decrypt(ciphertext.encode()))
    except (InvalidToken, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(message, dict):
        return None
    kind = message.get("type")
    if not isinstance(kind, str) or kind not in MATERIAL_KINDS:
        return None
    if kind == "text":
        content = message.get("text")
        if not isinstance(content, dict) or not isinstance(content.get("body"), str):
            return None
        if content["body"].strip().upper().startswith("VINCULAR "):
            return None
    return kind


async def route_once(database: Database, settings: Settings, limit: int = 25) -> int:
    """Atomically copy eligible encrypted messages into a tenant-scoped pending queue."""
    cipher = Fernet(settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
    async with database.sessions() as session, session.begin():
        await session.execute(
            text("""DELETE FROM whatsapp_material_events WHERE id IN (
              SELECT id FROM whatsapp_material_events WHERE expires_at<now()
              ORDER BY expires_at,id LIMIT 1000 FOR UPDATE SKIP LOCKED)""")
        )
        rows = (
            (
                await session.execute(
                    text("""SELECT i.id,i.ciphertext,i.expires_at,i.received_at,i.sender_hash,
                      l.tenant_id,l.business_id,l.actor_id
                      FROM whatsapp_inbox i JOIN whatsapp_channel_links l
                        ON l.sender_hash=i.sender_hash AND l.active
                      WHERE i.state='quarantined' AND i.event_kind='message'
                        AND i.received_at>=l.linked_at AND i.expires_at>now()
                      ORDER BY i.received_at,i.id LIMIT :limit FOR UPDATE OF i SKIP LOCKED"""),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        routed = 0
        for row in rows:
            kind = material_kind(cipher, row["ciphertext"])
            state = "linked" if kind else "discarded"
            if kind:
                await session.execute(
                    text("""INSERT INTO whatsapp_material_events
                      (id,tenant_id,business_id,kind,ciphertext,created_at,expires_at,sender_hash,group_id)
                      VALUES(:id,:tenant,:business,:kind,:ciphertext,:received,:expires,:sender,:group)
                      ON CONFLICT(id) DO NOTHING"""),
                    {
                        "id": row["id"],
                        "tenant": row["tenant_id"],
                        "business": row["business_id"],
                        "kind": kind,
                        "ciphertext": row["ciphertext"],
                        "expires": row["expires_at"],
                        "received": row["received_at"],
                        "sender": row["sender_hash"],
                        "group": material_group(
                            row["tenant_id"], row["business_id"], row["sender_hash"], row["received_at"]
                        ),
                    },
                )
                routed += 1
            await session.execute(
                text("UPDATE whatsapp_inbox SET state=:state WHERE id=:id"),
                {"state": state, "id": row["id"]},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:event,:action,:business)"""),
                {
                    "tenant": row["tenant_id"],
                    "actor": row["actor_id"],
                    "event": row["id"],
                    "action": "whatsapp.material_routed" if kind else "whatsapp.material_discarded",
                    "business": row["business_id"],
                },
            )
        return routed
