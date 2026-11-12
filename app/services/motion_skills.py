"""Immutable motion-format skill snapshots; no production workflow is enabled here."""

import hashlib
from pathlib import Path

from app.services.auth import AuthError

_SKILLS = {
    "instagram-reel-v13": ("reel", "6d5ae9e0478756b1ef006f3babf6591c6c0bbe243d8cc6aee4a2d8f5dd754822"),
    "instagram-reel-v12": ("reel", "9924e20bf34c8ee4c1de5ff4fab6e33370bbb5f60b3c29c05187158e0d32b8ec"),
    "instagram-reel-v11": ("reel", "998b792152dd4c513226155ad3c5340ec3640c5a93ca232925de47d91c577ce3"),
    "instagram-reel-v10": ("reel", "3ae3bb49051b9b0b42e9268eb75ebd5b7d80b8ce3bd41c994fb4c36480b47722"),
    "instagram-reel-v9": ("reel", "49a0cb2b52b5870c3f2e3a020abc3501b7701ab3521bad709054b92c0e4678a8"),
    "instagram-reel-v8": ("reel", "5050e1c0a4c523e28187eb393effde5f2e6be3e8a1ea0e502ed179a5d46c81fe"),
    "instagram-reel-v1": ("reel", "4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7"),
    "instagram-reel-v2": ("reel", "4401257fd8a4e73352ed55aa5985a9a636612a84f1efb5ce3d315661bc8edcab"),
    "instagram-reel-v3": ("reel", "40c7fbd49864507ba6b76c945af456fc159694e2611f829af6abb78865345661"),
    "instagram-reel-v4": ("reel", "45c20abcfad7bcac5892f24eb435c4e0f216ff219872d98895b2e0bae906cda6"),
    "instagram-reel-v7": ("reel", "f067fbd60372c8c291f9df28753d89af665a73dbaa280b2ea6e54facc49a9996"),
    "instagram-reel-v6": ("reel", "5fa1aa1f7044c523b519e31cf766bb2d01adf238f17e23625c30d868c9283432"),
    "instagram-reel-v5": ("reel", "c8c9e83de74053e3156c325bc7e599c1594977ede53e90d0552d6ca119e7345b"),
    "instagram-story-video-v1": ("story_video", "083981e2de27c68588878aaba430a92a68b9ee9eefc8ac74446d8484c39b5713"),
    "instagram-carrossel-motion-v1": (
        "carousel_motion",
        "b91757da20a4a415fe4116a15aec84b90e27c98c99182fa29cb195cfed4af0de",
    ),
}
_FORMATS = {
    "reel": "instagram-reel-v1",
    "story_video": "instagram-story-video-v1",
    "carousel_motion": "instagram-carrossel-motion-v1",
}
_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "motion_skills"


def load_motion_skill(skill_id: str, expected_hash: str, format: str) -> str:
    """Load only a registered version whose format and exact bytes match its snapshot."""
    skill = _SKILLS.get(skill_id)
    if skill is None or skill != (format, expected_hash):
        raise AuthError("MOTION_SKILL_CHANGED", 409)
    try:
        source = (_ASSETS / f"{skill_id}.md").read_bytes()
        if hashlib.sha256(source).hexdigest() != expected_hash:
            raise ValueError
        return source.decode("utf-8")
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise AuthError("MOTION_SKILL_CHANGED", 409) from exc


def resolve_motion_skill(format: str) -> tuple[str, str, str]:
    """Resolve a format to its version, digest and verified instructions."""
    skill_id = _FORMATS.get(format)
    if skill_id is None:
        raise AuthError("MOTION_SKILL_FORMAT_INVALID", 409)
    digest = _SKILLS[skill_id][1]
    return skill_id, digest, load_motion_skill(skill_id, digest, format)


def resolve_html_motion_skill(format: str) -> tuple[str, str, str]:
    """Resolve the version used by new HTML Reel captures, not legacy directions."""
    if format != "reel":
        raise AuthError("MOTION_SKILL_FORMAT_INVALID", 409)
    skill_id = "instagram-reel-v13"
    digest = _SKILLS[skill_id][1]
    return skill_id, digest, load_motion_skill(skill_id, digest, "reel")
