"""Recovery and cancellation contracts for private collection uploads."""

import asyncio
import base64
import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.business_collection import CollectionPhotoPromotion
from app.services import business_collection as collection
from app.services.auth import AuthError
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges
from app.tests.unit.test_brand_kits_service import Database, Session
from app.tests.unit.test_business_collection_contract import photo, upload


def service(monkeypatch):
    monkeypatch.setattr(collection, "require_catalog_owner", AsyncMock())
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    store = SimpleNamespace(put=AsyncMock(), get_image=AsyncMock(), delete=AsyncMock())
    instance = collection.BusinessCollectionService(SimpleNamespace(), Database(Session()), store)
    return instance, store


def promotion():
    return CollectionPhotoPromotion(
        operation_id=uuid4(),
        material_id=uuid4(),
        title="Local",
        space_kind="room",
        rights_confirmed=True,
        keep_in_collection=True,
    )


@pytest.mark.parametrize("method", ["upload", "promote"])
async def test_retry_recovers_recorded_upload_without_replacing_object(monkeypatch, method):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    expected = photo(id=photo_id)
    instance.reconcile = AsyncMock(return_value=0)
    instance._intent = AsyncMock(return_value={"id": photo_id, "resume_finalize": True})
    instance.resume_upload = AsyncMock(return_value=expected)
    body = upload() if method == "upload" else promotion()
    assert await getattr(instance, method)(tenant, business, actor, body) == expected
    instance.resume_upload.assert_awaited_once_with(tenant, business, actor, photo_id)
    store.put.assert_not_awaited()


async def test_invalid_image_after_valid_base64_retires_private_intent(monkeypatch):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    instance.reconcile = AsyncMock(return_value=0)
    instance._intent = AsyncMock(return_value={"id": photo_id, "state": "pending", "version": 0})
    instance._retire_upload = AsyncMock()
    body = upload(content_base64=base64.b64encode(b"invalid image data").decode())
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_INVALID"):
        await instance.upload(tenant, business, actor, body)
    instance._retire_upload.assert_awaited_once_with(tenant, business, actor, photo_id)
    store.put.assert_not_awaited()


@pytest.mark.parametrize("case", ["missing", "other_owner", "ready_no_receipt", "ready_receipt"])
async def test_resume_checks_owner_and_durable_receipt_before_object_access(monkeypatch, case):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    saved = photo(id=photo_id)
    row = {"actor_id": actor, "state": "ready", "operation_id": uuid4(), "request_hash": "hash"}
    if case == "missing":
        row = None
    elif case == "other_owner":
        row["actor_id"] = uuid4()
    instance._row = AsyncMock(return_value=row)
    instance._replay = AsyncMock(return_value=saved if case == "ready_receipt" else None)
    if case == "ready_receipt":
        assert await instance.resume_upload(tenant, business, actor, photo_id) == saved
    else:
        code = {
            "missing": "COLLECTION_PHOTO_NOT_FOUND",
            "other_owner": "COLLECTION_PHOTO_OWNER_REQUIRED",
            "ready_no_receipt": "COLLECTION_PHOTO_BUSY",
        }[case]
        with pytest.raises(AuthError, match=code):
            await instance.resume_upload(tenant, business, actor, photo_id)
    store.get_image.assert_not_awaited()


@pytest.mark.parametrize("state", ["pending", "failed", "missing", "wrong_operation"])
async def test_resume_staged_requires_matching_pending_operation(monkeypatch, state):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id, operation = (uuid4() for _ in range(5))
    row = {
        **photo(id=photo_id).model_dump(),
        "actor_id": actor,
        "state": "pending",
        "operation_id": operation,
        "upload_lease_until": None,
    }
    pending = (
        None
        if state == "missing"
        else {
            "operation_id": uuid4() if state == "wrong_operation" else operation,
            "status": state,
            "error_code": "SOURCE_REVOKED" if state == "failed" else None,
        }
    )
    instance._row = AsyncMock(return_value=row)
    monkeypatch.setattr(VisualPendingChanges, "status_in_session", AsyncMock(return_value=pending))
    if state in {"missing", "wrong_operation"}:
        with pytest.raises(AuthError, match="COLLECTION_PHOTO_BUSY"):
            await instance.resume_upload(tenant, business, actor, photo_id)
    else:
        result = await instance.resume_upload(tenant, business, actor, photo_id)
        assert result.pending_activation and result.pending_change == (state == "pending")
        assert result.pending_change_error == ("SOURCE_REVOKED" if state == "failed" else None)
    store.get_image.assert_not_awaited()


@pytest.mark.parametrize(
    "change",
    [
        {"state": "deleted"},
        {"version": 0, "upload_lease_until": "not-expired"},
        {"version": 0, "upload_owner": None},
        {"version": 0, "upload_single_attempt_confirmed": False},
        {"version": 0, "sha256": None},
        {"version": 0, "mime_type": "image/jpeg"},
        {"version": 0, "size_bytes": 0},
    ],
)
async def test_resume_refuses_incomplete_or_unstable_upload(monkeypatch, change):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    row = {
        "actor_id": actor,
        "state": "pending",
        "version": 0,
        "upload_lease_until": None,
        "upload_owner": uuid4(),
        "upload_single_attempt_confirmed": True,
        "sha256": "a" * 64,
        "mime_type": "image/png",
        "size_bytes": 12,
        **change,
    }
    instance._row = AsyncMock(return_value=row)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_READY"):
        await instance.resume_upload(tenant, business, actor, photo_id)
    store.get_image.assert_not_awaited()


@pytest.mark.parametrize("outcome", ["success", "failure", "cancelled"])
async def test_cancelled_resume_waits_for_finalization_and_preserves_object(monkeypatch, outcome):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    data = b"verified private object"
    row = {
        "actor_id": actor,
        "state": "pending",
        "version": 0,
        "upload_lease_until": None,
        "upload_owner": uuid4(),
        "upload_single_attempt_confirmed": True,
        "sha256": hashlib.sha256(data).hexdigest(),
        "mime_type": "image/png",
        "size_bytes": len(data),
        "object_key": "private/object",
        "operation_id": uuid4(),
        "request_hash": "hash",
        "source_sha256": None,
    }
    instance._row = AsyncMock(return_value=row)
    store.get_image.return_value = data
    entered, release = asyncio.Event(), asyncio.Event()
    finished = []

    async def finalize(*args):
        entered.set()
        await release.wait()
        finished.append(True)
        if outcome == "failure":
            raise RuntimeError("finalization failed")
        if outcome == "cancelled":
            raise asyncio.CancelledError
        return photo(id=photo_id)

    instance._finalize_photo = finalize
    task = asyncio.create_task(instance.resume_upload(tenant, business, actor, photo_id))
    await asyncio.wait_for(entered.wait(), 2)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done() and not finished
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done() and not finished
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished == [True]
    store.delete.assert_not_awaited()


async def test_other_owner_cannot_cancel_original_pending_upload(monkeypatch):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    instance._operation_guard = AsyncMock()
    instance._row = AsyncMock(return_value={"state": "pending", "version": 0, "actor_id": uuid4()})
    instance._replay = AsyncMock(return_value=None)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_OWNER_REQUIRED"):
        await instance.delete(tenant, business, actor, photo_id, uuid4(), 0)
    store.delete.assert_not_awaited()


async def test_pending_upload_with_live_writer_cannot_be_discarded(monkeypatch):
    instance, store = service(monkeypatch)
    tenant, business, actor, photo_id = (uuid4() for _ in range(4))
    instance._operation_guard = AsyncMock()
    instance._row = AsyncMock(return_value={"state": "pending", "version": 0, "actor_id": actor})
    instance._replay = AsyncMock(return_value=None)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_NOT_READY"):
        await instance.delete(tenant, business, actor, photo_id, uuid4(), 0)
    store.delete.assert_not_awaited()
