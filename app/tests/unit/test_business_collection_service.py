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
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.unit.test_brand_kits_service import Database, Rows, Session
from app.tests.unit.test_business_collection_contract import photo, upload


def service(monkeypatch, session=None):
    monkeypatch.setattr(collection, "require_catalog_owner", AsyncMock())
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
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
    instance._row = AsyncMock(
        return_value={"state": "pending", "version": 0, "request_hash": "other" if conflict else "same"}
    )
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OPERATION_CONFLICT" if conflict else "COLLECTION_PHOTO_BUSY"):
        await instance._intent(uuid4(), uuid4(), uuid4(), upload(), "same")
    store.put.assert_not_awaited()


async def test_staged_photo_without_matching_durable_request_never_replays(monkeypatch):
    from app.services.visual_pending_changes import VisualPendingChanges

    instance, store = service(monkeypatch)
    instance._row = AsyncMock(return_value={"state": "pending", "version": 1, "request_hash": "same"})
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value=None))
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_BUSY"):
        await instance._intent(uuid4(), uuid4(), uuid4(), upload(), "same")
    store.put.assert_not_awaited()


@pytest.mark.parametrize(
    "rows,expected",
    [
        ([None], "COLLECTION_PHOTO_NOT_FOUND"),
        ([{"operation_id": uuid4()}, None], "COLLECTION_PHOTO_NOT_READY"),
        ([{"operation_id": uuid4()}, {"state": "ready"}], "COLLECTION_PHOTO_NOT_READY"),
        ([{"operation_id": uuid4()}, {"state": "pending", "version": 2}], "COLLECTION_PHOTO_NOT_READY"),
        (
            [{"operation_id": uuid4()}, {"state": "pending", "version": 1, "upload_owner": uuid4()}],
            "COLLECTION_PHOTO_NOT_READY",
        ),
    ],
)
async def test_staged_activation_requires_intact_private_upload(monkeypatch, rows, expected):
    monkeypatch.setattr(collection.BusinessCollectionService, "_row", AsyncMock(side_effect=rows))
    monkeypatch.setattr(collection.BusinessCollectionService, "_operation_guard", AsyncMock())
    with pytest.raises(AuthError, match=expected):
        await collection.BusinessCollectionService._activate_staged_in_session(
            Session(), uuid4(), uuid4(), uuid4(), uuid4()
        )


@pytest.mark.parametrize(
    "pending,expected_version,error",
    [
        (None, 1, "COLLECTION_PHOTO_NOT_READY"),
        ({"status": "pending"}, 1, "COLLECTION_PHOTO_NOT_READY"),
        ({"status": "failed"}, 2, "COLLECTION_PHOTO_VERSION_CONFLICT"),
    ],
)
async def test_staged_photo_can_only_be_discarded_after_failure_with_matching_version(
    monkeypatch, pending, expected_version, error
):
    from app.services.visual_pending_changes import VisualPendingChanges

    instance, _ = service(monkeypatch)
    instance._operation_guard = AsyncMock()
    instance._row = AsyncMock(return_value={"state": "pending", "version": 1})
    instance._replay = AsyncMock(return_value=None)
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value=pending))
    with pytest.raises(AuthError, match=error):
        await instance.delete(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), expected_version)


async def test_upload_finalization_cannot_revive_a_deleting_intent(monkeypatch):
    instance, store = service(monkeypatch, Session(scalars=[uuid4(), uuid4()]))
    body = upload()
    actor = uuid4()
    instance._row = AsyncMock(
        return_value={"state": "deleting", "operation_id": body.operation_id, "request_hash": "hash", "actor_id": actor}
    )
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await instance._complete(
            uuid4(),
            uuid4(),
            actor,
            body,
            {"id": uuid4(), "object_key": "private/object", "upload_owner": uuid4()},
            FetchedMedia(b"bytes", "image/png", "a" * 64),
            "hash",
        )
    store.put.assert_awaited_once()


async def test_finalization_preserves_private_key_if_upload_lease_was_lost(monkeypatch):
    instance, _ = service(monkeypatch, Session(scalars=[None]))
    instance._retire_upload = AsyncMock()
    photo_id = uuid4()
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RETIRED"):
        await instance._prepare_and_finalize(
            tenant,
            business,
            actor,
            upload(),
            {"id": photo_id, "upload_owner": uuid4()},
            FetchedMedia(b"bytes", "image/png", "a" * 64),
            "hash",
            None,
        )
    instance._retire_upload.assert_not_awaited()


async def test_promotion_rejects_source_object_that_changed(monkeypatch):
    instance, store = service(monkeypatch)
    instance.reconcile = AsyncMock(return_value=0)
    instance._intent = AsyncMock(return_value={"state": "pending", "version": 0, "id": uuid4()})
    instance._retire_upload = AsyncMock()
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


@pytest.mark.parametrize(
    "row,replay,expected",
    [
        (None, None, "COLLECTION_PHOTO_NOT_FOUND"),
        ({"state": "pending", "version": 1}, None, "COLLECTION_PHOTO_NOT_READY"),
        ({"state": "ready", "version": 2}, None, "COLLECTION_PHOTO_VERSION_CONFLICT"),
        ({"state": "ready", "version": 1}, "replay", None),
    ],
)
async def test_deferred_photo_helpers_enforce_version_and_replay(monkeypatch, row, replay, expected):
    from app.services.business_collection import BusinessCollectionService

    session = Session()
    tenant, business, actor, photo_id, operation = (uuid4() for _ in range(5))
    body = CollectionPhotoUpdate(
        operation_id=operation, expected_version=1, title="Foto", space_kind="room", status="active"
    )
    saved = photo() if replay else None
    monkeypatch.setattr(BusinessCollectionService, "_operation_guard", AsyncMock())
    monkeypatch.setattr(BusinessCollectionService, "_row", AsyncMock(return_value=row))
    monkeypatch.setattr(BusinessCollectionService, "_replay", AsyncMock(return_value=saved))
    for call in (
        BusinessCollectionService._update_in_session(session, tenant, business, actor, photo_id, body),
        BusinessCollectionService._delete_in_session(session, tenant, business, actor, photo_id, operation, 1),
    ):
        if expected:
            with pytest.raises(AuthError, match=expected):
                await call
        else:
            await call


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
