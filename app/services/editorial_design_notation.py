"""Recognize measurements in private design directions, never in public copy.

Unknown numbers remain for factual validation. A percentage alone is not a
layout instruction: it must name a visual dimension or property.
"""

import re

_NUMBER = r"(?:\d+(?:[.,]\d+)?)"
_RANGE = _NUMBER + r"(?:\s*(?:[–—-]|a)\s*" + _NUMBER + r")?"
_PERCENT_NUMBER = r"(?:100|[0-9]{1,2}(?:[.,][0-9]+)?)"
_PERCENT_RANGE = _PERCENT_NUMBER + r"(?:\s*(?:[–—-]|a)\s*" + _PERCENT_NUMBER + r")?"
_PROPERTY = (
    r"(?:altura|largura|opacidade|transparência|margens?|espaçamento|padding|raio de borda|tamanho da fonte|entrelinha)"
)
_UNIT = r"(?:px|pixels?|pt|pontos tipográficos|rem)\b"
# Explicit proportions of a visual dimension, e.g. 20–25% da altura.
_PROPORTION = re.compile(
    r"(?<![\w.,])" + _PERCENT_RANGE + r"\s*%\s+(?:da|de|do)\s+"
    r"(?:altura|largura|área|imagem|quadro|canvas|tela|margem|margens|espaço\s+(?:livre|negativo|de respiro))\b",
    re.I,
)
_PROPERTY_PERCENT = re.compile(
    r"\b" + _PROPERTY + r"\s*(?:(?:de|em)\s+|[:=]\s*)?" + _PERCENT_RANGE + r"\s*%",
    re.I,
)
# Pixel/font units are technical; amounts, product counts and time units are not.
_TECHNICAL_UNIT = re.compile(r"(?<![\w.,])" + _RANGE + r"\s*" + _UNIT, re.I)
_CANVAS = re.compile(r"(?<![\w.,])\d+\s*[x×]\s*\d+\s*(?:px|pixels?)\b", re.I)
# Line counts describe typography only when explicitly attached to text or
# legibility. A bare "2 linhas" can instead describe a product catalogue.
_TEXT_LINES = re.compile(
    r"\b(?:legível|legível em tela|texto|título|subtítulo|legenda|chamada|art_text)"
    r"\s+(?:em|com)\s+(?:(?:no máximo|até)\s+)?"
    r"[1-9]\d?(?:\s*(?:[–—-]|a)\s*[1-9]\d?)?\s+linhas?\b",
    re.I,
)


def remove_design_measurements(direction: str) -> str:
    for pattern in (_PROPORTION, _PROPERTY_PERCENT, _CANVAS, _TECHNICAL_UNIT, _TEXT_LINES):
        direction = pattern.sub("medida visual", direction)
    return direction
