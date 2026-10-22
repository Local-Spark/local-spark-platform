"""Encrypted transactional mail outbox. SMTP happens outside the database transaction."""

import asyncio
import json
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import ZERO
from app.services.mail_templates import render_html


def send_mail(settings: Settings, payload: dict[str, str]) -> None:
    # Pending encrypted outbox messages may predate the rename. Keep their links
    # and action tokens intact while rendering the current product name.
    payload = {
        **payload,
        **{
            field: payload[field]
            .replace("na Local Spark", "no Meu Braço Direito")
            .replace("a Local Spark", "o Meu Braço Direito")
            .replace("Local Spark", "Meu Braço Direito")
            for field in ("subject", "body")
        },
    }
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = settings.mail_from, payload["to"], payload["subject"]
    message.set_content(payload["body"])
    html = render_html(payload)
    if html:
        message.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())  # type: ignore[union-attr]
        smtp.send_message(message)


async def deliver_once(database: Database, settings: Settings) -> bool:
    lease = uuid4()
    async with database.transaction(ZERO, ZERO) as db:
        await db.execute(
            text("""UPDATE auth_mail SET state='failed',lease_token=NULL,lease_until=NULL
        WHERE state='leased' AND lease_until<now() AND attempts>=8""")
        )
        # Expired actions/mail and limits are bounded by indexes; delivery workers also maintain their state.
        await db.execute(text("DELETE FROM auth_actions WHERE expires_at<now()"))
        await db.execute(text("DELETE FROM auth_challenges WHERE expires_at<now()"))
        await db.execute(text("DELETE FROM auth_limits WHERE expires_at<now()"))
        await db.execute(text("DELETE FROM auth_sessions WHERE expires_at<now()-interval '1 day'"))
        row = (
            (
                await db.execute(
                    text("""
UPDATE auth_mail SET state='leased',lease_token=:lease,lease_until=now()+interval '1
minute',attempts=attempts+1
WHERE id=(SELECT id FROM auth_mail WHERE ((state='pending' AND available_at<=now())
OR
(state='leased' AND lease_until<now())) AND attempts<8
ORDER BY available_at FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *
"""),
                    {"lease": lease},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return False
        item: dict[str, Any] = dict(row)
    success = True
    try:
        payload = json.loads(
            Fernet(settings.auth_encryption_key.get_secret_value().encode()).decrypt(item["ciphertext"].encode())
        )
        await asyncio.to_thread(send_mail, settings, payload)
    except Exception:
        # Never log SMTP payload, recipients, tokens, credentials or exception arguments.
        success = False
    async with database.transaction(ZERO, ZERO) as db:
        await db.execute(
            text("""
UPDATE auth_mail SET state=:state,available_at=now()+make_interval(secs=>:delay),
lease_until=NULL,lease_token=NULL
WHERE id=:id AND lease_token=:lease AND lease_until>now()
"""),
            {
                "id": item["id"],
                "lease": lease,
                "state": "sent" if success else "failed" if item["attempts"] >= 8 else "pending",
                "delay": min(3600, 2 ** item["attempts"]),
            },
        )
    return True
