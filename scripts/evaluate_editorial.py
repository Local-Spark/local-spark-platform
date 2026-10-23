"""Bounded synthetic editorial eval; live provider calls require --live."""

import argparse
import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.core.config import Settings
from app.services.editorial_proposals import EditorialProposalService

CASES = Path(__file__).resolve().parents[1] / "docs/evals/editorial-ptbr-v1.json"
REPORTS = Path(__file__).resolve().parents[1] / ".local/evals"


def inputs(case: dict) -> tuple[dict[str, object], set[UUID]]:
    facts = case["facts"]
    return (
        {
            "confirmed_facts": facts,
            "preferences": {"goal": case["goal"], "tone": "friendly", "avoided_topics": []},
            "material": case["material"],
            "material_kind": "text",
            "context_version": 1,
        },
        {UUID(fact["id"]) for fact in facts},
    )


async def evaluate(live: bool) -> dict:
    settings = Settings()
    cases = json.loads(CASES.read_text())
    if len(cases) > 5:
        raise ValueError("Synthetic eval is capped at five cases")
    if live and (settings.editorial_ai_mode != "openai" or not settings.openai_api_key):
        raise ValueError("Explicit OpenAI mode and key are required")
    provider = OpenAIEditorialProvider(settings)
    results = []
    for case in cases:
        data, fact_ids = inputs(case)
        baseline = EditorialProposalService._baseline(data)
        result: dict = {
            "case": case["id"],
            "baseline_safe": bool(fact_ids) and EditorialProposalService._safe(baseline, data, fact_ids),
            "baseline_questions": bool(baseline.questions),
        }
        if not fact_ids:
            result.update(
                status="needs_confirmed_fact", safe=True, asks_when_needed=True, input_tokens=0, output_tokens=0
            )
            results.append(result)
            continue
        if live:
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
                )
            except EditorialProviderError as exc:
                result.update(status="provider_error", code=str(exc))
        results.append(result)
    return {
        "run_at": datetime.now(UTC).isoformat(),
        "model": settings.editorial_ai_model if live else "baseline-v1",
        "live": live,
        "release_decision": "blocked_pending_semantic_review_and_staging",
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Send at most five synthetic cases to the configured provider"
    )
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.live))
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"editorial-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        {
            "report": str(target),
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
