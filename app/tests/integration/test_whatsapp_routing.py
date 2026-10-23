"""Signed-inbox follow-on routing through a narrow DB role, with real PostgreSQL."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.session import Database
from app.services.whatsapp_ingest import save_events, sender_hash
from app.services.whatsapp_routing import route_once

pytestmark = pytest.mark.integration


async def test_routing_is_tenant_scoped_durable_private_and_concurrent(admin, database, seeded, settings):
    key = Fernet.generate_key().decode()
    config = settings.model_copy(update={"meta_webhook_mode": "cloud", "meta_encryption_key": SecretStr(key)})
    businesses = (uuid4(), uuid4())
    phones = ("5511999999999", "5521999999999")
    async with admin.begin() as connection:
        for tenant, actor, business, phone in zip(
            (seeded["t1"], seeded["t2"]), (seeded["a1"], seeded["a2"]), businesses, phones, strict=True
        ):
            await connection.execute(
                text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
                {"id": business, "tenant": tenant},
            )
            await connection.execute(
                text("""INSERT INTO business_profiles
                (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
                VALUES(:tenant,:business,'Food','Rio','Test',:phone,true,'#6557ed')"""),
                {"tenant": tenant, "business": business, "phone": "+" + phone},
            )
            await connection.execute(
                text("""INSERT INTO whatsapp_channel_links
                (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
                VALUES(:tenant,:business,:actor,:sender,:proof,now()-interval '1 minute')"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "sender": sender_hash(config, phone),
                    "proof": uuid4(),
                },
            )
    meta = Database(config, meta=True)
    router1 = Database(config, correlator=True)
    router2 = Database(config, correlator=True)
    try:
        await save_events(
            meta,
            config,
            [
                ("routed-text", "message", {"from": phones[0], "type": "text", "text": {"body": "Oferta"}}),
                ("routed-photo", "message", {"from": phones[0], "type": "image", "image": {"id": "photo"}}),
                ("routed-image", "message", {"from": phones[1], "type": "image", "image": {"id": "media"}}),
                ("link-command", "message", {"from": phones[0], "type": "text", "text": {"body": "VINCULAR abc"}}),
                ("unsupported", "message", {"from": phones[0], "type": "reaction"}),
                ("unknown-sender", "message", {"from": "5531999999999", "type": "text", "text": {"body": "x"}}),
            ],
        )
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO whatsapp_material_events
                (id,tenant_id,business_id,kind,ciphertext,expires_at)
                VALUES(:id,:tenant,:business,'text','old',:expired)"""),
                {
                    "id": uuid4(),
                    "tenant": seeded["t1"],
                    "business": businesses[0],
                    "expired": datetime.now(UTC) - timedelta(days=1),
                },
            )
        results = await asyncio.gather(route_once(router1, config), route_once(router2, config))
        assert sum(results) == 3
        assert await route_once(router1, config) == 0
        async with admin.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        text("""SELECT id,tenant_id,business_id,kind,ciphertext,state,group_id
                          FROM whatsapp_material_events""")
                    )
                )
                .mappings()
                .all()
            )
            assert len(rows) == 3
            assert {(r["tenant_id"], r["business_id"], r["kind"]) for r in rows} == {
                (seeded["t1"], businesses[0], "text"),
                (seeded["t1"], businesses[0], "image"),
                (seeded["t2"], businesses[1], "image"),
            }
            first_group = {r["group_id"] for r in rows if r["business_id"] == businesses[0]}
            second_group = {r["group_id"] for r in rows if r["business_id"] == businesses[1]}
            assert len(first_group) == len(second_group) == 1
            assert first_group != second_group
            assert all("Oferta" not in r["ciphertext"] for r in rows)
            states = (
                await connection.execute(text("SELECT dedupe_key,state FROM whatsapp_inbox ORDER BY dedupe_key"))
            ).all()
            assert sorted(state for _, state in states) == [
                "discarded",
                "discarded",
                "linked",
                "linked",
                "linked",
                "quarantined",
            ]
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='whatsapp.material_routed'")
                )
                == 3
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='whatsapp.material_discarded'")
                )
                == 2
            )
        async with database.sessions() as session:
            with pytest.raises(ProgrammingError):
                await session.execute(text("SELECT * FROM whatsapp_material_events"))
        async with meta.sessions() as session:
            with pytest.raises(ProgrammingError):
                await session.execute(text("SELECT * FROM whatsapp_material_events"))
    finally:
        await meta.close()
        await router1.close()
        await router2.close()
