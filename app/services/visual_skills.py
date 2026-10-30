"""Immutable, opt-in visual skill snapshots for local experiments."""

import hashlib
from pathlib import Path

from app.core.config import Settings
from app.services.auth import AuthError

_SKILLS = {
    "instagram-feed-v1": ("photo", "40ac2fa82dc6dca05fea953d0a97910786ebbea71f5b71427c5c5a0bfe72506c"),
    "instagram-story-v1": ("story", "7917cb2fa633699198b13e6266e2f52136733499695101c4e6f7399130205b71"),
}
_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "visual_skills"


def select_visual_skill(settings: Settings, skill_id: str, format: str) -> str:
    if settings.environment not in {"development", "testing"} or not settings.visual_skill_experiment_enabled:
        raise AuthError("VISUAL_SKILL_DISABLED", 409)
    skill = _SKILLS.get(skill_id)
    if skill is None or skill[0] != format:
        raise AuthError("VISUAL_SKILL_FORMAT_INVALID", 409)
    return skill[1]


def load_visual_skill(skill_id: str, expected_hash: str, format: str) -> str:
    skill = _SKILLS.get(skill_id)
    if skill is None or skill != (format, expected_hash):
        raise AuthError("VISUAL_SKILL_CHANGED", 409)
    try:
        source = (_ASSETS / f"{skill_id}.md").read_bytes()
        if hashlib.sha256(source).hexdigest() != expected_hash:
            raise ValueError
        return source.decode("utf-8")
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise AuthError("VISUAL_SKILL_CHANGED", 409) from exc


def resolve_editorial_skill(format: str) -> tuple[str, str, str]:
    """Resolve one immutable format skill for an approved editorial briefing."""
    if format not in {"photo", "story"}:
        raise AuthError("VISUAL_SKILL_FORMAT_INVALID", 409)
    skill_id = "instagram-feed-v1" if format == "photo" else "instagram-story-v1"
    skill_hash = _SKILLS[skill_id][1]
    return skill_id, skill_hash, load_visual_skill(skill_id, skill_hash, format)
