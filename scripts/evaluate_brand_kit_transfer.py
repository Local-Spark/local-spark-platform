"""BL02 controlled, synthetic transfer eval. --live spends at most three image calls."""

import argparse
import base64
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values
from PIL import Image, ImageDraw, ImageFont, ImageOps

from scripts.brand_kit_catalog import KIT, ROOT, validate_kit
from scripts.evaluate_visual_context import load_case, retrieve_context, token_cost

MODEL = "gpt-image-2.5-flare"
QUALITY = "medium"
SIZE = "1024x1280"
MAX_TOTAL_USD = 0.30
SOURCE = ROOT / "docs/evals/assets/croissant-cc0.jpg"
REFERENCE = KIT / "assets/morning-pastries.jpg"
REPORTS = ROOT / ".local/evals/brand-kit-transfer"


def data_url(path: Path) -> str:
    mime = "image/jpeg" if path.suffix == ".jpg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def prompt(route: str, manifest: dict[str, Any]) -> str:
    base = (
        "Edite a primeira fotografia: mantenha um único croissant simples de manteiga, "
        "sem recheio ou cobertura, no primeiro plano. Crie uma cena fotográfica natural "
        "e editorial para cafeteria FICTÍCIA, com luz lateral suave e ambiente realista. "
        "A foto original é CC0 e NÃO representa produto de um negócio real. "
        "NÃO adicione nenhum texto, marca, logotipo, preço, embalagem, promoção, pessoa ou produto novo. "
        "Deixe o croissant visualmente fiel à primeira foto. Saída vertical 4:5."
    )
    if route == "no_kit":
        return base
    palette = manifest["palette"]
    styled = (
        f" Direção aprovada para este ensaio: verde profundo {palette['forest']}, "
        f"creme {palette['cream']} e caramelo {palette['caramel']}; fotografia acolhedora, "
        "produto grande, fundo de cafeteria discreto e área segura para legenda composta depois."
    )
    if route == "manifest":
        return base + styled
    if route == "manifest_reference":
        return (
            base
            + styled
            + (
                " A segunda imagem é APENAS referência de luz, tons e enquadramento do kit no mesmo formato. "
                "Não copie objetos, marca, cenário nem produto dela. "
                "O croissant da primeira imagem continua a fonte factual."
            )
        )
    raise ValueError("Unknown route")


def compose(
    source: Path,
    destination: Path,
    *,
    brand_name: str,
    headline: str,
    price_text: str,
    cta: str,
    palette: dict[str, str],
    demo_label: bool = False,
) -> None:
    """Apply the exact, confirmed copy after image generation, identically for all routes."""
    canvas = Image.new("RGB", (1080, 1350), palette["cream"])
    with Image.open(source) as image:
        canvas.paste(ImageOps.fit(image.convert("RGB"), (1080, 970)), (0, 0))
    draw = ImageDraw.Draw(canvas)
    serif = ImageFont.truetype(KIT / "fonts/DejaVuSerif.ttf", 52)
    sans = ImageFont.truetype(KIT / "fonts/DejaVuSans.ttf", 26)
    price_font = ImageFont.truetype(KIT / "fonts/DejaVuSans.ttf", 37)
    brand_line = brand_name.upper() + (" · EXEMPLO FICTÍCIO" if demo_label else "")
    for value, font in ((brand_line, sans), (headline, serif), (price_text, price_font), (cta, sans)):
        if draw.textbbox((0, 0), value, font=font)[2] > 948:
            raise ValueError("Confirmed copy exceeds recipe safe width")
    draw.rectangle((0, 970, 1080, 1350), fill=palette["forest"])
    draw.text((67, 1000), brand_line, font=sans, fill="#E5D5B9")
    draw.text((65, 1065), headline, font=serif, fill="#FFFFFF")
    draw.text((66, 1155), price_text, font=price_font, fill="#FFFFFF")
    draw.line((67, 1221, 1014, 1221), fill="#D6C8AE", width=2)
    draw.text((66, 1255), cta, font=sans, fill="#FFFFFF")
    canvas.save(destination, quality=90, optimize=True, subsampling=0)


def run_live(route: str, text: str, key: str, directory: Path, copy: dict[str, Any]) -> dict[str, Any]:
    inputs = [{"image_url": data_url(SOURCE)}]
    if route == "manifest_reference":
        inputs.append({"image_url": data_url(REFERENCE)})
    started = time.monotonic()
    with httpx.Client(timeout=240, trust_env=False) as client:
        response = client.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": MODEL,
                "images": inputs,
                "prompt": text,
                "quality": QUALITY,
                "size": SIZE,
                "output_format": "jpeg",
                "output_compression": 90,
                "n": 1,
                "safety_identifier": hashlib.sha256(b"bl02-synthetic-cafe-do-cedro").hexdigest(),
            },
        )
    latency = round(time.monotonic() - started, 2)
    if response.status_code != 200:
        error = response.json().get("error", {})
        return {
            "status": "provider_error",
            "http_status": response.status_code,
            "error_code": error.get("code"),
            "latency_s": latency,
            "attempts": 1,
            "cost_usd": None,
        }
    body = response.json()
    image = base64.b64decode(body["data"][0]["b64_json"], validate=True)
    raw = directory / f"{route}-raw.jpg"
    raw.write_bytes(image)
    output = directory / f"{route}.jpg"
    compose(raw, output, **copy)
    usage = body.get("usage")
    return {
        "status": "generated_pending_blind_review",
        "model": MODEL,
        "quality": QUALITY,
        "size": SIZE,
        "reference_count": len(inputs) - 1,
        "usage": usage,
        "cost_usd": token_cost(usage, MODEL) if usage else None,
        "latency_s": latency,
        "attempts": 1,
        "request_id": response.headers.get("x-request-id"),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output_file": output.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    manifest = validate_kit(KIT)
    case = load_case()
    context = retrieve_context(case)
    if context["decision"] != "generate_preview":
        raise SystemExit(f"Synthetic fixture blocked: {context['decision']}")
    if not context["facts"] or context["business"]["name"] != "Café do Cedro":
        raise SystemExit("Unexpected synthetic case")
    requested = case["requested_output"]
    confirmed_copy = {
        "brand_name": context["business"]["name"],
        "headline": requested["copy_exact"][0],
        "price_text": requested["copy_exact"][1],
        "cta": requested["cta_exact"],
        "palette": manifest["palette"],
        "demo_label": True,
    }
    directory = REPORTS / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    directory.mkdir(parents=True, exist_ok=False)
    routes = ("no_kit", "manifest", "manifest_reference", "local_compose")
    key = dotenv_values(ROOT / ".env").get("MEU_BRACO_DIREITO_OPENAI_API_KEY") if args.live else None
    if args.live and not key:
        raise SystemExit("Configured OpenAI API key required")
    results: dict[str, Any] = {}
    observed_cost = 0.0
    for route in routes:
        if route == "local_compose":
            started = time.monotonic()
            output = directory / "local_compose.jpg"
            compose(SOURCE, output, **confirmed_copy)
            results[route] = {
                "status": "generated_pending_blind_review",
                "model": "local_pillow",
                "reference_count": 0,
                "usage": None,
                "cost_usd": 0.0,
                "infra_cost_usd": "unmeasured",
                "latency_s": round(time.monotonic() - started, 2),
                "attempts": 1,
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_file": output.name,
            }
            continue
        brief = prompt(route, manifest)
        (directory / f"{route}-brief.txt").write_text(brief + "\n")
        if not args.live:
            results[route] = {"status": "dry_run", "provider_calls": 0}
            continue
        if observed_cost + 0.15 > MAX_TOTAL_USD:
            results[route] = {"status": "budget_blocked", "provider_calls": 0}
            continue
        result = run_live(route, brief, str(key), directory, confirmed_copy)
        results[route] = result
        observed_cost += result["cost_usd"] or 0.15
    report = {
        "case": "cafe-do-cedro-kit-transfer-v1",
        "business": "fully_synthetic",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "kit_manifest_sha256": hashlib.sha256((KIT / "manifest.json").read_bytes()).hexdigest(),
        "reference_sha256": hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        "model_rate_source": "https://developers.openai.com/api/docs/pricing",
        "max_total_usd": MAX_TOTAL_USD,
        "observed_api_cost_usd": round(observed_cost, 6),
        "human_review": "pending_blind_mobile_review",
        "owner_approval": "not_available_synthetic_case",
        "commercial_quality": "not_established",
        "routes": results,
    }
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "report": str(directory / "report.json"),
                "routes": {key: value["status"] for key, value in results.items()},
                "observed_api_cost_usd": report["observed_api_cost_usd"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
