"""Material processing uses restricted roles and rechecks access after routing."""

import hashlib
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.db.session import Database
from app.main import create_app
from app.services.whatsapp_ingest import save_events, sender_hash
from app.services.whatsapp_processing import MaterialClaim, MaterialProcessor, dispatch_materials, finish_dispatch
from app.services.whatsapp_retention import claim_upload_intents, reconcile_uploads
from app.services.whatsapp_routing import route_once
from app.tests.unit.test_core import access_token


async def test_text_material_consent_library_and_revocation(admin, database, auth_database, seeded, settings):
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    number = "5511999999999"
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test',:phone,true,'#6557ed')"""),
            {"tenant": tenant, "business": business, "phone": "+" + number},
        )
        await connection.execute(
            text("""INSERT INTO billing_sponsorships(id,tenant_id,actor_id,idempotency_key,reason)
              VALUES(:id,:tenant,:actor,'materials-test','Synthetic integration test')"""),
            {"id": uuid4(), "tenant": tenant, "actor": actor},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/whatsapp-materials"
    owner = {"Authorization": f"Bearer {access_token(cfg, actor)}"}
    foreign = {"Authorization": f"Bearer {access_token(cfg, seeded['a2'])}"}
    app = create_app(cfg, database, auth_database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
    ):
        assert (await client.get(base + "/consent", headers=owner)).json() == {"accepted": False}
        assert (await client.post(base + "/consent", headers=foreign, json={"accepted": True})).status_code == 403
        assert (await client.post(base + "/consent", headers=owner, json={"accepted": False})).status_code == 422
        assert (await client.post(base + "/consent", headers=owner, json={"accepted": True})).json() == {
            "accepted": True
        }
        assert (await client.post(base + "/consent", headers=owner, json={"accepted": True})).status_code == 200
        assert (await client.get(base + "/consent", headers=owner)).json() == {"accepted": True}
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO whatsapp_channel_links
                  (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
                  VALUES(:tenant,:business,:actor,:sender,:proof,now()-interval '1 minute')"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "sender": sender_hash(cfg, number),
                    "proof": uuid4(),
                },
            )
        meta = Database(cfg, meta=True)
        router = Database(cfg, correlator=True)
        try:
            await save_events(
                meta,
                cfg,
                [("idea-1", "message", {"from": number, "type": "text", "text": {"body": "Promoção de sexta"}})],
            )
            assert await route_once(router, cfg) == 1
            async with admin.connect() as connection:
                event = await connection.scalar(text("SELECT id FROM whatsapp_material_events"))
            media = AsyncMock()
            store = AsyncMock()
            processor = MaterialProcessor(cfg, router, media, store)
            assert await processor.process(event) == "processed"
            assert await processor.process(event) == "already_finished"
            media.fetch.assert_not_awaited()
            store.put.assert_not_awaited()
            response = await client.get(base, headers=owner)
            assert response.status_code == 200, response.text
            assert response.json()["items"][0]["text"] == "Promoção de sexta"
            async with admin.connect() as connection:
                group = (
                    await connection.execute(
                        text("""SELECT e.group_id,a.group_id FROM whatsapp_material_events e
                          JOIN whatsapp_material_assets a ON a.id=e.id WHERE e.id=:event"""),
                        {"event": event},
                    )
                ).one()
            assert response.json()["items"][0]["group_id"] == str(group[0])
            assert group[0] == group[1]
            async with admin.begin() as connection:
                await connection.execute(text("DELETE FROM whatsapp_material_events WHERE id=:event"), {"event": event})
            retained = await client.get(base, headers=owner)
            assert retained.json()["items"][0]["group_id"] == str(group[1])
            assert (await client.get(base, headers=foreign)).status_code == 403
            assert (await client.get(base + f"/{event}/download-link", headers=owner)).status_code == 404
            async with database.transaction(tenant, actor) as session:
                try:
                    await session.execute(text("SELECT ciphertext FROM whatsapp_material_events"))
                    raise AssertionError("app role could read encrypted payload")
                except ProgrammingError:
                    pass
            assert (await client.delete(base + "/consent", headers=owner)).json() == {"accepted": False}
            assert (await client.delete(base + "/consent", headers=owner)).status_code == 200
            async with admin.connect() as connection:
                active = await connection.scalar(
                    text("SELECT active FROM whatsapp_channel_links WHERE business_id=:business"),
                    {"business": business},
                )
            assert active is False
        finally:
            await meta.close()
            await router.close()


async def test_image_dispatch_receipt_and_access_recheck(admin, database, auth_database, seeded, settings, monkeypatch):
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    tenant, actor, business, number = seeded["t1"], seeded["a1"], uuid4(), "5511999999999"
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test',:phone,true,'#6557ed')"""),
            {"tenant": tenant, "business": business, "phone": "+" + number},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id,accepted_at)
          VALUES(:tenant,:business,:actor,now()-interval '1 minute')"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_channel_links
          (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
          VALUES(:tenant,:business,:actor,:sender,:proof,now()-interval '1 minute')"""),
            {
                "tenant": tenant,
                "business": business,
                "actor": actor,
                "sender": sender_hash(cfg, number),
                "proof": uuid4(),
            },
        )
        await connection.execute(
            text("""INSERT INTO billing_sponsorships(id,tenant_id,actor_id,idempotency_key,reason)
          VALUES(:id,:tenant,:actor,'media-test','Synthetic integration test')"""),
            {"id": uuid4(), "tenant": tenant, "actor": actor},
        )
    meta = Database(cfg, meta=True)
    router = Database(cfg, correlator=True)
    try:
        await save_events(
            meta,
            cfg,
            [
                (
                    "image-1",
                    "message",
                    {"from": number, "type": "image", "image": {"id": "123", "caption": "Meu lanche"}},
                )
            ],
        )
        assert await route_once(router, cfg) == 1
        async with admin.connect() as connection:
            event = await connection.scalar(text("SELECT id FROM whatsapp_material_events"))
        client = Mock()
        client.start_workflow = AsyncMock()
        assert await dispatch_materials(router, client, cfg, uuid4()) == 1
        assert await dispatch_materials(router, client, cfg, uuid4()) == 0
        media = AsyncMock()
        data = b"a checked image from the fake Meta adapter"
        media.fetch.return_value = FetchedMedia(data, "image/png", hashlib.sha256(data).hexdigest())
        store = AsyncMock()
        processor = MaterialProcessor(cfg, router, media, store)
        assert await processor.process(event) == "processed"
        media.fetch.assert_awaited_once_with("123", "image")
        store.put.assert_awaited_once()
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_upload_intents")) == 0
        app = create_app(cfg, database, auth_database)
        base = f"/api/v1/organizations/{tenant}/businesses/{business}/whatsapp-materials"
        owner = {"Authorization": f"Bearer {access_token(cfg, actor)}"}
        monkeypatch.setattr(MaterialStore, "signed_url", AsyncMock(return_value="http://localhost:9000/signed"))
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as browser,
        ):
            listed = (await browser.get(base, headers=owner)).json()["items"]
            assert listed[0]["text"] == "Meu lanche"
            assert listed[0]["has_file"] is True
            assert (await browser.get(base + f"/{event}/download-link", headers=owner)).json() == {
                "url": "http://localhost:9000/signed"
            }
        # A second queued message is denied if commercial access disappears before the activity.
        await save_events(
            meta, cfg, [("image-2", "message", {"from": number, "type": "image", "image": {"id": "124"}})]
        )
        assert await route_once(router, cfg) == 1
        async with admin.begin() as connection:
            second = await connection.scalar(
                text("SELECT id FROM whatsapp_material_events WHERE id<>:first"), {"first": event}
            )
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"), {"tenant": tenant}
            )
        assert await processor.process(second) == "failed"
        async with admin.connect() as connection:
            code = await connection.scalar(
                text("SELECT error_code FROM whatsapp_material_events WHERE id=:id"), {"id": second}
            )
        assert code == "ACCESS_OR_CONSENT_INACTIVE"
        terminal = MaterialClaim(uuid4(), tenant, business, uuid4(), 7)
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO whatsapp_material_events
                  (id,tenant_id,business_id,kind,ciphertext,state,expires_at,attempts,owner_id,fencing_token)
                  VALUES(:id,:tenant,:business,'text','encrypted','processing',
                    now()+interval '1 day',5,:owner,:fence)"""),
                {
                    "id": terminal.id,
                    "tenant": tenant,
                    "business": business,
                    "owner": terminal.owner_id,
                    "fence": terminal.fencing_token,
                },
            )
        await finish_dispatch(router, terminal, accepted=False)
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT error_code FROM whatsapp_material_events WHERE id=:id"), {"id": terminal.id}
                )
                == "TEMPORAL_UNAVAILABLE"
            )
            assert (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM audit_events WHERE operation_id=:id "
                        "AND action='whatsapp.material_dispatch_failed'"
                    ),
                    {"id": terminal.id},
                )
                == 1
            )
        # A change after S3 upload leaves a durable deletion intent, not an invisible object.
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=NULL WHERE tenant_id=:tenant"), {"tenant": tenant}
            )
        await save_events(
            meta, cfg, [("image-3", "message", {"from": number, "type": "image", "image": {"id": "125"}})]
        )
        assert await route_once(router, cfg) == 1
        async with admin.connect() as connection:
            third = await connection.scalar(
                text("SELECT id FROM whatsapp_material_events WHERE kind='image' AND id NOT IN (:first,:second)"),
                {"first": event, "second": second},
            )

        async def revoke_after_upload(_key, _media):
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"),
                    {"tenant": tenant},
                )

        store.put.side_effect = revoke_after_upload
        assert await processor.process(third) == "failed"
        async with admin.begin() as connection:
            intent = (
                await connection.execute(
                    text("SELECT id,object_key FROM whatsapp_upload_intents WHERE event_id=:event"),
                    {"event": third},
                )
            ).one()
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:event"), {"event": third}
                )
                == 0
            )
            await connection.execute(
                text("UPDATE whatsapp_upload_intents SET reconcile_after=now()-interval '1 second' WHERE id=:id"),
                {"id": intent.id},
            )

        store.delete.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        assert await reconcile_uploads(router, store, uuid4()) == 0
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE whatsapp_upload_intents SET delete_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": intent.id},
            )
        store.delete.side_effect = None
        assert await reconcile_uploads(router, store, uuid4()) == 1
        store.delete.assert_awaited_with(intent.object_key)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM whatsapp_upload_intents")) == 0
        # A sweeper claim made while an upload is in flight blocks its final commit.
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=NULL WHERE tenant_id=:tenant"), {"tenant": tenant}
            )
        await save_events(
            meta, cfg, [("image-4", "message", {"from": number, "type": "image", "image": {"id": "126"}})]
        )
        assert await route_once(router, cfg) == 1
        async with admin.connect() as connection:
            fourth = await connection.scalar(
                text(
                    "SELECT id FROM whatsapp_material_events WHERE kind='image' AND id NOT IN (:first,:second,:third)"
                ),
                {"first": event, "second": second, "third": third},
            )

        async def claim_during_upload(_key, _media):
            async with admin.begin() as connection:
                await connection.execute(
                    text("""UPDATE whatsapp_upload_intents SET reconcile_after=now()-interval '1 second'
                      WHERE event_id=:event"""),
                    {"event": fourth},
                )
            assert len(await claim_upload_intents(router, uuid4())) == 1

        store.put.side_effect = claim_during_upload
        assert await processor.process(fourth) == "failed"
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT error_code FROM whatsapp_material_events WHERE id=:id"), {"id": fourth}
                )
                == "UPLOAD_RECONCILING"
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM whatsapp_material_assets WHERE id=:id"), {"id": fourth}
                )
                == 0
            )
    finally:
        await meta.close()
        await router.close()
