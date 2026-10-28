"""One separately authorized, fixed synthetic image evaluation; not the product.

Default is a dry run. The live mode has a fixed, independent local ledger for
the new USD 1 grant and never retries a reserved request. It accepts no paths,
URLs, prompts or customer data through the CLI. It is not a provider-side cap.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from dotenv import dotenv_values

from app.adapters.brand_overlay import BrandOverlayError, render_brand_overlay
from app.adapters.material_media import FetchedMedia
from app.adapters.visual_ai import OpenAIVisualProvider, VisualAIError, VisualRequest, VisualResult
from app.schemas.brand_kits import BrandKitOverrides
from scripts.evaluate_bl042_guarded import (
    FIXTURE_HASH,
    LOGO_HASH,
    MODEL,
    PHOTO_HASH,
    _checked,
)
from scripts.evaluate_bl042_guarded import (
    synthetic_request as synthetic_request_v1,
)
from scripts.evaluate_visual_context import ROOT, token_cost

EVAL_ID = "bl042-synthetic-brand-finish-20261028-v2"
REQUEST_ID = UUID("317db9b4-5dd0-405c-82f9-e8e9841d05d8")
GRANT_USD_MICROS = 1_000_000
LEDGER = ROOT / ".local/evals/bl042-guarded-synthetic-v2/budget.sqlite3"
OUTPUT = ROOT / ".local/evals/bl042-guarded-synthetic-v2"
LEGACY_LEDGER = ROOT / ".local/evals/bl042-guarded-synthetic/budget.sqlite3"
PROMPT = (
    "Crie uma cena fotográfica editorial 4:5 para um ensaio FICTÍCIO de cafeteria. "
    "Use o croissant simples da imagem CC0 de referência como assunto principal e preserve sua aparência, "
    "sem recheio ou cobertura. Fotografia apetitosa, luz natural lateral e ambiente acolhedor discreto, "
    "com espaço limpo para uma identidade visual aplicada depois. Não mostre texto, letras, números, preço, "
    "logotipo, marca-d'água, cardápio ou símbolos. Não alegue representar um local ou produto real."
)


class Provider(Protocol):
    async def generate(self, request: VisualRequest) -> VisualResult: ...


@dataclass(frozen=True)
class EvalRequest:
    request: VisualRequest
    fingerprint: str
    kit: BrandKitOverrides
    logo: FetchedMedia
    statement: str
    cta: str


def synthetic_request() -> EvalRequest:
    """Use only fixed checked fixture bytes; never accept customer input."""
    checked = _checked(ROOT / "docs/evals/visual-context-cafe-v1.json", FIXTURE_HASH)
    fixture = json.loads(checked)
    base = synthetic_request_v1()
    photo = base.request.references[0]
    logo_data = base.request.references[1].content
    brand = fixture["proposed_web_profile"]["brand_kit"]
    requested = fixture["requested_output"]
    statement = " · ".join(requested["copy_exact"])
    cta = requested["cta_exact"]
    kit = BrandKitOverrides.model_validate(
        {
            "palette": {
                "primary": brand["primary_hex"],
                "background": brand["secondary_hex"],
                "accent": brand["accent_hex"],
            },
            "heading_font": "DejaVu Serif",
            "body_font": "DejaVu Sans",
            "brand_name": fixture["business_profile"]["name"],
            "tagline": "Pausas com sabor",
            "cta": cta,
            "logo_asset_id": "8c7f9f47-b206-45ec-a962-40ee8f824c6c",
            "formats": {
                "feed": {"layout": "photo_focus", "image_position": "center"},
                "story": {"layout": "photo_focus", "image_position": "center"},
                "reel_cover": {"layout": "photo_focus", "image_position": "center"},
            },
        }
    )
    request = VisualRequest(
        prompt=PROMPT,
        model=MODEL,
        quality="medium",
        size="1024x1280",
        output_format="png",
        request_id=REQUEST_ID,
        references=(photo,),
    )
    payload = json.dumps(
        {
            "fixture": FIXTURE_HASH,
            "photo": PHOTO_HASH,
            "logo": LOGO_HASH,
            "model": MODEL,
            "prompt": PROMPT,
            "id": str(REQUEST_ID),
            "kit": kit.model_dump(mode="json"),
            "statement": statement,
            "cta": cta,
            "size": request.size,
            "quality": request.quality,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return EvalRequest(
        request,
        hashlib.sha256(payload).hexdigest(),
        kit,
        FetchedMedia(logo_data, "image/png", LOGO_HASH),
        statement,
        cta,
    )


def reserve_once(path: Path, fingerprint: str) -> bool:
    """Consume the entire additional test grant once, durably, before network."""
    if path.resolve() == LEGACY_LEDGER.resolve() or path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Refusing legacy or symlink ledger")
    if len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
        raise ValueError("Invalid request fingerprint")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), grant_id TEXT, cap INTEGER)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, "
            "hold INTEGER NOT NULL, state TEXT NOT NULL, created TEXT NOT NULL, result TEXT)"
        )
        db.execute("INSERT OR IGNORE INTO policy VALUES(1,?,?)", (EVAL_ID, GRANT_USD_MICROS))
        if db.execute("SELECT grant_id,cap FROM policy WHERE id=1").fetchone() != (EVAL_ID, GRANT_USD_MICROS):
            raise ValueError("Unexpected evaluation budget policy")
        if db.execute("SELECT 1 FROM attempts LIMIT 1").fetchone():
            db.commit()
            return False
        db.execute(
            "INSERT INTO attempts VALUES(?,?,?,?,?,NULL)",
            (EVAL_ID, fingerprint, GRANT_USD_MICROS, "submitted", datetime.now(UTC).isoformat()),
        )
        db.commit()
    return True


def record_outcome(path: Path, state: str, details: dict[str, object]) -> None:
    if state not in {"completed_unreconciled", "uncertain", "postprocess_failed"}:
        raise ValueError("Invalid evaluation outcome")
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        cursor = db.execute(
            "UPDATE attempts SET state=?,result=? WHERE id=? AND state='submitted'",
            (state, json.dumps(details, sort_keys=True), EVAL_ID),
        )
        if cursor.rowcount != 1:
            raise ValueError("Evaluation attempt is not submitted")


async def run_once(provider: Provider, ledger: Path, directory: Path) -> str:
    """Generate one fixed scene and apply original synthetic brand; never retry."""
    prepared = synthetic_request()
    scene_path, feed_path = directory / "scene.png", directory / "feed.png"
    if directory.is_symlink() or scene_path.exists() or feed_path.exists():
        raise ValueError("Evaluation output already exists or is a symlink")
    directory.mkdir(parents=True, exist_ok=True)
    if not reserve_once(ledger, prepared.fingerprint):
        return "already_reserved_no_retry"
    try:
        result = await provider.generate(prepared.request)
    except (VisualAIError, OSError):
        # Even an error response may be charged; the grant remains held.
        record_outcome(ledger, "uncertain", {})
        return "uncertain"
    details: dict[str, object] = {
        "scene_sha256": result.sha256,
        "usage": result.usage,
        "provider_request_id": result.provider_request_id,
    }
    if result.usage:
        try:
            details["estimated_usd"] = token_cost(result.usage, "gpt-image-2.5-flare")
        except (KeyError, TypeError):
            pass
    try:
        if (
            result.mime_type != "image/png"
            or result.width != 1024
            or result.height != 1280
            or hashlib.sha256(result.content).hexdigest() != result.sha256
        ):
            raise BrandOverlayError("SYNTHETIC_SCENE_INVALID")
        with scene_path.open("xb") as stream:
            stream.write(result.content)
        finished = render_brand_overlay(
            FetchedMedia(result.content, result.mime_type, result.sha256),
            kit=prepared.kit,
            format="photo",
            statement=prepared.statement,
            cta=prepared.cta,
            logo=prepared.logo,
        )
        with feed_path.open("xb") as stream:
            stream.write(finished.data)
        details["feed_sha256"] = finished.sha256
    except (BrandOverlayError, OSError):
        record_outcome(ledger, "postprocess_failed", details)
        return "postprocess_failed"
    record_outcome(ledger, "completed_unreconciled", details)
    return "completed_unreconciled"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Make at most one paid synthetic request")
    args = parser.parse_args()
    prepared = synthetic_request()
    if not args.live:
        print(f"dry-run: fixed synthetic brand fixture verified; request={prepared.fingerprint}; provider_calls=0")
        return
    key = dotenv_values(ROOT / ".env").get("MEU_BRACO_DIREITO_OPENAI_API_KEY") or os.getenv(
        "MEU_BRACO_DIREITO_OPENAI_API_KEY"
    )
    if not key:
        raise SystemExit("OpenAI API key is not configured")
    result = asyncio.run(run_once(OpenAIVisualProvider(key), LEDGER, OUTPUT))
    print(f"isolated synthetic evaluation: {result}")


if __name__ == "__main__":
    main()
