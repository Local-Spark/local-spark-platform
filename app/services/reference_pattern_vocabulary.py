"""Own bounded observations: model output cannot introduce captions or facts."""

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from app.services.reference_learning_projection import DerivedPattern

PATTERN_VERSION = "reference-patterns-v1"


@dataclass(frozen=True)
class PatternQuestion:
    code: str
    dimension: Literal["editorial", "visual"]
    instruction: str
    options: tuple[tuple[str, str], ...]


PATTERN_QUESTIONS = (
    PatternQuestion(
        "tone",
        "editorial",
        "Qual tom predomina na legenda?",
        (
            ("friendly", "Tom acolhedor e próximo."),
            ("professional", "Tom profissional e informativo."),
            ("direct", "Tom direto e objetivo."),
            ("playful", "Tom leve e bem-humorado."),
            ("inspirational", "Tom inspirador."),
        ),
    ),
    PatternQuestion(
        "theme",
        "editorial",
        "Qual tema geral predomina na legenda?",
        (
            ("product", "Apresentação de produtos ou serviços."),
            ("offer", "Divulgação de ofertas."),
            ("education", "Conteúdo educativo e dicas."),
            ("process", "Bastidores e processos."),
            ("customer", "Experiências de clientes."),
            ("team", "Apresentação da equipe."),
            ("community", "Relação com a comunidade."),
            ("seasonal", "Temas sazonais e datas."),
        ),
    ),
    PatternQuestion(
        "format",
        "visual",
        "Qual formato visual predomina na imagem?",
        (
            ("photo", "Uso de fotografia."),
            ("text_card", "Uso de cards com texto."),
            ("infographic", "Uso de infográficos ou diagramas."),
            ("collage", "Uso de colagens e montagens."),
            ("illustration", "Uso de ilustrações."),
        ),
    ),
    PatternQuestion(
        "palette",
        "visual",
        "Qual paleta geral predomina na imagem?",
        (
            ("warm", "Predomínio de cores quentes."),
            ("cool", "Predomínio de cores frias."),
            ("neutral", "Predomínio de cores neutras."),
            ("vibrant", "Uso de cores vibrantes."),
            ("monochrome", "Uso de paleta monocromática."),
        ),
    ),
    PatternQuestion(
        "lighting",
        "visual",
        "Como é a iluminação geral da imagem?",
        (
            ("natural", "Iluminação com aparência natural."),
            ("soft", "Iluminação suave."),
            ("studio", "Iluminação com aparência de estúdio."),
            ("contrast", "Iluminação de alto contraste."),
        ),
    ),
    PatternQuestion(
        "composition",
        "visual",
        "Qual composição predomina na imagem?",
        (
            ("closeup", "Enquadramentos próximos e detalhes."),
            ("wide", "Enquadramentos amplos."),
            ("centered", "Composição com assunto centralizado."),
            ("minimal", "Composição com espaço livre."),
            ("grid", "Composição organizada em blocos."),
        ),
    ),
    PatternQuestion(
        "text_density",
        "visual",
        "Quanto texto aparece visualmente na imagem, sem transcrevê-lo?",
        (
            ("none", "Imagens sem texto sobreposto."),
            ("sparse", "Pouco texto sobreposto."),
            ("dominant", "Texto ocupa parte expressiva da imagem."),
        ),
    ),
    PatternQuestion(
        "subject",
        "visual",
        "Qual assunto visual geral predomina, sem identificar marcas ou pessoas?",
        (
            ("product", "Destaque visual para produtos."),
            ("people", "Destaque visual para pessoas."),
            ("space", "Destaque visual para ambientes."),
            ("process", "Destaque visual para processos."),
            ("abstract", "Destaque visual para formas e elementos abstratos."),
        ),
    ),
)


def aggregate_pattern_choices(choices: tuple[tuple[tuple[str, str], ...], ...]) -> tuple[DerivedPattern, ...]:
    """Most frequent observations; stable vocabulary order resolves equal counts.

    Each publication contributes its caption once; each accessible image has a
    visual vote. Unknown values are rejected rather than persisted as free text.
    """
    options = {question.code: dict(question.options) for question in PATTERN_QUESTIONS}
    counts: dict[str, Counter[str]] = {code: Counter() for code in options}
    for sample in choices:
        seen: set[str] = set()
        for dimension, code in sample:
            if dimension not in options or code not in {*options[dimension], "uncertain"} or dimension in seen:
                raise ValueError("REFERENCE_PATTERN_INVALID")
            seen.add(dimension)
            if code != "uncertain":
                counts[dimension][code] += 1
    patterns: list[DerivedPattern] = []
    for question in PATTERN_QUESTIONS:
        ranked = sorted(question.options, key=lambda pair: -counts[question.code][pair[0]])
        for code, observation in ranked[: 2 if question.code == "theme" else 1]:
            if counts[question.code][code]:
                patterns.append(DerivedPattern(dimension=question.dimension, observation=observation))
    return tuple(patterns)
