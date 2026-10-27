"""Validate a versioned public demo kit and export it to the web build.

Usage: python scripts/brand_kit_catalog.py --web-root ../local-spark-web
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "catalog/kits/cafe-pausas/v1"


def validate_kit(directory: Path) -> dict[str, Any]:
    manifest: dict[str, Any] = json.loads((directory / "manifest.json").read_text())
    if manifest["schema_version"] != "brand-kit-v1" or manifest["version"] < 1:
        raise ValueError("Unsupported kit version")
    if manifest["status"] != "public_demo" or manifest["rights"]["client_material"]:
        raise ValueError("Only fictional public demos may be exported")
    if not (directory / manifest["fonts"]["source"]).is_file() or not all(
        (directory / "fonts" / name).is_file() for name in ("DejaVuSerif.ttf", "DejaVuSans.ttf")
    ):
        raise ValueError("Licensed font sources missing")
    recipes = {item["id"] for item in manifest["recipes"]}
    if len(recipes) != len(manifest["recipes"]):
        raise ValueError("Duplicate recipe")
    media: dict[str, dict[str, Any]] = {}
    for item in manifest["media"]:
        path = item["path"]
        if path in media or not path.startswith("assets/") or Path(path).name != path.removeprefix("assets/"):
            raise ValueError("Invalid or duplicate media path")
        file = directory / path
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Missing or modified media: {path}")
        if not item["source"] or item["use_scope"] != "fictional_public_demo" or item["contains_real_client_material"]:
            raise ValueError("Media rights are incomplete")
        if item.get("derived_from"):
            if any(source not in media for source in item["derived_from"]) or not item.get("copy_source"):
                raise ValueError("Composed media provenance is incomplete")
        if file.suffix == ".jpg":
            with Image.open(file) as image:
                if image.width < 720 or image.height < 900:
                    raise ValueError("Image too small for public preview")
        elif file.suffix == ".mp4":
            if file.stat().st_size < 1024 or b"ftyp" not in file.read_bytes()[:32]:
                raise ValueError("Unplayable video container")
        else:
            raise ValueError("Unsupported media type")
        media[path] = item
    samples = manifest["samples"]
    if len([item for item in samples if item["kind"] == "post"]) != 10:
        raise ValueError("Pilot kit requires ten posts")
    if not {"story", "reel"}.issubset({item["kind"] for item in samples}):
        raise ValueError("Pilot kit requires story and reel")
    if len({item["id"] for item in samples}) != len(samples):
        raise ValueError("Duplicate sample")
    completed = [item for item in samples if item.get("copy_in_image")]
    if {item.get("content_type") for item in completed} != {"editorial_product", "offer", "menu_feature"}:
        raise ValueError("Pilot kit requires three complete editorial formats")
    for sample in samples:
        if sample["recipe_id"] not in recipes or sample["media"] not in media:
            raise ValueError("Unresolved sample recipe or media")
        if not sample["title"] or not sample["caption"]:
            raise ValueError("Sample copy missing")
        if sample.get("copy_in_image") and not media[sample["media"]].get("derived_from"):
            raise ValueError("Complete sample is missing source media")
        if sample["kind"] == "reel" and sample.get("poster") not in media:
            raise ValueError("Reel poster missing")
        if sample["kind"] in {"post", "story"}:
            with Image.open(directory / sample["media"]) as image:
                expected = (1080, 1350) if sample["kind"] == "post" else (1080, 1920)
                if image.size != expected:
                    raise ValueError("Sample dimensions do not match format")
    scenarios = manifest["scenarios"]
    if {item["id"] for item in scenarios} != {
        "text_only",
        "product_photo_offer",
        "venue_photo",
        "voice_note",
        "short_video",
        "no_message",
    } or len(scenarios) != 6:
        raise ValueError("Incomplete or duplicate input scenarios")
    for scenario in scenarios:
        if scenario["source_media"] and scenario["source_media"] not in media:
            raise ValueError("Scenario input media missing")
        if scenario["result_media"] and scenario["result_media"] not in media:
            raise ValueError("Scenario result media missing")
        if not all(scenario[field] for field in ("label", "message", "result_title", "decision")):
            raise ValueError("Scenario copy missing")
        if scenario["status"] not in {"demo_of_proposed_flow", "format_reference_only"}:
            raise ValueError("Scenario status missing")
        if scenario["id"] == "product_photo_offer":
            if scenario["source_media"] not in media[scenario["result_media"]].get("derived_from", []):
                raise ValueError("Offer must derive from the submitted photo")
        if scenario["id"] == "venue_photo" and scenario["source_media"] != scenario["result_media"]:
            raise ValueError("Venue scenario must preserve source photo")
    return manifest


def export_web(directory: Path, web_root: Path) -> None:
    manifest = validate_kit(directory)
    target = web_root / "public/brand-kits" / manifest["kit_id"] / f"v{manifest['version']}"
    target.mkdir(parents=True, exist_ok=True)
    for item in manifest["media"]:
        shutil.copy2(directory / item["path"], target / Path(item["path"]).name)
    data = web_root / "src/data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "cafe-kit-v1.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-root", type=Path)
    options = parser.parse_args()
    validate_kit(KIT)
    if options.web_root:
        export_web(KIT, options.web_root)
    print("cafe-pausas/v1: valid")
