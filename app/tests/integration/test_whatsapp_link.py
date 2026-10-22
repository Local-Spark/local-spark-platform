"""Owner plus signed WhatsApp proof in the restricted _test database."""

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

from app.db.session import Database
from app.main import create_app
from app.services.whatsapp_link import WhatsAppLinkService
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


def webhook(message_id: str, sender: str, body: str) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba-link",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {"phone_number_id": "phone-link"},
                                "messages": [
                                    {"id": message_id, "from": sender, "type": "text", "text": {"body": body}}
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    ).encode()
    signature = "sha256=" + hmac.new(b"app-link", raw, hashlib.sha256).hexdigest()
    return raw, {"x-hub-signature-256": signature}


async def test_owner_proves_sender_and_phone_change_revokes_link(admin, database, auth_database, seeded, settings):
    business, other_business = uuid4(), uuid4()
    async with admin.begin() as connection:
        for tenant, actor, target, phone in (
            (seeded["t1"], seeded["a1"], business, "+5511999999999"),
            (seeded["t2"], seeded["a2"], other_business, "+5521999999999"),
        ):
            await connection.execute(
                text("""INSERT INTO businesses(id,tenant_id,name,timezone)
                  VALUES(:id,:tenant,'Test','America/Sao_Paulo')"""),
                {"id": target, "tenant": tenant},
            )
            await connection.execute(
                text("""INSERT INTO business_profiles
                  (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
                  VALUES(:tenant,:business,'Food','Rio','Test',:phone,true,'#6557ed')"""),
                {"tenant": tenant, "business": target, "phone": phone},
            )
            await connection.execute(
                text("""INSERT INTO billing_sponsorships(id,tenant_id,actor_id,idempotency_key,reason)
                  VALUES(:id,:tenant,:actor,'link-test','Synthetic integration test')"""),
                {"id": uuid4(), "tenant": tenant, "actor": actor},
            )
    config = settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_database_url": SecretStr(os.environ["TEST_META_DATABASE_URL"]),
            "meta_verify_token": SecretStr("verify-link"),
            "meta_app_secret": SecretStr("app-link"),
            "meta_waba_id": "waba-link",
            "meta_phone_number_id": "phone-link",
            "meta_public_phone": "+5511988887777",
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )
    meta = Database(config, meta=True)
    app = create_app(config, database, auth_database, meta_database=meta)
    route = f"/api/v1/organizations/{seeded['t1']}/businesses/{business}/whatsapp-link"
    own = {"Authorization": f"Bearer {access_token(config, seeded['a1'])}"}
    foreign = {"Authorization": f"Bearer {access_token(config, seeded['a2'])}"}
    viewer = {"Authorization": f"Bearer {access_token(config, seeded['viewer'])}"}
    try:
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
        ):
            assert (await client.get(route, headers=foreign)).status_code == 403
            assert (await client.get(route, headers=viewer)).status_code == 403
            assert (await client.post(route, headers=foreign)).status_code == 403
            assert (await client.post(route, headers=viewer)).status_code == 403
            assert (await client.post(route + "/confirm", headers=viewer)).status_code == 403
            assert (await client.get(route, headers=own)).json() == {
                "enabled": True,
                "linked": False,
                "pending": False,
                "destination": "+5511988887777",
            }
            assert (await client.post(route + "/confirm", headers=own)).json()["error_code"] == (
                "WHATSAPP_LINK_NOT_PENDING"
            )
            assert (await client.post(route, headers=own)).json()["error_code"] == "WHATSAPP_CONSENT_REQUIRED"
            consent = route.replace("/whatsapp-link", "/whatsapp-materials/consent")
            assert (await client.post(consent, headers=own, json={"accepted": True})).status_code == 200
            other_consent = (
                f"/api/v1/organizations/{seeded['t2']}/businesses/{other_business}/whatsapp-materials/consent"
            )
            assert (await client.post(other_consent, headers=foreign, json={"accepted": True})).status_code == 200
            started = await client.post(route, headers=own)
            assert started.status_code == 201, started.text
            message = started.json()["message"]
            assert message.startswith("VINCULAR ")
            assert (await client.post(route, headers=own)).status_code == 429
            assert (await client.get(route, headers=own)).json()["pending"] is True
            assert (await client.post(route + "/confirm", headers=own)).status_code == 409
            raw, signed = webhook("wrong-sender", "5521999999999", message)
            assert (await client.post("/api/v1/webhooks/whatsapp", content=raw, headers=signed)).status_code == 200
            assert (await client.post(route + "/confirm", headers=own)).status_code == 409
            raw, signed = webhook("wrong-code", "5511999999999", "VINCULAR wrong")
            assert (await client.post("/api/v1/webhooks/whatsapp", content=raw, headers=signed)).status_code == 200
            assert (await client.post(route + "/confirm", headers=own)).status_code == 409
            raw, signed = webhook("right-code", "5511999999999", message)
            assert (await client.post("/api/v1/webhooks/whatsapp", content=raw, headers=signed)).status_code == 200
            assert (await client.post(route + "/confirm", headers=own)).json() == {"status": "linked"}
            other_route = f"/api/v1/organizations/{seeded['t2']}/businesses/{other_business}/whatsapp-link"
            other_owner = {"Authorization": f"Bearer {access_token(config, seeded['a2'])}"}
            other_started = await client.post(other_route, headers=other_owner)
            assert other_started.status_code == 201
            raw, signed = webhook("same-sender", "5511999999999", other_started.json()["message"])
            assert (await client.post("/api/v1/webhooks/whatsapp", content=raw, headers=signed)).status_code == 200
            assert (await client.post(other_route + "/confirm", headers=other_owner)).json()["error_code"] == (
                "WHATSAPP_PROOF_NOT_RECEIVED"
            )
            assert (await client.post(route + "/confirm", headers=own)).json() == {"status": "linked"}
            assert (await client.post(route, headers=own)).json() == {"status": "linked"}
            assert (await client.get(route, headers=own)).json()["linked"] is True
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
                    {"tenant": seeded["t1"], "actor": seeded["viewer"]},
                )
            assert (
                await client.patch(
                    f"/api/v1/organizations/{seeded['t1']}/businesses/{business}/phone-verification",
                    headers=viewer,
                    json={"phone": "+5511888888888"},
                )
            ).status_code == 200
            assert (await client.get(route, headers=own)).json()["linked"] is False
            assert (await client.post(route, headers=own)).status_code == 409
        async with admin.connect() as connection:
            row = (
                await connection.execute(
                    text("SELECT sender_hash,active FROM whatsapp_channel_links WHERE business_id=:business"),
                    {"business": business},
                )
            ).one()
            assert row.active is False
            assert "5511999999999" not in row.sender_hash
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='whatsapp.linked' AND resource_id=:business"),
                    {"business": business},
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("""SELECT count(*) FROM audit_events WHERE action='whatsapp.unlinked'
                  AND resource_id=:business AND actor_id=:actor"""),
                    {"business": business, "actor": seeded["viewer"]},
                )
                == 1
            )
    finally:
        await meta.close()


async def test_link_requires_verified_phone_and_plan(admin, database, seeded, settings):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:business,:tenant,'Test','UTC')"),
            {"business": business, "tenant": seeded["t1"]},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"business": business, "tenant": seeded["t1"]},
        )
    config = settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_public_phone": "+5511988887777",
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )
    service = WhatsAppLinkService(config, database, database)
    tenant, actor = seeded["t1"], seeded["a1"]
    with pytest.raises(Exception, match="PHONE_VERIFICATION_REQUIRED"):
        await service.start(tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE business_id=:business"),
            {"business": business},
        )
    with pytest.raises(Exception, match="PLAN_REQUIRED"):
        await service.start(tenant, business, actor)
    with pytest.raises(Exception, match="PLAN_REQUIRED"):
        await service.confirm(tenant, business, actor)
