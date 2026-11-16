"""Explicit visual requests may prioritize categories; vague requests preserve selection."""

import pytest

from app.services.space_photo_selection import requested_space_kind


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Faça um post mostrando a fachada da nossa loja.", "facade"),
        ("Use uma foto do balcão no story.", "counter"),
        ("Quero destacar o salão.", "room"),
        ("Mostre nosso espaço.", "environment"),
        (
            "Faz um story pra dar vontade de tomar um café com a gente hoje. "
            "Usa uma foto bonita do nosso acervo e coloca pouco texto.",
            None,
        ),
        (
            "Quero passar aquela sensação de fazer uma pausa e tomar um café com calma. "
            "Pode usar uma foto nossa que combine.",
            None,
        ),
        ("Não mostre a fachada.", None),
        ("Evite uma imagem do balcão.", None),
        ("Mostre a fachada ou o balcão.", None),
        ("A fachada está em reforma. Faça um convite para tomar café.", None),
    ],
)
def test_explicit_and_ambiguous_visual_requests(message, expected):
    assert requested_space_kind(message) == expected
