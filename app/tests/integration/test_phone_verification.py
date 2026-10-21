"""Phone is verified only after a real provider approval, never by a typed code alone."""

from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from app.adapters.twilio_verify import PhoneProviderError, TwilioVerify
from app.main import create_app
from app.services.auth import AuthError
from app.services.phone_verification import PhoneVerificationService, e164
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


@pytest.fixture
async def phone_business(admin, seeded):
    business = uuid4()
    async with admin.begin() as db:
        await db.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Nails','America/Sao_Paulo')"),
            {"id": business, "tenant": seeded["t1"]},
        )
        await db.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Beleza','São Paulo','Unhas','11999999999','#6557ed')"""),
            {"tenant": seeded["t1"], "business": business},
        )
    return business


@pytest.fixture
async def phone_api(database, auth_database, settings, monkeypatch):
    config = settings.model_copy(
        update={
            "phone_verify_mode": "twilio",
            "twilio_verify_service_sid": "VA" + "a" * 32,
            "twilio_api_key": "SK" + "a" * 32,
        }
    )
    start, check = AsyncMock(return_value="VE" + "b" * 32), AsyncMock(return_value=False)
    monkeypatch.setattr(TwilioVerify, "start", start)
    monkeypatch.setattr(TwilioVerify, "check", check)
    app = create_app(config, database, auth_database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url=config.public_web_url,
            headers={"Origin": config.public_web_url},
        ) as client,
    ):
        yield client, config, start, check


def route(tenant, business):
    return f"/api/v1/organizations/{tenant}/businesses/{business}/phone-verification"


async def test_owner_verifies_only_after_provider_approval(phone_api, phone_business, seeded, admin):
    client, config, start, check = phone_api
    url = route(seeded["t1"], phone_business)
    headers = {"Authorization": f"Bearer {access_token(config, seeded['a1'])}"}
    other = {"Authorization": f"Bearer {access_token(config, seeded['a2'])}"}
    assert (await client.get(url, headers=other)).status_code == 403
    status = (await client.get(url, headers=headers)).json()
    assert status == {
        "enabled": True,
        "phone": "11999999999",
        "destination": "+5511999999999",
        "verified": False,
        "state": None,
    }
    assert (await client.post(url, headers=headers)).json() == {"status": "pending"}
    start.assert_awaited_once_with("+5511999999999")
    assert (await client.post(url, headers=headers)).status_code == 429
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "123"})).status_code == 422
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "1234"})).status_code == 400
    async with admin.connect() as db:
        assert not await db.scalar(
            text("SELECT phone_verified FROM business_profiles WHERE tenant_id=:id"), {"id": seeded["t1"]}
        )
    check.return_value = True
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "9876"})).json() == {
        "status": "verified"
    }
    assert (await client.get(url, headers=headers)).json()["verified"] is True
    assert (await client.post(url, headers=headers)).json() == {"status": "verified"}
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "9876"})).json() == {
        "status": "verified"
    }


async def test_disabled_phone_delivery_does_not_accept_a_code(native_api, phone_business, seeded, settings):
    url = route(seeded["t1"], phone_business)
    headers = {"Authorization": f"Bearer {access_token(settings, seeded['a1'])}"}
    assert (await native_api.get(url, headers=headers)).json()["enabled"] is False
    assert (await native_api.post(url, headers=headers)).json()["error_code"] == "PHONE_VERIFY_UNAVAILABLE"
    assert (await native_api.post(url + "/confirm", headers=headers, json={"code": "1234"})).status_code == 503


async def test_provider_failure_and_attempt_limit(phone_api, phone_business, seeded, admin):
    client, config, start, check = phone_api
    url = route(seeded["t1"], phone_business)
    headers = {"Authorization": f"Bearer {access_token(config, seeded['a1'])}"}
    start.side_effect = PhoneProviderError("private")
    assert (await client.post(url, headers=headers)).status_code == 503
    assert (await client.get(url, headers=headers)).json()["state"] == "failed"
    async with admin.begin() as db:
        await db.execute(
            text("UPDATE phone_verification_requests SET requested_at=now()-interval '2 minutes'"),
        )
    start.side_effect = None
    assert (await client.post(url, headers=headers)).status_code == 202
    check.side_effect = PhoneProviderError("private")
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "1234"})).status_code == 503
    check.side_effect = None
    for _ in range(4):
        assert (await client.post(url + "/confirm", headers=headers, json={"code": "1234"})).status_code == 400
    assert (await client.post(url + "/confirm", headers=headers, json={"code": "1234"})).status_code == 409
    async with admin.connect() as db:
        assert not await db.scalar(
            text("SELECT phone_verified FROM business_profiles WHERE tenant_id=:id"), {"id": seeded["t1"]}
        )


async def test_service_guards_and_changed_phone(database, admin, phone_business, seeded, settings):
    config = settings.model_copy(update={"phone_verify_mode": "twilio"})
    provider = AsyncMock(start=AsyncMock(return_value="VE" + "c" * 32), check=AsyncMock(return_value=True))
    service = PhoneVerificationService(config, database, provider)
    tenant, owner = seeded["t1"], seeded["a1"]
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.status(tenant, uuid4(), owner)
    assert (await service.status(tenant, phone_business, owner))["state"] is None
    with pytest.raises(AuthError, match="INVALID_PHONE_CODE"):
        await service.confirm(tenant, phone_business, owner, "abc")
    with pytest.raises(AuthError, match="PHONE_VERIFY_NOT_PENDING"):
        await service.confirm(tenant, phone_business, owner, "1234")
    assert (await service.start(tenant, phone_business, owner))["status"] == "pending"
    with pytest.raises(AuthError, match="PHONE_VERIFY_WAIT"):
        await service.start(tenant, phone_business, owner)
    async with admin.begin() as db:
        await db.execute(text("UPDATE phone_verification_requests SET provider_sid=NULL"))
    with pytest.raises(AuthError, match="PHONE_VERIFY_NOT_PENDING"):
        await service.confirm(tenant, phone_business, owner, "1234")
    async with admin.begin() as db:
        await db.execute(
            text(
                "UPDATE phone_verification_requests SET provider_sid='VEvalid',requested_at=now()-interval '2 minutes'"
            )
        )

    async def change_profile(_sid, _code):
        async with admin.begin() as db:
            await db.execute(
                text("UPDATE business_profiles SET phone='11888888888' WHERE tenant_id=:tenant"),
                {"tenant": tenant},
            )
        return True

    provider.check.side_effect = change_profile
    with pytest.raises(AuthError, match="PHONE_VERIFY_RETRY"):
        await service.confirm(tenant, phone_business, owner, "1234")
    async with admin.connect() as db:
        assert not await db.scalar(
            text("SELECT phone_verified FROM business_profiles WHERE tenant_id=:tenant"), {"tenant": tenant}
        )


async def test_obsolete_start_cannot_publish_code(database, admin, phone_business, seeded, settings):
    config = settings.model_copy(update={"phone_verify_mode": "twilio"})
    tenant, owner = seeded["t1"], seeded["a1"]

    async def supersede(_phone):
        async with admin.begin() as db:
            await db.execute(text("UPDATE phone_verification_requests SET state='failed'"))
        return "VE" + "d" * 32

    provider = AsyncMock(start=AsyncMock(side_effect=supersede))
    service = PhoneVerificationService(config, database, provider)
    with pytest.raises(AuthError, match="PHONE_VERIFY_RETRY"):
        await service.start(tenant, phone_business, owner)


async def test_direct_success_and_replay(database, phone_business, seeded, settings):
    config = settings.model_copy(update={"phone_verify_mode": "twilio"})
    provider = AsyncMock(start=AsyncMock(return_value="VE" + "e" * 32), check=AsyncMock(return_value=True))
    service = PhoneVerificationService(config, database, provider)
    tenant, owner = seeded["t1"], seeded["a1"]
    assert (await service.start(tenant, phone_business, owner))["status"] == "pending"
    assert (await service.confirm(tenant, phone_business, owner, "1234"))["status"] == "verified"
    assert (await service.start(tenant, phone_business, owner))["status"] == "verified"
    assert (await service.confirm(tenant, phone_business, owner, "1234"))["status"] == "verified"


def test_brazilian_phone_normalization_and_rejection():
    assert e164("+55 (11) 99999-9999") == "+5511999999999"
    assert e164("5511999999999") == "+5511999999999"
    assert e164("11999999999") == "+5511999999999"
    with pytest.raises(AuthError, match="PHONE_FORMAT_UNSUPPORTED"):
        e164("12345")
    with pytest.raises(AuthError, match="PHONE_FORMAT_UNSUPPORTED"):
        e164("+441234567890")


async def test_owner_can_correct_phone_and_old_code_cannot_verify_new_number(phone_api, phone_business, seeded, admin):
    client, config, start, check = phone_api
    url = route(seeded["t1"], phone_business)
    owner = {"Authorization": f"Bearer {access_token(config, seeded['a1'])}"}
    other = {"Authorization": f"Bearer {access_token(config, seeded['a2'])}"}
    assert (await client.patch(url, headers=other, json={"phone": "48984359057"})).status_code == 403
    assert (await client.patch(url, headers=owner, json={"phone": "123"})).status_code == 422
    assert (await client.post(url, headers=owner)).status_code == 202
    assert (await client.patch(url, headers=owner, json={"phone": "(48) 98435-9057"})).json() == {
        "phone": "+5548984359057",
        "destination": "+5548984359057",
        "verified": False,
    }
    assert (await client.get(url, headers=owner)).json() == {
        "enabled": True,
        "phone": "+5548984359057",
        "destination": "+5548984359057",
        "verified": False,
        "state": None,
    }
    check.return_value = True
    assert (await client.post(url + "/confirm", headers=owner, json={"code": "1234"})).status_code == 409
    assert (await client.post(url, headers=owner)).status_code == 202
    assert start.await_args_list[-1].args == ("+5548984359057",)
    assert (await client.post(url + "/confirm", headers=owner, json={"code": "1234"})).json() == {"status": "verified"}
    async with admin.connect() as db:
        assert await db.scalar(
            text("SELECT phone_verified FROM business_profiles WHERE tenant_id=:tenant"), {"tenant": seeded["t1"]}
        )
    assert (await client.patch(url, headers=owner, json={"phone": "48984359057"})).json()["verified"] is False
    async with admin.connect() as db:
        assert not await db.scalar(
            text("SELECT phone_verified FROM business_profiles WHERE tenant_id=:tenant"), {"tenant": seeded["t1"]}
        )


async def test_status_can_display_invalid_legacy_number(database, admin, phone_business, seeded, settings):
    async with admin.begin() as db:
        await db.execute(
            text("UPDATE business_profiles SET phone='12345' WHERE tenant_id=:tenant"), {"tenant": seeded["t1"]}
        )
    service = PhoneVerificationService(settings, database, AsyncMock())
    assert (await service.status(seeded["t1"], phone_business, seeded["a1"]))["destination"] is None


async def test_non_owner_cannot_set_verified_flag_through_runtime_role(database, phone_business, seeded):
    async with database.transaction(seeded["t1"], seeded["viewer"]) as db:
        updated = await db.scalar(
            text("""UPDATE business_profiles SET phone_verified=true
              WHERE tenant_id=:tenant AND business_id=:business RETURNING phone_verified"""),
            {"tenant": seeded["t1"], "business": phone_business},
        )
        assert updated is None
