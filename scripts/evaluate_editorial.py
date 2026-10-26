"""Bounded synthetic editorial eval; live provider calls require --live."""

import argparse
import asyncio
import csv
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.core.config import Settings
from app.services.editorial_proposals import EditorialProposalService

CASES = Path(__file__).resolve().parents[1] / "docs/evals/editorial-ptbr-v2.json"
REPORTS = Path(__file__).resolve().parents[1] / ".local/evals"


def inputs(case: dict) -> tuple[dict[str, object], set[UUID]]:
    facts = case["facts"]
    return (
        {
            "confirmed_facts": facts,
            "preferences": {"goal": case["goal"], "tone": "friendly", "avoided_topics": []},
            "material": case["material"],
            "material_kind": case.get("material_kind", "text"),
            "source_asset_id": case.get("source_asset_id"),
            "context_version": 1,
        },
        {UUID(fact["id"]) for fact in facts},
    )


def storyboard_valid(draft, facts: list[dict], source_asset_id: str | None) -> bool:
    if not facts:
        return not draft.script
    roles = [scene.role for scene in draft.script]
    if roles.count("fact") != 1 or roles.count("cta") != 1 or roles.count("material") > 1:
        return False
    fact = draft.script[roles.index("fact")]
    expected = facts[0]["statement"].rstrip(". ") + "."
    if fact.on_screen_text != expected or fact.voiceover != expected or fact.fact_ids != [UUID(facts[0]["id"])]:
        return False
    return all(scene.source_asset_id == UUID(source_asset_id) for scene in draft.script if scene.role == "material")


async def evaluate(live: bool, max_live_cases: int = 5) -> dict:
    settings = Settings()
    cases = json.loads(CASES.read_text())
    if len(cases) > 12:
        raise ValueError("Synthetic eval is capped at twelve cases")
    if not 1 <= max_live_cases <= 12:
        raise ValueError("Live eval call cap must be between one and twelve")
    if live and (settings.editorial_ai_mode != "openai" or not settings.openai_api_key):
        raise ValueError("Explicit OpenAI mode and key are required")
    provider = OpenAIEditorialProvider(settings)
    results = []
    live_calls = 0
    for case in cases:
        data, fact_ids = inputs(case)
        baseline = EditorialProposalService._baseline(data)
        result: dict = {
            "case": case["id"],
            "baseline_safe": bool(fact_ids) and EditorialProposalService._safe(baseline, data, fact_ids),
            "baseline_questions": bool(baseline.questions),
            "baseline_storyboard_valid": storyboard_valid(baseline, case["facts"], case.get("source_asset_id")),
            "human_review": "pending",
            "status": "baseline_completed",
            "input_tokens": 0,
            "output_tokens": 0,
        }
        result["safe"] = result["baseline_safe"] if fact_ids and not live else None
        if not fact_ids:
            result.update(
                status="needs_confirmed_fact", safe=True, asks_when_needed=True, input_tokens=0, output_tokens=0
            )
            results.append(result)
            continue
        if live:
            if live_calls >= max_live_cases:
                result.update(status="not_run_call_cap", safe=None, input_tokens=0, output_tokens=0)
                results.append(result)
                continue
            live_calls += 1
            start = time.perf_counter()
            try:
                draft, input_tokens, output_tokens = await provider.propose(data, uuid4())
                safe = EditorialProposalService._safe(draft, data, fact_ids)
                guarded = EditorialProposalService._ground(draft, data) if safe else None
                result.update(
                    status="completed",
                    safe=safe,
                    asks_when_needed=not case["must_ask"] or bool(draft.questions),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=round((time.perf_counter() - start) * 1000),
                    draft=draft.model_dump(mode="json"),
                    delivered_draft=guarded.model_dump(mode="json") if guarded else None,
                    storyboard_valid=storyboard_valid(guarded, case["facts"], case.get("source_asset_id"))
                    if guarded
                    else False,
                )
            except EditorialProviderError as exc:
                result.update(status="provider_error", code=str(exc))
        results.append(result)
    return {
        "run_at": datetime.now(UTC).isoformat(),
        "model": settings.editorial_ai_model if live else "baseline-v1",
        "live": live,
        "max_live_cases": max_live_cases if live else 0,
        "release_decision": "blocked_pending_semantic_review_and_staging",
        "cases": results,
    }


def write_review_sheet(report: dict, target: Path) -> None:
    with target.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case",
                "candidate",
                "factual_error",
                "usefulness_1_to_5",
                "clarity_1_to_5",
                "edits_to_approve",
                "abstention_appropriate",
                "reviewer_notes",
            ],
        )
        writer.writeheader()
        for item in report["cases"]:
            writer.writerow({"case": item["case"], "candidate": "baseline-v1"})
            if report["live"] and item.get("status") == "completed":
                writer.writerow({"case": item["case"], "candidate": report["model"]})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Send synthetic cases to the configured provider, with a call cap"
    )
    parser.add_argument("--max-live-cases", type=int, default=5, help="Maximum paid calls when --live is set (1–12)")
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.live, args.max_live_cases))
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"editorial-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_review_sheet(report, target.with_suffix(".review.csv"))
    print(
        {
            "report": str(target),
            "review_sheet": str(target.with_suffix(".review.csv")),
            "model": report["model"],
            "cases": len(report["cases"]),
            "completed": sum(item.get("status") == "completed" for item in report["cases"]),
            "confirmation_required": sum(item.get("status") == "needs_confirmed_fact" for item in report["cases"]),
            "guard_pass": sum(item.get("safe") is True for item in report["cases"]),
            "baseline_guard_pass": sum(item["baseline_safe"] for item in report["cases"]),
            "input_tokens": sum(item.get("input_tokens", 0) for item in report["cases"]),
            "output_tokens": sum(item.get("output_tokens", 0) for item in report["cases"]),
        }
    )


if __name__ == "__main__":
    main()
