"""Checks for specific real-world leaks without imposing a fixed vocabulary."""

from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.schemas.editorial_proposals import ProposalDraft
from app.services.editorial_copy_quality import public_copy_has_no_internal_artifacts


def _draft() -> ProposalDraft:
    return ProposalDraft(
        title="Seu momento",
        format="story",
        angle="Apresentar o trabalho e convidar ao contato",
        fact_ids=[uuid4()],
        hypotheses=[],
        questions=[],
        art_text="Alongamento acrílico decorado — R$ 95,00",
        caption="Conheça nosso alongamento acrílico decorado por R$ 95,00.",
        cta="Fale com a gente",
    )


@pytest.mark.parametrize("field", ["art_text", "caption", "cta"])
@pytest.mark.parametrize(
    "artifact", ["c7c027d8-42b3-5db9-b98e-629176c38bf0", "asset_id", "fact_ids", "asset id: registro"]
)
def test_public_copy_rejects_leaked_identifiers(field, artifact):
    proposal = _draft().model_copy(update={field: f"Conheça {artifact}"})
    assert not public_copy_has_no_internal_artifacts(proposal)


@pytest.mark.parametrize(
    "direction",
    [
        "Foto close-up das unhas com alongamento acrílico decorado, enquadramento vertical centrado nas mãos.",
        "Imagem centralizada com preço",
        "Foto das unhas com enquadramento centralizado",
        "Close-up das unhas decoradas",
        "Use a foto enviada como fundo",
        "Aplique tipografia destacada",
    ],
)
def test_visual_direction_is_not_treated_as_text_to_print(direction):
    assert not public_copy_has_no_internal_artifacts(_draft().model_copy(update={"art_text": direction}))


@pytest.mark.parametrize("text", ["Uma foto para recordar", "Alongamento em destaque", "Sua pausa merece um café!"])
def test_public_copy_keeps_natural_language(text):
    assert public_copy_has_no_internal_artifacts(_draft().model_copy(update={"art_text": text}))


def test_prompt_separates_public_text_from_directions_and_internal_metadata(settings):
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    request = OpenAIEditorialProvider(cfg).build_request({"editorial_skill": {"instructions": "Story criativo"}})
    developer = request["input"][0]["content"]
    assert "art_text deve conter somente o texto final" in developer
    assert "Nunca inclua IDs, UUIDs" in developer
    assert "Coloque instruções de fotografia, composição e tipografia apenas em creative_brief" in developer
    assert "registre dúvidas e pendências em questions" in developer
