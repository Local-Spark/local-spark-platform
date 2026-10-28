"""Scratch-only tests for the partial durable material proposal."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.services.whatsapp_ingest import save_events
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.services.whatsapp_retention import purge_once

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("kind", ["text", "image", "audio", "video"])
async def test_linked_original_and_dedupe_survive_after_40_days(admin, database, seeded, settings, kind):
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    cipher = Fernet(key.encode())
    tenant, actor, business, event = seeded["t1"], seeded["a1"], uuid4(), uuid4()
    dedupe_key = "f" * 64
    payload = {
        "from": "5511999999999",
        "type": kind,
        kind: {"body": "Promoção"} if kind == "text" else {"id": "example"},
    }
    ciphertext = cipher.encrypt(json.dumps(payload).encode()).decode()
    body = cipher.encrypt("Promoção".encode()).decode()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles(tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_inbox
          (id,dedupe_key,event_kind,ciphertext,state,received_at,expires_at)
          VALUES(:id,:key,'message',:cipher,'linked',now()-interval '40 days',now()-interval '33 days')"""),
            {"id": event, "key": dedupe_key, "cipher": ciphertext},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_events
          (id,tenant_id,business_id,kind,ciphertext,state,created_at,expires_at)
          VALUES(:id,:tenant,:business,:kind,:cipher,'processed',now()-interval '40 days',NULL)"""),
            {"id": event, "tenant": tenant, "business": business, "kind": kind, "cipher": ciphertext},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
          (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type,created_at)
          VALUES(:id,:tenant,:business,:kind,:cipher,:object,:mime,now()-interval '40 days')"""),
            {
                "id": event,
                "tenant": tenant,
                "business": business,
                "kind": kind,
                "cipher": body,
                "object": None if kind == "text" else f"private/{kind}",
                "mime": None if kind == "text" else "application/octet-stream",
            },
        )
    router = Database(cfg, correlator=True)
    meta = Database(cfg, meta=True)
    store = AsyncMock()
    try:
        assert await purge_once(router, store, uuid4()) == 0
        store.delete.assert_not_awaited()
        await save_events(meta, cfg, [(dedupe_key, "message", payload)])
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_inbox WHERE dedupe_key=:key"), {"key": dedupe_key}
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_events WHERE id=:id"), {"id": event}
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:id"), {"id": event}
                )
                == 1
            )
        assert [
            item["id"] for item in await WhatsAppMaterialsService(cfg, database).list_materials(tenant, business, actor)
        ] == [event]
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert (
                await session.scalar(text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:id"), {"id": event})
                == 0
            )
    finally:
        await router.close()
        await meta.close()
