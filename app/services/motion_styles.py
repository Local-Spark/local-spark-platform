"""Immutable motion-style snapshots; this module never chooses a style.

The catalogue is input to a future per-request creative decision. It contains
no customer data and does not activate model calls, rendering or publication.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.services.auth import AuthError

_STYLES = {
    "editorial-janela-v1": (1, "a1a3769d35495d08722ecfd7bd981a2ba3646105705c0e43377624ae9f48ab1f"),
    "tipografia-em-ritmo-v1": (1, "1bcbd0d526dd90426335cc1b488c7615ade85bda5d2a421f0a491fb1bce71156"),
    "clareza-neutra-v1": (1, "b47d7256db13b32ce7f9e236196aee60cc14a7576b4c7efd07225291712d1391"),
}
_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "motion_styles"
_MAX_BYTES = 65536


@dataclass(frozen=True)
class MotionStyleSnapshot:
    id: str
    version: int
    sha256: str
    content: str


def resolve_motion_style(style_id: str, expected_version: int, expected_hash: str) -> MotionStyleSnapshot:
    """Resolve a selected ID/version/hash only if its exact snapshot is intact."""
    if type(expected_version) is not int or _STYLES.get(style_id) != (expected_version, expected_hash):
        raise AuthError("MOTION_STYLE_CHANGED", 409)
    try:
        with (_ASSETS / f"{style_id}.json").open("rb") as file:
            source = file.read(_MAX_BYTES + 1)
        if len(source) > _MAX_BYTES or hashlib.sha256(source).hexdigest() != expected_hash:
            raise ValueError
        content = source.decode("utf-8")
        data = json.loads(content)
        if (
            not isinstance(data, dict)
            or data.get("id") != style_id
            or type(data.get("version")) is not int
            or data["version"] != expected_version
        ):
            raise ValueError
        return MotionStyleSnapshot(style_id, expected_version, expected_hash, content)
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise AuthError("MOTION_STYLE_CHANGED", 409) from exc


def list_motion_styles() -> tuple[MotionStyleSnapshot, ...]:
    """Return every registered fiche, including its complete verified capabilities."""
    return tuple(resolve_motion_style(style_id, version, digest) for style_id, (version, digest) in _STYLES.items())


def html_style_card(content: str) -> dict:
    """Project verified historical style guidance onto the HTML executor contract.

    The snapshot hash identifies the original fiche, not this projection. Its
    declarative-executor limits must not be presented as HTML capabilities.
    """
    card = json.loads(content)
    card.pop("current_visual_subset", None)
    card.pop("execution_restrictions", None)
    return card
