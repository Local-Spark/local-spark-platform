"""Check whether public-facing action copy names an owner-confirmed channel.

This is a conservative precheck, not a substitute for reviewing a generated
piece: it does not inspect the actual rendered image or verify live links.
"""

import re
from typing import Any

from app.schemas.editorial_proposals import ProposalDraft

_CHANNELS: tuple[tuple[re.Pattern[str], frozenset[str]], ...] = (
    (re.compile(r"\b(?:whats(?:app)?|zap)\b", re.I), frozenset({"whatsapp"})),
    (re.compile(r"\bi\s*food\b", re.I), frozenset({"ifood"})),
    (re.compile(r"\b(?:direct|dm|mensagem direta)\b", re.I), frozenset({"instagram_direct"})),
    (re.compile(r"\b(?:ligue|telefone|liga[cç][aã]o telef[oô]nica)\b", re.I), frozenset({"phone"})),
    (re.compile(r"\b(?:site|website)\b", re.I), frozenset({"order_link", "booking_link", "ifood"})),
    (re.compile(r"\blink\b", re.I), frozenset({"order_link", "booking_link", "ifood", "whatsapp"})),
    (
        re.compile(r"\b(?:visite|venha|passe)\s+(?:a|em|na|para a)\s+(?:(?:nossa|a)\s+)?loja\b", re.I),
        frozenset({"physical_location"}),
    ),
)
_URL = re.compile(
    r"(?i)\b(?:(?:https?://|www\.)[^\s<>]+|(?:[a-z0-9-]+\.)+(?:com(?:\.br)?|br|net|org|app|me)(?:/[^\s<>]*)?)"
)
_HANDLE = re.compile(r"(?<![\w@])@[a-zA-Z0-9_][a-zA-Z0-9_.]*")
_UNCONFIRMED_INTERACTION = re.compile(
    r"(?i)\b(?:clique|toque|arraste|aperte)\b.{0,45}\b(?:link|bot[aã]o|saiba mais|aqui|sticker)\b"
    r"|\blink\s+(?:na|da)\s+bio\b|\blink\s+(?:do|no)\s+stor(?:y|ies)\b"
)


def public_action_matches_destination(draft: ProposalDraft, preferences: dict[str, Any]) -> bool:
    """Reject unsupported named channels, URL substitutions and assumed taps."""
    public_copy = " ".join(
        value for value in (draft.title, draft.angle, draft.art_text, draft.caption, draft.cta) if value
    )
    if _UNCONFIRMED_INTERACTION.search(public_copy):
        return False
    destination = preferences.get("cta_destination")
    kind = destination.get("type") if isinstance(destination, dict) else None
    target = destination.get("value") if isinstance(destination, dict) else None
    if any(pattern.search(public_copy) and kind not in allowed for pattern, allowed in _CHANNELS):
        return False
    for match in _URL.finditer(public_copy):
        url = match.group().rstrip(".,;:!?)]}")
        if not isinstance(target, str) or url != target:
            return False
    for match in _HANDLE.finditer(public_copy):
        handle = match.group().rstrip(".")
        if kind != "instagram_direct" or not isinstance(target, str) or handle.casefold() != target.casefold():
            return False
    return True
