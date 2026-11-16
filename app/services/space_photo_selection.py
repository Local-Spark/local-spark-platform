"""Conservative photo selection using registered categories, never inferred titles."""

import re
import unicodedata

from sqlalchemy import text

_CATEGORIES = {
    "facade": r"\bfachada\b",
    "counter": r"\bbalcao\b",
    "room": r"\b(?:sala|salao)\b",
    "environment": r"\b(?:ambiente|espaco)\b",
}
_VISUAL_REQUEST = re.compile(r"\b(?:mostr\w*|destac\w*|apresent\w*|exib\w*|foto|fotografia|imagem|foco)\b")
_NEGATION = re.compile(r"\b(?:nao|sem|evit\w*|exceto|menos)\b")


def requested_space_kind(message: str) -> str | None:
    normalized = "".join(
        char for char in unicodedata.normalize("NFKD", message.casefold()) if not unicodedata.combining(char)
    )
    # Uncertain or negated wording retains the established selection; no guessing.
    if _NEGATION.search(normalized):
        return None
    kinds = set()
    for clause in re.split(r"[.!?;\n]", normalized):
        intent = _VISUAL_REQUEST.search(clause)
        if intent:
            subject = clause[intent.end() : intent.end() + 80]
            kinds.update(kind for kind, pattern in _CATEGORIES.items() if re.search(pattern, subject))
    return next(iter(kinds)) if len(kinds) == 1 else None


async def select_space_photo(session, tenant, business, message):
    preferred = requested_space_kind(message)
    photo = (
        (
            await session.execute(
                text("""SELECT id,space_kind FROM business_collection_photos
              WHERE tenant_id=:tenant AND business_id=:business
                AND state='ready' AND status='active' AND rights_scope='business_collection_confirmed'
                AND item_id IS NULL AND delete_owner IS NULL AND delete_lease_until IS NULL
                AND (space_kind IN ('environment','room','counter') OR space_kind=:preferred)
              ORDER BY CASE WHEN space_kind=:preferred THEN 0 ELSE 1 END,
                CASE space_kind WHEN 'environment' THEN 0 WHEN 'room' THEN 1 ELSE 2 END,id LIMIT 1"""),
                {"tenant": tenant, "business": business, "preferred": preferred},
            )
        )
        .mappings()
        .one_or_none()
    )
    matched = bool(photo and preferred and photo["space_kind"] == preferred)
    reason = (
        "Categoria cadastrada correspondente ao pedido explícito."
        if matched
        else "Sem foto elegível da categoria solicitada; mantida a seleção habitual."
        if preferred
        else "Sem indicação visual inequívoca de categoria; mantida a seleção habitual."
    )
    return (photo["id"] if photo else None), {
        "policy": "explicit_space_category_v1",
        "requested_kind": preferred,
        "selected_kind": photo["space_kind"] if photo else None,
        "selected_id": str(photo["id"]) if photo else None,
        "matched_explicit_request": matched,
        "reason": reason if photo else "Nenhuma foto de espaço elegível no acervo.",
    }
