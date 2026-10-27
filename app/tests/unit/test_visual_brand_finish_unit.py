"""Verified brand finishing remains local and rejects changed inputs."""

import hashlib
import io
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from pydantic import SecretStr

from app.adapters.material_media import FetchedMedia
from app.adapters.visual_ai import VisualReference, VisualRequest
from app.services.auth import AuthError
from app.services.visual_brand_finish import VisualBrandFinishService
from app.services.visual_context import VisualContextSnapshot
from app.services.visual_references import VisualReferenceSource
from app.services.visual_requests import PreparedVisualRequest, visual_request_digest
from app.tests.integration.test_brand_kits import _overrides


def picture(size=(64, 64), color="white"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    data = buf.getvalue()
    return FetchedMedia(data, "image/png", hashlib.sha256(data).hexdigest())


@pytest.fixture
def brand_case(settings, monkeypatch):
    tenant, business, actor, proposal, briefing, source, operation = [uuid4() for _ in range(7)]
    context = VisualContextSnapshot(tenant, business, proposal, briefing, source, "photo", 1, 0, 1, "a" * 64)
    ref = picture()
    sources = (VisualReferenceSource("item_photo", source, 1, ref.sha256, ref.sha256),)
    request = VisualRequest(
        "Original text",
        "gpt-image-2.5-flare-2026-09-08",
        "medium",
        "1024x1280",
        "png",
        operation,
        (VisualReference(ref.data, ref.mime_type),),
    )
    original = PreparedVisualRequest(context, sources, "old", request)
    monkeypatch.setattr(
        "app.services.visual_brand_finish.VisualRequestService.prepare", AsyncMock(return_value=original)
    )
    capture = AsyncMock(return_value=context)
    monkeypatch.setattr("app.services.visual_brand_finish.VisualContextService.capture", capture)
    read = AsyncMock(return_value=("prepared", {"offering": {"name": "Croissant"}}))
    monkeypatch.setattr("app.services.visual_brand_finish.EditorialBriefingService.read_valid", read)
    row = {
        "brand_kit_document": {"overrides": _overrides()},
        "document": {
            "title": "Uma ideia",
            "format": "photo",
            "angle": "Apresentar um produto",
            "fact_ids": [],
            "hypotheses": [],
            "questions": [],
            "script": [
                {
                    "role": "fact",
                    "visual": "brand_card",
                    "on_screen_text": "Croissant.",
                    "voiceover": "Croissant.",
                    "fact_ids": [str(uuid4())],
                },
                {
                    "role": "cta",
                    "visual": "brand_card",
                    "on_screen_text": "Fale com o negócio",
                    "voiceover": "Entre em contato",
                    "fact_ids": [],
                },
            ],
        },
    }
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row)))
    )

    class DB:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            yield session

    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr("test-key")})
    store = SimpleNamespace(get_image=AsyncMock())
    service = VisualBrandFinishService(cfg, DB(), store)
    return SimpleNamespace(
        ids=(tenant, business, actor, proposal, operation),
        context=context,
        original=original,
        row=row,
        session=session,
        read=read,
        capture=capture,
        service=service,
        store=store,
    )


async def test_prepare_builds_signed_text_free_scene_and_preserves_copy_for_overlay(brand_case):
    c = brand_case
    prepared = await c.service.prepare(*c.ids)
    prompt = prepared.request.request.prompt
    assert "Croissant" in prompt and "Não acrescente palavras" in prompt
    assert "Fale com o negócio" not in prompt
    assert prepared.statement == "Croissant." and prepared.cta == "Fale com o negócio"
    assert prepared.request.request_hash == visual_request_digest(
        "test-key", c.context, c.original.sources, prepared.request.request
    )
    assert "Croissant" not in repr(prepared)


async def test_prepared_logo_is_loaded_by_owner_and_checked_by_hash(brand_case):
    c = brand_case
    logo = picture(color="red")
    c.row["brand_kit_document"]["overrides"]["logo_asset_id"] = str(uuid4())
    logo_row = {"object_key": "private/key", "sha256": logo.sha256, "mime_type": "image/png"}
    c.session.execute.side_effect = [
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: c.row)),
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: logo_row)),
    ]
    c.store.get_image.return_value = logo.data
    result = await c.service.prepare(*c.ids)
    assert result.logo == logo
    c.session.execute.side_effect = [
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: c.row)),
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: logo_row)),
    ]
    c.store.get_image.return_value = b"different bytes"
    with pytest.raises(AuthError, match="VISUAL_LOGO_CHANGED"):
        await c.service.prepare(*c.ids)


async def test_context_change_blocks_before_provider_request(brand_case):
    brand_case.capture.return_value = replace(brand_case.context, fingerprint="b" * 64)
    with pytest.raises(AuthError, match="VISUAL_CONTEXT_CHANGED"):
        await brand_case.service.prepare(*brand_case.ids)


@pytest.mark.parametrize("failure", ["tenant", "business", "proposal", "operation", "briefing", "row", "script", "key"])
async def test_prepare_rejects_mismatched_or_unverified_inputs(brand_case, monkeypatch, failure):
    c = brand_case
    original = c.original
    if failure in {"tenant", "business", "proposal"}:
        attr = {"tenant": "tenant_id", "business": "business_id", "proposal": "proposal_id"}[failure]
        original = replace(original, context=replace(c.context, **{attr: uuid4()}))
    elif failure == "operation":
        original = replace(original, request=replace(original.request, request_id=uuid4()))
    elif failure == "briefing":
        c.read.return_value = ("unavailable", None)
    elif failure == "row":
        c.session.execute.return_value = SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))
    elif failure == "script":
        c.row["document"]["script"] = []
    else:
        c.service.settings = c.service.settings.model_copy(update={"meta_encryption_key": None})
    monkeypatch.setattr(
        "app.services.visual_brand_finish.VisualRequestService.prepare", AsyncMock(return_value=original)
    )
    with pytest.raises(AuthError):
        await c.service.prepare(*c.ids)


async def test_missing_logo_or_wrong_tenant_rejects_preparation(brand_case):
    c = brand_case
    c.row["brand_kit_document"]["overrides"]["logo_asset_id"] = str(uuid4())
    c.session.execute.side_effect = [
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: c.row)),
        SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None)),
    ]
    with pytest.raises(AuthError, match="VISUAL_LOGO_CHANGED"):
        await c.service.prepare(*c.ids)


async def test_space_reference_uses_explicit_real_location_direction(brand_case, monkeypatch):
    c = brand_case
    space = picture()
    source = VisualReferenceSource("space_photo", uuid4(), 1, space.sha256, space.sha256)
    original = replace(
        c.original,
        sources=(source,),
        request=replace(c.original.request, references=(VisualReference(space.data, "image/png"),)),
    )
    monkeypatch.setattr(
        "app.services.visual_brand_finish.VisualRequestService.prepare", AsyncMock(return_value=original)
    )
    result = await c.service.prepare(*c.ids)
    assert "espaço real do negócio" in result.request.request.prompt
    assert "Sem referência do espaço" not in result.request.request.prompt


async def test_finish_renders_actual_scene_with_exact_verified_inputs(brand_case, monkeypatch):
    c = brand_case
    prepared = await c.service.prepare(*c.ids)
    fresh = AsyncMock(return_value=prepared)
    monkeypatch.setattr(c.service, "prepare", fresh)
    scene = picture((1024, 1280), "blue")
    result = await c.service.finish(c.ids[2], prepared, scene)
    with Image.open(io.BytesIO(result.data)) as image:
        assert image.size == (1024, 1280) and image.format == "PNG"
    assert result.sha256 == hashlib.sha256(result.data).hexdigest()
    assert fresh.await_count == 2


@pytest.mark.parametrize("changed_at", ["before", "after"])
async def test_finish_discards_candidate_when_source_changes(brand_case, monkeypatch, changed_at):
    c = brand_case
    prepared = await c.service.prepare(*c.ids)
    changed = replace(prepared, cta="Outra mensagem")
    c.service.prepare = AsyncMock(side_effect=([changed] if changed_at == "before" else [prepared, changed]))
    monkeypatch.setattr("app.services.visual_brand_finish.render_brand_overlay", lambda *args, **kwargs: picture())
    with pytest.raises(AuthError, match="VISUAL_CONTEXT_CHANGED"):
        await c.service.finish(c.ids[2], prepared, picture())
