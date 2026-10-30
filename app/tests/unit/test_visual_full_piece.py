"""Full-piece requests keep the customer context and verified logo as sources."""

import hashlib
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.editorial_consent_scope import admitted_visual_run
from app.services.visual_brand_finish import FULL_RECIPE
from app.services.visual_requests import visual_request_digest
from app.tests.unit.test_visual_brand_finish_unit import brand_case as fixture_brand_case
from app.tests.unit.test_visual_brand_finish_unit import picture
from app.tests.unit.visual_full_fixture import configure_full as _configure
from app.tests.unit.visual_full_fixture import result as _result

brand_case = fixture_brand_case


async def test_full_piece_sends_complete_context_and_real_logo(brand_case):
    case = brand_case
    scope, message, logo = _configure(case, logo=True)
    with admitted_visual_run(scope):
        prepared = await case.service.prepare(*case.ids)
    prompt = prepared.request.request.prompt
    assert message in prompt
    assert "Pausa com sabor" in prompt
    assert "Croissant R$ 18,00" in prompt
    assert "Croissant por R$ 18,00" in prompt
    assert "Faça seu pedido" in prompt
    assert "logomarca original autorizada" in prompt
    assert "Não acrescente palavras" not in prompt
    assert "Orientação criativa de referência versionada" in prompt
    assert prepared.request.skill_id == "instagram-feed-v1"
    assert prepared.request.skill_sha256 == case.row["document"]["editorial_skill_sha256"]
    assert prepared.request.skill_sha256 in prompt
    assert prepared.recipe == FULL_RECIPE
    assert len(prepared.request.request.references) == 3
    assert logo is not None and prepared.request.request.references[-2].content == logo.data
    assert prepared.request.sources[-2].kind == "brand_logo"
    assert prepared.request.sources[-2].normalized_sha256 == hashlib.sha256(logo.data).hexdigest()
    assert prepared.request.sources[-1].kind == "kit_example"
    assert prepared.request.sources[-1].catalog_id == "cafe-pausas"
    assert prepared.request.sources[-1].asset_path == "assets/post-editorial-croissant.jpg"
    assert "imagem de exemplo do kit é fictícia" in prompt
    assert prepared.request.request_hash == visual_request_digest(
        case.service.settings.meta_encryption_key.get_secret_value(),
        case.context,
        prepared.request.sources,
        prepared.request.request,
    )
    for field, value in (("catalog_id", "other"), ("asset_path", "assets/other.jpg")):
        altered = (*prepared.request.sources[:-1], replace(prepared.request.sources[-1], **{field: value}))
        assert prepared.request.request_hash != visual_request_digest(
            case.service.settings.meta_encryption_key.get_secret_value(),
            case.context,
            altered,
            prepared.request.request,
        )
    assert message not in repr(prepared)


async def test_full_piece_without_original_logo_has_no_fabricated_reference(brand_case):
    scope, _, _ = _configure(brand_case)
    with admitted_visual_run(scope):
        prepared = await brand_case.service.prepare(*brand_case.ids)
    assert len(prepared.request.request.references) == 2
    assert "ausência de logomarca" in prepared.request.request.prompt


async def test_full_piece_includes_non_expiring_business_context_with_source(brand_case, monkeypatch):
    case = brand_case
    scope, _, _ = _configure(case)
    context = replace(case.context, context_version=1)
    original = replace(case.original, context=context)
    monkeypatch.setattr(
        "app.services.visual_brand_finish.VisualRequestService.prepare", AsyncMock(return_value=original)
    )
    case.capture.return_value = context
    case.row.update(
        business_name="Café Horizonte",
        business_category="Cafeteria",
        business_city="São Paulo",
        business_description="Café de bairro",
        business_context_document={
            "facts": [
                {
                    "id": str(uuid4()),
                    "kind": "differentiator",
                    "statement": "Receitas da família",
                    "source_detail": "Informado pelo titular",
                    "valid_until": None,
                },
                {
                    "id": str(uuid4()),
                    "kind": "offer",
                    "statement": "Oferta temporária",
                    "source_detail": "Informado pelo titular",
                    "valid_until": "2099-12-31",
                },
                {
                    "id": str(uuid4()),
                    "kind": "offer",
                    "statement": "Oferta expirada",
                    "source_detail": "Informado pelo titular",
                    "valid_until": "2000-01-01",
                },
            ],
            "preferences": {"tone": "friendly", "goal": "sales", "avoided_topics": []},
        },
    )
    with admitted_visual_run(scope):
        prepared = await case.service.prepare(*case.ids)
    prompt = prepared.request.request.prompt
    assert "Café Horizonte" in prompt and "Café de bairro" in prompt
    assert "Receitas da família" in prompt and "Informado pelo titular" in prompt
    assert "Oferta expirada" not in prompt
    assert "Oferta temporária" not in prompt
    assert "não ampliam a autorização comercial" in prompt


async def test_full_piece_requires_pinned_context(brand_case, monkeypatch):
    case = brand_case
    scope, _, _ = _configure(case)
    context = replace(case.context, context_version=1)
    monkeypatch.setattr(
        "app.services.visual_brand_finish.VisualRequestService.prepare",
        AsyncMock(return_value=replace(case.original, context=context)),
    )
    case.row["business_context_document"] = None
    with admitted_visual_run(scope), pytest.raises(AuthError, match="VISUAL_CONTEXT_CHANGED"):
        await case.service.prepare(*case.ids)


async def test_full_piece_finish_keeps_provider_image_and_rechecks_context(brand_case, monkeypatch):
    case = brand_case
    scope, _, _ = _configure(case)
    with admitted_visual_run(scope):
        prepared = await case.service.prepare(*case.ids)
    monkeypatch.setattr(case.service, "prepare", AsyncMock(return_value=prepared))
    scene = picture()
    assert await case.service.finish(case.ids[2], prepared, scene) is scene
    assert case.service.prepare.await_count == 2


@pytest.mark.parametrize("failure", ["recipe", "source", "brief", "skill"])
async def test_full_piece_rejects_missing_or_changed_context(brand_case, failure):
    case = brand_case
    scope, _, _ = _configure(case)
    rows = list(case.session.execute.side_effect)
    if failure == "recipe":
        rows[0].mappings().one_or_none()["visual_recipe"] = "legacy_overlay"
    elif failure == "source":
        rows[2] = _result(None)
    elif failure == "brief":
        case.row["document"]["creative_brief"] = None
    else:
        case.row["document"]["editorial_skill_sha256"] = "0" * 64
    case.session.execute.side_effect = rows
    with admitted_visual_run(scope), pytest.raises(AuthError):
        await case.service.prepare(*case.ids)


@pytest.mark.parametrize("mode", ["none", "no_preview", "legacy", "production", "key"])
async def test_new_generation_requires_admitted_full_recipe_and_key(brand_case, mode):
    case = brand_case
    scope, _, _ = _configure(case)
    if mode == "none":
        with pytest.raises(AuthError, match="VISUAL_RECIPE_CHANGED"):
            await case.service.prepare(*case.ids)
        return
    if mode == "no_preview":
        scope = replace(scope, preview=None)
    elif mode == "legacy":
        scope = replace(scope, visual_recipe="legacy_overlay")
    elif mode == "production":
        case.service.settings = case.service.settings.model_copy(update={"environment": "production"})
    else:
        case.service.settings = case.service.settings.model_copy(update={"meta_encryption_key": None})
    with admitted_visual_run(scope), pytest.raises(AuthError):
        await case.service.prepare(*case.ids)


@pytest.mark.parametrize("mode", ["partial", "snapshot", "missing_editorial", "different_editorial", "undecryptable"])
async def test_full_piece_rejects_skill_or_source_provenance_mismatch(brand_case, mode):
    case = brand_case
    scope, _, _ = _configure(case)
    rows = list(case.session.execute.side_effect)
    if mode == "partial":
        scope = replace(scope, skill_id="instagram-feed-v1")
    elif mode == "snapshot":
        rows[0] = _result(None)
    elif mode == "missing_editorial":
        case.row["document"]["editorial_skill_id"] = None
    elif mode == "different_editorial":
        scope = replace(scope, skill_id="instagram-story-v1", skill_sha256="a" * 64)
        rows[0] = _result(
            {"visual_skill_id": scope.skill_id, "visual_skill_sha256": scope.skill_sha256, "visual_recipe": FULL_RECIPE}
        )
    else:
        rows[2] = _result({"ciphertext": "invalid", "transcript_ciphertext": None})
    case.session.execute.side_effect = rows
    with admitted_visual_run(scope), pytest.raises(AuthError):
        await case.service.prepare(*case.ids)
