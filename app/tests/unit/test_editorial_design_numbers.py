"""Private design notation must not grant authority to public commercial claims."""

from uuid import uuid4

import pytest

from app.schemas.editorial_proposals import CreativeBrief, ProposalDraft
from app.services.editorial_proposals import EditorialProposalService


@pytest.fixture
def editorial_case():
    identifier = uuid4()
    title = "Ambiente ilustrativo de referência 2 — ilustrativa • Pexels 31777028"
    proposal = ProposalDraft(
        title="Convite para uma pausa",
        format="photo",
        angle="Conheça o Café Aurora",
        fact_ids=[identifier],
        hypotheses=[],
        questions=[],
        art_text="Café Aurora",
        caption="Que tal uma pausa com calma?",
        cta="Conheça nosso cardápio",
        creative_brief=CreativeBrief(
            objective="Convidar para conhecer o negócio",
            concept="Uma pausa com calma",
            visual_direction="Faixa #FFF8EC com 85% opacidade",
            hierarchy="1) Foto 2) Nome 3) Logo",
            photo_use=f"Usar o arquivo autorizado {title}",
        ),
    )
    data = {
        "confirmed_facts": [{"id": str(identifier), "statement": "Café Aurora"}],
        "preferences": {},
        "eligible_formats": ["photo"],
        "requested_format": "photo",
        "available_materials": [{"title": title, "authorized": True}],
    }
    return proposal, data, {identifier}


def test_exact_authorized_label_and_private_opacity_are_not_commercial_values(editorial_case):
    proposal, data, ids = editorial_case
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) is None
    data["available_materials"][0]["authorized"] = False
    assert (
        EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )


@pytest.mark.parametrize(
    "caption,reason",
    [
        ("Que tal 85 cafés?", "EDITORIAL_UNCONFIRMED_NUMBER"),
        ("Conheça a foto 31777028", "EDITORIAL_UNCONFIRMED_NUMBER"),
        ("Que tal uma pausa com calma hoje?", "EDITORIAL_UNCONFIRMED_CLAIM"),
        ("Temos desconto para você", "EDITORIAL_UNCONFIRMED_CLAIM"),
    ],
)
def test_design_metadata_never_authorizes_public_claims(editorial_case, caption, reason):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(update={"caption": caption})
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) == reason


def test_wrong_material_and_unbounded_opacity_still_fail(editorial_case):
    proposal, data, ids = editorial_case
    for field, value in [("photo_use", "Usar a foto 987654"), ("visual_direction", "Opacidade de 185%")]:
        changed = proposal.model_copy(
            update={"creative_brief": proposal.creative_brief.model_copy(update={field: value})}
        )
        assert (
            EditorialProposalService._generated_rejection(changed, data, ids, full_piece=True)
            == "EDITORIAL_UNCONFIRMED_NUMBER"
        )


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Ambiente ilustrativo de referência 2", None),
        ("Ambiente ilustrativo de referência 25", "EDITORIAL_UNCONFIRMED_NUMBER"),
        ("Ambiente ilustrativo de referência 3", "EDITORIAL_UNCONFIRMED_NUMBER"),
    ],
)
def test_authorized_title_without_provenance_suffix(editorial_case, name, expected):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(
        update={
            "creative_brief": proposal.creative_brief.model_copy(
                update={
                    "photo_use": f"Usar a '{name}' autorizada como imagem principal",
                    "visual_direction": f"Usar a foto ({name}) como plano de fundo",
                }
            )
        }
    )
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) == expected


def test_editorial_reference_omits_identifiers_but_keeps_illustrative_declaration():
    from app.services.editorial_materials import editorial_material_reference

    reference = editorial_material_reference(
        {
            "role": "space_photo",
            "title": "Ambiente ilustrativo de referência 2 — ilustrativa • Pexels 31777028",
        }
    )
    assert reference["title"] == "Foto de ambiente (imagem ilustrativa)"
    assert reference["declared_illustrative"] is True


@pytest.mark.parametrize(
    "direction",
    [
        "Reserve faixa inferior em 20–25% da altura para aplicar o texto.",
        "Use 20-25% da largura e margens de 5–10%.",
        "Texto de 24–32px, entrelinha de 120px e canvas 1080×1350px.",
        "Opacidade de 80 a 90%, fonte de 16pt e espaçamento de 1.5rem.",
    ],
)
def test_design_measurement_families_do_not_require_commercial_facts(editorial_case, direction):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(
        update={"creative_brief": proposal.creative_brief.model_copy(update={"photo_use": direction})}
    )
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) is None


@pytest.mark.parametrize(
    "direction",
    [
        "Escreva 20–25% de desconto na arte.",
        "Exiba 2 cafés pelo preço de 1.",
        "Atendimento em 24 horas.",
        "Reserve 125% da altura.",
    ],
)
def test_commercial_and_unknown_numbers_in_direction_still_require_evidence(editorial_case, direction):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(
        update={"creative_brief": proposal.creative_brief.model_copy(update={"photo_use": direction})}
    )
    assert (
        EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )


def test_visual_measurement_notation_is_never_exempt_in_public_text(editorial_case):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(update={"caption": "Reserve 20–25% da altura"})
    assert (
        EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )


@pytest.mark.parametrize("measure", ["10% de espaço livre nas bordas", "10% de espaço negativo", "5–10% de margem"])
def test_private_clear_space_measurements(editorial_case, measure):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(
        update={
            "creative_brief": proposal.creative_brief.model_copy(
                update={"photo_use": f"Garantir margem segura ({measure})."}
            )
        }
    )
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) is None


def test_number_rejection_identifies_field_and_source_excerpt(editorial_case):
    proposal, data, ids = editorial_case
    proposal = proposal.model_copy(update={"caption": "Compre 12 cafés"})
    diagnostics = {}
    assert (
        EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True, diagnostics=diagnostics)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )
    assert diagnostics["violations"] == [{"field": "caption", "numbers": ["12"], "excerpt": "Compre 12 cafés"}]


@pytest.mark.parametrize("noun", ["foto", "fotografia"])
def test_photo_coverage_is_private_design_not_public_fact(editorial_case, noun):
    proposal, data, ids = editorial_case
    direction = f"Evitar adicionar elementos gráficos que cubram mais que 20% da {noun}."
    proposal = proposal.model_copy(
        update={"creative_brief": proposal.creative_brief.model_copy(update={"photo_use": direction})}
    )
    assert EditorialProposalService._generated_rejection(proposal, data, ids, full_piece=True) is None
    public = proposal.model_copy(update={"caption": direction})
    assert (
        EditorialProposalService._generated_rejection(public, data, ids, full_piece=True)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )
    discount = proposal.model_copy(
        update={
            "creative_brief": proposal.creative_brief.model_copy(
                update={"photo_use": f"{direction} Exibir 20% de desconto."}
            )
        }
    )
    assert (
        EditorialProposalService._generated_rejection(discount, data, ids, full_piece=True)
        == "EDITORIAL_UNCONFIRMED_NUMBER"
    )
