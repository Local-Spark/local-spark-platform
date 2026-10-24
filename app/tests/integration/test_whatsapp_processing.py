"""Material processing uses restricted roles and rechecks access after routing."""

import hashlib
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.core.identity import Identity
from app.db.session import Database
from app.main import create_app
from app.services.administration import review_whatsapp_reply, whatsapp_reply_issues
from app.services.auth import AuthError
from app.services.editorial_conversation import record_inbound_text
from app.services.whatsapp_delivery import process_receipts
from app.services.whatsapp_ingest import save_events, sender_hash
from app.services.whatsapp_processing import MaterialClaim, MaterialProcessor, dispatch_materials, finish_dispatch
from app.services.whatsapp_replies import ClaimedReply, dispatch_reply, finish_reply
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
        assert (await client.get(base + "/audio-consent", headers=owner)).json() == {"accepted": False}
        assert (await client.post(base + "/audio-consent", headers=foreign, json={"accepted": True})).status_code == 403
        assert (await client.post(base + "/audio-consent", headers=owner, json={"accepted": True})).json() == {
            "accepted": True
        }
        assert (await client.get(base + "/audio-consent", headers=owner)).json() == {"accepted": True}
        assert (await client.post(base + "/audio-consent", headers=owner, json={"accepted": False})).json() == {
            "accepted": False
        }
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
                [
                    (
                        "idea-1",
                        "message",
                        {"from": number, "type": "text", "text": {"body": "Hoje o X-tudo está 20 reais"}},
                    )
                ],
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
            assert response.json()["items"][0]["text"] == "Hoje o X-tudo está 20 reais"
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
            async with admin.connect() as connection:
                decision = (
                    (
                        await connection.execute(
                            text("""SELECT id,operation_id,state,intent,proposal,reply
                          FROM editorial_conversation_decisions WHERE business_id=:business"""),
                            {"business": business},
                        )
                    )
                    .mappings()
                    .one()
                )
                original = (
                    (
                        await connection.execute(
                            text("""SELECT id,tenant_id,business_id,sender_hash,created_at
                          FROM whatsapp_material_events WHERE id=:event"""),
                            {"event": event},
                        )
                    )
                    .mappings()
                    .one()
                )
            assert decision["operation_id"] == event
            assert decision["state"] == "awaiting_confirmation"
            assert decision["intent"] == "price"
            assert decision["proposal"]["summary"] == "X-tudo: R$ 20,00 hoje"
            assert "Confirmar" in decision["reply"]
            conversation_base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-conversation"
            assert (await client.get(conversation_base, headers=foreign)).status_code == 403
            listed = await client.get(conversation_base, headers=owner)
            assert listed.status_code == 200
            assert listed.json()[0]["id"] == str(decision["id"])
            send_cfg = cfg.model_copy(
                update={
                    "meta_access_token": SecretStr("test-token"),
                    "meta_graph_version": "v23.0",
                    "meta_phone_number_id": "123",
                    "meta_reply_enabled": True,
                    "meta_daily_message_limit": 10,
                }
            )

            def respond(request):
                assert request.url.path == "/v23.0/123/messages"
                return httpx.Response(200, json={"messages": [{"id": "wamid.test-prompt"}]})

            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as graph:
                assert await dispatch_reply(router, send_cfg, graph) is True
                assert await dispatch_reply(router, send_cfg, graph) is False
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT state FROM editorial_whatsapp_replies WHERE id=:id"), {"id": decision["id"]}
                    )
                    == "accepted"
                )
            await save_events(
                meta,
                cfg,
                [("receipt-delivered", "status", {"id": "wamid.test-prompt", "status": "delivered"})],
            )
            assert await process_receipts(router, cfg) == 1
            await save_events(
                meta,
                cfg,
                [("receipt-sent-late", "status", {"id": "wamid.test-prompt", "status": "sent"})],
            )
            assert await process_receipts(router, cfg) == 1
            assert await process_receipts(router, cfg) == 0
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT delivery_state FROM editorial_whatsapp_replies WHERE id=:id"),
                        {"id": decision["id"]},
                    )
                    == "delivered"
                )
            await save_events(
                meta,
                cfg,
                [
                    (
                        "command-1",
                        "message",
                        {
                            "from": number,
                            "type": "text",
                            "text": {"body": "Confirmar"},
                            "context": {"id": "wamid.test-prompt"},
                        },
                    )
                ],
            )
            assert await route_once(router, cfg) == 1
            async with admin.connect() as connection:
                command_event = await connection.scalar(
                    text("SELECT id FROM whatsapp_material_events WHERE id<>:event"), {"event": event}
                )
            assert await processor.process(command_event) == "processed"
            assert await processor.process(command_event) == "already_finished"
            assert (await client.get(conversation_base, headers=owner)).json()[0]["state"] == "confirmed"
            context = await client.get(
                f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context", headers=owner
            )
            assert context.json()["facts"][0]["statement"] == "X-tudo: R$ 20,00 hoje"
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT ack_state FROM editorial_whatsapp_replies WHERE id=:id"),
                        {"id": decision["id"]},
                    )
                    == "pending"
                )
            limited = send_cfg.model_copy(update={"meta_daily_message_limit": 1})
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as graph:
                assert await dispatch_reply(router, limited, graph) is False
            async with admin.begin() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT ack_state FROM editorial_whatsapp_replies WHERE id=:id"),
                        {"id": decision["id"]},
                    )
                    == "pending"
                )
                await connection.execute(
                    text("UPDATE editorial_whatsapp_replies SET ack_next_attempt_at=now() WHERE id=:id"),
                    {"id": decision["id"]},
                )
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as graph:
                assert await dispatch_reply(router, limited, graph) is False
            async with admin.begin() as connection:
                assert (
                    await connection.scalar(
                        text("""SELECT count(*) FROM audit_events
                      WHERE operation_id=:id AND action='whatsapp.ack_budget_deferred'"""),
                        {"id": decision["id"]},
                    )
                    == 1
                )
                await connection.execute(
                    text("UPDATE editorial_whatsapp_replies SET ack_next_attempt_at=now() WHERE id=:id"),
                    {"id": decision["id"]},
                )
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda _: httpx.Response(200, json={"messages": [{"id": "wamid.test-ack"}]})
                )
            ) as graph:
                assert await dispatch_reply(router, send_cfg, graph) is True
            await finish_reply(router, ClaimedReply(decision["id"], "", "", ack=True), "accepted", "wamid.duplicate")
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT ack_provider_message_id FROM editorial_whatsapp_replies WHERE id=:id"),
                        {"id": decision["id"]},
                    )
                    == "wamid.test-ack"
                )
                assert (
                    await connection.scalar(
                        text("""SELECT count(*) FROM audit_events
                      WHERE operation_id=:id AND action='whatsapp.ack_accepted'"""),
                        {"id": decision["id"]},
                    )
                    == 1
                )
            await save_events(
                meta,
                cfg,
                [
                    (
                        "receipt-ack-failed",
                        "status",
                        {"id": "wamid.test-ack", "status": "failed", "errors": [{"code": 131031}]},
                    )
                ],
            )
            assert await process_receipts(router, cfg) == 1
            await save_events(
                meta,
                cfg,
                [("unknown-receipt", "status", {"id": "wamid.unknown", "status": "sent"})],
            )
            assert await process_receipts(router, cfg) == 0
            async with admin.begin() as connection:
                await connection.execute(
                    text("""UPDATE whatsapp_inbox SET received_at=now()-interval '3 minutes'
                      WHERE dedupe_key='unknown-receipt'""")
                )
                await connection.execute(
                    text("""INSERT INTO whatsapp_inbox(id,dedupe_key,event_kind,ciphertext)
                      VALUES(:id,'broken-receipt','status','not-encrypted')"""),
                    {"id": uuid4()},
                )
            assert await process_receipts(router, cfg) == 2
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT state FROM whatsapp_inbox WHERE dedupe_key='unknown-receipt'"))
                    == "discarded"
                )
            async with admin.connect() as connection:
                receipt_state = (
                    await connection.execute(
                        text("""SELECT ack_state,ack_delivery_state,ack_provider_error_code
                          FROM editorial_whatsapp_replies WHERE id=:id"""),
                        {"id": decision["id"]},
                    )
                ).one()
                assert receipt_state == ("accepted", "failed", "131031")
            async with admin.begin() as connection:
                await connection.execute(
                    text("INSERT INTO platform_staff(actor_id,active) VALUES(:actor,true)"),
                    {"actor": seeded["a2"]},
                )
            issues = "/api/v1/admin/whatsapp-replies"
            staff = {"Authorization": f"Bearer {access_token(cfg, seeded['a2'])}"}
            assert (await client.get(issues, headers=owner)).status_code == 403
            review = issues + f"/{decision['id']}/review"
            assert (await client.post(review, headers=owner, json={"outcome": "investigating"})).status_code == 403
            authenticate = app.state.identity_verifier.authenticate
            app.state.identity_verifier.authenticate = AsyncMock(
                return_value=Identity(seeded["a2"], cfg.jwt_issuer, str(seeded["a2"]), "Test")
            )
            listing = await client.get(issues, headers=staff)
            assert listing.status_code == 200, listing.text
            assert len(listing.json()["items"]) == 1
            assert listing.json()["items"][0]["ack_provider_error_code"] == "131031"
            assert number not in listing.text and "Confirma?" not in listing.text
            assert (await client.post(review, headers=staff, json={"outcome": "investigating"})).status_code == 200
            assert (await client.post(review, headers=staff, json={"outcome": "closed_no_retry"})).status_code == 200
            assert (await client.post(review, headers=staff, json={"outcome": "retry"})).status_code == 422
            assert (
                await client.post(issues + f"/{uuid4()}/review", headers=staff, json={"outcome": "investigating"})
            ).status_code == 404
            assert (await client.get(issues, headers=staff)).json()["items"][0]["review_outcome"] == "closed_no_retry"
            operator_database = Database(cfg)
            try:
                async with operator_database.transaction(seeded["t2"], seeded["a2"]) as session:
                    assert (await whatsapp_reply_issues(session, seeded["a2"], tenant, 10))["items"][0][
                        "id"
                    ] == decision["id"]
                    assert (await review_whatsapp_reply(session, seeded["a2"], decision["id"], "investigating"))[
                        "review_outcome"
                    ] == "investigating"
                    with pytest.raises(AuthError, match="WHATSAPP_REPLY_NOT_FOUND"):
                        await review_whatsapp_reply(session, seeded["a2"], uuid4(), "investigating")
            finally:
                await operator_database.close()
            app.state.identity_verifier.authenticate = authenticate
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE platform_staff SET active=false WHERE actor_id=:actor"),
                    {"actor": seeded["a2"]},
                )
            async with router.sessions() as session, session.begin():
                await record_inbound_text(session, original, "Hoje o X-tudo está 20 reais", number, Fernet(key))
            async with admin.connect() as connection:
                assert await connection.scalar(text("SELECT count(*) FROM editorial_conversation_decisions")) == 1
                assert (
                    await connection.scalar(
                        text("SELECT count(*) FROM audit_events WHERE action='editorial.conversation_received'")
                    )
                    == 1
                )
            await save_events(
                meta, cfg, [("unclear-1", "message", {"from": number, "type": "text", "text": {"body": "Oi"}})]
            )
            assert await route_once(router, cfg) == 1
            async with admin.connect() as connection:
                unclear_event = await connection.scalar(
                    text("""SELECT id FROM whatsapp_material_events
                      WHERE id<>:first AND id<>:command"""),
                    {"first": event, "command": command_event},
                )
            assert await processor.process(unclear_event) == "processed"
            async with admin.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT count(*) FROM editorial_conversation_decisions WHERE state='needs_review'")
                    )
                    == 1
                )
                assert await connection.scalar(text("SELECT count(*) FROM editorial_whatsapp_replies")) == 1
            async with admin.begin() as connection:
                await connection.execute(text("DELETE FROM whatsapp_material_events WHERE id=:event"), {"event": event})
            retained = await client.get(base, headers=owner)
            assert any(item["group_id"] == str(group[1]) for item in retained.json()["items"])
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
