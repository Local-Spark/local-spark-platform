import asyncio
import hashlib
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.identity import Identity
from app.schemas.onboarding import OnboardingCreate
from app.services.administration import overview
from app.services.business import AccessDenied, create_business
from app.services.onboarding import provision_initial_business, session_context, sync_identity

pytestmark = pytest.mark.integration
ZERO = UUID(int=0)


@pytest.fixture
def identity():
    return Identity(uuid4(), "https://identity.example", str(uuid4()), "Ana", "ana@example.com", True)


@pytest.fixture
def onboarding_payload():
    return OnboardingCreate(
        name="Ana Studio",
        category="Beleza",
        city="São Paulo",
        description="Unhas e cuidados",
        phone="+5511999999999",
        accept_terms=True,
        accept_privacy=True,
    )


async def test_concurrent_onboarding_is_atomic_and_replayable(database, admin, identity, onboarding_payload):
    async def register():
        async with database.transaction(ZERO, identity.actor_id) as session:
            return await provision_initial_business(session, identity, onboarding_payload)

    results = await asyncio.gather(*(register() for _ in range(5)))
    assert len({result.tenant_id for result in results}) == 1
    assert sum(not result.replayed for result in results) == 1
    async with database.transaction(ZERO, identity.actor_id) as session:
        view = await session_context(session, identity)
    assert view.organizations[0].onboarding_completed
    assert view.organizations[0].business_count == 1 and not view.is_staff
    async with admin.connect() as connection:
        for table in (
            "tenants",
            "memberships",
            "businesses",
            "business_profiles",
            "onboarding_registrations",
        ):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM outbox_events")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM consents")) == 2
        assert await connection.scalar(text("SELECT phone_verified FROM business_profiles")) is False
        legacy_json = onboarding_payload.model_dump_json(exclude={"state_code", "city_ibge_code"})
        assert (
            await connection.scalar(text("SELECT request_hash FROM onboarding_registrations"))
            == hashlib.sha256(legacy_json.encode()).hexdigest()
        )


async def test_structured_location_and_custom_brand_persist_atomically(
    api, admin, identity, onboarding_payload, monkeypatch
):
    monkeypatch.setattr(api._transport.app.state.identity_verifier, "authenticate", AsyncMock(return_value=identity))
    headers = {"Authorization": "Bearer test-session"}
    payload = {
        **onboarding_payload.model_dump(),
        "state_code": "SP",
        "city_ibge_code": "3550308",
        "category": "Conserto de instrumentos musicais",
        "brand_color": "#12abEF",
    }
    bad = await api.post("/api/v1/onboarding", headers=headers, json={**payload, "state_code": "RJ"})
    assert bad.status_code == 422
    response = await api.post("/api/v1/onboarding", headers=headers, json=payload)
    assert response.status_code == 201
    replay = await api.post("/api/v1/onboarding", headers=headers, json=payload)
    assert replay.status_code == 200 and replay.json()["business_id"] == response.json()["business_id"]
    async with admin.connect() as db:
        profile = (
            (
                await db.execute(
                    text("SELECT category,city,state_code,city_ibge_code,brand_color FROM business_profiles")
                )
            )
            .mappings()
            .one()
        )
        assert dict(profile) == {key: payload[key] for key in profile}
        assert await db.scalar(text("SELECT count(*) FROM outbox_events")) == 0


async def test_onboarding_conflict_revocation_and_unverified_email(database, admin, identity, onboarding_payload):
    from app.services.business import IdempotencyConflict

    async with database.transaction(ZERO, identity.actor_id) as session:
        initial = await provision_initial_business(session, identity, onboarding_payload)
    async with database.transaction(ZERO, identity.actor_id) as session:
        replay = await provision_initial_business(session, identity, onboarding_payload)
    assert replay.replayed and replay.business_id == initial.business_id
    with pytest.raises(IdempotencyConflict):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await provision_initial_business(
                session, identity, onboarding_payload.model_copy(update={"name": "Changed"})
            )
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE memberships SET active=false"))
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await provision_initial_business(session, identity, onboarding_payload)
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await provision_initial_business(session, replace(identity, email_verified=False), onboarding_payload)


async def test_onboarding_failure_rolls_back_every_resource(database, admin, identity, onboarding_payload, monkeypatch):
    monkeypatch.setattr(
        "app.services.onboarding.create_business", AsyncMock(side_effect=RuntimeError("injected failure"))
    )
    with pytest.raises(RuntimeError):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await provision_initial_business(session, identity, onboarding_payload)
    async with admin.connect() as connection:
        for table in ("user_accounts", "tenants", "memberships", "onboarding_registrations", "businesses", "consents"):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0


async def test_account_revocation_cannot_be_reactivated(database, admin, identity, onboarding_payload):
    async with database.transaction(ZERO, identity.actor_id) as session:
        result = await provision_initial_business(session, identity, onboarding_payload)
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE user_accounts SET active=false"))
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await sync_identity(session, identity)
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await session_context(session, identity)
    with pytest.raises(AccessDenied):
        async with database.transaction(result.tenant_id, identity.actor_id) as session:
            await create_business(session, result.tenant_id, identity.actor_id, "revoked-command", onboarding_payload)


async def test_rls_blocks_ownership_hijack_and_cross_account_profile(database, admin, identity, onboarding_payload):
    async with database.transaction(ZERO, identity.actor_id) as session:
        original = await provision_initial_business(session, identity, onboarding_payload)
    intruder = replace(identity, actor_id=uuid4(), subject=str(uuid4()))
    async with database.transaction(ZERO, intruder.actor_id) as session:
        await sync_identity(session, intruder)
        assert (await session_context(session, intruder)).organizations == []
        assert not (await session.execute(text("SELECT * FROM business_profiles"))).all()
    with pytest.raises(DBAPIError):
        async with database.transaction(original.tenant_id, intruder.actor_id) as session:
            await session.execute(
                text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES (:tenant,:actor,'owner')"),
                {"tenant": original.tenant_id, "actor": intruder.actor_id},
            )
    with pytest.raises(DBAPIError):
        async with database.transaction(original.tenant_id, intruder.actor_id) as session:
            await session.execute(
                text(
                    "INSERT INTO onboarding_registrations(actor_id,tenant_id,request_hash) "
                    "VALUES (:actor,:tenant,:hash)"
                ),
                {"tenant": original.tenant_id, "actor": intruder.actor_id, "hash": "a" * 64},
            )


async def test_onboarding_http_and_me(api, database, monkeypatch, identity, onboarding_payload):
    monkeypatch.setattr(api._transport.app.state.identity_verifier, "authenticate", AsyncMock(return_value=identity))
    headers = {"Authorization": "Bearer verified-by-provider"}
    assert (await api.get("/api/v1/me", headers=headers)).status_code == 403
    first = await api.post("/api/v1/session", headers=headers)
    assert first.status_code == 200 and not first.json()["is_staff"]
    response = await api.post("/api/v1/onboarding", headers=headers, json=onboarding_payload.model_dump())
    assert response.status_code == 201
    replay = await api.post("/api/v1/onboarding", headers=headers, json=onboarding_payload.model_dump())
    assert replay.status_code == 200 and replay.json()["tenant_id"] == response.json()["tenant_id"]
    view = await api.get("/api/v1/me", headers=headers)
    assert len(view.json()["organizations"]) == 1
    assert (await api.get("/api/v1/admin/overview", headers=headers)).status_code == 403
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, identity.actor_id) as session:
            await overview(session, identity.actor_id)
    assert (await api.get("/api/v1/admin/organizations", headers=headers)).status_code == 403


async def test_staff_projection_audit_pagination_and_revocation(
    api, admin, database, monkeypatch, identity, onboarding_payload
):
    from app.services.administration import organizations, overview

    async with database.transaction(ZERO, identity.actor_id) as session:
        await provision_initial_business(session, identity, onboarding_payload)
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO platform_staff(actor_id) VALUES (:actor)"), {"actor": identity.actor_id}
        )
        await connection.execute(text("INSERT INTO tenants(id,name) VALUES (:id,'Another business')"), {"id": uuid4()})
    async with database.transaction(ZERO, identity.actor_id) as session:
        summary = await overview(session, identity.actor_id)
        page = await organizations(session, identity.actor_id, "", 1, None)
        next_page = await organizations(session, identity.actor_id, "", 1, UUID(page["next_cursor"]))
        empty = await organizations(session, identity.actor_id, "does-not-exist", 1, None)
    assert summary["totals"] == {"organizations": 2, "users": 1, "businesses": 1, "onboarded": 1}
    assert sum(day["count"] for day in summary["registrations"]) == 2
    assert len(next_page["items"]) == 1 and next_page["next_cursor"] is None
    assert empty == {"items": [], "next_cursor": None}
    monkeypatch.setattr(api._transport.app.state.identity_verifier, "authenticate", AsyncMock(return_value=identity))
    headers = {"Authorization": "Bearer staff"}
    assert (await api.get("/api/v1/admin/overview", headers=headers)).status_code == 200
    assert (await api.get("/api/v1/admin/organizations?q=Ana", headers=headers)).json()["items"][0][
        "name"
    ] == "Ana Studio"
    async with admin.begin() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM platform_audit")) == 6
        await connection.execute(text("UPDATE platform_staff SET active=false"))
    assert (await api.get("/api/v1/admin/overview", headers=headers)).status_code == 403
