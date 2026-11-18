"""Versioned CTA shadow parser selection; historical v2 bytes remain unchanged."""

from pathlib import Path
from typing import Any

from app.services.auth import AuthError

READABILITY_GUARD_PATH = Path(__file__).resolve().parents[1] / "assets/motion_photo/photo-guard-v3.js"
PHOTO_READABILITY_CONTRACT = {
    "version": "motion-photo-readability-v1",
    "dom_guard_sha256": "40893feaaaa53d1c4cb2ba91ef34898d34a7c4781baaf8af8c5bebf8d6d94080",
}


def readability_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("photo_readability_contract")
    if contract is None:
        return False
    if contract != PHOTO_READABILITY_CONTRACT:
        raise AuthError("MOTION_PHOTO_READABILITY_CONTRACT_CHANGED", 409)
    return True
