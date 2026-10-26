"""Render synthetic static-art review cards without customer media or paid APIs."""

import argparse
import csv
import io
import json
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from app.adapters.static_preview import TEMPLATE_VERSION, render_static_preview

CASES = Path(__file__).resolve().parents[1] / "docs/evals/static-art-ptbr-v1.json"
REPORTS = Path(__file__).resolve().parents[1] / ".local/evals/static-art"
SHAPES = {"square": (500, 500), "portrait": (500, 760), "landscape": (900, 500), "panorama": (1200, 240)}
REVIEW_FIELDS = (
    "case_id",
    "template_version",
    "legibility_1_to_5",
    "product_visible_1_to_5",
    "brand_fit_1_to_5",
    "cta_clear_1_to_5",
    "fact_exact_yes_no",
    "critical_error_yes_no",
    "accepted_yes_no",
    "requested_adjustment",
    "reviewer_role",
    "reviewed_at",
)


def synthetic_photo(shape: str) -> bytes | None:
    if shape == "none":
        return None
    size = SHAPES[shape]
    image = Image.new("RGB", size, "#eadabd")
    draw = ImageDraw.Draw(image)
    width, height = size
    draw.rectangle((0, 0, width // 5, height), fill="#e4534d")
    draw.rectangle((width * 4 // 5, 0, width, height), fill="#4a76be")
    draw.ellipse((width // 3, height // 3, width * 2 // 3, height * 2 // 3), fill="#41966b")
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def generate(cases: list[dict], output_dir: Path) -> list[dict]:
    if not 1 <= len(cases) <= 20:
        raise ValueError("Static-art evaluation requires 1–20 curated cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    thumbs = Image.new("RGB", (4 * 300, ((len(cases) + 3) // 4) * 430), "#e8e8e8")
    draw = ImageDraw.Draw(thumbs)
    results = []
    seen = set()
    for index, case in enumerate(cases):
        case_id = case["id"]
        if not re.fullmatch(r"[a-z0-9-]{1,60}", case_id) or case_id in seen:
            raise ValueError("Case IDs must be unique, short and filename-safe")
        seen.add(case_id)
        source = synthetic_photo(case["source_shape"])
        start = time.perf_counter()
        media = render_static_preview(
            business_name=case["business_name"],
            statement=case["statement"],
            brand_color=case["brand_color"],
            format=case["format"],
            source_image=source,
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        (output_dir / f"{case_id}.jpg").write_bytes(media.data)
        with Image.open(io.BytesIO(media.data)) as rendered:
            thumb = ImageOps.contain(rendered, (280, 375))
            x, y = (index % 4) * 300, (index // 4) * 430
            thumbs.paste(thumb, (x + (300 - thumb.width) // 2, y))
            draw.text((x + 10, y + 388), case_id[:34], fill="#182137")
        results.append(
            {
                "case_id": case_id,
                "segment": case["segment"],
                "format": case["format"],
                "source_shape": case["source_shape"],
                "template_version": TEMPLATE_VERSION,
                "sha256": media.sha256,
                "bytes": len(media.data),
                "render_ms": elapsed_ms,
                "human_review": "pending",
            }
        )
    thumbs.save(output_dir / "contact-sheet.jpg", "JPEG", quality=88)
    (output_dir / "measurements.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    with (output_dir / "human-review.csv").open("w", newline="") as review:
        writer = csv.DictWriter(review, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows({"case_id": item["case_id"], "template_version": TEMPLATE_VERSION} for item in results)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPORTS)
    args = parser.parse_args()
    print(json.dumps(generate(json.loads(CASES.read_text()), args.output_dir), indent=2, ensure_ascii=False))
