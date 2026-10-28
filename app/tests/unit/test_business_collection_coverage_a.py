"""Isolated failure and replay cases for collection photo finalization."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.material_media import FetchedMedia, MaterialError
from app.services import business_collection as collection
from app.services.auth import AuthError
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges
from app.tests.unit.test_brand_kits_service import Database, Session
from app.tests.unit.test_business_collection_contract import photo, upload


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(collection, "require_catalog_owner", AsyncMock())
    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    service = collection.BusinessCollectionService(SimpleNamespace(), Database(Session()), store)
    service._operation_guard = AsyncMock()
    return service, store


async def test_repeated_request_resumes_only_recorded_private_upload(setup):
    service, store = setup
    service._row = AsyncMock(
        return_value={
            "state": "pending",
            "version": 0,
            "request_hash": "digest",
            "upload_lease_until": None,
            "upload_owner": uuid4(),
            "sha256": "abc",
        }
    )
    result = await service._intent(uuid4(), uuid4(), uuid4(), upload(), "digest")
    assert result["resume_finalize"] is True
    store.put.assert_not_awaited()


async def test_retire_does_not_cancel_pending_command_after_other_commit(setup, monkeypatch):
    service, _ = setup
    service.reconcile = AsyncMock(return_value=0)
    apply = AsyncMock()
    monkeypatch.setattr(VisualPendingChanges, "apply_pending_in_session", apply)
    await service._retire_upload(uuid4(), uuid4(), uuid4(), uuid4())
    apply.assert_not_awaited()
    service.reconcile.assert_awaited_once()


def finalizer_row(actor, operation, **overrides):
    return {
        "actor_id": actor,
        "operation_id": operation,
        "request_hash": "digest",
        "state": "pending",
        "version": 0,
        "upload_lease_until": None,
        "upload_owner": "writer",
        "sha256": "sha",
        "mime_type": "image/png",
        "size_bytes": 4,
        "source_sha256": None,
        "source": "upload",
        "title": "Foto",
        "item_id": None,
        "space_kind": "room",
        "sort_order": 0,
        **overrides,
    }


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "operation",
        "hash",
        "owner",
        "ready_missing",
        "ready_replay",
        "pending_missing",
        "pending_wrong_operation",
        "source_changed",
    ],
)
async def test_finalize_validates_identity_replay_and_whatsapp_source(setup, monkeypatch, kind):
    service, _ = setup
    tenant, business, actor, operation, photo_id = (uuid4() for _ in range(5))
    row = finalizer_row(actor, operation)
    if kind == "missing":
        row = None
    elif kind == "operation":
        row["operation_id"] = uuid4()
    elif kind == "hash":
        row["request_hash"] = "other"
    elif kind == "owner":
        row["actor_id"] = uuid4()
    elif kind.startswith("ready"):
        row["state"] = "ready"
    elif kind.startswith("pending_"):
        row["version"] = 1
    elif kind == "source_changed":
        row.update(source="whatsapp", source_material_id=uuid4(), source_sha256="expected")
        service._source = AsyncMock(return_value={"sha256": "changed"})
        service._destination = AsyncMock()
    service._row = AsyncMock(return_value=row)
    saved = photo()
    service._replay = AsyncMock(return_value=saved if kind == "ready_replay" else None)
    monkeypatch.setattr(
        VisualPendingChanges,
        "status_in_session",
        AsyncMock(return_value={"operation_id": uuid4()} if kind == "pending_wrong_operation" else None),
    )
    args = (
        tenant,
        business,
        actor,
        operation,
        {"id": photo_id, "upload_owner": "writer"},
        FetchedMedia(b"data", "image/png", "sha"),
        "digest",
    )
    if kind == "ready_replay":
        assert await service._finalize_photo(*args) == saved
    else:
        error = {
            "missing": "COLLECTION_PHOTO_OPERATION_CONFLICT",
            "operation": "COLLECTION_PHOTO_OPERATION_CONFLICT",
            "hash": "COLLECTION_PHOTO_OPERATION_CONFLICT",
            "owner": "COLLECTION_PHOTO_OWNER_REQUIRED",
            "ready_missing": "COLLECTION_PHOTO_BUSY",
            "pending_missing": "COLLECTION_PHOTO_BUSY",
            "pending_wrong_operation": "COLLECTION_PHOTO_BUSY",
            "source_changed": "COLLECTION_SOURCE_NOT_AVAILABLE",
        }[kind]
        with pytest.raises(AuthError, match=error):
            await service._finalize_photo(*args, source_sha="expected" if kind == "source_changed" else None)


@pytest.mark.parametrize(
    "field,value",
    [
        ("upload_lease_until", "active"),
        ("upload_owner", "other"),
        ("sha256", "other"),
        ("mime_type", "image/jpeg"),
        ("size_bytes", 99),
        ("source_sha256", "other"),
    ],
)
async def test_finalize_rejects_mismatched_private_snapshot(setup, field, value):
    service, _ = setup
    actor, operation = uuid4(), uuid4()
    service._row = AsyncMock(return_value=finalizer_row(actor, operation, **{field: value}))
    service._destination = AsyncMock()
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_RECOVERY_MISMATCH"):
        await service._finalize_photo(
            uuid4(),
            uuid4(),
            actor,
            operation,
            {"id": uuid4(), "upload_owner": "writer"},
            FetchedMedia(b"data", "image/png", "sha"),
            "digest",
        )
    service._destination.assert_not_awaited()


@pytest.mark.parametrize("case", ["actor", "source"])
async def test_activation_rechecks_owner_and_original_photo_hash(monkeypatch, case):
    actor, operation = uuid4(), uuid4()
    row = {
        "operation_id": operation,
        "state": "pending",
        "version": 1,
        "upload_owner": None,
        "actor_id": uuid4() if case == "actor" else actor,
        "title": "Foto",
        "item_id": None,
        "space_kind": "room",
        "sort_order": 0,
        "source": "whatsapp",
        "source_material_id": uuid4(),
        "source_sha256": "original",
    }
    monkeypatch.setattr(collection.BusinessCollectionService, "_row", AsyncMock(side_effect=[row, row]))
    monkeypatch.setattr(collection.BusinessCollectionService, "_operation_guard", AsyncMock())
    monkeypatch.setattr(collection.BusinessCollectionService, "_destination", AsyncMock())
    monkeypatch.setattr(collection.BusinessCollectionService, "_source", AsyncMock(return_value={"sha256": "changed"}))
    with pytest.raises(
        AuthError, match="COLLECTION_PHOTO_OWNER_REQUIRED" if case == "actor" else "COLLECTION_SOURCE_NOT_AVAILABLE"
    ):
        await collection.BusinessCollectionService._activate_staged_in_session(
            Session(), uuid4(), uuid4(), actor, uuid4()
        )


async def test_cancelled_request_drains_failing_finalize_without_deleting(setup):
    service, store = setup
    service.database = Database(Session(scalars=[uuid4()]))
    started, release = asyncio.Event(), asyncio.Event()

    async def finalize(*_args):
        started.set()
        await release.wait()
        raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)

    service._prepare_and_finalize = finalize
    service._retire_upload = AsyncMock()
    task = asyncio.create_task(
        service._complete(
            uuid4(),
            uuid4(),
            uuid4(),
            upload(),
            {"id": uuid4(), "object_key": "private", "upload_owner": uuid4()},
            FetchedMedia(b"data", "image/png", "sha"),
            "digest",
        )
    )
    await asyncio.wait_for(started.wait(), 2)
    task.cancel()
    await asyncio.sleep(0)
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)
    store.put.assert_awaited_once()
    service._retire_upload.assert_not_awaited()


async def test_finalize_task_cancelled_does_not_delete_possible_commit(setup):
    service, _ = setup
    service.database = Database(Session(scalars=[uuid4()]))
    service._prepare_and_finalize = AsyncMock(side_effect=asyncio.CancelledError)
    service._retire_upload = AsyncMock()
    with pytest.raises(asyncio.CancelledError):
        await service._complete(
            uuid4(),
            uuid4(),
            uuid4(),
            upload(),
            {"id": uuid4(), "object_key": "private", "upload_owner": uuid4()},
            FetchedMedia(b"data", "image/png", "sha"),
            "digest",
        )
    service._retire_upload.assert_not_awaited()
