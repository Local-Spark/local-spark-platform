"""BL01/BL02 fixture checks without paid provider calls."""

import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.brand_kit_catalog import KIT, export_web, validate_kit
from scripts.evaluate_brand_kit_transfer import SOURCE, compose, prompt


def fixture_copy(tmp_path: Path) -> Path:
    directory = tmp_path / "kit"
    directory.mkdir()
    (directory / "assets").symlink_to(KIT / "assets", target_is_directory=True)
    (directory / "fonts").symlink_to(KIT / "fonts", target_is_directory=True)
    (directory / "manifest.json").write_bytes((KIT / "manifest.json").read_bytes())
    return directory


def test_pilot_catalog_has_complete_distinct_media_and_rights() -> None:
    manifest = validate_kit(KIT)
    posts = [item for item in manifest["samples"] if item["kind"] == "post"]
    assert len(posts) == len({item["media"] for item in posts}) == 10
    assert {item["kind"] for item in manifest["samples"]} == {"post", "story", "reel"}
    assert all(item["sha256"] and item["source"] for item in manifest["media"])
    assert {item["content_type"] for item in posts if item.get("copy_in_image")} == {
        "editorial_product",
        "offer",
        "menu_feature",
    }
    assert {item["id"] for item in manifest["scenarios"]} == {
        "text_only",
        "product_photo_offer",
        "venue_photo",
        "voice_note",
        "short_video",
        "no_message",
    }
    media = {item["path"]: item for item in manifest["media"]}
    offer = next(item for item in manifest["scenarios"] if item["id"] == "product_photo_offer")
    assert offer["source_media"] in media[offer["result_media"]]["derived_from"]
    venue = next(item for item in manifest["scenarios"] if item["id"] == "venue_photo")
    assert venue["source_media"] == venue["result_media"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data["media"][0].update(sha256="bad"), "Missing or modified media"),
        (lambda data: data["media"][0].update(source=""), "Media rights"),
        (lambda data: data["media"][-1].update(derived_from=["assets/missing.jpg"]), "Composed media provenance"),
        (lambda data: data["samples"].append(data["samples"][0]), "Pilot kit requires ten posts"),
        (lambda data: data["samples"][0].pop("copy_in_image"), "Pilot kit requires three complete"),
        (lambda data: data["samples"][0].update(media="assets/croissant.jpg"), "Complete sample is missing source"),
        (lambda data: data["media"][0].update(path="assets/../escape.jpg"), "Invalid or duplicate media path"),
        (lambda data: data["rights"].update(client_material=True), "Only fictional public demos"),
        (lambda data: data["scenarios"].pop(), "Incomplete or duplicate input scenarios"),
        (lambda data: data["scenarios"][1].update(source_media="assets/missing.jpg"), "Scenario input media missing"),
        (lambda data: data["scenarios"][1].update(result_media="assets/missing.jpg"), "Scenario result media missing"),
        (
            lambda data: data["scenarios"][1].update(result_media="assets/post-menu-pause.jpg"),
            "Offer must derive from the submitted photo",
        ),
        (
            lambda data: data["scenarios"][2].update(result_media="assets/cappuccino.jpg"),
            "Venue scenario must preserve",
        ),
    ],
)
def test_catalog_rejects_broken_manifest(tmp_path: Path, change: object, message: str) -> None:
    directory = fixture_copy(tmp_path)
    data = json.loads((directory / "manifest.json").read_text())
    change(data)  # type: ignore[operator]
    (directory / "manifest.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        validate_kit(directory)


def test_export_copies_manifest_and_versioned_media(tmp_path: Path) -> None:
    export_web(KIT, tmp_path)
    copied = tmp_path / "public/brand-kits/cafe-pausas/v1/reel-pausas.mp4"
    assert copied.read_bytes() == (KIT / "assets/reel-pausas.mp4").read_bytes()
    assert json.loads((tmp_path / "src/data/cafe-kit-v1.json").read_text()) == validate_kit(KIT)


def test_transfer_briefs_hold_one_variable_and_local_composition_is_exact(tmp_path: Path) -> None:
    manifest = validate_kit(KIT)
    without = prompt("no_kit", manifest)
    compact = prompt("manifest", manifest)
    reference = prompt("manifest_reference", manifest)
    assert without in compact and compact in reference
    assert "segunda imagem" in reference
    with pytest.raises(ValueError, match="Unknown route"):
        prompt("wrong", manifest)
    output = tmp_path / "preview.jpg"
    copy = {
        "brand_name": "Café do Cedro",
        "headline": "Croissant de manteiga",
        "price_text": "R$ 18",
        "cta": "Peça informações pelo WhatsApp",
        "palette": manifest["palette"],
        "demo_label": True,
    }
    compose(SOURCE, output, **copy)
    with Image.open(output) as image:
        assert image.size == (1080, 1350)
    other = tmp_path / "other.jpg"
    compose(SOURCE, other, **{**copy, "headline": "Um novo título"})
    assert output.read_bytes() != other.read_bytes()
    with pytest.raises(ValueError, match="safe width"):
        compose(SOURCE, other, **{**copy, "headline": "Título " * 50})
