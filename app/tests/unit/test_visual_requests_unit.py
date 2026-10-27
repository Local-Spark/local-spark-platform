"""Visual prompts use only revalidated facts and identifiable references."""

from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.visual_ai import VisualReference
from app.services.auth import AuthError
from app.services.editorial_proposals import _catalog_fact
from app.services.visual_context import VisualContextSnapshot
from app.services.visual_references import VisualReferenceBundle, VisualReferenceSource
from app.services.visual_requests import VisualRequestService
from app.tests.integration.test_brand_kits import _overrides


@pytest.fixture
def case(settings, monkeypatch):
    tenant, business, actor, proposal, briefing, source, operation, item = [uuid4() for _ in range(8)]
    context = VisualContextSnapshot(tenant, business, proposal, briefing, source, "photo", 1, 0, 1, "a" * 64)
    catalog = {"offering": {"id": str(item), "version": 1, "name": "Croissant", "kind": "product"}}
    fact_id = _catalog_fact(catalog)["id"]
    draft = {
        "title": "Uma ideia",
        "format": "photo",
        "angle": "Apresentar um produto",
        "fact_ids": [fact_id],
        "hypotheses": [],
        "questions": [],
        "script": [
            {
                "role": "fact",
                "visual": "brand_card",
                "on_screen_text": "Croissant.",
                "voiceover": "Croissant.",
                "fact_ids": [fact_id],
            },
            {
                "role": "cta",
                "visual": "brand_card",
                "on_screen_text": "Fale com o negócio",
                "voiceover": "Entre em contato",
                "fact_ids": [],
            },
        ],
    }
    row = {"brand_kit_document": {"overrides": _overrides()}, "document": draft, "context_version": 0}
    sources = (
        VisualReferenceSource("source_photo", source, 1, "a" * 64, "b" * 64),
        VisualReferenceSource("item_photo", uuid4(), 1, "c" * 64, "d" * 64),
        VisualReferenceSource("space_photo", uuid4(), 1, "e" * 64, "f" * 64),
    )
    refs = VisualReferenceBundle(context, sources, tuple(VisualReference(b"opaque", "image/png") for _ in sources))
    monkeypatch.setattr("app.services.visual_requests.VisualReferenceService.load", AsyncMock(return_value=refs))
    capture = AsyncMock(return_value=context)
    monkeypatch.setattr("app.services.visual_requests.VisualContextService.capture", capture)
    read = AsyncMock(return_value=("prepared", catalog))
    monkeypatch.setattr("app.services.visual_requests.EditorialBriefingService.read_valid", read)
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))),
        scalar=AsyncMock(),
    )

    class DB:
        @asynccontextmanager
        async def transaction(self, tenant, actor):
            yield session

    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr("test-key")})
    service = VisualRequestService(cfg, DB())
    return SimpleNamespace(
        ids=(tenant, business, actor, proposal, operation),
        context=context,
        row=row,
        catalog=catalog,
        refs=refs,
        capture=capture,
        read=read,
        session=session,
        service=service,
    )


async def test_request_contains_verified_copy_and_reference_order(case):
    result = await case.service.prepare(*case.ids)
    assert result.request.size == "1024x1280" and result.request.output_format == "png"
    prompt = result.request.prompt
    assert 'Texto exato autorizado: "Croissant."' in prompt
    assert 'Chamada exata autorizada: "Fale com o negócio"' in prompt
    assert "Referência 1: imagem enviada" in prompt
    assert "Referência 2: produto" in prompt and "Referência 3: espaço" in prompt
    assert len(result.request.references) == 3 and len(result.request_hash) == 64
    assert "Croissant" not in repr(result)


async def test_story_without_space_uses_correct_size_and_concept_rule(case, monkeypatch):
    context = replace(case.context, format="story")
    refs = replace(case.refs, context=context, sources=(), references=())
    monkeypatch.setattr("app.services.visual_requests.VisualReferenceService.load", AsyncMock(return_value=refs))
    case.capture.return_value = context
    result = await case.service.prepare(*case.ids)
    assert result.request.size == "1152x2048"
    assert "não apresente um local inventado" in result.request.prompt


@pytest.mark.parametrize("reason", ["missing", "briefing", "fact", "cta", "changed", "key"])
async def test_unverified_or_changed_context_fails_closed(case, reason):
    if reason == "missing":
        case.session.execute.return_value = SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))
    elif reason == "briefing":
        case.read.return_value = ("unavailable", None)
    elif reason == "fact":
        case.row["document"]["script"][0]["on_screen_text"] = "R$ 10."
    elif reason == "cta":
        case.row["document"]["script"][1]["on_screen_text"] = "Promoção hoje"
    elif reason == "changed":
        case.capture.return_value = replace(case.context, fingerprint="b" * 64)
    else:
        case.service.settings = case.service.settings.model_copy(update={"meta_encryption_key": None})
    with pytest.raises(AuthError):
        await case.service.prepare(*case.ids)


async def test_current_owner_fact_must_be_valid_in_business_timezone(case):
    fact_id = uuid4()
    today = datetime.now(UTC).date()
    scene = case.row["document"]["script"][0]
    scene.update(fact_ids=[str(fact_id)], on_screen_text="Promoção válida.", voiceover="Promoção válida.")
    case.row["context_version"] = 1
    document = {
        "facts": [
            {
                "id": str(fact_id),
                "kind": "offer",
                "statement": "Promoção válida",
                "source_detail": "Confirmação",
                "valid_until": (today + timedelta(days=1)).isoformat(),
            }
        ]
    }
    case.session.scalar.side_effect = [document, "UTC"]
    assert "Promoção válida." in (await case.service.prepare(*case.ids)).request.prompt
    document["facts"][0]["valid_until"] = (today - timedelta(days=1)).isoformat()
    case.session.scalar.side_effect = [document, "UTC"]
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await case.service.prepare(*case.ids)


async def test_missing_script_and_unverified_fact_fail(case):
    case.row["document"]["script"] = []
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await case.service.prepare(*case.ids)


async def test_unknown_fact_without_context_fails(case):
    case.row["document"]["script"][0]["fact_ids"] = [str(uuid4())]
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await case.service.prepare(*case.ids)


async def test_missing_context_version_document_fails(case):
    case.row["document"]["script"][0]["fact_ids"] = [str(uuid4())]
    case.row["context_version"] = 1
    case.session.scalar.side_effect = [None, "UTC"]
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await case.service.prepare(*case.ids)
