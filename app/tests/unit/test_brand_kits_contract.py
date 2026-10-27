"""Focused BL02 contract checks without a database or external services."""

import base64
import hashlib
import io
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from pydantic import ValidationError
from starlette.requests import Request

from app.api.deps import get_actor
from app.api.v1 import brand_kits as routes
from app.schemas.brand_kits import (
    BrandKitConfirmRequest,
    BrandKitDraftRequest,
    BrandKitLogoRead,
    BrandKitLogoUpload,
    BrandKitLogoUrl,
    BrandKitOverrides,
)
from app.services import brand_kits as kits
from app.services.auth import AuthError


def _logo_body(raw: bytes, mime_type: str = "image/png") -> BrandKitLogoUpload:
    return BrandKitLogoUpload(
        operation_id=uuid4(),
        mime_type=mime_type,
        content_base64=base64.b64encode(raw).decode(),
        rights_confirmed=True,
    )


def _image_bytes(format_name: str = "PNG", *, metadata: bool = False) -> bytes:
    output = io.BytesIO()
    image = Image.new("RGB", (2, 3), "#244739")
    if format_name == "PNG" and metadata:
        info = PngImagePlugin.PngInfo()
        info.add_text("private_note", "must be removed")
        image.save(output, format=format_name, pnginfo=info)
    else:
        image.save(output, format=format_name)
    return output.getvalue()


def _request(chunks: list[bytes], headers: dict[str, str]) -> Request:
    messages = [
        {"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1}
        for index, chunk in enumerate(chunks)
    ]

    async def receive():
        return messages.pop(0) if messages else {"type": "http.request", "body": b"", "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/logo",
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
        },
        receive,
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value["palette"].update(primary=value["palette"]["background"]),
        lambda value: value["palette"].update(accent="purple"),
        lambda value: value.update(heading_font="Unknown Font"),
        lambda value: value.update(brand_name="   "),
        lambda value: value.update(cta="x"),
        lambda value: value["formats"]["feed"].update(layout="text_focus"),
        lambda value: value["formats"]["story"].update(image_position="left"),
        lambda value: value.update(extra="not allowed"),
    ],
)
def test_editor_rejects_invalid_overrides(change):
    value = kits._default_overrides("Café da Ana", kits._manifest()).model_dump(mode="json")
    change(value)
    with pytest.raises(ValidationError):
        BrandKitOverrides.model_validate(value)


def test_draft_and_confirmation_require_versioned_contract():
    overrides = kits._default_overrides("Café da Ana", kits._manifest())
    valid = BrandKitDraftRequest(
        operation_id=uuid4(), expected_version=0, kit_id=kits.KIT_ID, kit_version=kits.KIT_VERSION, overrides=overrides
    )
    assert valid.overrides.brand_name == "Café da Ana"
    for change in ({"expected_version": -1}, {"kit_id": "other"}, {"kit_version": 2}):
        with pytest.raises(ValidationError):
            BrandKitDraftRequest.model_validate({**valid.model_dump(mode="json"), **change})
    with pytest.raises(ValidationError):
        BrandKitConfirmRequest(operation_id=uuid4(), expected_version=0)
    with pytest.raises(ValidationError):
        BrandKitLogoUpload(operation_id=uuid4(), mime_type="image/png", content_base64="A" * 16, rights_confirmed=False)


@pytest.mark.parametrize("invalid", ["identity", "version", "unregistered", "composed"])
def test_manifest_rejects_untrusted_editor_sources(tmp_path, monkeypatch, invalid):
    document = json.loads(kits.MANIFEST.read_text(encoding="utf-8"))
    if invalid == "identity":
        document["kit_id"] = "another-kit"
    elif invalid == "version":
        document["version"] = 2
    elif invalid == "unregistered":
        document["editor"]["preview_sources"]["feed"] = "assets/not-registered.jpg"
    else:
        document["media"].append({"path": "assets/post-unsafe.jpg"})
        document["editor"]["preview_sources"]["feed"] = "assets/post-unsafe.jpg"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setattr(kits, "MANIFEST", path)
    with pytest.raises(RuntimeError):
        kits._manifest()


def test_manifest_commercial_gate_tracks_status(tmp_path, monkeypatch):
    document = kits._manifest()
    assert not kits.kit_commercially_available()
    document["status"] = "approved"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setattr(kits, "MANIFEST", path)
    assert kits.kit_commercially_available()


@pytest.mark.parametrize("environment,selectable", [("testing", True), ("production", False)])
async def test_catalog_uses_manifest_and_real_business_name_without_paid_generation(
    monkeypatch, environment, selectable
):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    session = SimpleNamespace(scalar=AsyncMock(return_value="Café da Ana"))

    class Database:
        @asynccontextmanager
        async def transaction(self, tenant_id, actor_id):
            assert (tenant_id, actor_id) == (tenant, actor)
            yield session

    owner = AsyncMock()
    monkeypatch.setattr(kits.BrandKitService, "_owner", owner)
    service = kits.BrandKitService(SimpleNamespace(environment=environment), Database(), store=object())
    catalog = await service.catalog(tenant, business, actor)
    owner.assert_awaited_once_with(session, tenant, business, actor)
    item = catalog.kits[0]
    assert (item.kit_id, item.kit_version, item.selectable) == (kits.KIT_ID, kits.KIT_VERSION, selectable)
    assert item.default_overrides.brand_name == "Café da Ana"
    assert set(item.preview_images) == {"feed", "story", "reel_cover"}
    assert all(source.startswith("/brand-kits/cafe-pausas/v1/") for source in item.preview_images.values())
    assert item.options.layouts["feed"] == ["photo_focus", "offer_focus"]


async def test_catalog_rejects_missing_business(monkeypatch):
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))

    class Database:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            yield session

    monkeypatch.setattr(kits.BrandKitService, "_owner", AsyncMock())
    service = kits.BrandKitService(SimpleNamespace(environment="testing"), Database(), store=object())
    with pytest.raises(AuthError) as failure:
        await service.catalog(uuid4(), uuid4(), uuid4())
    assert (failure.value.code, failure.value.status) == ("BUSINESS_NOT_FOUND", 404)


def test_normalize_logo_preserves_pixels_and_removes_private_metadata():
    original = _image_bytes(metadata=True)
    media, raw_digest = kits._normalize_logo(_logo_body(original))
    assert (media.mime_type, raw_digest) == ("image/png", hashlib.sha256(original).hexdigest())
    assert media.sha256 == hashlib.sha256(media.data).hexdigest()
    with Image.open(io.BytesIO(media.data)) as normalized:
        assert normalized.size == (2, 3)
        assert "private_note" not in normalized.info


def test_normalize_logo_retains_alpha_channel():
    output = io.BytesIO()
    Image.new("RGBA", (2, 3), (36, 71, 57, 80)).save(output, format="PNG")
    media, _ = kits._normalize_logo(_logo_body(output.getvalue()))
    with Image.open(io.BytesIO(media.data)) as normalized:
        assert normalized.mode == "RGBA"
        assert normalized.getpixel((0, 0))[3] == 80


def test_normalize_logo_applies_exif_orientation():
    output = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (2, 3), "red").save(output, format="JPEG", exif=exif)
    media, _ = kits._normalize_logo(_logo_body(output.getvalue(), "image/jpeg"))
    with Image.open(io.BytesIO(media.data)) as normalized:
        assert normalized.size == (3, 2)


@pytest.mark.parametrize(
    "raw,mime_type,limit_name,limit_value,expected",
    [
        (b"invalid image data", "image/png", None, None, "BRAND_KIT_LOGO_INVALID"),
        (_image_bytes(), "image/jpeg", None, None, "BRAND_KIT_LOGO_INVALID"),
        (_image_bytes(), "image/png", "LOGO_MAX_BYTES", 1, "BRAND_KIT_LOGO_SIZE"),
        (_image_bytes(), "image/png", "LOGO_MAX_SIDE", 1, "BRAND_KIT_LOGO_INVALID"),
        (_image_bytes(), "image/png", "LOGO_MAX_PIXELS", 1, "BRAND_KIT_LOGO_INVALID"),
        (_image_bytes(), "image/png", "LOGO_MAX_STORED_BYTES", 1, "BRAND_KIT_LOGO_SIZE"),
    ],
)
def test_normalize_logo_enforces_type_dimensions_and_byte_limits(
    monkeypatch, raw, mime_type, limit_name, limit_value, expected
):
    if limit_name:
        monkeypatch.setattr(kits, limit_name, limit_value)
    with pytest.raises(AuthError) as failure:
        kits._normalize_logo(_logo_body(raw, mime_type))
    assert failure.value.code == expected


def test_normalize_logo_rejects_non_base64_and_empty_body():
    for content in ("not-base64!", ""):
        body = BrandKitLogoUpload.model_construct(
            operation_id=uuid4(), mime_type="image/png", content_base64=content, rights_confirmed=True
        )
        with pytest.raises(AuthError) as failure:
            kits._normalize_logo(body)
        assert failure.value.code == ("BRAND_KIT_LOGO_INVALID" if content else "BRAND_KIT_LOGO_SIZE")


@pytest.mark.parametrize(
    "headers,chunks,code,status",
    [
        ({"content-type": "application/json", "content-length": "bad"}, [b"{}"], "BRAND_KIT_LOGO_SIZE", 413),
        ({"content-type": "application/json", "content-length": "3000001"}, [b"{}"], "BRAND_KIT_LOGO_SIZE", 413),
        ({"content-type": "text/plain"}, [b"{}"], "BRAND_KIT_LOGO_INVALID", 415),
        ({"content-type": "application/json"}, [b"x" * 3_000_001], "BRAND_KIT_LOGO_SIZE", 413),
        ({"content-type": "application/json"}, [b"{bad"], "BRAND_KIT_LOGO_INVALID", 422),
        ({"content-type": "application/json"}, [b"{}"], "BRAND_KIT_LOGO_INVALID", 422),
        ({"content-type": "application/json"}, [], "BRAND_KIT_LOGO_INVALID", 422),
    ],
)
async def test_logo_route_caps_http_body_before_service(headers, chunks, code, status, monkeypatch):
    service = SimpleNamespace(upload_logo=AsyncMock())
    monkeypatch.setattr(routes, "service", lambda request: service)
    with pytest.raises(AuthError) as failure:
        await routes.logo_upload(uuid4(), uuid4(), _request(chunks, headers), uuid4())
    assert (failure.value.code, failure.value.status) == (code, status)
    service.upload_logo.assert_not_awaited()


@pytest.mark.parametrize("multiple_chunks", [False, True])
async def test_logo_route_passes_valid_contract_to_service(monkeypatch, multiple_chunks):
    payload = _logo_body(_image_bytes()).model_dump(mode="json")
    expected = BrandKitLogoRead(id=uuid4(), preview_url="https://example.invalid/private")
    service = SimpleNamespace(upload_logo=AsyncMock(return_value=expected))
    monkeypatch.setattr(routes, "service", lambda request: service)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    encoded = json.dumps(payload).encode()
    chunks = [b"", encoded[:13], encoded[13:]] if multiple_chunks else [encoded]
    result = await routes.logo_upload(tenant, business, _request(chunks, {"content-type": "application/json"}), actor)
    assert result == expected
    called = service.upload_logo.await_args.args
    assert called[:3] == (tenant, business, actor)
    assert isinstance(called[3], BrandKitLogoUpload)


def test_logo_http_upload_reconcile_and_private_url(monkeypatch):
    tenant, business, actor, logo_id = uuid4(), uuid4(), uuid4(), uuid4()
    uploaded = BrandKitLogoRead(id=logo_id, preview_url="https://example.invalid/private-preview")
    private = BrandKitLogoUrl(url="https://example.invalid/private-logo")
    fake = SimpleNamespace(
        upload_logo=AsyncMock(return_value=uploaded),
        reconcile_pending_logos=AsyncMock(return_value=2),
        logo_url=AsyncMock(return_value=private),
    )
    monkeypatch.setattr(routes, "service", lambda request: fake)
    app = FastAPI()
    app.include_router(routes.brand_kits_router)
    app.dependency_overrides[get_actor] = lambda: actor
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/brand-kit"

    with TestClient(app) as client:
        upload = client.post(f"{base}/logo", json=_logo_body(_image_bytes()).model_dump(mode="json"))
        reconcile = client.post(f"{base}/logo/reconcile")
        preview = client.get(f"{base}/logo/{logo_id}")

    assert (upload.status_code, upload.json()) == (201, uploaded.model_dump(mode="json"))
    assert (reconcile.status_code, reconcile.json()) == (200, {"reconciled": 2})
    assert (preview.status_code, preview.json()) == (200, private.model_dump(mode="json"))
    assert fake.upload_logo.await_args.args[:3] == (tenant, business, actor)
    assert isinstance(fake.upload_logo.await_args.args[3], BrandKitLogoUpload)
    fake.reconcile_pending_logos.assert_awaited_once_with(tenant, business, actor)
    fake.logo_url.assert_awaited_once_with(tenant, business, actor, logo_id)
