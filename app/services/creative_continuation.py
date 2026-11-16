"""Channel-independent assembly of explicit creation replies, never inferred facts."""

import re
import unicodedata

from app.services.auth import AuthError


def continued_instruction(original: str, note: str, *, questions: list[str] | None = None) -> str:
    label = "Resposta do solicitante" if questions else "Ajuste solicitado"
    parts = [original, "\nPerguntas pendentes:\n" + "\n".join(questions)] if questions else [original]
    parts.append(f"\n{label}:\n{note.strip()}")
    result = "\n".join(parts)
    if not note.strip() or len(result) > 4000:
        raise AuthError("CREATION_CONTINUATION_MESSAGE_LIMIT", 422)
    return result


_FORMAT_QUESTIONS = {
    "Você quer um post no feed, um story estático ou um reel?",
    "O que você quer divulgar e em qual formato? Confirme os detalhes necessários para criar a peça.",
}


def confirmed_reply_format(questions: list[str], note: str) -> str | None:
    """Only an exact, single format answer to a persisted system question is decisive."""
    if len(questions) != 1 or questions[0] not in _FORMAT_QUESTIONS:
        return None
    answer = " ".join(
        "".join(
            char for char in unicodedata.normalize("NFKD", note.casefold()) if not unicodedata.combining(char)
        ).split()
    )
    match = re.fullmatch(
        r"(?:(?:pro|para o|no|um|quero um|quero|pode ser) )?"
        r"(feed|post no feed|story|story estatico|reel)"
        r"(?: mesmo| mesmo, por favor| por favor)?[.!]?",
        answer,
    )
    if not match:
        return None
    return {"feed": "photo", "post no feed": "photo", "story": "story", "story estatico": "story", "reel": "reel"}[
        match[1]
    ]


def copied_format_reply(message: str) -> str | None:
    """Read an explicit answer in a copied conversation, never infer server provenance.

    Reusing a request copies its display text but intentionally has no parent run.
    Only the final complete question/answer block can supply a format. Other text,
    conflicting answers and instructions after the answer keep normal interpretation.
    """
    normalized = message.replace("\r\n", "\n").replace("\\n", "\n")
    original, marker, remainder = normalized.rpartition("\n\nPerguntas pendentes:\n")
    if not marker or not original.strip():
        return None
    questions, marker, reply = remainder.partition("\n\nResposta do solicitante:\n")
    if not marker:
        return None
    return confirmed_reply_format(questions.splitlines(), reply)
