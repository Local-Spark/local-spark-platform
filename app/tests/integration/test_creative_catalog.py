"""BL04 catalog context respects owner, tenant, source versions and local time."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog import catalog_candidates, selected_catalog_snapshot, validate_catalog_snapshot
from app.tests.integration.test_business_catalog import _business, _payload

pytestmark = pytest.mark.integration


async def _photo(admin, tenant, business, actor, *, item=None, kind=None, archived=False):
    photo = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_collection_photos
              (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,sha256,mime_type,size_bytes,
               title,item_id,space_kind,sort_order,status,version,state,source,rights_scope)
              VALUES(:id,:tenant,:business,:operation,:actor,:hash,:object,:sha,'image/png',10,
               'Fixture',:item,:kind,0,:status,1,'ready','upload','business_collection_confirmed')"""),
            {
                "id": photo,
                "tenant": tenant,
                "business": business,
                "operation": uuid4(),
                "actor": actor,
                "hash": "a" * 64,
                "object": f"synthetic/{photo}",
                "sha": "b" * 64,
                "item": item,
                "kind": kind,
                "status": "archived" if archived else "active",
            },
        )
    return photo


async def test_retrieval_and_snapshot_exclude_other_tenants_drafts_expired_prices_and_archived_photos(
    admin, database, seeded
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    other = await _business(admin, seeded["t2"])
    data = _payload()
    item = UUID(data["offerings"][0]["id"])
    data["offerings"][0]["price_valid_until"] = "2026-10-27"
    data["offerings"][1]["aliases"] = ["Croissant escondido"]
    service = BusinessCatalogService(database)
    await service.update(tenant, business, actor, CatalogUpdate.model_validate(data))
    await service.update(seeded["t2"], other, seeded["a2"], CatalogUpdate.model_validate(_payload()))
    item_photo = await _photo(admin, tenant, business, actor, item=item)
    space_photo = await _photo(admin, tenant, business, actor, kind="room")
    await _photo(admin, tenant, business, actor, kind="environment", archived=True)
    instant = datetime(2026, 10, 28, 1, 0, tzinfo=UTC)
    async with admin.begin() as session:
        await session.execute(text("UPDATE businesses SET timezone='America/Sao_Paulo' WHERE id=:id"), {"id": business})
    async with database.transaction(tenant, actor) as session:
        candidates = await catalog_candidates(session, tenant, business, actor, "Faça uma foto do folhado")
        assert candidates == {
            "status": "needs_selection",
            "catalog_version": 1,
            "candidates": [{"id": str(item), "kind": "product", "name": "Croissant"}],
        }
        snapshot = await selected_catalog_snapshot(
            session, tenant, business, actor, "foto do folhado", item, 1, instant
        )
        assert snapshot["offering"]["price"]["status"] == "valid"
        assert snapshot["item_photo"]["id"] == str(item_photo)
        assert snapshot["space_photo"]["id"] == str(space_photo)
        assert len(snapshot["promotions"]) == 1
        assert "object_key" not in str(snapshot) and "url" not in str(snapshot)
        assert await validate_catalog_snapshot(session, tenant, business, actor, snapshot, instant) == "valid"
    async with database.transaction(tenant, actor) as session:
        expired = await selected_catalog_snapshot(
            session, tenant, business, actor, "foto do croissant", item, 1, datetime(2026, 10, 28, 4, tzinfo=UTC)
        )
        assert expired["offering"]["price"]["status"] == "expired"
        assert expired["offering"]["price"]["amount_minor"] is None
        assert (
            await validate_catalog_snapshot(
                session, tenant, business, actor, snapshot, datetime(2026, 10, 28, 4, tzinfo=UTC)
            )
            == "price_changed_or_expired"
        )
    async with admin.begin() as session:
        await session.execute(
            text("UPDATE business_collection_photos SET status='archived' WHERE id=:id"), {"id": item_photo}
        )
    async with database.transaction(tenant, actor) as session:
        assert (
            await validate_catalog_snapshot(session, tenant, business, actor, snapshot, instant)
            == "photo_changed_or_removed"
        )
    async with database.transaction(tenant, seeded["viewer"]) as session:
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await catalog_candidates(session, tenant, business, seeded["viewer"], "croissant")
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await catalog_candidates(session, seeded["t2"], business, seeded["a2"], "croissant")
    changed = deepcopy(data)
    changed["operation_id"] = str(uuid4())
    changed["expected_version"] = 1
    changed["offerings"][0]["state"] = "archived"
    changed["promotions"][0]["state"] = "archived"
    await service.update(tenant, business, actor, CatalogUpdate.model_validate(changed))
    async with database.transaction(tenant, actor) as session:
        with pytest.raises(AuthError, match="COLLECTION_CONTEXT_CHANGED"):
            await selected_catalog_snapshot(session, tenant, business, actor, "croissant", item, 1, instant)
        assert (await catalog_candidates(session, tenant, business, actor, "croissant"))["status"] == "not_found"
        assert await validate_catalog_snapshot(session, tenant, business, actor, snapshot, instant) == "catalog_changed"
