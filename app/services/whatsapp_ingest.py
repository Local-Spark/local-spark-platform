"""Durable, encrypted quarantine for signed WhatsApp events before channel binding."""

import json
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database


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
        }
        for key, kind, payload in events
    ]
    async with database.sessions() as session, session.begin():
        await session.execute(text("DELETE FROM whatsapp_inbox WHERE expires_at < now()"))
        await session.execute(
            text("""INSERT INTO whatsapp_inbox(id,dedupe_key,event_kind,ciphertext)
            VALUES(:id,:key,:kind,:ciphertext) ON CONFLICT(dedupe_key) DO NOTHING"""),
            rows,
        )
