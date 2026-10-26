"""Render private synthetic F04.2b cases and measure wall/CPU time without paid APIs."""

import argparse
import asyncio
import csv
import io
import json
import re
import resource
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from app.adapters.video_preview import VIDEO_TEMPLATE_VERSION, render_video_preview

CASES = Path(__file__).resolve().parents[1] / "docs/evals/video-ptbr-v1.json"
REPORTS = Path(__file__).resolve().parents[1] / ".local/evals/video"
SOURCE_SIZES = {"landscape_clip": (640, 360), "portrait_clip": (360, 640), "square_photo": (500, 500)}
REVIEW_FIELDS = (
    "case_id",
    "segment",
    "source_kind",
    "consent_ref",
    "artifact_sha256",
    "mobile_review_yes_no",
    "legibility_1_to_5",
    "subject_visible_1_to_5",
    "cut_coherence_1_to_5",
    "fact_exact_yes_no",
    "critical_error_yes_no",
    "accepted_yes_no",
    "reviewer_role",
    "reviewed_at",
)


def _synthetic_image(shape: str) -> bytes:
    width, height = SOURCE_SIZES[shape]
    image = Image.new("RGB", (width, height), "#4ca77c")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height // 10), fill="#f8de5e")
    draw.rectangle((0, height * 9 // 10, width, height), fill="#a743ab")
    draw.rectangle((0, 0, width // 8, height), fill="#e7433b")
    draw.rectangle((width * 7 // 8, 0, width, height), fill="#355bc7")
    draw.ellipse((width // 3, height // 3, width * 2 // 3, height * 2 // 3), fill="#f6d482")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def _synthetic_clip(image: bytes, seconds: int, folder: Path) -> bytes:
    source = folder / "source.png"
    target = folder / "source.mp4"
    source.write_bytes(image)
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            "24",
            "-i",
            str(source),
            "-t",
            str(seconds),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ],
        check=True,
        timeout=30,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return target.read_bytes()


def _cpu_seconds() -> float:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def _review_frame(video: Path, second: int, target: Path) -> Image.Image:
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(second),
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(target),
        ],
        check=True,
        timeout=20,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    with Image.open(target) as frame:
        return ImageOps.contain(frame.convert("RGB"), (240, 427))


async def generate(cases: list[dict], output_dir: Path) -> list[dict]:
    if not 1 <= len(cases) <= 20:
        raise ValueError("Video evaluation requires 1–20 curated cases")
    seen: set[str] = set()
    for case in cases:
        case_id = case["id"]
        if not re.fullmatch(r"[a-z0-9-]{1,60}", case_id) or case_id in seen:
            raise ValueError("Case IDs must be unique, short and filename-safe")
        seen.add(case_id)
        if case["source_shape"] not in {*SOURCE_SIZES, "none"}:
            raise ValueError("Unsupported source shape")
    output_dir.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (3 * 260, len(cases) * 465), "#e8e8e8")
    draw = ImageDraw.Draw(sheet)
    results = []
    for index, case in enumerate(cases):
        case_id, shape = case["id"], case["source_shape"]
        with tempfile.TemporaryDirectory(prefix="video-eval-") as temporary:
            folder = Path(temporary)
            photo = _synthetic_image(shape) if shape in SOURCE_SIZES else None
            clip = _synthetic_clip(photo, case["source_seconds"], folder) if shape.endswith("_clip") else None
            before_cpu, started = _cpu_seconds(), time.perf_counter()
            media = await render_video_preview(
                business_name=case["business_name"],
                statement=case["statement"],
                brand_color=case["brand_color"],
                source_image=photo if shape == "square_photo" else None,
                source_video=clip,
                intro_text=case["intro_text"],
                cta_text=case["cta_text"],
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            cpu_ms = round((_cpu_seconds() - before_cpu) * 1000)
            target = output_dir / f"{case_id}.mp4"
            target.write_bytes(media.data)
            for column, second in enumerate((1, 4, 7)):
                thumb = _review_frame(target, second, folder / f"frame-{second}.png")
                x, y = column * 260, index * 465
                sheet.paste(thumb, (x + (260 - thumb.width) // 2, y))
                draw.text((x + 10, y + 435), f"{case_id[:24]} / {second}s", fill="#182137")
        results.append(
            {
                "case_id": case_id,
                "segment": case["segment"],
                "source_kind": "clip" if clip else "photo" if photo else "none",
                "source_shape": shape,
                "template_version": VIDEO_TEMPLATE_VERSION,
                "sha256": media.sha256,
                "bytes": len(media.data),
                "render_ms": elapsed_ms,
                "cpu_ms": cpu_ms,
                "human_review": "pending",
            }
        )
    sheet.save(output_dir / "contact-sheet.jpg", "JPEG", quality=88)
    (output_dir / "measurements.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    with (output_dir / "human-review.csv").open("w", newline="") as review:
        writer = csv.DictWriter(review, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(
            {
                "case_id": item["case_id"],
                "segment": item["segment"],
                "source_kind": item["source_kind"],
                "artifact_sha256": item["sha256"],
            }
            for item in results
        )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPORTS)
    args = parser.parse_args()
    print(
        json.dumps(asyncio.run(generate(json.loads(CASES.read_text()), args.output_dir)), indent=2, ensure_ascii=False)
    )
