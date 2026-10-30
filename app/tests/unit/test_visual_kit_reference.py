import hashlib

import pytest

from app.services.auth import AuthError
from app.services.brand_kits import _manifest
from app.services.visual_kit_reference import load_kit_example


@pytest.mark.parametrize(
    "format,path",
    [("photo", "assets/post-editorial-croissant.jpg"), ("story", "assets/story-pausa.jpg")],
)
def test_pinned_demo_reference(settings, format, path):
    source, reference = load_kit_example(settings, {"kit_id": "cafe-pausas", "kit_version": 1}, format)
    assert (source.kind, source.catalog_id, source.version, source.asset_path) == (
        "kit_example",
        "cafe-pausas",
        1,
        path,
    )
    assert source.normalized_sha256 == hashlib.sha256(reference.content).hexdigest()
    assert reference.mime_type == "image/png"


@pytest.mark.parametrize(
    "document,format,environment",
    [
        ({"kit_id": "other", "kit_version": 1}, "photo", "testing"),
        ({"kit_id": "cafe-pausas", "kit_version": 2}, "photo", "testing"),
        ({"kit_id": "cafe-pausas", "kit_version": 1}, "video", "testing"),
        ({"kit_id": "cafe-pausas", "kit_version": 1}, "photo", "production"),
    ],
)
def test_unsupported_reference_is_rejected(settings, document, format, environment):
    with pytest.raises(AuthError, match="VISUAL_KIT_REFERENCE_UNAVAILABLE"):
        load_kit_example(settings.model_copy(update={"environment": environment}), document, format)


@pytest.mark.parametrize("change", ["rights", "status", "hash", "scope", "client_material", "missing"])
def test_changed_manifest_is_rejected(settings, monkeypatch, change):
    manifest = _manifest()
    entry = next(item for item in manifest["media"] if item["path"] == "assets/post-editorial-croissant.jpg")
    if change == "rights":
        manifest["rights"]["scope"] = "unknown"
    elif change == "status":
        manifest["status"] = "other"
    elif change == "hash":
        entry["sha256"] = "0" * 64
    elif change == "scope":
        entry["use_scope"] = "unknown"
    elif change == "client_material":
        entry["contains_real_client_material"] = True
    else:
        manifest["media"].remove(entry)
    monkeypatch.setattr("app.services.visual_kit_reference._manifest", lambda: manifest)
    with pytest.raises(AuthError, match="VISUAL_KIT_REFERENCE_CHANGED"):
        load_kit_example(settings, {"kit_id": "cafe-pausas", "kit_version": 1}, "photo")


def test_changed_asset_is_rejected(settings, monkeypatch, tmp_path):
    manifest = _manifest()
    asset = tmp_path / "assets" / "post-editorial-croissant.jpg"
    asset.parent.mkdir()
    asset.write_bytes(b"modified")
    monkeypatch.setattr("app.services.visual_kit_reference.MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.visual_kit_reference._manifest", lambda: manifest)
    with pytest.raises(AuthError, match="VISUAL_KIT_REFERENCE_CHANGED"):
        load_kit_example(settings, {"kit_id": "cafe-pausas", "kit_version": 1}, "photo")
