"""Signed callback -> restricted encrypted inbox, using the dedicated _test database."""

import asyncio
import hashlib
import hmac
import json
import os
from uuid import uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.session import Database
from app.main import create_app

pytestmark = pytest.mark.integration


async def test_signed_event_is_encrypted_deduplicated_and_isolated(admin, database, auth_database, settings):
    key = Fernet.generate_key()
    config = settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_database_url": SecretStr(os.environ["TEST_META_DATABASE_URL"]),
            "meta_verify_token": SecretStr("verify-unit"),
            "meta_app_secret": SecretStr("app-unit"),
            "meta_waba_id": "waba-unit",
            "meta_phone_number_id": "phone-unit",
            "meta_encryption_key": SecretStr(key.decode()),
        }
    )
    body = json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba-unit",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {"phone_number_id": "phone-unit"},
                                "messages": [
                                    {
                                        "id": "wamid-unit",
                                        "from": "5511999999999",
                                        "type": "text",
                                        "text": {"body": "teste"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    ).encode()
    signature = "sha256=" + hmac.new(b"app-unit", body, hashlib.sha256).hexdigest()
    meta = Database(config, meta=True)
    app = create_app(config, database, auth_database, meta_database=meta)
    try:
        async with meta.sessions() as session, session.begin():
            await session.execute(
                text("""INSERT INTO whatsapp_inbox(id,dedupe_key,event_kind,ciphertext,expires_at)
                VALUES(:id,:key,'message','expired',now() - interval '1 day')"""),
                {"id": uuid4(), "key": "expired-unit"},
            )
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
        ):
            endpoint = "/api/v1/webhooks/whatsapp"
            headers = {"x-hub-signature-256": signature}
            assert (await client.post(endpoint, content=body, headers=headers)).status_code == 200
            assert all(
                response.status_code == 200
                for response in await asyncio.gather(
                    *(client.post(endpoint, content=body, headers=headers) for _ in range(5))
                )
            )
            assert (await client.get("/health/ready")).status_code == 200
        async with admin.connect() as connection:
            rows = (await connection.execute(text("SELECT * FROM whatsapp_inbox"))).mappings().all()
            assert len(rows) == 1
            assert rows[0]["state"] == "quarantined"
            assert "5511999999999" not in rows[0]["ciphertext"]
            assert json.loads(Fernet(key).decrypt(rows[0]["ciphertext"].encode()))["text"]["body"] == "teste"
        async with database.sessions() as session:
            with pytest.raises(ProgrammingError):
                await session.execute(text("SELECT * FROM whatsapp_inbox"))
        async with meta.sessions() as session:
            assert await session.scalar(text("SELECT count(*) FROM whatsapp_inbox")) == 1
    finally:
        await meta.close()
