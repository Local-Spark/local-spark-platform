"""Provider inputs come only from the validated briefing and private collection."""

import hashlib
import io
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from PIL import Image

from app.adapters.material_media import FetchedMedia
from app.services.auth import AuthError
from app.services.visual_context import VisualContextSnapshot
from app.services.visual_references import VisualReferenceService


@pytest.fixture
def case(settings, monkeypatch):
    tenant, business, actor, proposal, briefing, source = [uuid4() for _ in range(6)]
    image = Image.new("RGB", (80, 80), "red")
    raw = io.BytesIO()
    exif = Image.Exif()
    exif[270] = "private text"
    image.save(raw, format="PNG", exif=exif)
    data = raw.getvalue()
    photo_id = uuid4()
    photo = {"id": str(photo_id), "version": 1, "sha256": hashlib.sha256(data).hexdigest(), "space_kind": None}
    catalog = {"item_photo": photo, "space_photo": None}
    context = VisualContextSnapshot(tenant, business, proposal, briefing, source, "photo", 1, 0, 1, "a" * 64)
    capture = AsyncMock(return_value=context)
    read = AsyncMock(return_value=("prepared", catalog))
    monkeypatch.setattr("app.services.visual_references.VisualContextService.capture", capture)
    monkeypatch.setattr("app.services.visual_references.EditorialBriefingService.read_valid", read)
    row = {"object_key": "private/key", "mime_type": "image/png"}
    source_row = {"id": source, "kind": "text", "object_key": None, "mime_type": None, "sha256": None}

    async def execute(statement, params):
        value = source_row if "whatsapp_material_assets" in str(statement) else row
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: value))

    session = SimpleNamespace(execute=AsyncMock(side_effect=execute))

    class DB:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            yield session

    store = SimpleNamespace(get_image=AsyncMock(return_value=data))
    service = VisualReferenceService(settings, DB(), store)
    return SimpleNamespace(
        ids=(tenant, business, actor, proposal),
        context=context,
        catalog=catalog,
        photo=photo,
        service=service,
        capture=capture,
        read=read,
        session=session,
        store=store,
        source_row=source_row,
    )


async def test_reference_is_checked_and_normalized_without_private_metadata(case):
    result = await case.service.load(*case.ids)
    assert len(result.references) == 1 and result.sources[0].id == UUID(case.photo["id"])
    assert result.sources[0].source_sha256 == case.photo["sha256"]
    assert result.sources[0].normalized_sha256 == hashlib.sha256(result.references[0].content).hexdigest()
    with Image.open(io.BytesIO(result.references[0].content)) as image:
        assert not image.getexif()
    assert "private/key" not in repr(result) and "private text" not in repr(result)
    assert case.capture.await_count == 2


async def test_no_photos_is_valid_and_does_not_read_storage(case):
    case.catalog["item_photo"] = None
    result = await case.service.load(*case.ids)
    assert not result.references and not result.sources
    case.store.get_image.assert_not_awaited()


async def test_multiple_sources_have_stable_order(case):
    case.catalog["space_photo"] = {**case.photo, "id": str(uuid4()), "space_kind": "room"}
    result = await case.service.load(*case.ids)
    assert [s.kind for s in result.sources] == ["item_photo", "space_photo"]


@pytest.mark.parametrize("reason", ["briefing", "deleted", "tampered", "changed"])
async def test_fails_closed_when_context_or_media_changes(case, reason):
    if reason == "briefing":
        case.read.return_value = ("context_changed", None)
    elif reason == "deleted":
        case.session.execute.side_effect = None
        case.session.execute.return_value = SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))
    elif reason == "tampered":
        case.store.get_image.return_value = b"altered"
    else:
        case.capture.side_effect = [case.context, replace(case.context, fingerprint="b" * 64)]
    with pytest.raises(AuthError):
        await case.service.load(*case.ids)


@pytest.mark.parametrize("size", [(4097, 2), (2, 4097), (4000, 4000)])
async def test_rejects_provider_incompatible_dimensions(case, size, monkeypatch):
    raw = io.BytesIO()
    Image.new("RGB", size).save(raw, format="PNG")
    content = raw.getvalue()
    monkeypatch.setattr(
        "app.services.visual_references.normalize_photo",
        lambda *args: FetchedMedia(content, "image/png", hashlib.sha256(content).hexdigest()),
    )
    with pytest.raises(AuthError, match="VISUAL_REFERENCE_TOO_LARGE"):
        await case.service.load(*case.ids)


async def test_rejects_provider_incompatible_bytes(case, monkeypatch):
    content = b"x" * (5 * 1024 * 1024 + 1)
    monkeypatch.setattr(
        "app.services.visual_references.normalize_photo",
        lambda *args: FetchedMedia(content, "image/png", hashlib.sha256(content).hexdigest()),
    )
    # Open happens before the dimension check; use a valid oversized PNG through
    # a mocked image header to exercise the hard byte limit safely.
    monkeypatch.setattr("app.services.visual_references.Image.open", lambda *args: Image.new("RGB", (1, 1)))
    with pytest.raises(AuthError, match="VISUAL_REFERENCE_TOO_LARGE"):
        await case.service.load(*case.ids)


async def test_whatsapp_image_is_normalized_without_becoming_catalog_photo(case):
    case.source_row.update(kind="image", object_key="temporary/key", mime_type="image/png", sha256=case.photo["sha256"])
    result = await case.service.load(*case.ids)
    assert [source.kind for source in result.sources] == ["source_photo", "item_photo"]
    assert result.sources[0].id == case.context.source_asset_id
    with Image.open(io.BytesIO(result.references[0].content)) as image:
        assert not image.getexif()


async def test_whatsapp_photo_orientation_is_applied_before_removing_exif(case):
    raw = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (20, 40), "red").save(raw, format="JPEG", exif=exif)
    data = raw.getvalue()
    case.catalog["item_photo"] = None
    case.store.get_image.return_value = data
    case.source_row.update(
        kind="image", object_key="temporary/key", mime_type="image/jpeg", sha256=hashlib.sha256(data).hexdigest()
    )
    result = await case.service.load(*case.ids)
    with Image.open(io.BytesIO(result.references[0].content)) as image:
        assert image.size == (40, 20) and not image.getexif()


async def test_whatsapp_image_requires_metadata(case):
    case.source_row.update(kind="image", object_key=None)
    with pytest.raises(AuthError, match="VISUAL_SOURCE_NOT_READY"):
        await case.service.load(*case.ids)


async def test_photo_removed_after_briefing_validation_fails(case):
    source = case.source_row

    async def execute(statement, params):
        row = source if "whatsapp_material_assets" in str(statement) else None
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))

    case.session.execute.side_effect = execute
    with pytest.raises(AuthError, match="VISUAL_REFERENCE_CHANGED"):
        await case.service.load(*case.ids)
