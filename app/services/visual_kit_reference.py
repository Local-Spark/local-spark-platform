"""Pinned demonstration-kit images for private development/testing only."""

import hashlib
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.adapters.visual_ai import VisualReference
from app.core.config import Settings
from app.services.auth import AuthError
from app.services.brand_kits import KIT_ID, KIT_VERSION, MANIFEST, _manifest
from app.services.business_collection import normalize_photo
from app.services.visual_references import VisualReferenceSource

_EXAMPLES = {
    "photo": (
        "assets/post-editorial-croissant.jpg",
        "330d7825c785a8af1d4b731c1317b4ed3da3b4f7dc8a1ff18f2738968646573b",
    ),
    "story": ("assets/story-pausa.jpg", "07248680806a48fcdcad639f216581ea5b00a3a30024567febe2595329b9b3ce"),
}


def load_kit_example(
    settings: Settings, document: dict[str, Any], format: str
) -> tuple[VisualReferenceSource, VisualReference]:
    """Return exactly one registered example; it is not a source of client facts."""
    if settings.environment not in {"development", "testing"}:
        raise AuthError("VISUAL_KIT_REFERENCE_UNAVAILABLE", 409)
    selected = _EXAMPLES.get(format)
    if selected is None or document.get("kit_id") != KIT_ID or document.get("kit_version") != KIT_VERSION:
        raise AuthError("VISUAL_KIT_REFERENCE_UNAVAILABLE", 409)
    path, expected = selected
    try:
        manifest = _manifest()
        rights = manifest["rights"]
        candidates = [entry for entry in manifest["media"] if entry.get("path") == path]
        if (
            manifest["status"] != "public_demo"
            or rights.get("scope") != "fictional_public_demo"
            or len(candidates) != 1
            or candidates[0].get("sha256") != expected
            or candidates[0].get("use_scope") != "fictional_public_demo"
            or candidates[0].get("contains_real_client_material") is not False
        ):
            raise ValueError
        asset = MANIFEST.parent / path
        if asset.is_symlink() or not asset.resolve().is_relative_to(MANIFEST.parent.resolve()):
            raise ValueError
        raw = asset.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError
        normalized = normalize_photo(raw, "image/jpeg")
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise AuthError("VISUAL_KIT_REFERENCE_CHANGED", 409) from exc
    identifier = uuid5(NAMESPACE_URL, f"kit-example:{KIT_ID}:{KIT_VERSION}:{path}:{expected}")
    source = VisualReferenceSource("kit_example", identifier, KIT_VERSION, expected, normalized.sha256, KIT_ID, path)
    return source, VisualReference(normalized.data, normalized.mime_type)
