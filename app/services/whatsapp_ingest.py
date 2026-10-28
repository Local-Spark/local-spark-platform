"""Durable, encrypted quarantine for signed WhatsApp events before channel binding."""

import base64
import hashlib
import hmac
import json
import re
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database


def sender_hash(settings: Settings, sender: str) -> str | None:
    """Blind-index an E.164 sender without storing its phone in a queryable column."""
    digits = re.sub(r"\D", "", sender)
    if not re.fullmatch(r"[1-9]\d{7,14}", digits):
        return None
    key = base64.urlsafe_b64decode(settings.meta_encryption_key.get_secret_value())  # type: ignore[union-attr]
    return hmac.new(key, f"+{digits}".encode(), hashlib.sha256).hexdigest()


async def save_events(database: Database, settings: Settings, events: list[tuple[str, str, dict[str, Any]]]) -> None:
    if not events:
        return
    cipher = Fernet(settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
    rows = [
        {
            "id": uuid4(),
            "key": key,
            "kind": kind,
            "ciphertext": cipher.encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode(),
            "sender_hash": sender_hash(settings, payload["from"])
            if kind == "message" and isinstance(payload.get("from"), str)
            else None,
        }
        for key, kind, payload in events
    ]
    async with database.sessions() as session, session.begin():
        await session.execute(
            text(
                "DELETE FROM whatsapp_inbox WHERE expires_at < now() AND NOT (event_kind='message' AND state='linked')"
            )
        )
        await session.execute(
            text("""INSERT INTO whatsapp_inbox(id,dedupe_key,event_kind,ciphertext,sender_hash)
            VALUES(:id,:key,:kind,:ciphertext,:sender_hash) ON CONFLICT(dedupe_key) DO NOTHING"""),
            rows,
        )
