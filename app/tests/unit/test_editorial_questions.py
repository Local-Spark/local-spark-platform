"""Redundant photo requests must not hide genuine blockers."""

import pytest

from app.services.editorial_questions import resolve_selected_photo_questions

QUESTION = (
    "Você pode enviar o arquivo da foto de ambiente que prefere usar (space_photo) "
    "ou confirmar qual imagem do acervo devo aplicar?"
)
SELECTED = {"role": "space_photo", "authorized": True, "selected_for_generation": True}


def test_resolve_photo_logistics_keeps_commercial_question():
    factual = "Qual o preço do café?"
    assert resolve_selected_photo_questions([QUESTION, factual], [SELECTED]) == ([factual], [QUESTION])


@pytest.mark.parametrize(
    "materials",
    [
        [],
        [{**SELECTED, "authorized": False}],
        [{**SELECTED, "selected_for_generation": False}],
        [{**SELECTED, "role": "brand_logo"}],
    ],
)
def test_missing_or_unselected_photo_keeps_question(materials):
    assert resolve_selected_photo_questions([QUESTION], materials) == ([QUESTION], [])


@pytest.mark.parametrize(
    "question",
    [
        "Você pode enviar a foto de ambiente e confirmar o preço de R$ 20?",
        "Você tem autorização das pessoas na foto de ambiente?",
        "Pode enviar a foto da fachada reformada?",
    ],
)
def test_mixed_factual_and_other_photo_questions_are_preserved(question):
    assert resolve_selected_photo_questions([question], [SELECTED]) == ([question], [])
