"""One-request, synthetic visual-context eval. Default mode validates and writes a brief only."""

import argparse
import base64
import csv
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values
from PIL import Image

from app.schemas.editorial_context import ContextContent
from app.schemas.onboarding import OnboardingCreate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/evals/visual-context-cafe-v1.json"
REPORTS = ROOT / ".local/evals/visual-context-v1"
MODEL_RATES_USD_PER_MILLION = {
    "gpt-image-2.5-flare": {"image_input": 8, "text_input": 5, "image_output": 30},
    "gpt-image-2.5-sunburst": {"image_input": 8, "text_input": 5, "image_output": 30},
}
SAFE_COMPETITOR_PATTERNS = {
    "product_closeup": "produto grande, pouco texto e leitura rápida em celular",
    "preparation_video": "vídeo de preparo somente com clipe próprio autorizado",
}


def load_case(path: Path = FIXTURE) -> dict[str, Any]:
    case: dict[str, Any] = json.loads(path.read_text())
    if case["fixture_kind"] != "fully_synthetic_business_with_cc0_reference_photo":
        raise ValueError("This eval permits only its synthetic/CC0 fixture")
    profile = case["business_profile"]
    onboarding_fields = (
        "name",
        "category",
        "description",
        "city",
        "state_code",
        "city_ibge_code",
        "timezone",
        "phone",
        "brand_color",
    )
    OnboardingCreate.model_validate(
        {
            **{field: profile[field] for field in onboarding_fields},
            "accept_terms": profile["accept_terms"],
            "accept_privacy": profile["accept_privacy"],
            "terms_version": profile["terms_version"],
        }
    )
    ContextContent.model_validate({key: case["editorial_context"][key] for key in ("facts", "preferences")})
    assets = {asset["asset_id"]: asset for asset in case["authorized_assets"]}
    if len(assets) != len(case["authorized_assets"]):
        raise ValueError("Duplicate asset ID")
    for asset in assets.values():
        if asset["tenant_id"] != case["tenant_id"]:
            raise ValueError("Cross-tenant eval asset")
        if asset["use"] not in {"eval_only", "eval_only_stand_in_not_real_cafe_product"}:
            raise ValueError("Asset is not licensed for this eval")
        file = ROOT / asset["path"]
        if not file.is_file() or not file.resolve().is_relative_to(ROOT / "docs/evals/assets"):
            raise ValueError("Missing or out-of-scope eval asset")
        if asset.get("sha256") and hashlib.sha256(file.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("Asset hash mismatch")
    return case


def retrieve_context(case: dict[str, Any]) -> dict[str, Any]:
    """Mock read-only tenant tools; a production gateway must query RLS-scoped rows."""
    from datetime import date

    now = date.fromisoformat(case["as_of"][:10])
    business = case["business_profile"]
    event = case["conversation_event"]
    if not case["ai_processing_consent"]["owner_confirmed"]:
        return {"decision": "ask_owner_no_paid_generation", "reason": "ai_consent_missing"}
    billing = case["billing_access"]
    if billing["visual_usd_remaining_this_month"] < case["requested_output"]["max_usd_for_generation"]:
        return {"decision": "deny_budget_no_paid_generation", "reason": "insufficient_budget"}
    assets = {asset["asset_id"]: asset for asset in case["authorized_assets"]}
    selected = [assets[item] for item in event["asset_ids"]]
    facts = [
        fact
        for fact in case["editorial_context"]["facts"]
        if fact["valid_until"] is None or date.fromisoformat(fact["valid_until"]) >= now
    ]
    catalog = case["proposed_web_profile"]["catalog"]
    price = next((fact for fact in facts if fact["id"] == catalog[0]["price_fact_id"]), None)
    if price is None:
        return {"decision": "ask_owner_no_paid_generation", "reason": "no_current_confirmed_price"}
    if any(asset["kind"] == "finished_art" for asset in selected):
        return {"decision": "preserve_existing_art_no_paid_generation", "reason": "finished_art"}
    if not selected:
        return {"decision": "ask_for_real_product_photo_or_offer_non_product_design", "reason": "no_source_photo"}
    if any(asset["tenant_id"] != case["tenant_id"] for asset in selected):
        return {"decision": "deny_access_no_generation", "reason": "cross_tenant_asset"}
    if any(asset["kind"] != "raw_photo" for asset in selected):
        return {"decision": "ask_owner_no_paid_generation", "reason": "unsupported_source_kind"}
    return {
        "decision": "generate_preview",
        "tenant_id": case["tenant_id"],
        "business_id": case["business_id"],
        "profile_version": business["profile_version"],
        "context_version": case["editorial_context"]["version"],
        "brand_version": case["proposed_web_profile"]["brand_kit"]["version"],
        "billing_plan": billing["plan"],
        "visual_usd_remaining_this_month": billing["visual_usd_remaining_this_month"],
        "business": {key: business[key] for key in ("name", "category", "description", "city", "state_code")},
        "audience": case["proposed_web_profile"]["audience"],
        "brand": case["proposed_web_profile"]["brand_kit"],
        "policy": case["proposed_web_profile"]["content_policy"],
        "catalog": catalog,
        "facts": facts,
        "preferences": case["editorial_context"]["preferences"],
        "assets": selected,
        "competitor_patterns": [
            SAFE_COMPETITOR_PATTERNS[item["pattern_code"]]
            for item in case["competitor_observations"]
            if item["pattern_code"] in SAFE_COMPETITOR_PATTERNS
        ],
        "recent_content": [
            {"theme": item["theme"], "hook": item["hook"], "owner_feedback": item["owner_feedback"]}
            for item in case["recent_publications"]
        ],
        "request": event["text"],
        "output": case["requested_output"],
    }


def build_prompt(context: dict[str, Any]) -> str:
    if context["decision"] != "generate_preview":
        raise ValueError("No eligible generation")
    brand = context["brand"]
    requested = context["output"]
    exact = "; ".join(requested["copy_exact"] + [requested["cta_exact"]])
    facts = "; ".join(fact["statement"] for fact in context["facts"] if fact["kind"] in {"product", "price"})
    repeated = "; ".join(item["hook"] for item in context["recent_content"])
    competitor = "; ".join(context["competitor_patterns"])
    return (
        "Crie UMA arte completa de feed 4:5, em português do Brasil, para uma cafeteria FICTÍCIA. "
        "É um ensaio privado: não declare que a fotografia representa um produto ou local real dessa empresa. "
        "A primeira imagem é o croissant CC0 de referência; a segunda é o logotipo sintético da marca. "
        "Use o croissant simples como assunto principal, sem recheio, cobertura, outro produto ou aparência alterada. "
        "Faça uma fotografia editorial natural, com alimento grande e apetitoso, "
        "luz lateral suave e fundo de café discreto. "
        f"Identidade: {context['business']['name']}; {brand['visual_style']} "
        f"Paleta: verde {brand['primary_hex']}, creme {brand['secondary_hex']}, caramelo {brand['accent_hex']}; "
        f"hierarquia: {brand['composition']} "
        "Inclua o logo da segunda imagem apenas UMA vez, pequeno, sem deformar letras ou inventar símbolo. "
        f"Textos na peça, EXATAMENTE como escritos, sem variantes nem texto adicional: {exact}. "
        f"Fatos confirmados: {facts}. "
        f"Pedido do dono: {context['request']} "
        f"Evite repetir os ganchos recentes: {repeated}. "
        f"Hipóteses de formato de concorrência (NÃO copiar): {competitor}. "
        "Não escreva promoção, desconto, validade 'hoje', estoque, ingrediente novo, endereço, horário, "
        "métrica, promessa ou afirmação de disponibilidade. Não acrescente hashtags ou emojis na arte. "
        "Legibilidade em celular, margens seguras, texto com contraste; preço e nome sem erros. "
        "Se não conseguir preservar o logo exato, deixe uma área limpa para aplicação posterior."
    )


def token_cost(usage: dict[str, Any], model: str = "gpt-image-2.5-flare") -> float:
    details = usage["input_tokens_details"]
    output = usage["output_tokens_details"]
    rates = MODEL_RATES_USD_PER_MILLION[model]
    return float(
        round(
            (
                details["image_tokens"] * rates["image_input"]
                + details["text_tokens"] * rates["text_input"]
                + output["image_tokens"] * rates["image_output"]
            )
            / 1_000_000,
            6,
        )
    )


def image_data(asset: dict[str, Any]) -> str:
    path = ROOT / asset["path"]
    media_type = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{media_type};base64,{base64.b64encode(path.read_bytes()).decode()}"


def live_edit(case: dict[str, Any], prompt: str, model: str, quality: str) -> tuple[bytes, dict[str, Any]]:
    key = dotenv_values(ROOT / ".env").get("MEU_BRACO_DIREITO_OPENAI_API_KEY")
    if not key:
        raise ValueError("Configured OpenAI API key required for --live")
    assets = {asset["asset_id"]: asset for asset in case["authorized_assets"]}
    source = assets[case["conversation_event"]["asset_ids"][0]]
    logo = assets[case["proposed_web_profile"]["brand_kit"]["logo_asset_id"]]
    started = time.monotonic()
    with httpx.Client(timeout=240, trust_env=False) as client:
        response = client.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "images": [{"image_url": image_data(source)}, {"image_url": image_data(logo)}],
                "prompt": prompt,
                "quality": quality,
                "size": case["requested_output"]["size"],
                "output_format": "jpeg",
                "output_compression": 90,
                "n": 1,
                "safety_identifier": hashlib.sha256(case["tenant_id"].encode()).hexdigest(),
            },
        )
    elapsed = round(time.monotonic() - started, 2)
    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ValueError(f"Provider rejected request: HTTP {response.status_code}, code={error.get('code')}")
    body = response.json()
    image = base64.b64decode(body["data"][0]["b64_json"], validate=True)
    return image, {
        "model": model,
        "quality": quality,
        "size": case["requested_output"]["size"],
        "usage": body.get("usage"),
        "elapsed_seconds": elapsed,
        "request_id": response.headers.get("x-request-id"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Spend at most one Images API request on synthetic/CC0 data"
    )
    parser.add_argument("--model", choices=tuple(MODEL_RATES_USD_PER_MILLION), default="gpt-image-2.5-flare")
    parser.add_argument("--quality", choices=("medium", "high"), default="high")
    args = parser.parse_args()
    case = load_case()
    context = retrieve_context(case)
    if context["decision"] != "generate_preview":
        raise SystemExit(f"Generation blocked: {context['decision']}")
    prompt = build_prompt(context)
    run = REPORTS / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True, exist_ok=False)
    (run / "brief.txt").write_text(prompt + "\n")
    (run / "retrieved-context.json").write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n")
    report: dict[str, Any] = {
        "case": "cafe-do-cedro-v1",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "business": "synthetic",
        "source": "CC0 stock photo, not real café product",
        "tool_retrieval": "fixture_only",
        "provider_calls": 0,
        "human_review": "pending",
        "release_decision": "blocked_pending_owner_review_and_real_authorized_assets",
    }
    if args.live:
        image, provider = live_edit(case, prompt, args.model, args.quality)
        with (run / "image.jpg").open("wb") as output:
            output.write(image)
        with Image.open(run / "image.jpg") as result:
            dimensions = result.size
        report.update(
            provider_calls=1,
            provider=provider,
            dimensions=dimensions,
            image_sha256=hashlib.sha256(image).hexdigest(),
        )
        if provider["usage"]:
            report["estimated_usd_at_pinned_2026_10_26_standard_rates"] = token_cost(provider["usage"], args.model)
            report["within_fixture_generation_budget"] = (
                report["estimated_usd_at_pinned_2026_10_26_standard_rates"]
                <= case["requested_output"]["max_usd_for_generation"]
            )
    (run / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    with (run / "human-review.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "case",
                "product_fidelity_1_to_5",
                "brand_fidelity_1_to_5",
                "mobile_readability_1_to_5",
                "exact_text",
                "exact_price",
                "logo_correct",
                "invented_claim",
                "would_publish",
                "notes",
            ]
        )
        writer.writerow(["cafe-do-cedro-v1", "", "", "", "", "", "", "", "", ""])
    print(
        json.dumps(
            {
                "report": str(run / "report.json"),
                "image": str(run / "image.jpg") if args.live else None,
                "provider_calls": report["provider_calls"],
                "cost_usd": report.get("estimated_usd_at_pinned_2026_10_26_standard_rates"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
