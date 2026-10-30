"""Narrow checks for leaked internal identifiers and obvious layout instructions.

These checks cannot prove that arbitrary natural-language copy is suitable or
factually true; the owner still reviews the proposed copy and finished image.
"""

import re

from app.schemas.editorial_proposals import ProposalDraft

_UUID = re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.IGNORECASE)
_INTERNAL_FIELD = re.compile(r"\b(?:asset_id|fact_ids?|source_asset_id|editorial_skill_id)\b", re.IGNORECASE)
_LABELED_IDENTIFIER = re.compile(r"\b(?:asset|fact|fonte|arquivo)\s+(?:id|uuid)\s*[:=]", re.IGNORECASE)
_VISUAL_INSTRUCTION = re.compile(
    r"^\s*(?:foto(?:grafia)?|imagem)\s+(?:close[- ]?up|em\s+close|centralizada|vertical\s+centralizada)\b"
    r"|^\s*(?:foto(?:grafia)?|imagem)\b.{0,110}\b(?:enquadramento|centralizada|zoom|close[- ]?up)\b"
    r"|^\s*close[- ]?up\s+(?:da|do|das|dos)\b"
    r"|^\s*(?:usar|use|utilize|aplique|inserir|insira)\s+(?:a\s+)?(?:foto|imagem|tipografia|fonte)\b",
    re.IGNORECASE,
)


def public_copy_has_no_internal_artifacts(draft: ProposalDraft) -> bool:
    """Reject obvious non-public material without rewriting the model's copy."""
    for value in (draft.art_text, draft.caption, draft.cta):
        if value and (_UUID.search(value) or _INTERNAL_FIELD.search(value) or _LABELED_IDENTIFIER.search(value)):
            return False
    return not bool(draft.art_text and _VISUAL_INSTRUCTION.search(draft.art_text))
