"""Experimental creative briefs preserve evidence and do not expose traces."""

import json
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.adapters.editorial_ai import FULL_PIECE_FORMAT, OpenAIEditorialProvider
from app.schemas.editorial_proposals import CreativeBrief, ProposalDraft
from app.services.auth import AuthError
from app.services.editorial_proposals import (
    EditorialProposalService,
    _decode_request_trace,
    _encode_request_trace,
    generated_copy_matches_fact,
    natural_generated_copy_matches_fact,
)
from app.services.visual_skills import resolve_editorial_skill


def draft():
    return ProposalDraft(
        title="Uma pausa especial",
        format="photo",
        angle="Apresente o croissant na pausa do dia",
        fact_ids=[uuid4()],
        hypotheses=[],
        questions=[],
        art_text="Croissant por R$ 19,90",
        caption="Seu momento merece um croissant por R$ 19,90",
        cta="Mande uma mensagem",
        creative_brief=CreativeBrief(
            objective="Apresentar o produto",
            concept="Convidar o público para uma pausa",
            visual_direction="Fotografia aconchegante e tipografia legível",
            hierarchy="Produto em destaque e preço legível",
            photo_use="Use a foto enviada como referência do produto",
        ),
    )


def test_full_piece_request_includes_skill_context_and_brief_without_vocabulary_whitelist(settings):
    cfg = settings.model_copy(
        update={
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("fake"),
        }
    )
    payload = {
        "material": "Quero divulgar meu croissant",
        "editorial_skill": {
            "id": "instagram-feed-v1",
            "sha256": "a" * 64,
            "instructions": "Priorize uma ideia original.",
        },
    }
    request = OpenAIEditorialProvider(cfg).build_request(payload)
    assert request["text"]["format"] == FULL_PIECE_FORMAT
    assert "creative_brief" in request["text"]["format"]["schema"]["required"]
    developer = request["input"][0]["content"]
    assert "skill editorial versionada" in developer and "estas palavras de estilo" not in developer
    assert json.loads(request["input"][1]["content"]) == payload


def test_natural_copy_allows_new_words_but_still_checks_values_and_avoided_topics():
    proposal = draft()
    fact = "Croissant por R$ 19,90"
    assert not generated_copy_matches_fact(proposal, fact, [])
    assert natural_generated_copy_matches_fact(proposal, fact, [])
    assert not natural_generated_copy_matches_fact(
        proposal.model_copy(update={"art_text": "Croissant R$ 29,90"}), fact, []
    )
    assert not natural_generated_copy_matches_fact(proposal.model_copy(update={"cta": "Envie mensagem hoje"}), fact, [])
    assert not natural_generated_copy_matches_fact(proposal, fact, ["pausa"])
    assert not natural_generated_copy_matches_fact(proposal.model_copy(update={"creative_brief": None}), fact, [])


def test_format_ratio_in_art_direction_does_not_authorize_numbers_in_visible_copy():
    proposal = draft()
    assert proposal.creative_brief is not None
    brief = proposal.creative_brief.model_copy(update={"visual_direction": "Fotografia vertical 9:16"})
    story = proposal.model_copy(update={"format": "story", "creative_brief": brief})
    assert natural_generated_copy_matches_fact(story, "Croissant por R$ 19,90", [])
    assert not natural_generated_copy_matches_fact(
        story.model_copy(update={"art_text": "9 croissants"}), "Croissant por R$ 19,90", []
    )


@pytest.mark.parametrize("fmt,ratio", [("story", "9:16"), ("photo", "4:5")])
def test_technical_direction_notation_does_not_block_valid_creative_brief(fmt, ratio):
    proposal = draft()
    assert proposal.creative_brief is not None
    brief = proposal.creative_brief.model_copy(
        update={
            "visual_direction": f"Imagem {ratio}, cores #702321 e #FCF4E5, margens de 10%",
            "hierarchy": "1) Foto 2) Texto e preço 3) CTA",
            "photo_use": "Foto 2f075099-f621-5bc5-8e81-dad99622f9f0",
        }
    )
    proposal = proposal.model_copy(update={"format": fmt, "creative_brief": brief})
    assert natural_generated_copy_matches_fact(proposal, "Croissant por R$ 19,90", [])


@pytest.mark.parametrize(
    "field,value",
    [
        ("caption", "Croissant por R$ 10,00"),
        ("art_text", "3 croissants"),
        ("cta", "Peça hoje"),
    ],
)
def test_technical_direction_does_not_authorize_unsupported_public_copy(field, value):
    proposal = draft()
    assert proposal.creative_brief is not None
    brief = proposal.creative_brief.model_copy(
        update={"visual_direction": "Cores #702321, margens de 10%", "hierarchy": "1) Foto 2) Texto 3) CTA"}
    )
    proposal = proposal.model_copy(update={"creative_brief": brief, field: value})
    assert not natural_generated_copy_matches_fact(proposal, "Croissant por R$ 19,90", [])


@pytest.mark.parametrize(
    "visual_direction", ["Apresentar desconto de 10%", "Mostrar preço R$ 25,00", "Entregar em 2 horas"]
)
def test_technical_direction_filter_still_rejects_unsupported_commercial_claims(visual_direction):
    proposal = draft()
    assert proposal.creative_brief is not None
    brief = proposal.creative_brief.model_copy(update={"visual_direction": visual_direction})
    assert not natural_generated_copy_matches_fact(
        proposal.model_copy(update={"creative_brief": brief}), "Croissant por R$ 19,90", []
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("caption", "Croissant por R$ 19,90 (asset_id)"),
        ("art_text", "Foto close-up do croissant"),
        ("cta", "Ver 2f075099-f621-5bc5-8e81-dad99622f9f0"),
    ],
)
def test_full_piece_rejects_public_internal_artifacts(field, value):
    proposal = draft().model_copy(update={field: value})
    assert not natural_generated_copy_matches_fact(proposal, "Croissant por R$ 19,90", [])


def test_configured_phone_is_allowed_but_does_not_authorize_other_numbers():
    proposal = draft().model_copy(update={"cta": "Ligue para 11999999999"})
    fact_id = proposal.fact_ids[0]
    data = {
        "confirmed_facts": [{"id": str(fact_id), "statement": "Croissant por R$ 19,90"}],
        "preferences": {"avoided_topics": [], "cta_destination": {"type": "phone", "value": "11999999999"}},
        "requested_format": "photo",
        "eligible_formats": ["photo"],
    }
    assert EditorialProposalService._safe_generated(proposal, data, {fact_id}, full_piece=True)
    wrong_phone = proposal.model_copy(update={"cta": "Ligue para 11999999998"})
    assert not EditorialProposalService._safe_generated(wrong_phone, data, {fact_id}, full_piece=True)
    wrong_price = proposal.model_copy(update={"caption": "R$ 29,90. Ligue para 11999999999"})
    assert not EditorialProposalService._safe_generated(wrong_price, data, {fact_id}, full_piece=True)
    no_destination = {**data, "preferences": {"avoided_topics": []}}
    assert not EditorialProposalService._safe_generated(proposal, no_destination, {fact_id}, full_piece=True)


def test_request_trace_encrypted_and_authenticated():
    key = Fernet.generate_key().decode()
    request = {"body": {"pedido": "informação privada do negócio"}, "client_request_id": str(uuid4())}
    digest, ciphertext = _encode_request_trace(key, request)
    assert "informação privada" not in ciphertext
    assert _decode_request_trace(key, digest, ciphertext) == request
    with pytest.raises(AuthError, match="EDITORIAL_TRACE_UNAVAILABLE"):
        _decode_request_trace(key, "0" * 64, ciphertext)
    with pytest.raises(AuthError, match="EDITORIAL_TRACE_UNAVAILABLE"):
        _decode_request_trace(Fernet.generate_key().decode(), digest, ciphertext)


@pytest.mark.parametrize("format,expected", [("photo", "instagram-feed-v1"), ("story", "instagram-story-v1")])
def test_briefing_selects_the_versioned_skill_for_its_confirmed_format(format, expected):
    skill_id, digest, instructions = resolve_editorial_skill(format)
    assert skill_id == expected and len(digest) == 64
    assert "Direção criativa" in instructions or "## Criação" in instructions


def test_video_does_not_receive_an_unrelated_feed_or_story_skill():
    with pytest.raises(AuthError, match="VISUAL_SKILL_FORMAT_INVALID"):
        resolve_editorial_skill("short_video")
