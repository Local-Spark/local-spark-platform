"""Owner deletion and expiry never expose another business's materials."""

from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.adapters.material_media import MaterialError
from app.db.session import Database
from app.main import create_app
from app.services.whatsapp_retention import (
    claim_expired_assets,
    claim_upload_intents,
    finish_purge,
    finish_upload_reconcile,
    purge_expired_raw,
    purge_once,
)
from app.tests.unit.test_core import access_token


async def test_owner_request_is_private_and_purge_retries_storage(admin, database, auth_database, seeded, settings):
    first, second = uuid4(), uuid4()
    event, other_event = uuid4(), uuid4()
    async with admin.begin() as connection:
        for tenant, business, asset, key in (
            (seeded["t1"], first, event, "private/first"),
            (seeded["t2"], second, other_event, "private/second"),
        ):
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
                text("""INSERT INTO whatsapp_material_assets
                  (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type)
                  VALUES(:id,:tenant,:business,'video','cipher',:key,'video/mp4')"""),
                {"id": asset, "tenant": tenant, "business": business, "key": key},
            )
    app = create_app(settings, database, auth_database)
    base = f"/api/v1/organizations/{seeded['t1']}/businesses/{first}/whatsapp-materials"
    owner = {"Authorization": f"Bearer {access_token(settings, seeded['a1'])}"}
    foreign = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    router = Database(settings, correlator=True)
    try:
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
        ):
            assert (await client.get(base, headers=owner)).json()["items"][0]["id"] == str(event)
            assert (await client.delete(f"{base}/{event}", headers=foreign)).status_code == 403
            assert (await client.delete(f"{base}/{other_event}", headers=owner)).status_code == 404
            for _ in range(2):
                response = await client.delete(f"{base}/{event}", headers=owner)
                assert response.status_code == 409
                assert response.json()["error_code"] == "WHATSAPP_MATERIAL_DELETE_UNAVAILABLE"
            assert (await client.get(base, headers=owner)).json()["items"][0]["id"] == str(event)
        # Simulate an existing historical deletion request; production migration
        # explicitly blocks such records pending review instead of creating one.
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:id"),
                {"id": event},
            )
        storage = AsyncMock()
        storage.delete.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        assert await purge_once(router, storage, uuid4()) == 0
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_material_assets")) == 2
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": event},
            )
        storage.delete.side_effect = None
        assert await purge_once(router, storage, uuid4()) == 1
        storage.delete.assert_awaited_with("private/first")
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_material_assets")) == 1
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:id"), {"id": other_event}
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("""SELECT count(*) FROM audit_events WHERE operation_id=:id
                  AND action='whatsapp.material_delete_requested'"""),
                    {"id": event},
                )
                == 0
            )
    finally:
        await router.close()


@pytest.mark.parametrize("kind", ["text", "image", "audio", "video"])
async def test_whatsapp_material_cannot_be_deleted_via_api(admin, database, auth_database, seeded, settings, kind):
    business, photo = uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles(tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": seeded["t1"], "business": business},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
              (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type)
              VALUES(:id,:tenant,:business,:kind,'cipher','private/material','image/png')"""),
            {"id": photo, "tenant": seeded["t1"], "business": business, "kind": kind},
        )
    app = create_app(settings, database, auth_database)
    base = f"/api/v1/organizations/{seeded['t1']}/businesses/{business}/whatsapp-materials"
    owner = {"Authorization": f"Bearer {access_token(settings, seeded['a1'])}"}
    foreign = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
    ):
        assert (await client.delete(f"{base}/{photo}", headers=foreign)).status_code == 403
        assert (await client.delete(f"{base}/{uuid4()}", headers=owner)).status_code == 404
        for _ in range(2):
            response = await client.delete(f"{base}/{photo}", headers=owner)
            assert response.status_code == 409
            assert response.json()["error_code"] == "WHATSAPP_MATERIAL_DELETE_UNAVAILABLE"
        assert [item["id"] for item in (await client.get(base, headers=owner)).json()["items"]] == [str(photo)]
    async with admin.connect() as connection:
        assert await connection.scalar(
            text("SELECT delete_requested_at IS NULL FROM whatsapp_material_assets WHERE id=:id"), {"id": photo}
        )
        assert (
            await connection.scalar(
                text("""SELECT count(*) FROM audit_events
              WHERE operation_id=:id AND action='whatsapp.material_delete_requested'"""),
                {"id": photo},
            )
            == 0
        )


async def test_manual_claim_fencing_preserves_expired_material_and_cleans_unattributed_inbox(admin, seeded, settings):
    business, event, raw = uuid4(), uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
              (id,tenant_id,business_id,kind,ciphertext,expires_at)
              VALUES(:id,:tenant,:business,'text','cipher',now()-interval '1 day')"""),
            {"id": event, "tenant": seeded["t1"], "business": business},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_inbox(id,dedupe_key,event_kind,ciphertext,expires_at)
              VALUES(:id,:dedupe,'message','cipher',now()-interval '1 day')"""),
            {"id": raw, "dedupe": "0" * 64},
        )
    router = Database(settings, correlator=True)
    first, second = uuid4(), uuid4()
    try:
        await purge_expired_raw(router)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_inbox WHERE id=:id"), {"id": raw}) == 0
        assert await claim_expired_assets(router, first) == []
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:id"), {"id": event}
            )
        claims = await claim_expired_assets(router, first)
        assert len(claims) == 1
        assert await claim_expired_assets(router, second) == []
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_material_assets SET delete_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": event},
            )
        newer = (await claim_expired_assets(router, second))[0]
        assert newer.fencing_token > claims[0].fencing_token
        assert not await finish_purge(router, first, claims[0])
        assert await finish_purge(router, second, newer)
        assert not await finish_purge(router, second, newer)
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:id"), {"id": event}
                )
                == 0
            )
    finally:
        await router.close()


async def test_upload_intent_reconciliation_is_fenced_and_never_claims_final_asset(admin, database, seeded, settings):
    business, orphan, attached = uuid4(), uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        for intent, key in ((orphan, "private/orphan"), (attached, "private/attached")):
            await connection.execute(
                text("""INSERT INTO whatsapp_upload_intents
                  (id,event_id,tenant_id,business_id,object_key,reconcile_after)
                  VALUES(:id,:event,:tenant,:business,:key,now()-interval '1 minute')"""),
                {"id": intent, "event": uuid4(), "tenant": seeded["t1"], "business": business, "key": key},
            )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
              (id,tenant_id,business_id,kind,ciphertext,object_key)
              VALUES(:id,:tenant,:business,'image','encrypted','private/attached')"""),
            {"id": uuid4(), "tenant": seeded["t1"], "business": business},
        )
    router = Database(settings, correlator=True)
    first, second = uuid4(), uuid4()
    try:
        async with database.transaction(seeded["t1"], seeded["a1"]) as session:
            try:
                await session.execute(text("SELECT object_key FROM whatsapp_upload_intents"))
                raise AssertionError("app role could read upload intents")
            except ProgrammingError:
                pass
        claims = await claim_upload_intents(router, first)
        assert len(claims) == 1 and claims[0].id == orphan
        assert await claim_upload_intents(router, second) == []
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_upload_intents SET delete_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": orphan},
            )
        newer = (await claim_upload_intents(router, second))[0]
        assert newer.fencing_token > claims[0].fencing_token
        assert not await finish_upload_reconcile(router, first, claims[0])
        assert await finish_upload_reconcile(router, second, newer)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_upload_intents")) == 1
            assert (
                await connection.scalar(
                    text("""SELECT count(*) FROM audit_events
                  WHERE operation_id=:id AND action='whatsapp.upload_reconciled'"""),
                    {"id": orphan},
                )
                == 1
            )
    finally:
        await router.close()
