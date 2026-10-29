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
from app.services.visual_copy_authorization import authorize_visual_copy
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
    row = {
        "brand_kit_document": {"overrides": _overrides()},
        "document": draft,
        "context_version": 0,
        "expires_at": datetime.now(UTC) + timedelta(days=7),
    }
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
    monkeypatch.setattr("app.services.visual_copy_authorization.EditorialBriefingService.read_valid", read)
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


async def _authorize_copy(case):
    return await authorize_visual_copy(
        case.session, case.service.settings, case.service.database, *case.ids[:4], case.context.briefing_id
    )


def _context_fact(case, *, validity=None, statement="Preço confirmado", timezone="UTC"):
    fact_id = uuid4()
    case.row["context_version"] = 1
    case.row["document"]["script"][0].update(
        fact_ids=[str(fact_id)], on_screen_text=statement + ".", voiceover=statement + "."
    )
    document = {
        "facts": [
            {
                "id": str(fact_id),
                "kind": "other",
                "statement": statement,
                "source_detail": "Confirmação do titular",
                "valid_until": validity,
            }
        ]
    }
    case.session.scalar.side_effect = [document, timezone]
    return document


async def test_copy_without_temporal_sources_keeps_proposal_deadline_and_hides_private_text(case):
    copy = await _authorize_copy(case)
    assert copy.statement == "Croissant." and copy.cta == "Fale com o negócio"
    assert copy.valid_until == case.row["expires_at"]
    assert "Croissant" not in repr(copy) and "Fale com" not in repr(copy)


@pytest.mark.parametrize("variant", ["no_kit", "no_catalog"])
async def test_copy_requires_the_confirmed_kit_and_prepared_catalog(case, variant):
    if variant == "no_kit":
        case.row["brand_kit_document"] = None
    else:
        case.read.return_value = ("prepared", None)
    with pytest.raises(AuthError, match="VISUAL_CONTEXT_CHANGED"):
        await _authorize_copy(case)


@pytest.mark.parametrize("variant", ["two_facts", "no_fact_id", "missing_cta", "voiceover"])
async def test_copy_shape_and_literal_voiceover_are_checked_by_the_shared_rule(case, variant):
    script = case.row["document"]["script"]
    if variant == "two_facts":
        script.append(dict(script[0]))
    elif variant == "no_fact_id":
        script[0]["fact_ids"] = []
    elif variant == "missing_cta":
        script.pop()
    else:
        script[0]["voiceover"] = "Uma alegação alterada"
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await _authorize_copy(case)


@pytest.mark.parametrize("variant", ["missing_timezone", "missing_fact", "unbounded_fact"])
async def test_context_fact_requires_a_known_business_clock_and_matching_fact(case, variant):
    document = _context_fact(case, timezone=None if variant == "missing_timezone" else "UTC")
    if variant == "missing_fact":
        document["facts"] = []
    if variant == "unbounded_fact":
        assert (await _authorize_copy(case)).valid_until == case.row["expires_at"]
    else:
        with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
            await _authorize_copy(case)


async def test_context_validity_uses_end_of_business_day_even_after_utc_midnight(case, monkeypatch):
    from app.services import visual_copy_authorization as module

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 30, 1, tzinfo=UTC).astimezone(tz)

    monkeypatch.setattr(module, "datetime", Clock)
    case.row["expires_at"] = datetime(2026, 11, 3, tzinfo=UTC)
    _context_fact(case, validity="2026-10-29", timezone="America/Sao_Paulo")
    assert (await _authorize_copy(case)).valid_until == datetime(2026, 10, 30, 3, tzinfo=UTC)


@pytest.mark.parametrize("variant", ["valid", "missing_timezone", "expired", "not_set", "missing_validity"])
async def test_prepared_snapshot_price_also_limits_the_authorization_window(case, variant):
    day = datetime.now(UTC).date() + timedelta(days=-1 if variant == "expired" else 1)
    case.catalog["offering"]["price"] = {
        "status": "not_set" if variant == "not_set" else "valid",
        "valid_until": None if variant == "missing_validity" else day.isoformat(),
    }
    case.session.scalar.return_value = None if variant == "missing_timezone" else "UTC"
    if variant in {"missing_timezone", "expired"}:
        with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
            await _authorize_copy(case)
    else:
        deadline = (await _authorize_copy(case)).valid_until
        if variant == "valid":
            assert deadline.date() == day + timedelta(days=1)
        else:
            assert deadline == case.row["expires_at"]


async def test_context_fact_and_snapshot_price_share_the_same_timezone_and_take_the_earliest_deadline(case):
    day = datetime.now(UTC).date()
    _context_fact(case, validity=(day + timedelta(days=1)).isoformat(), timezone="UTC")
    case.catalog["offering"]["price"] = {"status": "valid", "valid_until": (day + timedelta(days=2)).isoformat()}
    copy = await _authorize_copy(case)
    assert copy.valid_until.date() == day + timedelta(days=2)
    assert case.session.scalar.await_count == 2


@pytest.mark.parametrize("variant", ["empty", "ends", "starts", "expired"])
async def test_promotion_window_cannot_outlive_snapshot_validity(case, variant):
    now = datetime.now(UTC)
    end = now + timedelta(hours=-1 if variant == "expired" else 3)
    case.catalog["promotions"] = [] if variant == "empty" else [{"ends_at": end.isoformat()}]
    start = now + timedelta(hours=1)
    case.session.scalar.return_value = start if variant == "starts" else None
    if variant == "expired":
        with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
            await _authorize_copy(case)
    else:
        copy = await _authorize_copy(case)
        expected = case.row["expires_at"] if variant == "empty" else start if variant == "starts" else end
        assert copy.valid_until == expected
        assert case.session.scalar.await_args.args[1]["started_at"] <= datetime.now(UTC)


async def test_a_proposal_that_expires_during_authorization_cannot_return_a_live_proof(case):
    case.row["expires_at"] = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(AuthError, match="VISUAL_COPY_UNVERIFIED"):
        await _authorize_copy(case)
