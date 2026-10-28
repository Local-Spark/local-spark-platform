"""Private durable collection photos: real RLS, CAS, retries and source independence."""

import asyncio
import hashlib
import threading
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.adapters.material_media import MaterialError
from app.schemas.business_catalog import CatalogUpdate, Offering
from app.schemas.business_collection import CollectionPhotoPromotion, CollectionPhotoUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.business_collection import BusinessCollectionService
from app.tests.unit.test_business_collection_contract import picture, upload
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _business(admin, seeded, name="Collection business"):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,:name,'UTC')"),
            {"id": business, "tenant": seeded["t1"], "name": name},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": seeded["t1"], "business": business},
        )
    return business


class Store:
    # This fake performs exactly one write per put call.
    single_attempt_put = True

    def __init__(self):
        self.objects = {}
        self.reads = 0
        self.fail_put = False
        self.fail_delete = False

    async def put(self, key, media):
        if self.fail_put:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        await asyncio.sleep(0)
        self.objects[key] = media.data

    async def get_image(self, key, *, max_bytes=5 * 1024 * 1024):
        self.reads += 1
        if key not in self.objects:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        value = self.objects[key]
        if len(value) > max_bytes:
            raise MaterialError("MEDIA_SIZE_EXCEEDED")
        return value

    async def signed_url(self, key, mime):
        assert key in self.objects and mime == "image/png"
        return f"https://private.test/{key}?expires=120"

    async def delete(self, key):
        if self.fail_delete:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        self.objects.pop(key, None)


async def test_photo_crud_http_audit_versions_owner_rls_and_product_state(
    admin,
    api,
    database,
    seeded,
    settings,
    monkeypatch,
):
    from app.api.v1 import business_collection as routes

    business = await _business(admin, seeded)
    second_business = await _business(admin, {**seeded, "t1": seeded["t2"]}, "Second business")
    tenant, actor = seeded["t1"], seeded["a1"]
    store = Store()
    service = BusinessCollectionService(settings, database, store)
    monkeypatch.setattr(routes, "service", lambda request: service)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/collection/photos"
    assert (await api.get(path, headers=owner)).json() == []
    for unauthorized in (seeded["viewer"], seeded["a2"]):
        headers = {"Authorization": f"Bearer {access_token(settings, unauthorized)}"}
        assert (await api.get(path, headers=headers)).status_code == 403
        assert (await api.post(path, headers=headers, json=upload().model_dump(mode="json"))).status_code == 403
    body = upload()
    result = await api.post(path, headers=owner, json=body.model_dump(mode="json"))
    assert result.status_code == 201, result.text
    saved = result.json()
    photo = saved["id"]
    assert saved["version"] == 1 and saved["status"] == "active"
    assert "object_key" not in saved and "url" not in saved
    assert (await api.get(f"{path}/{photo}/url", headers=owner)).json()["expires_in_seconds"] == 120
    conflict = await api.post(path, headers=owner, json={**body.model_dump(mode="json"), "title": "Other"})
    assert conflict.json()["error_code"] == "COLLECTION_PHOTO_OPERATION_CONFLICT"
    change = {
        "operation_id": str(uuid4()),
        "expected_version": 1,
        "title": "Sala principal",
        "item_id": None,
        "space_kind": "room",
        "sort_order": 3,
        "status": "archived",
    }
    edited = await api.patch(f"{path}/{photo}", headers=owner, json=change)
    assert edited.status_code == 200 and edited.json()["version"] == 2
    assert (await api.patch(f"{path}/{photo}", headers=owner, json=change)).json() == edited.json()
    assert (await api.post(path, headers=owner, json=body.model_dump(mode="json"))).json() == saved
    wrong_operation = await api.patch(f"{path}/{photo}", headers=owner, json={**change, "title": "Changed"})
    assert wrong_operation.json()["error_code"] == "COLLECTION_PHOTO_OPERATION_CONFLICT"
    stale = await api.patch(f"{path}/{photo}", headers=owner, json={**change, "operation_id": str(uuid4())})
    assert stale.json()["error_code"] == "COLLECTION_PHOTO_VERSION_CONFLICT"
    cross_path = f"/api/v1/organizations/{seeded['t2']}/businesses/{second_business}/collection/photos"
    other_owner = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    assert (await api.get(f"{cross_path}/{photo}/url", headers=owner)).status_code == 403
    assert (await api.get(f"{cross_path}/{photo}/url", headers=other_owner)).status_code == 404
    assert (await api.get(f"{cross_path}/{photo}/history", headers=other_owner)).status_code == 404
    assert (
        await api.patch(f"{cross_path}/{photo}", headers=other_owner, json={**change, "operation_id": str(uuid4())})
    ).status_code == 404
    assert (
        await api.delete(
            f"{cross_path}/{photo}", headers=other_owner, params={"operation_id": str(uuid4()), "expected_version": 2}
        )
    ).status_code == 404
    assert len((await api.get(path, headers=owner)).json()) == 1
    missing = await api.get(f"{path}/{uuid4()}/url", headers=owner)
    assert missing.status_code == 404
    history = (await api.get(f"{path}/{photo}/history", headers=owner)).json()
    assert [row["version"] for row in history] == [2, 1]
    assert history[1]["photo"]["title"] == "Balcão"
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_collection_photos")) == 0
        assert await session.scalar(text("SELECT count(*) FROM business_collection_photo_versions")) == 0
    async with database.transaction(tenant, seeded["viewer"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_collection_photos")) == 0
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM outbox_events")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action LIKE 'collection.%'")) == 2

    offering = Offering(id=uuid4(), kind="product", name="Croissant", state="active")
    catalog = BusinessCatalogService(database)
    await catalog.update(
        tenant, business, actor, CatalogUpdate(operation_id=uuid4(), expected_version=0, offerings=[offering])
    )
    item_body = upload(space_kind=None, item_id=str(offering.id))
    item_photo = await service.upload(tenant, business, actor, item_body)
    with pytest.raises(AuthError, match="COLLECTION_ITEM_NOT_ACTIVE"):
        await service.upload(
            seeded["t2"], second_business, seeded["a2"], item_body.model_copy(update={"operation_id": uuid4()})
        )
    await catalog.update(
        tenant,
        business,
        actor,
        CatalogUpdate(
            operation_id=uuid4(), expected_version=1, offerings=[offering.model_copy(update={"state": "archived"})]
        ),
    )
    archive = CollectionPhotoUpdate(
        operation_id=uuid4(), expected_version=1, title="Produto anterior", item_id=offering.id, status="archived"
    )
    archived = await service.update(tenant, business, actor, item_photo.id, archive)
    assert archived.status == "archived"
    with pytest.raises(AuthError, match="COLLECTION_ITEM_NOT_ACTIVE"):
        await service.update(
            tenant,
            business,
            actor,
            item_photo.id,
            archive.model_copy(update={"operation_id": uuid4(), "expected_version": 2, "status": "active"}),
        )


async def test_concurrent_photo_upload_and_edit_have_one_identity_and_cas(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    store = Store()
    service = BusinessCollectionService(settings, database, store)
    body = upload()
    first = await service.upload(tenant, business, actor, body)
    assert await service.upload(tenant, business, actor, body) == first and len(store.objects) == 1
    edit = CollectionPhotoUpdate(
        operation_id=uuid4(), expected_version=1, title="Updated", space_kind="counter", status="active"
    )
    results = await asyncio.gather(
        service.update(tenant, business, actor, first.id, edit),
        service.update(tenant, business, actor, first.id, edit.model_copy(update={"operation_id": uuid4()})),
        return_exceptions=True,
    )
    assert sum(isinstance(row, AuthError) and row.code == "COLLECTION_PHOTO_VERSION_CONFLICT" for row in results) == 1
    store.fail_put = True
    retry_body = upload()
    with pytest.raises(MaterialError):
        await service.upload(tenant, business, actor, retry_body)
    pending = [photo for photo in await service.list_photos(tenant, business, actor) if photo.version == 0]
    assert len(pending) == 1
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_collection_photos SET upload_lease_until=now()-interval '1 minute' WHERE id=:id"),
            {"id": pending[0].id},
        )
    assert (await service.delete(tenant, business, actor, pending[0].id, uuid4(), 0)).status == "quarantined"
    store.fail_put = False
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_BUSY"):
        await service.upload(tenant, business, actor, retry_body)
    assert (
        await service.upload(tenant, business, actor, retry_body.model_copy(update={"operation_id": uuid4()}))
    ).version == 1


async def test_whatsapp_promotion_is_explicit_private_copy_and_survives_original_purge(
    admin,
    database,
    seeded,
    settings,
):
    business = await _business(admin, seeded)
    other_business = await _business(admin, {**seeded, "t1": seeded["t2"]}, "Other")
    tenant, actor, material = seeded["t1"], seeded["a1"], uuid4()
    store = Store()
    raw = picture()
    key = f"original/{material}"
    store.objects[key] = raw
    service = BusinessCollectionService(settings, database, store)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id)
          VALUES(:tenant,:business,:actor)"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
          (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type,size_bytes,sha256)
          VALUES(:id,:tenant,:business,'image','private',:key,'image/png',:size,:sha)"""),
            {
                "id": material,
                "tenant": tenant,
                "business": business,
                "key": key,
                "size": len(raw),
                "sha": hashlib.sha256(raw).hexdigest(),
            },
        )
    body = CollectionPhotoPromotion(
        operation_id=uuid4(),
        material_id=material,
        title="Local real",
        space_kind="environment",
        rights_confirmed=True,
        keep_in_collection=True,
    )
    with pytest.raises(AuthError, match="COLLECTION_SOURCE_NOT_AVAILABLE"):
        await service.promote(
            seeded["t2"], other_business, seeded["a2"], body.model_copy(update={"operation_id": uuid4()})
        )
    copy = await service.promote(tenant, business, actor, body)
    assert copy.source == "whatsapp" and copy.source_material_id == material
    assert copy.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert len(store.objects) == 2
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE whatsapp_processing_consents SET revoked_at=now()"))
        await connection.execute(text("DELETE FROM whatsapp_material_assets WHERE id=:id"), {"id": material})
    store.objects.pop(key)
    assert await service.promote(tenant, business, actor, body) == copy
    assert store.reads == 1
    assert (await service.url(tenant, business, actor, copy.id)).url
    with pytest.raises(AuthError, match="COLLECTION_SOURCE_NOT_AVAILABLE"):
        await service.promote(tenant, business, actor, body.model_copy(update={"operation_id": uuid4()}))


async def test_delete_tombstone_retry_and_abandoned_intent_cleanup(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    store = Store()
    service = BusinessCollectionService(settings, database, store)
    photo = await service.upload(tenant, business, actor, upload())
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_VERSION_CONFLICT"):
        await service.delete(tenant, business, actor, photo.id, uuid4(), 2)
    operation = uuid4()
    store.fail_delete = True
    assert (await service.delete(tenant, business, actor, photo.id, operation, 1)).status == "deleting"
    assert await service.list_photos(tenant, business, actor) == []
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_FOUND"):
        await service.url(tenant, business, actor, photo.id)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_READY"):
        await service.update(
            tenant,
            business,
            actor,
            photo.id,
            CollectionPhotoUpdate(
                operation_id=uuid4(), expected_version=2, title="Again", space_kind="room", status="active"
            ),
        )
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_collection_photos SET delete_lease_until=now()-interval '1 minute'")
        )
    store.fail_delete = False
    assert (await service.delete(tenant, business, actor, photo.id, operation, 1)).status == "deleted"
    assert len(store.objects) == 0
    assert [row.photo.status for row in await service.history(tenant, business, actor, photo.id)] == [
        "deleted",
        "active",
    ]
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_READY"):
        await service.delete(tenant, business, actor, photo.id, uuid4(), 2)
    bad = upload(content_base64="not-valid-base64!")
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_INVALID"):
        await service.upload(tenant, business, actor, bad)
    assert await service.reconcile(tenant, business, actor) == 0
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_collection_photos SET created_at=now()-interval '2 hours',
          upload_lease_until=now()-interval '1 hour' WHERE state='pending'""")
        )
    assert await service.reconcile(tenant, business, actor) == 0
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await service.upload(tenant, business, actor, bad)


class BlockingStore(Store):
    def __init__(self, outcome="success"):
        super().__init__()
        self.outcome = outcome
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.put_calls = 0

    async def put(self, key, media):
        self.put_calls += 1
        self.started.set()
        await asyncio.wait_for(self.release.wait(), timeout=5)
        await super().put(key, media)
        if self.outcome == "ambiguous":
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        if self.outcome == "cancelled":
            raise asyncio.CancelledError()


async def test_same_operation_never_starts_a_second_writer(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    store = BlockingStore()
    service = BusinessCollectionService(settings, database, store)
    body = upload()
    task = asyncio.create_task(service.upload(tenant, business, actor, body))
    await asyncio.wait_for(store.started.wait(), timeout=5)
    try:
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_BUSY"):
            await service.upload(tenant, business, actor, body)
        assert store.put_calls == 1
    finally:
        store.release.set()
    saved = await task
    assert await service.upload(tenant, business, actor, body) == saved
    assert (await service.delete(tenant, business, actor, saved.id, uuid4(), 1)).status == "deleted"
    assert store.objects == {}


@pytest.mark.parametrize("fail_compensation", [False, True])
@pytest.mark.parametrize("outcome", ["success", "ambiguous", "cancelled"])
async def test_delayed_put_is_not_cleaned_before_writer_stops(
    admin,
    database,
    seeded,
    settings,
    fail_compensation,
    outcome,
):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    store = BlockingStore(outcome)
    service = BusinessCollectionService(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(store.started.wait(), timeout=5)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_collection_photos SET created_at=now()-interval '2 hours',
          upload_lease_until=now()-interval '1 hour' WHERE state='pending'""")
        )
    assert await service.reconcile(tenant, business, actor) == 0
    assert store.objects == {}
    store.fail_delete = fail_compensation
    store.release.set()
    if outcome == "success":
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
            await task
    else:
        with pytest.raises(MaterialError if outcome == "ambiguous" else asyncio.CancelledError):
            await task
    # Neither a timeout nor an expired lease proves that a storage write has
    # stopped. The owner may discard the intent while its private key remains
    # quarantined for later, separately verified cleanup.
    assert len(store.objects) == 1
    pending = (await service.list_photos(tenant, business, actor))[0]
    assert pending.pending_uncertain and pending.pending_cancelable
    assert (await service.delete(tenant, business, actor, pending.id, uuid4(), 0)).status == "quarantined"
    assert len(store.objects) == 1
    assert (await service.list_photos(tenant, business, actor))[0].pending_quarantined
    assert (await service.removals(tenant, business, actor))["pending"] == 0


async def test_operation_reuse_across_photos_is_conflict_before_mutation(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    service = BusinessCollectionService(settings, database, Store())
    first = await service.upload(tenant, business, actor, upload())
    second = await service.upload(tenant, business, actor, upload())
    edit = CollectionPhotoUpdate(
        operation_id=uuid4(), expected_version=1, title="First changed", space_kind="counter", status="active"
    )
    await service.update(tenant, business, actor, first.id, edit)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT"):
        await service.update(tenant, business, actor, second.id, edit)
    assert (await service.history(tenant, business, actor, second.id))[0].version == 1
    third = await service.upload(tenant, business, actor, upload())
    concurrent = edit.model_copy(update={"operation_id": uuid4()})
    results = await asyncio.gather(
        service.update(tenant, business, actor, second.id, concurrent),
        service.update(tenant, business, actor, third.id, concurrent),
        return_exceptions=True,
    )
    assert (
        sum(isinstance(item, AuthError) and item.code == "COLLECTION_PHOTO_OPERATION_CONFLICT" for item in results) == 1
    )
    delete_operation = uuid4()
    await service.delete(tenant, business, actor, first.id, delete_operation, 2)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT"):
        await service.delete(tenant, business, actor, second.id, delete_operation, 1)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT"):
        await service.upload(tenant, business, actor, upload(operation_id=str(concurrent.operation_id)))


async def test_cancelled_threaded_put_is_drained_and_private_key_is_preserved(admin, database, seeded, settings):
    class ThreadStore(Store):
        def __init__(self):
            super().__init__()
            self.started = asyncio.Event()
            self.release = threading.Event()

        async def put(self, key, media):
            loop = asyncio.get_running_loop()

            def write():
                loop.call_soon_threadsafe(self.started.set)
                assert self.release.wait(timeout=5)
                self.objects[key] = media.data

            await asyncio.to_thread(write)

    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    store = ThreadStore()
    service = BusinessCollectionService(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(store.started.wait(), timeout=5)
    try:
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert await service.reconcile(tenant, business, actor) == 0
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT state FROM business_collection_photos")) == "pending"
        # Repeated cancellation must not allow cleanup before the writer ends.
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        store.release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=5)
    assert len(store.objects) == 1 and (await service.removals(tenant, business, actor))["pending"] == 0
    pending = (await service.list_photos(tenant, business, actor))[0]
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE business_collection_photos SET upload_lease_until=now()-interval '1 minute' WHERE id=:id"),
            {"id": pending.id},
        )
    assert (await service.delete(tenant, business, actor, pending.id, uuid4(), 0)).status == "quarantined"
    assert len(store.objects) == 1
