"""BL03 media validation, transport bounds and immutable private contracts."""

import base64
import hashlib
import io
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from pydantic import ValidationError

from app.api.deps import get_actor
from app.api.v1 import business_collection as routes
from app.schemas.business_collection import (
    CollectionPhoto,
    CollectionPhotoDeletion,
    CollectionPhotoMetadata,
    CollectionPhotoPromotion,
    CollectionPhotoUpdate,
    CollectionPhotoUpload,
    CollectionPhotoUrl,
    CollectionPhotoVersion,
)
from app.services import business_collection as collection
from app.services.auth import AuthError
from app.tests.unit.test_brand_kits_contract import _request


def picture(mode="RGB", size=(3, 4), fmt="PNG", **kwargs):
    output = io.BytesIO()
    Image.new(mode, size, "#244739").save(output, format=fmt, **kwargs)
    return output.getvalue()


def upload(**change):
    return CollectionPhotoUpload.model_validate(
        {
            "operation_id": str(uuid4()),
            "title": "Balcão",
            "space_kind": "counter",
            "sort_order": 0,
            "mime_type": "image/png",
            "content_base64": base64.b64encode(picture()).decode(),
            "rights_confirmed": True,
            **change,
        }
    )


def photo(**change):
    return CollectionPhoto.model_validate(
        {
            "id": uuid4(),
            "version": 1,
            "title": "Balcão",
            "item_id": None,
            "space_kind": "counter",
            "sort_order": 0,
            "status": "active",
            "source": "upload",
            "source_material_id": None,
            "mime_type": "image/png",
            "sha256": "a" * 64,
            "source_sha256": None,
            "size_bytes": 30,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            **change,
        }
    )


@pytest.mark.parametrize(
    "change",
    [
        {"item_id": str(uuid4())},
        {"space_kind": None},
        {"space_kind": "other"},
        {"title": "  "},
        {"sort_order": -1},
        {"rights_confirmed": False},
        {"mime_type": "image/gif"},
    ],
)
def test_upload_requires_destination_title_image_type_and_rights(change):
    with pytest.raises(ValidationError):
        upload(**change)


def test_product_destination_and_explicit_promotion_permission():
    item = CollectionPhotoMetadata(title="Produto", item_id=uuid4())
    assert item.space_kind is None
    body = {
        "operation_id": uuid4(),
        "title": "Local",
        "space_kind": "environment",
        "material_id": uuid4(),
        "rights_confirmed": True,
        "keep_in_collection": True,
    }
    assert CollectionPhotoPromotion.model_validate(body).keep_in_collection
    with pytest.raises(ValidationError):
        CollectionPhotoPromotion.model_validate({**body, "keep_in_collection": False})


@pytest.mark.parametrize(
    "mode,fmt,mime",
    [
        ("RGB", "PNG", "image/png"),
        ("RGBA", "PNG", "image/png"),
        ("RGB", "JPEG", "image/jpeg"),
        ("RGB", "WEBP", "image/webp"),
    ],
)
def test_normalization_preserves_pixels_and_strips_private_metadata(mode, fmt, mime):
    info = PngImagePlugin.PngInfo()
    info.add_text("private_note", "remove this")
    raw = picture(mode, fmt=fmt, **({"pnginfo": info} if fmt == "PNG" else {}))
    media = collection.normalize_photo(raw, mime)
    assert media.sha256 == hashlib.sha256(media.data).hexdigest()
    with Image.open(io.BytesIO(media.data)) as result:
        assert result.size == (3, 4) and "private_note" not in result.info
        assert result.mode == mode


def test_exif_orientation_is_applied_before_private_copy():
    exif = Image.Exif()
    exif[274] = 6
    media = collection.normalize_photo(picture(fmt="JPEG", exif=exif), "image/jpeg")
    with Image.open(io.BytesIO(media.data)) as result:
        assert result.size == (4, 3) and not result.getexif()


@pytest.mark.parametrize(
    "raw,mime,limit,code",
    [
        (b"", "image/png", 10, "COLLECTION_PHOTO_SIZE"),
        (b"abc", "image/png", 2, "COLLECTION_PHOTO_SIZE"),
        (b"not image", "image/png", 100, "COLLECTION_PHOTO_INVALID"),
        (picture(), "image/jpeg", 10000, "COLLECTION_PHOTO_INVALID"),
        (picture(size=(8193, 1)), "image/png", 100000, "COLLECTION_PHOTO_INVALID"),
        (picture(size=(4001, 4000)), "image/png", 1000000, "COLLECTION_PHOTO_INVALID"),
    ],
)
def test_invalid_photos_do_not_become_stored_media(raw, mime, limit, code):
    with pytest.raises(AuthError, match=code):
        collection.normalize_photo(raw, mime, limit)


def test_animation_and_unbounded_normalized_output_are_rejected(monkeypatch):
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        output, format="PNG", save_all=True, append_images=[Image.new("RGB", (2, 2), "blue")]
    )
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_INVALID"):
        collection.normalize_photo(output.getvalue(), "image/png")
    monkeypatch.setattr(collection, "STORED_MAX_BYTES", 1)
    with pytest.raises(AuthError, match="COLLECTION_PHOTO_SIZE"):
        collection.normalize_photo(picture(), "image/png")


@pytest.mark.parametrize(
    "headers,chunks,code,status",
    [
        ({"content-type": "application/json", "content-length": "bad"}, [b"{}"], "COLLECTION_PHOTO_SIZE", 413),
        ({"content-type": "application/json", "content-length": "3000001"}, [b"{}"], "COLLECTION_PHOTO_SIZE", 413),
        ({"content-type": "text/plain"}, [b"{}"], "COLLECTION_PHOTO_INVALID", 415),
        ({"content-type": "application/json"}, [b"x" * 3000001], "COLLECTION_PHOTO_SIZE", 413),
        ({"content-type": "application/json"}, [b"{bad"], "COLLECTION_PHOTO_INVALID", 422),
        ({"content-type": "application/json"}, [b"{}"], "COLLECTION_PHOTO_INVALID", 422),
    ],
)
async def test_upload_transport_caps_before_service(monkeypatch, headers, chunks, code, status):
    fake = SimpleNamespace(upload=AsyncMock())
    monkeypatch.setattr(routes, "service", lambda request: fake)
    with pytest.raises(AuthError) as failure:
        await routes.photo_upload(uuid4(), uuid4(), _request(chunks, headers), uuid4())
    assert (failure.value.code, failure.value.status) == (code, status)
    fake.upload.assert_not_awaited()


def test_photo_http_operations_share_owner_business_scope(monkeypatch, settings):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    saved = photo()
    fake = SimpleNamespace(
        list_photos=AsyncMock(return_value=[saved]),
        upload=AsyncMock(return_value=saved),
        promote=AsyncMock(return_value=saved),
        update=AsyncMock(return_value=saved),
        resume_upload=AsyncMock(return_value=saved),
        url=AsyncMock(return_value=CollectionPhotoUrl(url="https://private.invalid/photo")),
        history=AsyncMock(
            return_value=[
                CollectionPhotoVersion(version=1, action="uploaded", photo=saved, created_at=saved.created_at)
            ]
        ),
        delete=AsyncMock(return_value=CollectionPhotoDeletion(status="deleted")),
        reconcile=AsyncMock(return_value=1),
        removals=AsyncMock(return_value={"pending": 2}),
    )
    default = routes.service(
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings, database=object())))
    )
    assert isinstance(default, collection.BusinessCollectionService)
    monkeypatch.setattr(routes, "service", lambda request: fake)
    app = FastAPI()
    app.include_router(routes.collection_router)
    app.dependency_overrides[get_actor] = lambda: actor
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/collection/photos"
    with TestClient(app) as client:
        assert client.get(path).json()[0]["id"] == str(saved.id)
        assert client.post(path, json=upload().model_dump(mode="json")).status_code == 201
        promotion = CollectionPhotoPromotion(
            operation_id=uuid4(),
            material_id=uuid4(),
            title="Local",
            space_kind="room",
            rights_confirmed=True,
            keep_in_collection=True,
        )
        assert client.post(path + "/from-whatsapp", json=promotion.model_dump(mode="json")).status_code == 201
        update = CollectionPhotoUpdate(
            operation_id=uuid4(), expected_version=1, title="Balcão novo", space_kind="counter", status="archived"
        )
        assert client.patch(f"{path}/{saved.id}", json=update.model_dump(mode="json")).status_code == 200
        assert client.get(f"{path}/{saved.id}/url").json()["expires_in_seconds"] == 120
        assert client.post(f"{path}/{saved.id}/resume").json()["id"] == str(saved.id)
        assert client.get(f"{path}/{saved.id}/history").json()[0]["version"] == 1
        assert (
            client.delete(
                f"{path}/{saved.id}", params={"operation_id": str(uuid4()), "expected_version": 1}
            ).status_code
            == 202
        )
        assert client.post(path + "/reconcile").json() == {"reconciled": 1}
        assert client.get(path + "/removals").json() == {"pending": 2}
    for method in (
        fake.list_photos,
        fake.upload,
        fake.promote,
        fake.update,
        fake.resume_upload,
        fake.url,
        fake.history,
        fake.delete,
        fake.reconcile,
        fake.removals,
    ):
        assert method.await_args.args[:3] == (tenant, business, actor)


async def test_upload_transport_supports_chunked_body(monkeypatch):
    body = upload()
    encoded = body.model_dump_json().encode()
    fake = SimpleNamespace(upload=AsyncMock(return_value=photo()))
    monkeypatch.setattr(routes, "service", lambda request: fake)
    await routes.photo_upload(
        uuid4(), uuid4(), _request([b"", encoded[:15], encoded[15:]], {"content-type": "application/json"}), uuid4()
    )
    assert fake.upload.await_args.args[3] == body
