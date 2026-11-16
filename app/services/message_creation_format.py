"""Channel-independent format admission; text-only requests have no silent default."""

import re

from app.services.editorial_conversation import NEGATION

_FEED_REQUEST = re.compile(r"\b(?:post|postagem|imagem|foto)\s+(?:(?:para\s+o|pro|no|de|do)\s+)?feed\b", re.IGNORECASE)
_OTHER = re.compile(
    r"\b(?:story|stories|reels?|v[ií]deos?|carrossel|carross[eé]is|motion|movimento|animad[oa]s?)\b", re.IGNORECASE
)


def message_format(message: str, interpreted: str | None, material_kind: str) -> str | None:
    # Only an unambiguous affirmative static request can repair an abstention.
    if (
        interpreted is None
        and _FEED_REQUEST.search(message)
        and not NEGATION.search(message)
        and not _OTHER.search(message)
    ):
        return "photo"
    if interpreted is not None:
        return {"short_video": "reel"}.get(interpreted, interpreted)
    return {"video": "reel", "image": "photo"}.get(material_kind)
