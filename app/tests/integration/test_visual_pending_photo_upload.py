"""Photo inclusions use a private staging record while visual work is admitted."""

import asyncio
import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.schemas.business_collection import CollectionPhotoPromotion
from app.services.auth import AuthError
from app.services.business_collection import BusinessCollectionService
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_proposals import _business
from app.tests.unit.test_business_collection_contract import picture, upload

pytestmark = pytest.mark.integration


async def test_upload_reserves_gate_before_storage_and_waits_for_both_work_and_put(admin, database, seeded, settings):
    class PausedStore(Store):
        def __init__(self):
            super().__init__()
            self.entered, self.release = asyncio.Event(), asyncio.Event()

        async def put(self, key, media):
            self.entered.set()
            await self.release.wait()
            await super().put(key, media)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    operation = uuid4()
    assert await gate.admit(tenant, business, actor, uuid4(), operation, 1)
    store = PausedStore()
    service = BusinessCollectionService(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(store.entered.wait(), 5)
    try:
        pending = (await service.list_photos(tenant, business, actor))[0]
        assert pending.version == 0 and pending.pending_activation and pending.pending_change
        with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
            await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
        # Once the SHA is committed, expiry alone cannot prove the writer stopped.
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_collection_photos SET upload_lease_until=now()-interval '1 minute'")
            )
        pending = (await service.list_photos(tenant, business, actor))[0]
        assert pending.pending_uncertain and pending.pending_cancelable
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_collection_photos SET upload_lease_until=now()+interval '10 minutes'")
            )
        await gate.finish(tenant, business, actor, operation, 1)
        assert (await service.list_photos(tenant, business, actor))[0].version == 0
        with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
            await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    finally:
        store.release.set()
    result = await asyncio.wait_for(task, 5)
    assert not result.pending_activation
    assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)


async def test_invalid_upload_does_not_leave_gate_blocked(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    service = BusinessCollectionService(settings, database, Store())
    body = upload().model_copy(update={"content_base64": "invalid!"})
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_INVALID"):
        await service.upload(tenant, business, actor, body)
    assert await service.list_photos(tenant, business, actor) == []
    assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)


async def test_expired_unstarted_upload_is_visible_and_cancelled_before_any_put(admin, database, seeded, settings):
    class PausedBeforeHash(BusinessCollectionService):
        def __init__(self, settings, database, store):
            super().__init__(settings, database, store)
            self.entered, self.release = asyncio.Event(), asyncio.Event()

        async def _complete(self, *args, **kwargs):
            self.entered.set()
            await self.release.wait()
            return await super()._complete(*args, **kwargs)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    store = Store()
    service = PausedBeforeHash(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(service.entered.wait(), 5)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_collection_photos SET upload_lease_until=now()-interval '1 minute'")
            )
        pending = (await service.list_photos(tenant, business, actor))[0]
        assert pending.version == 0 and pending.pending_cancelable and pending.pending_change
        assert (await service.delete(tenant, business, actor, pending.id, uuid4(), 0)).status == "deleted"
        assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    finally:
        service.release.set()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await task
    assert store.objects == {}


async def test_completed_put_rejected_at_finalization_can_be_cancelled(admin, database, seeded, settings):
    class RejectedFinalize(BusinessCollectionService):
        async def _finalize_photo(self, *args, **kwargs):
            raise AuthError("COLLECTION_SOURCE_NOT_AVAILABLE", 409)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    store = Store()
    service = RejectedFinalize(settings, database, store)
    with pytest.raises(AuthError, match="COLLECTION_SOURCE_NOT_AVAILABLE"):
        await service.upload(tenant, business, actor, upload())
    pending = (await service.list_photos(tenant, business, actor))[0]
    assert pending.version == 0 and pending.pending_recovery and pending.pending_cancelable
    assert len(store.objects) == 1
    assert (await service.delete(tenant, business, actor, pending.id, uuid4(), 0)).status == "deleted"
    assert store.objects == {}
    assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)


async def test_cancelled_completed_put_cannot_be_revived_by_delayed_finalizer(admin, database, seeded, settings):
    class PausedFinalizer(BusinessCollectionService):
        def __init__(self, settings, database, store):
            super().__init__(settings, database, store)
            self.entered, self.release = asyncio.Event(), asyncio.Event()

        async def _finalize_photo(self, *args, **kwargs):
            self.entered.set()
            await self.release.wait()
            return await super()._finalize_photo(*args, **kwargs)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    store = Store()
    service = PausedFinalizer(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(service.entered.wait(), 5)
    try:
        pending = (await service.list_photos(tenant, business, actor))[0]
        assert pending.pending_recovery and pending.pending_cancelable
        assert (await service.delete(tenant, business, actor, pending.id, uuid4(), 0)).status == "deleted"
    finally:
        service.release.set()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await task
    assert store.objects == {} and await service.list_photos(tenant, business, actor) == []


async def test_uploaded_photo_waits_privately_then_activates_once(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    first, second = uuid4(), uuid4()
    assert await gate.admit(tenant, business, actor, uuid4(), first, 1)
    assert await gate.admit(tenant, business, actor, uuid4(), second, 2)
    store = Store()
    service = BusinessCollectionService(settings, database, store)
    body = upload()
    staged = await service.upload(tenant, business, actor, body)
    assert staged.pending_change and staged.pending_activation and staged.version == 1
    assert await service.upload(tenant, business, actor, body) == staged
    assert len(store.objects) == 1
    assert (await service.list_photos(tenant, business, actor))[0] == staged
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_FOUND"):
        await service.url(tenant, business, actor, staged.id)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    async with admin.connect() as connection:
        record = (
            (
                await connection.execute(
                    text("SELECT state,payload FROM business_visual_pending_changes WHERE operation_id=:op"),
                    {"op": body.operation_id},
                )
            )
            .mappings()
            .one()
        )
        assert record["state"] == "pending" and record["payload"] == {"photo_id": str(staged.id)}
    await gate.finish(tenant, business, actor, first, 1)
    assert (await service.list_photos(tenant, business, actor))[0].pending_activation
    await gate.finish(tenant, business, actor, second, 2)
    ready = (await service.list_photos(tenant, business, actor))[0]
    assert not ready.pending_change and not ready.pending_activation
    assert (await service.url(tenant, business, actor, ready.id)).url
    assert len(await service.history(tenant, business, actor, ready.id)) == 1
    assert await service.upload(tenant, business, actor, body) == ready
    assert len(store.objects) == 1


async def test_pending_whatsapp_photo_rechecks_origin_and_failed_upload_can_be_discarded(
    admin, database, seeded, settings
):
    tenant, actor, material = seeded["t1"], seeded["a1"], uuid4()
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    operation = uuid4()
    assert await gate.admit(tenant, business, actor, uuid4(), operation, 1)
    store = Store()
    data = picture()
    key = f"original/{material}"
    store.objects[key] = data
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id) VALUES(:t,:b,:a)"),
            {"t": tenant, "b": business, "a": actor},
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_material_assets
              (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type,size_bytes,sha256)
              VALUES(:id,:t,:b,'image','private',:key,'image/png',:size,:sha)"""),
            {
                "id": material,
                "t": tenant,
                "b": business,
                "key": key,
                "size": len(data),
                "sha": hashlib.sha256(data).hexdigest(),
            },
        )
    service = BusinessCollectionService(settings, database, store)
    body = CollectionPhotoPromotion(
        operation_id=uuid4(),
        material_id=material,
        title="Espaço",
        space_kind="room",
        rights_confirmed=True,
        keep_in_collection=True,
    )
    staged = await service.promote(tenant, business, actor, body)
    assert staged.pending_activation and staged.pending_change
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE whatsapp_processing_consents SET revoked_at=now()"))
    await gate.finish(tenant, business, actor, operation, 1)
    failed = (await service.list_photos(tenant, business, actor))[0]
    assert failed.pending_activation and not failed.pending_change
    assert failed.pending_change_error == "COLLECTION_SOURCE_NOT_AVAILABLE"
    assert (await service.promote(tenant, business, actor, body)).pending_change_error == failed.pending_change_error
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    assert (await service.delete(tenant, business, actor, failed.id, uuid4(), failed.version)).status == "deleted"
    assert await service.list_photos(tenant, business, actor) == []
    assert len(store.objects) == 1 and key in store.objects
    assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)


@pytest.mark.parametrize("pause_after_commit", [False, True])
@pytest.mark.parametrize("generation_running", [False, True])
async def test_cancel_during_confirmation_never_deletes_a_committed_or_uncertain_photo(
    admin, database, seeded, settings, pause_after_commit, generation_running
):
    class PausedFinalize(BusinessCollectionService):
        def __init__(self, settings, database, store):
            super().__init__(settings, database, store)
            self.entered, self.release = asyncio.Event(), asyncio.Event()

        async def _finalize_photo(self, *args, **kwargs):
            if not pause_after_commit:
                self.entered.set()
                await self.release.wait()
            result = await super()._finalize_photo(*args, **kwargs)
            if pause_after_commit:
                self.entered.set()
                await self.release.wait()
            return result

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    operation = uuid4()
    if generation_running:
        await gate.enable(tenant, business, actor)
        assert await gate.admit(tenant, business, actor, uuid4(), operation, 1)
    store = Store()
    service = PausedFinalize(settings, database, store)
    body = upload()
    task = asyncio.create_task(service.upload(tenant, business, actor, body))
    await asyncio.wait_for(service.entered.wait(), 5)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    service.release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 5)
    saved = await service.upload(tenant, business, actor, body)
    assert len(store.objects) == 1 and saved.pending_activation == generation_running
    if generation_running:
        await gate.finish(tenant, business, actor, operation, 1)
        assert not (await service.list_photos(tenant, business, actor))[0].pending_activation


async def test_unknown_finalization_outcome_is_not_cleaned_by_timeout(admin, database, seeded, settings):
    class UncertainFinalize(BusinessCollectionService):
        async def _finalize_photo(self, *args, **kwargs):
            raise RuntimeError("synthetic unknown database outcome")

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    store = Store()
    service = UncertainFinalize(settings, database, store)
    body = upload()
    with pytest.raises(RuntimeError, match="synthetic unknown database outcome"):
        await service.upload(tenant, business, actor, body)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_collection_photos SET created_at=now()-interval '2 hours'
          WHERE tenant_id=:tenant AND business_id=:business"""),
            {"tenant": tenant, "business": business},
        )
        state = (
            (
                await connection.execute(
                    text("""SELECT state,version,upload_lease_until
          FROM business_collection_photos WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one()
        )
    assert state["state"] == "pending" and state["version"] == 0 and state["upload_lease_until"] is None
    assert await service.reconcile(tenant, business, actor) == 0
    assert len(store.objects) == 1
    waiting = (await service.list_photos(tenant, business, actor))[0]
    assert waiting.pending_recovery and waiting.pending_activation and waiting.version == 0
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_FOUND"):
        await service.url(tenant, business, actor, waiting.id)
    original_key, original_data = next(iter(store.objects.items()))
    store.objects[original_key] = b"different bytes"
    resumed = BusinessCollectionService(settings, database, store)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RECOVERY_MISMATCH"):
        await resumed.resume_upload(tenant, business, actor, waiting.id)
    assert store.objects[original_key] == b"different bytes"
    store.objects.pop(original_key)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RECOVERY_UNAVAILABLE"):
        await resumed.resume_upload(tenant, business, actor, waiting.id)
    assert store.objects == {}
    store.objects[original_key] = original_data
    other_owner = seeded["viewer"]
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": other_owner},
        )
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OWNER_REQUIRED"):
        await resumed.resume_upload(tenant, business, other_owner, waiting.id)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": actor},
        )
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await resumed.resume_upload(tenant, business, actor, waiting.id)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": actor},
        )
    ready = await resumed.resume_upload(tenant, business, actor, waiting.id)
    assert not ready.pending_recovery and not ready.pending_activation
    assert (await resumed.url(tenant, business, actor, ready.id)).url
    assert len(store.objects) == 1


async def test_recovery_racing_original_finalization_never_rewrites_or_creates_duplicate(
    admin, database, seeded, settings
):
    class PausedBeforeFinalize(BusinessCollectionService):
        def __init__(self, settings, database, store):
            super().__init__(settings, database, store)
            self.entered, self.release = asyncio.Event(), asyncio.Event()

        async def _finalize_photo(self, *args, **kwargs):
            self.entered.set()
            await self.release.wait()
            return await super()._finalize_photo(*args, **kwargs)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate, operation = VisualConsentGate(database), uuid4()
    await gate.enable(tenant, business, actor)
    assert await gate.admit(tenant, business, actor, uuid4(), operation, 1)
    store = Store()
    original = PausedBeforeFinalize(settings, database, store)
    task = asyncio.create_task(original.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(original.entered.wait(), 5)
    try:
        service = BusinessCollectionService(settings, database, store)
        waiting = (await service.list_photos(tenant, business, actor))[0]
        assert waiting.pending_recovery
        recovered = await service.resume_upload(tenant, business, actor, waiting.id)
        assert recovered.pending_change and recovered.pending_activation and not recovered.pending_recovery
    finally:
        original.release.set()
    assert await task == recovered
    await gate.finish(tenant, business, actor, operation, 1)
    assert len(store.objects) == 1
    assert len(await service.history(tenant, business, actor, recovered.id)) == 1
