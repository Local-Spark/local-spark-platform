"""Real restricted PostgreSQL proves address lifecycle and isolation."""

import asyncio
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.schemas.business_address import BusinessAddressWrite
from app.services.auth import AuthError
from app.services.business_address import BusinessAddressService
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def setup_shop(admin, seeded):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await conn.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    return tenant, business, actor


def payload(version=0, number="123", operation=None):
    return BusinessAddressWrite(
        operation_id=operation or uuid4(),
        expected_version=version,
        address={"street": "Rua das Flores", "number": number, "city": "São Paulo", "state_code": "SP"},
    )


async def test_address_route_versions_replay_and_private_events(admin, api, seeded, settings, database):
    tenant, business, actor = await setup_shop(admin, seeded)
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/address"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    assert (await api.get(path)).status_code == 401
    for headers in (other, viewer):
        assert (await api.get(path, headers=headers)).status_code == 403
        assert (await api.put(path, headers=headers, json=payload().model_dump(mode="json"))).status_code == 403
    assert (await api.get(path, headers=owner)).json() == {"version": 0, "address": None, "updated_at": None}
    first = payload().model_copy(update={"operation_id": UUID("00000000-0000-4000-8000-000000000456")})
    saved = await api.put(path, headers=owner, json=first.model_dump(mode="json"))
    assert saved.status_code == 200, saved.text
    v1 = saved.json()
    assert v1["version"] == 1 and v1["address"]["number"] == "123"
    assert (await api.put(path, headers=owner, json=first.model_dump(mode="json"))).json() == v1
    conflict = first.model_copy(update={"expected_version": 1})
    response = await api.put(path, headers=owner, json=conflict.model_dump(mode="json"))
    assert response.status_code == 409 and response.json()["error_code"] == "BUSINESS_ADDRESS_OPERATION_CONFLICT"
    stale = await api.put(path, headers=owner, json=payload(0, "999").model_dump(mode="json"))
    assert stale.status_code == 409 and stale.json()["error_code"] == "BUSINESS_ADDRESS_VERSION_CONFLICT"
    unchanged = await api.put(path, headers=owner, json=payload(1).model_dump(mode="json"))
    assert unchanged.json() == v1
    second = await api.put(path, headers=owner, json=payload(1, "456").model_dump(mode="json"))
    assert second.json()["version"] == 2
    assert (await api.put(path, headers=owner, json=first.model_dump(mode="json"))).json() == v1
    assert (await api.get(path, headers=owner)).json() == second.json()
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM business_address_versions")) == 2
        assert await conn.scalar(text("SELECT count(*) FROM business_address_operations")) == 3
        assert await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='business.address_saved'")) == 3
        events = (
            (await conn.execute(text("SELECT payload FROM outbox_events WHERE event_type='business.address_saved'")))
            .scalars()
            .all()
        )
        assert len(events) == 3 and all(
            set(item) == {"business_id", "actor_id", "operation_id", "address_version"} for item in events
        )
        # UUIDs legitimately contain street-number digits; the field allowlist above proves no address payload.
        assert all("Flores" not in str(item) for item in events)
    async with database.transaction(tenant, actor) as session:
        with pytest.raises(DBAPIError):
            await session.execute(text("UPDATE business_address_versions SET address='{}'::jsonb"))


async def test_address_shared_owners_and_revocation(admin, database, seeded):
    tenant, business, actor = await setup_shop(admin, seeded)
    second = seeded["a2"]
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": tenant, "actor": second},
        )
    service = BusinessAddressService(database)
    first = payload()
    saved = await service.save(tenant, business, actor, first)
    assert await service.read(tenant, business, second) == saved
    assert await service.save(tenant, business, second, payload(1)) == saved
    with pytest.raises(AuthError, match="BUSINESS_ADDRESS_OPERATION_CONFLICT"):
        await service.save(tenant, business, second, first)
    changed = await service.save(tenant, business, second, payload(1, "321"))
    assert (await service.read(tenant, business, actor)) == changed
    for t, a in ((seeded["t2"], second), (tenant, seeded["viewer"])):
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await service.read(t, business, a)
        async with database.transaction(t, a) as session:
            assert await session.scalar(text("SELECT count(*) FROM business_address_versions")) == 0
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.read(tenant, uuid4(), actor)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": second},
        )
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.save(tenant, business, second, payload(2))
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": second},
        )
        await conn.execute(text("UPDATE user_accounts SET active=false WHERE id=:actor"), {"actor": second})
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.read(tenant, business, second)
    async with database.transaction(tenant, second) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_address_versions")) == 0


async def test_concurrent_address_saves_and_replays(admin, database, seeded):
    tenant, business, actor = await setup_shop(admin, seeded)
    service = BusinessAddressService(database)
    results = await asyncio.gather(
        service.save(tenant, business, actor, payload()),
        service.save(tenant, business, actor, payload(number="456")),
        return_exceptions=True,
    )
    assert sum(isinstance(item, AuthError) for item in results) == 1
    failure = next(item for item in results if isinstance(item, AuthError))
    assert failure.code == "BUSINESS_ADDRESS_VERSION_CONFLICT"
    operation = payload(1, "999")
    a, b = await asyncio.gather(
        service.save(tenant, business, actor, operation), service.save(tenant, business, actor, operation)
    )
    assert a == b and a.version == 2
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM business_address_operations")) == 2
        assert await conn.scalar(text("SELECT count(*) FROM business_address_versions")) == 2


async def test_address_and_events_roll_back_together(admin, database, seeded):
    tenant, business, actor = await setup_shop(admin, seeded)
    async with admin.begin() as conn:
        await conn.execute(
            text("""CREATE FUNCTION address_test_reject_audit() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.action='business.address_saved' THEN RAISE EXCEPTION 'TEST_ONLY'; END IF; RETURN NEW; END $$""")
        )
        await conn.execute(
            text(
                "CREATE TRIGGER address_test_reject BEFORE INSERT ON audit_events "
                "FOR EACH ROW EXECUTE FUNCTION address_test_reject_audit()"
            )
        )
    try:
        with pytest.raises(DBAPIError):
            await BusinessAddressService(database).save(tenant, business, actor, payload())
        async with admin.connect() as conn:
            for table in (
                "business_address_versions",
                "business_address_heads",
                "business_address_operations",
                "outbox_events",
            ):
                assert await conn.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    finally:
        async with admin.begin() as conn:
            await conn.execute(text("DROP TRIGGER address_test_reject ON audit_events"))
            await conn.execute(text("DROP FUNCTION address_test_reject_audit()"))
