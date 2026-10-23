"""Owner-only local conversation decisions are durable, isolated and idempotent."""

import asyncio
from uuid import uuid4

from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_conversation import SimulateMessage
from app.services.auth import AuthError
from app.services.editorial_conversation import EditorialConversationService
from app.tests.unit.test_core import access_token


async def assert_service_error(settings, code, method, *args):
    database = Database(settings)
    service = EditorialConversationService(settings, database)
    try:
        try:
            await getattr(service, method)(*args)
        except AuthError as error:
            assert error.code == code
        else:
            raise AssertionError(f"Expected {code}")
    finally:
        await database.close()


async def test_local_conversation_confirmation_and_replay(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','America/Sao_Paulo')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-conversation"
    context = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    payload = {"operation_id": str(uuid4()), "text": "O X-tudo está 20 reais hoje"}
    assert (await api.post(base + "/simulate", json=payload, headers=viewer)).status_code == 403
    assert (await api.post(base + "/simulate", json=payload, headers=other)).status_code == 403
    created = await api.post(base + "/simulate", json=payload, headers=owner)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["state"] == "awaiting_confirmation"
    assert body["intent"] == "price"
    assert body["summary"] == "X-tudo: R$ 20,00 hoje"
    assert (await api.post(base + "/simulate", json=payload, headers=owner)).json() == body
    conflict = await api.post(base + "/simulate", json={**payload, "text": "Outro texto"}, headers=owner)
    assert conflict.json()["error_code"] == "CONVERSATION_OPERATION_CONFLICT"
    await assert_service_error(
        settings,
        "CONVERSATION_OPERATION_CONFLICT",
        "simulate",
        tenant,
        business,
        actor,
        SimulateMessage(**{**payload, "text": "Outro texto"}),
    )
    assert (await api.post(base + f"/{body['id']}/decide", json={"confirmed": True}, headers=viewer)).status_code == 403
    confirmed = await api.post(base + f"/{body['id']}/decide", json={"confirmed": True}, headers=owner)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["state"] == "confirmed"
    assert (
        await api.post(base + f"/{body['id']}/decide", json={"confirmed": True}, headers=owner)
    ).json() == confirmed.json()
    assert (await api.post(base + f"/{body['id']}/decide", json={"confirmed": False}, headers=owner)).json()[
        "error_code"
    ] == "CONVERSATION_DECISION_CONFLICT"
    facts = (await api.get(context, headers=owner)).json()["facts"]
    assert len(facts) == 1
    assert facts[0]["kind"] == "price"
    assert facts[0]["statement"] == body["summary"]
    assert facts[0]["source_detail"] == "Confirmado pelo proprietário"
    assert (await api.post(base + f"/{uuid4()}/decide", json={"confirmed": True}, headers=owner)).json()[
        "error_code"
    ] == "CONVERSATION_NOT_FOUND"
    assert (await api.post(base + f"/{body['id']}/decide", json={"confirmed": True}, headers=other)).status_code == 403
    await assert_service_error(settings, "CONVERSATION_NOT_FOUND", "decide", tenant, business, actor, uuid4(), True)
    await assert_service_error(
        settings, "CONVERSATION_DECISION_CONFLICT", "decide", tenant, business, actor, body["id"], False
    )
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM editorial_conversation_decisions")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM business_context_versions")) == 1
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM audit_events WHERE action LIKE 'editorial.conversation_%'")
            )
            == 2
        )


async def test_local_conversation_review_discard_and_invalid_timezone(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-conversation"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    unknown = (
        await api.post(base + "/simulate", json={"operation_id": str(uuid4()), "text": "Oi"}, headers=owner)
    ).json()
    assert unknown["state"] == "needs_review"
    assert unknown["summary"] is None
    assert (await api.post(base + f"/{unknown['id']}/decide", json={"confirmed": True}, headers=owner)).json()[
        "error_code"
    ] == "CONVERSATION_NOT_CONFIRMABLE"
    await assert_service_error(
        settings, "CONVERSATION_NOT_CONFIRMABLE", "decide", tenant, business, actor, unknown["id"], True
    )
    availability = (
        await api.post(
            base + "/simulate",
            json={"operation_id": str(uuid4()), "text": "Hoje tenho agenda livre às 15h"},
            headers=owner,
        )
    ).json()
    assert availability["intent"] == "availability"
    discarded = await api.post(base + f"/{availability['id']}/decide", json={"confirmed": False}, headers=owner)
    assert discarded.json()["state"] == "discarded"
    assert (
        await api.post(base + f"/{availability['id']}/decide", json={"confirmed": False}, headers=owner)
    ).json() == discarded.json()
    assert (await api.post(base + f"/{availability['id']}/decide", json={"confirmed": True}, headers=owner)).json()[
        "error_code"
    ] == "CONVERSATION_DECISION_CONFLICT"
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE businesses SET timezone='Invalid/Zone' WHERE id=:id"), {"id": business})
    assert (
        await api.post(base + "/simulate", json={"operation_id": str(uuid4()), "text": "Oi"}, headers=owner)
    ).json()["error_code"] == "BUSINESS_TIMEZONE_INVALID"
    await assert_service_error(
        settings,
        "BUSINESS_TIMEZONE_INVALID",
        "simulate",
        tenant,
        business,
        actor,
        SimulateMessage(operation_id=uuid4(), text="Oi"),
    )
    assert (
        await api.get(f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context", headers=owner)
    ).json()["facts"] == []


async def test_simulator_disabled_outside_local(settings):
    from unittest.mock import Mock

    from app.schemas.editorial_conversation import SimulateMessage
    from app.services.auth import AuthError

    service = EditorialConversationService(settings.model_copy(update={"environment": "production"}), Mock())
    try:
        await service.simulate(uuid4(), uuid4(), uuid4(), SimulateMessage(operation_id=uuid4(), text="Oi"))
    except AuthError as error:
        assert error.code == "CONVERSATION_SIMULATOR_DISABLED"
    else:
        raise AssertionError("Simulator must be disabled")
    try:
        await service.decide(uuid4(), uuid4(), uuid4(), uuid4(), True)
    except AuthError as error:
        assert error.code == "CONVERSATION_SIMULATOR_DISABLED"
    else:
        raise AssertionError("Simulator must be disabled")


async def test_concurrent_replay_and_existing_context(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    db = Database(settings)
    service = EditorialConversationService(settings, db)
    payload = SimulateMessage(operation_id=uuid4(), text="Hoje tenho agenda livre às 15h")
    try:
        first, second = await asyncio.gather(
            service.simulate(tenant, business, actor, payload),
            service.simulate(tenant, business, actor, payload),
        )
        assert first == second
        confirmed = await service.decide(tenant, business, actor, first.id, True)
        assert confirmed.state == "confirmed"
        assert (await service.decide(tenant, business, actor, first.id, True)) == confirmed
        context = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
        owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
        facts = (await api.get(context, headers=owner)).json()["facts"]
        assert len(facts) == 1 and facts[0]["kind"] == "hours"
        # A second confirmation appends to an existing context version.
        second_intent = await service.simulate(
            tenant,
            business,
            actor,
            SimulateMessage(operation_id=uuid4(), text="O X-tudo está 20 reais hoje"),
        )
        await service.decide(tenant, business, actor, second_intent.id, True)
        assert len((await api.get(context, headers=owner)).json()["facts"]) == 2
        to_discard = await service.simulate(
            tenant,
            business,
            actor,
            SimulateMessage(operation_id=uuid4(), text="Hoje tenho agenda livre às 16h"),
        )
        assert (await service.decide(tenant, business, actor, to_discard.id, False)).state == "discarded"
        assert len((await api.get(context, headers=owner)).json()["facts"]) == 2
    finally:
        await db.close()


async def test_confirmation_respects_context_fact_limit(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    facts = [
        {"id": str(uuid4()), "kind": "product", "statement": f"Produto {index}", "source_detail": "Dono"}
        for index in range(20)
    ]
    saved = await api.put(
        base + "/editorial-context",
        json={"operation_id": str(uuid4()), "expected_version": 0, "facts": facts},
        headers=owner,
    )
    assert saved.status_code == 200, saved.text
    created = (
        await api.post(
            base + "/editorial-conversation/simulate",
            json={"operation_id": str(uuid4()), "text": "Hoje tenho agenda livre às 15h"},
            headers=owner,
        )
    ).json()
    result = await api.post(
        base + f"/editorial-conversation/{created['id']}/decide",
        json={"confirmed": True},
        headers=owner,
    )
    assert result.json()["error_code"] == "CONTEXT_FACT_LIMIT"
    await assert_service_error(settings, "CONTEXT_FACT_LIMIT", "decide", tenant, business, actor, created["id"], True)
    assert len((await api.get(base + "/editorial-context", headers=owner)).json()["facts"]) == 20
