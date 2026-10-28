"""BL03.1 catalog CRUD, snapshots, CAS, confirmation and restricted-role isolation."""

import asyncio
from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _business(admin, tenant):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Catalog business','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles(tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    return business


def _base(tenant, business):
    return f"/api/v1/organizations/{tenant}/businesses/{business}/catalog"


def _headers(settings, actor):
    return {"Authorization": f"Bearer {access_token(settings, actor)}"}


def _payload(version=0):
    product, service = str(uuid4()), str(uuid4())
    return {
        "operation_id": str(uuid4()),
        "expected_version": version,
        "offerings": [
            {
                "id": product,
                "kind": "product",
                "state": "active",
                "name": "Croissant",
                "description": "Assado no café",
                "category": "Salgados",
                "aliases": ["Folhado"],
                "price_minor": 1800,
                "price_valid_until": "2026-12-31",
                "position": 1,
            },
            {
                "id": service,
                "kind": "service",
                "state": "draft",
                "name": "Encomenda de brunch",
                "duration_minutes": 60,
                "booking_instructions": "Agende pelo WhatsApp",
                "position": 2,
            },
        ],
        "promotions": [
            {
                "id": str(uuid4()),
                "offering_id": product,
                "title": "Croissant da tarde",
                "state": "active",
                "price_minor": 1500,
                "starts_at": "2026-10-01T10:00:00-03:00",
                "ends_at": "2026-11-01T18:00:00-03:00",
            }
        ],
    }


def _next(payload, version):
    return {**deepcopy(payload), "expected_version": version, "operation_id": str(uuid4())}


async def test_catalog_progressive_crud_confirm_archive_replay_and_immutable_history(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    base, headers = _base(tenant, business), _headers(settings, actor)
    assert (await api.get(base, headers=headers)).json() == {
        "offerings": [],
        "promotions": [],
        "version": 0,
        "updated_at": None,
        "pending_change": None,
    }
    assert (await api.get(base + "/history", headers=headers)).json() == []
    assert (await api.get(base + "/versions/1", headers=headers)).status_code == 404
    assert (await api.get(base + "/versions/0", headers=headers)).status_code == 422
    original = _payload()
    first = await api.put(base, headers=headers, json=original)
    assert first.status_code == 200, first.text
    first_document = first.json()
    assert first_document["version"] == 1 and first_document["updated_at"]
    assert first_document["offerings"][0]["currency"] == "BRL"
    assert first_document["offerings"][1]["state"] == "draft"
    assert (await api.put(base, headers=headers, json=original)).json() == first_document
    edited = _next(original, 1)
    edited["offerings"][0].update(name="Croissant artesanal", price_valid_until="2020-01-01", position=2)
    edited["offerings"][1].update(state="active", position=1)
    second = await api.put(base, headers=headers, json=edited)
    assert second.status_code == 200, second.text
    assert second.json()["version"] == 2 and second.json()["offerings"][1]["state"] == "active"
    assert (await api.put(base, headers=headers, json=original)).json() == first_document
    assert (await api.get(base + "/versions/1", headers=headers)).json() == first_document
    assert (await api.put(base, headers=headers, json={**original, "offerings": [], "promotions": []})).json()[
        "error_code"
    ] == "CATALOG_OPERATION_CONFLICT"
    stale = await api.put(base, headers=headers, json=_next(original, 0))
    assert stale.json()["error_code"] == "CATALOG_VERSION_CONFLICT"
    omitted = await api.put(base, headers=headers, json={**_next(edited, 2), "offerings": [], "promotions": []})
    assert omitted.json()["error_code"] == "CATALOG_ARCHIVE_REQUIRED"
    omitted_promo = await api.put(base, headers=headers, json={**_next(edited, 2), "promotions": []})
    assert omitted_promo.json()["error_code"] == "CATALOG_ARCHIVE_REQUIRED"
    archived = _next(edited, 2)
    archived["offerings"][0].update(state="archived", price_minor=None, price_valid_until=None)
    archived["promotions"][0]["state"] = "archived"
    third = await api.put(base, headers=headers, json=archived)
    assert third.status_code == 200, third.text
    assert third.json()["version"] == 3 and third.json()["offerings"][0]["state"] == "archived"
    restored = await api.put(base, headers=headers, json=_next(original, 3))
    assert restored.status_code == 200 and restored.json()["version"] == 4
    history = (await api.get(base + "/history", headers=headers)).json()
    assert [row["version"] for row in history] == [4, 3, 2, 1]
    assert all(row["actor_id"] == str(actor) for row in history)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_catalog_versions")) == 4
        assert await connection.scalar(text("SELECT count(*) FROM business_offerings")) == 2
        assert await connection.scalar(text("SELECT count(*) FROM business_offering_promotions")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='catalog.updated'")) == 4
        assert await connection.scalar(text("SELECT count(*) FROM outbox_events")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM billing_accounts")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM business_brand_kit_versions")) == 0
        assert await connection.scalar(text("SELECT min(version) FROM business_offerings")) == 4


async def test_catalog_concurrency_and_operation_reuse_across_businesses(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    other_business = await _business(admin, tenant)
    base, headers = _base(tenant, business), _headers(settings, actor)
    payload = _payload()
    simultaneous = await asyncio.gather(*[api.put(base, headers=headers, json=payload) for _ in range(2)])
    assert [response.status_code for response in simultaneous] == [200, 200]
    assert simultaneous[0].json() == simultaneous[1].json()
    competing = await asyncio.gather(*[api.put(base, headers=headers, json=_next(payload, 1)) for _ in range(2)])
    assert sorted(response.status_code for response in competing) == [200, 409]
    wrong_business = await api.put(_base(tenant, other_business), headers=headers, json=payload)
    assert wrong_business.json()["error_code"] == "CATALOG_OPERATION_CONFLICT"
    # Different businesses may independently start at version zero with fresh operations.
    assert (await api.put(_base(tenant, other_business), headers=headers, json=_next(payload, 0))).status_code == 200
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_catalog_versions")) == 3
        assert await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='catalog.updated'")) == 3


async def test_catalog_change_waits_for_admitted_work_and_is_applied_once(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    service, gate = BusinessCatalogService(database), VisualConsentGate(database)
    first = _payload()
    assert (await service.update(tenant, business, actor, CatalogUpdate.model_validate(first))).version == 1
    await gate.enable(tenant, business, actor)
    run, operation = uuid4(), uuid4()
    assert await gate.admit(tenant, business, actor, run, operation, 1)
    changed = _next(first, 1)
    changed["offerings"][0]["price_minor"] = 2200
    changed["promotions"][0]["price_minor"] = 1900
    request = CatalogUpdate.model_validate(changed)
    pending = await service.update(tenant, business, actor, request)
    assert pending.version == 1 and pending.offerings[0].price_minor == 1800
    assert pending.pending_change is not None and pending.pending_change.operation_id == request.operation_id
    assert (await service.update(tenant, business, actor, request)) == pending
    assert (await service.read(tenant, business, actor)).pending_change == pending.pending_change
    assert (await service.read(tenant, business, actor, 1)).pending_change is None
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    conflicting = _next(first, 1)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_ALREADY_PENDING"):
        await service.update(tenant, business, actor, CatalogUpdate.model_validate(conflicting))
    await gate.finish(tenant, business, actor, operation, 1)
    updated = await service.read(tenant, business, actor)
    assert updated.version == 2 and updated.pending_change is None
    assert updated.offerings[0].price_minor == 2200 and updated.promotions[0].price_minor == 1900
    assert (await service.update(tenant, business, actor, request)) == updated
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_catalog_versions")) == 2


async def test_catalog_owner_only_rls_composite_references_and_history_permissions(
    admin, api, database, seeded, settings
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    other_business = await _business(admin, tenant)
    foreign_business = await _business(admin, seeded["t2"])
    headers, base = _headers(settings, actor), _base(tenant, business)
    payload = _payload()
    assert (await api.put(base, headers=headers, json=payload)).status_code == 200
    foreign_payload = _payload()
    assert (
        await api.put(
            _base(seeded["t2"], foreign_business), headers=_headers(settings, seeded["a2"]), json=foreign_payload
        )
    ).status_code == 200
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO platform_staff(actor_id,active) VALUES(:actor,true)"), {"actor": seeded["a2"]}
        )
        await connection.execute(
            text("UPDATE auth_sessions SET mfa_verified=true WHERE user_id=:actor"), {"actor": seeded["a2"]}
        )
    for denied_actor in (seeded["viewer"], seeded["a2"]):
        denied = _headers(settings, denied_actor)
        assert (await api.get(base, headers=denied)).status_code == 403
        assert (await api.get(base + "/history", headers=denied)).status_code == 403
        assert (await api.put(base, headers=denied, json=_next(payload, 1))).status_code == 403
    assert (await api.get(_base(tenant, foreign_business), headers=headers)).status_code == 403
    assert (await api.get(_base(tenant, uuid4()), headers=headers)).status_code == 403
    for table in (
        "business_catalog_heads",
        "business_catalog_versions",
        "business_offerings",
        "business_offering_promotions",
    ):
        async with database.transaction(tenant, seeded["a2"]) as session:
            assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == 0
        async with database.transaction(tenant, seeded["viewer"]) as session:
            assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, seeded["a2"]) as session:
            await session.execute(
                text("INSERT INTO business_catalog_heads(tenant_id,business_id) VALUES(:t,:b)"),
                {"t": tenant, "b": other_business},
            )
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(text("UPDATE business_catalog_versions SET document='{}'::jsonb"))
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(text("DELETE FROM business_offerings"))
    # A promotion cannot point to an offering from a different business, even inside one tenant.
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO business_catalog_heads(tenant_id,business_id) VALUES(:t,:b)"),
            {"t": tenant, "b": other_business},
        )
        await connection.execute(
            text("""INSERT INTO business_catalog_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
          VALUES(:t,:b,1,:op,:actor,:hash,'{}'::jsonb)"""),
            {"t": tenant, "b": other_business, "op": uuid4(), "actor": actor, "hash": "a" * 64},
        )
        with pytest.raises(DBAPIError):
            async with connection.begin_nested():
                await connection.execute(
                    text("""INSERT INTO business_offering_promotions
                  (tenant_id,business_id,id,offering_id,title,state,starts_at,ends_at,version)
                  VALUES(:t,:b,:id,:offering,'Wrong business','draft',now(),now()+interval '1 day',1)"""),
                    {"t": tenant, "b": other_business, "id": uuid4(), "offering": payload["offerings"][0]["id"]},
                )


async def test_catalog_audit_failure_rolls_back_head_snapshot_and_projections(admin, database, seeded, monkeypatch):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    service = BusinessCatalogService(database)

    async def failed_audit(*_args):
        raise RuntimeError("Audit unavailable")

    monkeypatch.setattr("app.services.business_catalog.audit_catalog_change", failed_audit)
    with pytest.raises(RuntimeError, match="Audit unavailable"):
        await service.update(tenant, business, actor, CatalogUpdate.model_validate(_payload()))
    assert (await service.read(tenant, business, actor)).version == 0
    async with admin.connect() as connection:
        for table in (
            "business_catalog_heads",
            "business_catalog_versions",
            "business_offerings",
            "business_offering_promotions",
        ):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
