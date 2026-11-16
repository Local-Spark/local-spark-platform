"""Channel-independent assembly of explicit creation replies, never inferred facts."""

from app.services.auth import AuthError


def continued_instruction(original: str, note: str, *, questions: list[str] | None = None) -> str:
    label = "Resposta do solicitante" if questions else "Ajuste solicitado"
    parts = [original, "\nPerguntas pendentes:\n" + "\n".join(questions)] if questions else [original]
    parts.append(f"\n{label}:\n{note.strip()}")
    result = "\n".join(parts)
    if not note.strip() or len(result) > 4000:
        raise AuthError("CREATION_CONTINUATION_MESSAGE_LIMIT", 422)
    return result
