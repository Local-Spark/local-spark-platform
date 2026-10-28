"""Discarding an uncertain upload never deletes a key that a late writer can recreate."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.services.auth import AuthError
from app.services.business_collection import BusinessCollectionService
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_proposals import _business
from app.tests.unit.test_business_collection_contract import upload

pytestmark = pytest.mark.integration


async def test_quarantined_late_writer_cannot_revive_or_delete_key(admin, database, seeded, settings):
    class PausedStore(Store):
        def __init__(self):
            super().__init__()
            self.entered = asyncio.Event()
            self.release = asyncio.Event()

        async def put(self, key, media):
            self.entered.set()
            await self.release.wait()
            await super().put(key, media)

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    store = PausedStore()
    service = BusinessCollectionService(settings, database, store)
    body = upload()
    task = asyncio.create_task(service.upload(tenant, business, actor, body))
    await asyncio.wait_for(store.entered.wait(), 5)
    pending = (await service.list_photos(tenant, business, actor))[0]
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE business_collection_photos SET upload_lease_until=now()-interval '1 minute'
                    WHERE tenant_id=:tenant AND business_id=:business AND id=:photo"""),
                {"tenant": tenant, "business": business, "photo": pending.id},
            )
        pending = (await service.list_photos(tenant, business, actor))[0]
        assert pending.pending_uncertain and pending.pending_cancelable
        op = uuid4()
        assert (await service.delete(tenant, business, actor, pending.id, op, 0)).status == "quarantined"
        assert (await service.delete(tenant, business, actor, pending.id, op, 0)).status == "quarantined"
        quarantined = (await service.list_photos(tenant, business, actor))[0]
        assert quarantined.pending_quarantined and not quarantined.pending_uncertain
        # SQL from the previous worker version did not check upload_owner or
        # upload_quarantined. The database must reject it even through the app role.
        with pytest.raises(IntegrityError):
            async with database.transaction(tenant, actor) as session:
                await session.execute(
                    text("""UPDATE business_collection_photos SET state='deleting',delete_lease_until=NULL
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND actor_id=:actor
                        AND state='pending' AND version=0"""),
                    {"tenant": tenant, "business": business, "id": pending.id, "actor": actor},
                )
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_FOUND"):
            await service.url(tenant, business, actor, pending.id)
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_BUSY"):
            await service.upload(tenant, business, actor, body)
        assert await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    finally:
        store.release.set()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await asyncio.wait_for(task, 5)
    assert len(store.objects) == 1
    assert await service.reconcile(tenant, business, actor) == 0
    assert (await service.list_photos(tenant, business, actor))[0].pending_quarantined


async def test_legacy_null_lease_requires_quarantine_and_owner_cannot_be_impersonated(
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
    store = Store()
    service = PausedBeforeFinalize(settings, database, store)
    task = asyncio.create_task(service.upload(tenant, business, actor, upload()))
    await asyncio.wait_for(service.entered.wait(), 5)
    photo = (await service.list_photos(tenant, business, actor))[0]
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE business_collection_photos SET upload_single_attempt_confirmed=false
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": photo.id},
            )
        legacy = (await service.list_photos(tenant, business, actor))[0]
        assert legacy.pending_uncertain and legacy.pending_cancelable and not legacy.pending_recovery
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_READY"):
            await service.resume_upload(tenant, business, actor, photo.id)
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await service.delete(tenant, business, seeded["viewer"], photo.id, uuid4(), 0)
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await service.delete(tenant, business, seeded["a2"], photo.id, uuid4(), 0)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": tenant, "actor": seeded["viewer"]},
            )
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": tenant, "actor": actor},
            )
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_OWNER_REQUIRED"):
            await service.delete(tenant, business, seeded["viewer"], photo.id, uuid4(), 0)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": tenant, "actor": actor},
            )
        assert (await service.delete(tenant, business, actor, photo.id, uuid4(), 0)).status == "quarantined"
    finally:
        service.release.set()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RECOVERY_MISMATCH"):
        await asyncio.wait_for(task, 5)
    assert len(store.objects) == 1
    assert (await service.list_photos(tenant, business, actor))[0].pending_quarantined
