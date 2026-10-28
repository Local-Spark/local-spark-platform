"""Unknown storage outcomes are preserved, not compensated as successful deletes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.services import business_collection as collection
from app.tests.unit.test_brand_kits_service import Database, Session
from app.tests.unit.test_business_collection_contract import upload


async def test_put_timeout_does_not_delete_object_that_may_arrive_later(monkeypatch):
    monkeypatch.setattr(collection, "require_catalog_owner", AsyncMock())
    store = SimpleNamespace(put=AsyncMock(side_effect=MaterialError("MATERIAL_STORAGE_UNAVAILABLE")))
    service = collection.BusinessCollectionService(SimpleNamespace(), Database(Session(scalars=[uuid4()])), store)
    service._retire_upload = AsyncMock()
    with pytest.raises(MaterialError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await service._complete(
            uuid4(),
            uuid4(),
            uuid4(),
            upload(),
            {"id": uuid4(), "object_key": "private", "upload_owner": uuid4()},
            FetchedMedia(b"bytes", "image/png", "a" * 64),
            "digest",
        )
    service._retire_upload.assert_not_awaited()


async def test_s3_put_uses_one_attempt_so_a_success_is_not_followed_by_an_old_retry(monkeypatch, settings):
    client = SimpleNamespace(put_object=lambda **kwargs: None)
    calls = []
    monkeypatch.setattr(
        "app.adapters.material_media.boto3.client", lambda *args, **kwargs: calls.append(kwargs) or client
    )
    store = MaterialStore(settings.model_copy(update={"material_storage_bucket": "test-private"}))
    await store.put("private/key", FetchedMedia(b"test", "image/png", "a" * 64))
    assert calls[0]["config"].retries["total_max_attempts"] == 1
