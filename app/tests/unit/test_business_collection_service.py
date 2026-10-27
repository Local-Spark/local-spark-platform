"""Failure boundaries of durable collection media without database greenlet tracing."""

import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.material_media import FetchedMedia
from app.schemas.business_collection import CollectionPhotoPromotion, CollectionPhotoUpdate
from app.services import business_collection as collection
from app.services.auth import AuthError
from app.tests.unit.test_brand_kits_service import Database, Rows, Session
from app.tests.unit.test_business_collection_contract import photo, upload


def service(monkeypatch, session=None):
    monkeypatch.setattr(collection, "require_catalog_owner", AsyncMock())
    store = SimpleNamespace(put=AsyncMock(), get_image=AsyncMock(), delete=AsyncMock(), signed_url=AsyncMock())
    instance = collection.BusinessCollectionService(SimpleNamespace(), Database(session or Session()), store)
    return instance, store


async def test_replay_detects_reused_operation_with_different_content():
    session = Session(results=[Rows({"request_hash": "old", "document": {}})])
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT"):
        await collection.BusinessCollectionService._replay(session, uuid4(), uuid4(), uuid4(), uuid4(), "new")


@pytest.mark.parametrize("method", ["history", "update", "delete"])
async def test_owner_cannot_access_a_photo_from_another_business(monkeypatch, method):
    instance, _ = service(monkeypatch)
    instance._row = AsyncMock(return_value=None)
    args = (uuid4(), uuid4(), uuid4(), uuid4())
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_FOUND"):
        if method == "history":
            await instance.history(*args)
        elif method == "update":
            await instance.update(
                *args,
                CollectionPhotoUpdate(
                    operation_id=uuid4(), expected_version=1, title="Local", space_kind="room", status="active"
                ),
            )
        else:
            await instance.delete(*args, uuid4(), 1)


@pytest.mark.parametrize("conflict", [True, False])
async def test_intent_rejects_payload_conflict_or_lease_lost_to_cleanup(monkeypatch, conflict):
    instance, store = service(monkeypatch, Session(scalars=[None]))
    instance._row = AsyncMock(return_value={"state": "pending", "request_hash": "other" if conflict else "same"})
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT" if conflict else "COLLECTION_PHOTO_BUSY"):
        await instance._intent(uuid4(), uuid4(), uuid4(), upload(), "same")
    store.put.assert_not_awaited()


async def test_upload_finalization_cannot_revive_a_deleting_intent(monkeypatch):
    instance, store = service(monkeypatch)
    instance._row = AsyncMock(return_value={"state": "deleting"})
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await instance._complete(
            uuid4(),
            uuid4(),
            uuid4(),
            upload(),
            {"id": uuid4(), "object_key": "private/object"},
            FetchedMedia(b"bytes", "image/png", "a" * 64),
            "hash",
        )
    store.put.assert_awaited_once()


async def test_promotion_rejects_source_object_that_changed(monkeypatch):
    instance, store = service(monkeypatch)
    instance.reconcile = AsyncMock(return_value=0)
    instance._intent = AsyncMock(return_value={"state": "pending"})
    instance._source = AsyncMock(
        return_value={"object_key": "trusted/private", "mime_type": "image/png", "sha256": "a" * 64}
    )
    store.get_image.return_value = b"replaced object"
    body = CollectionPhotoPromotion(
        operation_id=uuid4(),
        material_id=uuid4(),
        title="Photo",
        space_kind="facade",
        rights_confirmed=True,
        keep_in_collection=True,
    )
    assert hashlib.sha256(store.get_image.return_value).hexdigest() != "a" * 64
    with pytest.raises(AuthError, match="COLLECTION_SOURCE_NOT_AVAILABLE"):
        await instance.promote(uuid4(), uuid4(), uuid4(), body)
    store.put.assert_not_awaited()


async def test_update_replay_returns_immutable_original_version(monkeypatch):
    instance, store = service(monkeypatch)
    saved = photo()
    instance._row = AsyncMock(return_value={"state": "ready", "version": 3})
    instance._replay = AsyncMock(return_value=saved)
    result = await instance.update(
        uuid4(),
        uuid4(),
        uuid4(),
        saved.id,
        CollectionPhotoUpdate(
            operation_id=uuid4(), expected_version=1, title="Old edit", space_kind="room", status="active"
        ),
    )
    assert result == saved and result.version == 1
    store.put.assert_not_awaited()


async def test_cleanup_does_not_finalize_after_lease_fencing_was_lost(monkeypatch):
    candidate = {"id": uuid4(), "object_key": "private/orphan", "delete_fencing_token": 7}
    session = Session(results=[Rows(rows=[candidate])], scalars=[None])
    instance, store = service(monkeypatch, session)
    audit = AsyncMock()
    monkeypatch.setattr(collection, "audit_catalog_change", audit)
    assert await instance.reconcile(uuid4(), uuid4(), uuid4()) == 0
    store.delete.assert_awaited_once_with(candidate["object_key"])
    audit.assert_not_awaited()
    statement, params = session.statements[-1]
    assert params["fence"] == 7 and "delete_fencing_token=:fence" in statement
    assert "delete_lease_until>now()" in statement
