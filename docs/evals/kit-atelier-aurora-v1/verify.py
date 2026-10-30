"""Verify fixture files and dimensions without network or product integration."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
manifest = json.loads((ROOT / "manifest.json").read_text())


def check(path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path


for item in manifest["media"]:
    check(ROOT / item["source"], item["source_sha256"])
    image_path = ROOT / item["raster"]
    check(image_path, item["raster_sha256"])
    with Image.open(image_path) as image:
        assert image.format == "PNG" and image.size == (item["width"], item["height"])
for font in manifest["fonts"]:
    check(REPO / font["path"], font["sha256"])
check(REPO / manifest["font_license"]["path"], manifest["font_license"]["sha256"])
check(ROOT / manifest["renderer"]["path"], manifest["renderer"]["sha256"])
print("Fixture QA: hashes e dimensões válidos; sem integração ao catálogo.")
