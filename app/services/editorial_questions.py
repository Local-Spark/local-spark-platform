"""Resolve redundant photo logistics only when the selected source is available.

Full-sentence patterns deliberately exclude mixed factual/rights questions.
Unknown wording remains a question; this is not a semantic truth classifier.
"""

import re
import unicodedata

_PREFIX = r"(?:voce pode |pode |poderia |voce poderia )?"
_PHOTO = r"(?:a foto de ambiente|o arquivo da foto de ambiente)"
_CHOICE = r"(?:confirmar|informar|indicar) qual (?:imagem|foto) do acervo (?:devo|devemos) (?:aplicar|usar|utilizar)"
_PATTERNS = (
    re.compile(
        _PREFIX
        + r"(?:enviar|anexar) "
        + _PHOTO
        + r"(?: que (?:prefere|deseja) (?:usar|utilizar))?(?: \(space_photo\))?"
        + r"(?: ou "
        + _CHOICE
        + r")?\??"
    ),
    re.compile(_PREFIX + _CHOICE + r"\??"),
    re.compile(r"qual foto de ambiente (?:voce prefere|deseja) (?:usar|utilizar)\??"),
)


def resolve_selected_photo_questions(questions, materials):
    selected = any(
        item.get("role") == "space_photo"
        and item.get("authorized") is True
        and item.get("selected_for_generation") is True
        for item in materials
    )
    remaining, resolved = [], []
    for question in questions:
        normalized = " ".join(
            "".join(
                char for char in unicodedata.normalize("NFKD", question.casefold()) if not unicodedata.combining(char)
            ).split()
        )
        if selected and any(pattern.fullmatch(normalized) for pattern in _PATTERNS):
            resolved.append(question)
        else:
            remaining.append(question)
    return remaining, resolved
