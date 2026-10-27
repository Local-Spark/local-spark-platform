"""One synthetic-only visual evaluation with a durable, shared local spend hold.

This is an isolated evaluation, not the multi-tenant application or a provider
spending limit. The fixed ledger never releases a hold or repeats a submission.
Only the repository's pinned synthetic fixture and CC0 photograph may be used.
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

from app.adapters.visual_ai import OpenAIVisualProvider, VisualAIError, VisualReference, VisualRequest, VisualResult
from scripts.evaluate_visual_context import ROOT, build_prompt, retrieve_context, token_cost

FIXTURE_HASH = "5a4d03a78745efefb45db980965fa08a8d5d72ea28492e93ec08174fba570f0a"
PHOTO_HASH = "519772437eca1f7d2383edeebf80dc4beaf3d5e3039910cee5b975643de182ed"
LOGO_HASH = "a9060161285fecd15441238fc20f10e5a2c9285161b701d326d4a289545e6e3f"
EVAL_ID = "bl042-synthetic-feed-20261027-v1"
REQUEST_ID = UUID("1f90eb69-412d-411a-b421-5d29546e883a")
HISTORY_HOLD_MICROS = 500_000
CALL_HOLD_MICROS = 500_000
CAP_MICROS = 1_000_000
MODEL = "gpt-image-2.5-flare-2026-09-08"


class Provider(Protocol):
    async def generate(self, request: VisualRequest) -> VisualResult: ...


@dataclass(frozen=True)
class EvalRequest:
    request: VisualRequest
    fingerprint: str


def _checked(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Synthetic fixture hash mismatch; paid evaluation blocked")
    return data


def synthetic_request() -> EvalRequest:
    # Fixed paths and hashes make it impossible to substitute a customer's files
    # merely by changing fixture JSON or supplying a CLI path.
    fixture = _checked(ROOT / "docs/evals/visual-context-cafe-v1.json", FIXTURE_HASH)
    photo = _checked(ROOT / "docs/evals/assets/croissant-cc0.jpg", PHOTO_HASH)
    logo = _checked(ROOT / "docs/evals/assets/cafe-do-cedro-logo.png", LOGO_HASH)
    # Parse the checked bytes, never re-read the file after validating its hash.
    case = json.loads(fixture)
    context = retrieve_context(case)
    if context.get("decision") != "generate_preview" or context["business"]["name"] != "Café do Cedro":
        raise ValueError("Synthetic fixture is not eligible")
    prompt = build_prompt(context)
    payload = json.dumps(
        {
            "fixture": FIXTURE_HASH,
            "photo": PHOTO_HASH,
            "logo": LOGO_HASH,
            "prompt": prompt,
            "model": MODEL,
            "quality": "medium",
            "size": "1024x1280",
            "id": str(REQUEST_ID),
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    request = VisualRequest(
        prompt=prompt,
        model=MODEL,
        quality="medium",
        size="1024x1280",
        output_format="jpeg",
        request_id=REQUEST_ID,
        references=(VisualReference(photo, "image/jpeg"), VisualReference(logo, "image/png")),
    )
    return EvalRequest(request, hashlib.sha256(payload).hexdigest())


def reserve_once(path: Path, fingerprint: str) -> bool:
    """Atomically reserve all remaining test authority before network access.

    SQLite serializes independent local processes. A prior/unknown submission is
    never sent again. The hold is a conservative estimate, not a provider cap.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Refusing a symlink ledger")
    with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), history INTEGER, cap INTEGER)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, "
            "hold INTEGER NOT NULL, state TEXT NOT NULL, created TEXT NOT NULL, result TEXT)"
        )
        db.execute("INSERT OR IGNORE INTO policy(id,history,cap) VALUES(1,?,?)", (HISTORY_HOLD_MICROS, CAP_MICROS))
        if db.execute("SELECT history,cap FROM policy WHERE id=1").fetchone() != (HISTORY_HOLD_MICROS, CAP_MICROS):
            raise ValueError("Unexpected evaluation budget policy")
        existing = db.execute("SELECT id,request_hash,hold FROM attempts").fetchall()
        if existing:
            db.commit()
            return False
        if HISTORY_HOLD_MICROS + CALL_HOLD_MICROS > CAP_MICROS:
            raise ValueError("Evaluation budget exhausted")
        db.execute(
            "INSERT INTO attempts VALUES(?,?,?,?,?,NULL)",
            (EVAL_ID, fingerprint, CALL_HOLD_MICROS, "submitted", datetime.now(UTC).isoformat()),
        )
        db.commit()
    return True


def record_outcome(path: Path, state: str, result: dict[str, object]) -> None:
    if state not in {"completed_unreconciled", "uncertain"}:
        raise ValueError("Invalid evaluation outcome")
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute(
            "UPDATE attempts SET state=?,result=? WHERE id=? AND state='submitted'",
            (state, json.dumps(result, sort_keys=True), EVAL_ID),
        )


async def run_once(provider: Provider, ledger: Path, output: Path) -> str:
    prepared = synthetic_request()
    if not reserve_once(ledger, prepared.fingerprint):
        return "already_reserved_no_retry"
    try:
        result = await provider.generate(prepared.request)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result.content)
        details: dict[str, object] = {
            "sha256": result.sha256,
            "usage": result.usage,
            "provider_request_id": result.provider_request_id,
        }
        if result.usage:
            try:
                details["estimated_usd"] = token_cost(result.usage, "gpt-image-2.5-flare")
            except (KeyError, TypeError):
                pass
        record_outcome(ledger, "completed_unreconciled", details)
        return "completed_unreconciled"
    except (VisualAIError, OSError):
        # A failed response, dropped connection or output write may still be
        # charged; keep the full hold and never retry.
        record_outcome(ledger, "uncertain", {})
        return "uncertain"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Make at most one paid synthetic request")
    args = parser.parse_args()
    prepared = synthetic_request()
    if not args.live:
        print(f"dry-run: fixed synthetic fixture verified; request={prepared.fingerprint}; provider_calls=0")
        return
    key = dotenv_values(ROOT / ".env").get("MEU_BRACO_DIREITO_OPENAI_API_KEY") or os.getenv(
        "MEU_BRACO_DIREITO_OPENAI_API_KEY"
    )
    if not key:
        raise SystemExit("OpenAI API key is not configured")
    directory = ROOT / ".local/evals/bl042-guarded-synthetic"
    result = asyncio.run(run_once(OpenAIVisualProvider(key), directory / "budget.sqlite3", directory / "feed.jpg"))
    print(f"synthetic evaluation: {result}")


if __name__ == "__main__":
    main()
