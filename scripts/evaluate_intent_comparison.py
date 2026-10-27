"""Compare real catalog adapters on the same checked-in synthetic cases.

Offline is the default. Live requires both keys, an explicit budget and a new
exclusive journal. There are no retries, fallback or customer-data inputs.
All datasets are synthetic and previously inspected. The multi-turn cases are
concatenated into one input; this is not an independent test of WhatsApp memory.
"""

import argparse
import asyncio
import hashlib
import json
import os
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, uuid4, uuid5

import httpx
from pydantic import SecretStr

from app.adapters.catalog_intent_ai import CatalogInterpretationError, OpenAICatalogIntentProvider
from app.adapters.jev_intent_ai import JevIntentError, JevIntentProvider
from scripts.evaluate_jev_intent import load_cases

CASES = Path(__file__).resolve().parents[1] / "docs/evals/jev-briefing-smoke-v1.json"
CASES_SHA256 = "805b204d692d691fc116a0c86ca1d2a28790361916eef10ed4af9540429485fe"
HISTORIES = Path(__file__).resolve().parents[1] / "app/tests/fixtures/intent-conversation-v1.json"
HISTORIES_SHA256 = "a67d7a9121170c3eebb0d1c4552430792ccacf707a674d1ae35335fa8c7977f6"
JEV_MODEL = "jev-1.14.0"
OPENAI_MODEL = "gpt-6-luna"  # Current alias; OpenAI does not list a dated snapshot for this model.
OPENAI_REASONING_EFFORT = "none"
MAX_INPUT_TOKENS = 64_000
MAX_OPENAI_OUTPUT_TOKENS = 1024  # Evaluation only; the adapter default remains 320.
LEGACY_OPENAI_OUTPUT_TOKENS = 320
# USD per million tokens; checked 2026-10-27. Input includes conservative
# allowance for cache writes and a 10% regional premium; no built-in tools.
JEV_INPUT = Decimal("0.042")
OPENAI_INPUT = Decimal("0.1375")
OPENAI_OUTPUT = Decimal("0.55")
MILLION = Decimal(1_000_000)
JEV_RESERVE = MAX_INPUT_TOKENS * JEV_INPUT / MILLION
OPENAI_RESERVE = (MAX_INPUT_TOKENS * OPENAI_INPUT + MAX_OPENAI_OUTPUT_TOKENS * OPENAI_OUTPUT) / MILLION
MAX_AUTHORIZED_USD = Decimal("1")


def cases() -> list[dict[str, Any]]:
    raw = CASES.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CASES_SHA256:
        raise ValueError("Synthetic fixture checksum mismatch")
    dataset = json.loads(raw)
    if dataset.get("synthetic") is not True or dataset.get("version") != "jev-briefing-smoke-v1":
        raise ValueError("Only the pinned synthetic fixture is allowed")
    items = [{**item, "kind": "catalog_adapter"} for item in dataset["cases"]]
    raw_histories = HISTORIES.read_bytes()
    if hashlib.sha256(raw_histories).hexdigest() != HISTORIES_SHA256:
        raise ValueError("Synthetic history fixture checksum mismatch")
    histories = json.loads(raw_histories)
    if histories.get("synthetic") is not True or histories.get("version") != "intent-conversation-v1":
        raise ValueError("Only the pinned synthetic history fixture is allowed")
    for item in histories["cases"]:
        turns = item["turns"]
        message = "Histórico do cliente:\n" + "\n".join(f"{index + 1}. {turn}" for index, turn in enumerate(turns))
        items.append({**item, "message": message, "kind": "synthetic_history"})
    _, intents = load_cases()
    items.extend(
        {
            "id": f"intent-{item['id']}",
            "message": item["message"],
            "candidates": [],
            "expected": [item["expected"], None, None],
            "kind": "intent_only",
            "split": item["split"],
        }
        for item in intents
    )
    return items


def reserve(count: int, budget: Decimal | None, jev_key: str | None, openai_key: str | None) -> Decimal:
    total = (JEV_RESERVE + OPENAI_RESERVE) * count
    if budget is None or not budget.is_finite() or budget <= 0 or budget > MAX_AUTHORIZED_USD:
        raise ValueError("Live evaluation requires an explicit total budget up to USD 1")
    if not jev_key or not openai_key:
        raise ValueError("Both TypeSafe and OpenAI credentials are required")
    if total > budget:
        raise ValueError(f"Budget must cover the conservative maximum of USD {total}")
    return total


def _journal_write(stream: Any, payload: dict[str, Any]) -> None:
    stream.seek(0)
    stream.truncate()
    json.dump(payload, stream, ensure_ascii=False)
    stream.flush()
    os.fsync(stream.fileno())


def _estimate(name: str, incoming: int, outgoing: int) -> Decimal:
    return (incoming * JEV_INPUT if name == "jev" else incoming * OPENAI_INPUT + outgoing * OPENAI_OUTPUT) / MILLION


def _costs(report: dict[str, Any]) -> dict[str, str]:
    known = sum(
        (
            _estimate(name, row["input_tokens"], row["output_tokens"])
            for name, details in report["providers"].items()
            for row in details["rows"]
        ),
        Decimal(0),
    )
    unresolved = Decimal(0)
    stopped = report.get("stopped_at") or report.get("pending")
    if stopped and report.get("status") in {"uncertain", "submitted"}:
        usage = report.get("last_error", {}).get("usage")
        if usage:
            known += _estimate(stopped["provider"], usage["input_tokens"], usage["output_tokens"])
        else:
            if stopped["provider"] == "jev":
                unresolved = JEV_RESERVE
            else:
                cap = (
                    report.get("provider_settings", {})
                    .get("openai", {})
                    .get("max_output_tokens", LEGACY_OPENAI_OUTPUT_TOKENS)
                )
                if type(cap) is not int or not 1 <= cap <= 1024:
                    raise ValueError("Invalid historical OpenAI output cap")
                unresolved = (MAX_INPUT_TOKENS * OPENAI_INPUT + cap * OPENAI_OUTPUT) / MILLION
    return {
        "known_estimated_upper_usd": str(known),
        "uncertain_reserved_usd": str(unresolved),
        "incurred_upper_usd": str(known + unresolved),
    }


def _previous(paths: list[Path]) -> tuple[set[str], Decimal, list[str]]:
    """Count submitted cases and conservative cost across referenced journals."""
    submitted: set[str] = set()
    incurred = Decimal(0)
    documents = [path.read_bytes() for path in paths]
    hashes = [hashlib.sha256(document).hexdigest() for document in documents]
    if len(set(hashes)) != len(hashes):
        raise ValueError("Duplicate prior journals")
    for document in documents:
        prior = json.loads(document)
        if (
            prior.get("fixtures", {}).get("catalog") != CASES_SHA256
            or prior.get("fixtures", {}).get("histories") != HISTORIES_SHA256
        ):
            raise ValueError("Prior journal does not match the fixture versions")
        if prior.get("status") not in {"completed", "uncertain", "submitted"}:
            raise ValueError("Cannot resume a prior run with unknown cost or provider limit exceeded")
        if not set(prior.get("prior_journal_digests", [])) <= set(hashes):
            raise ValueError("Include all earlier journals in the budget history")
        for details in prior["providers"].values():
            submitted.update(row["id"] for row in details["rows"])
        pending = prior.get("stopped_at") or prior.get("pending")
        if pending:
            submitted.add(pending["case"])
        incurred += Decimal(_costs(prior)["incurred_upper_usd"])
    return submitted, incurred, hashes


class _ObservedTransport(httpx.AsyncBaseTransport):
    """Record only bounded diagnostic codes and usage, never response text."""

    def __init__(self, delegate: httpx.AsyncBaseTransport | None) -> None:
        self._owned = delegate is None
        self._delegate = delegate or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        self.diagnostic: dict[str, Any] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        try:
            response = await self._delegate.handle_async_request(request)
            payload = await response.aread()
        except httpx.TimeoutException:
            self.diagnostic["transport"] = "timeout"
            raise
        except httpx.HTTPError:
            self.diagnostic["transport"] = "http_transport_error"
            raise
        self.diagnostic["http_status"] = response.status_code
        try:
            body = json.loads(payload)
            if isinstance(body, dict):
                status = body.get("status")
                if status in {"completed", "incomplete", "failed"}:
                    self.diagnostic["provider_status"] = status
                incomplete = body.get("incomplete_details")
                if isinstance(incomplete, dict) and incomplete.get("reason") in {"max_output_tokens", "content_filter"}:
                    self.diagnostic["reason"] = incomplete["reason"]
                error = body.get("error")
                if isinstance(error, dict) and error.get("code") in {
                    "invalid_api_key",
                    "model_not_found",
                    "insufficient_quota",
                    "rate_limit_exceeded",
                    "invalid_request_error",
                    "unsupported_value",
                    "context_length_exceeded",
                }:
                    self.diagnostic["provider_code"] = error["code"]
                usage = body.get("usage")
                if isinstance(usage, dict) and all(
                    type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens")
                ):
                    self.diagnostic["usage"] = {k: usage[k] for k in ("input_tokens", "output_tokens")}
        except (TypeError, ValueError):
            pass
        headers = dict(response.headers)
        headers.pop("content-encoding", None)
        headers.pop("content-length", None)
        return httpx.Response(response.status_code, headers=headers, content=payload, request=request)

    async def aclose(self) -> None:
        if self._owned:
            await self._delegate.aclose()


def _outcome(case: dict[str, Any], result: Any, elapsed: float) -> dict[str, Any]:
    actual = [result.intent, result.decision, result.format]
    expected = case["expected"]
    item_name = case.get("expected_candidate") or (case["candidates"][0]["name"] if expected[1] == "selected" else None)
    expected_item = uuid5(NAMESPACE_DNS, f"comparison:{item_name}") if item_name is not None else None
    checks = {
        "intent": actual[0] == expected[0],
    }
    if case["kind"] != "intent_only":
        checks.update(
            decision=actual[1] == expected[1],
            format=actual[2] == expected[2],
            candidate=result.offering_id == expected_item,
        )
    return {
        "id": case["id"],
        "kind": case["kind"],
        "expected": expected,
        "actual": actual,
        "checks": checks,
        "joint_correct": all(checks.values()),
        "latency_ms": round(elapsed * 1000, 3),
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


async def evaluate(
    *,
    live: bool = False,
    limit: int = 61,
    offset: int = 0,
    budget: Decimal | None = None,
    jev_key: str | None = None,
    openai_key: str | None = None,
    journal: Path | None = None,
    prior_journals: list[Path] | None = None,
    jev_transport: httpx.AsyncBaseTransport | None = None,
    openai_transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    fixture = cases()
    if offset < 0 or not 1 <= limit <= len(fixture) - offset:
        raise ValueError("Invalid number of cases")
    selected = fixture[offset : offset + limit]
    report: dict[str, Any] = {
        "fixtures": {
            "catalog": CASES_SHA256,
            "histories": HISTORIES_SHA256,
            "intents": "checked_in_jev_intent_ptbr_v1",
        },
        "synthetic": True,
        "independent_holdout": False,
        "scope": "single_messages_and_concatenated_synthetic_histories_not_conversation_memory_or_worker",
        "model_aliases": {"jev": JEV_MODEL, "openai": OPENAI_MODEL},
        "provider_settings": {
            "openai": {
                "reasoning_effort": OPENAI_REASONING_EFFORT,
                "max_output_tokens": MAX_OPENAI_OUTPUT_TOKENS,
                "service_tier": "default",
                "store": False,
            },
            "jev": {"model": JEV_MODEL},
        },
        "pricing_source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
        "providers": {"jev": {"rows": []}, "openai": {"rows": []}},
        "status": "not_run",
        "offset": offset,
    }
    if not live:
        report["planned_cases"] = [case["id"] for case in selected]
        return report
    total = reserve(len(selected), budget, jev_key, openai_key)
    if journal is None:
        raise ValueError("Live evaluation requires a new exclusive journal path")
    previous = prior_journals or []
    if offset and not previous:
        raise ValueError("A continuation requires prior journal(s)")
    submitted, prior_cost, previous_hashes = _previous(previous)
    if any(case["id"] in submitted for case in selected):
        raise ValueError("A selected case was already submitted in a prior journal")
    assert budget is not None
    if total + prior_cost > budget:
        raise ValueError("Total budget must also cover known and uncertain prior usage")
    # Exclusive file creation makes accidental reruns using the same journal
    # fail before network IO; prior uncertain billing is never retried.
    fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        report.update(
            status="submitted",
            reserved_max_usd=str(total),
            budget_usd=str(budget),
            prior_incurred_upper_usd=str(prior_cost),
            prior_journal_count=len(previous),
            prior_journal_digests=previous_hashes,
        )
        _journal_write(stream, report)
        assert jev_key and openai_key
        for case in selected:
            candidates = [
                {**candidate, "id": str(uuid5(NAMESPACE_DNS, f"comparison:{candidate['name']}"))}
                for candidate in case["candidates"]
            ]
            for name in ("jev", "openai"):
                observer = _ObservedTransport(jev_transport if name == "jev" else openai_transport)
                provider = (
                    JevIntentProvider(SecretStr(jev_key), JEV_MODEL, transport=observer)
                    if name == "jev"
                    else OpenAICatalogIntentProvider(
                        SecretStr(openai_key),
                        OPENAI_MODEL,
                        transport=observer,
                        reasoning_effort=OPENAI_REASONING_EFFORT,
                        max_output_tokens=MAX_OPENAI_OUTPUT_TOKENS,
                    )
                )
                report["pending"] = {"provider": name, "case": case["id"]}
                _journal_write(stream, report)
                start = time.perf_counter()
                try:
                    result = await provider.interpret(case["message"], candidates, ["photo", "story"], uuid4())
                except (CatalogInterpretationError, JevIntentError) as exc:
                    report.update(status="uncertain", stopped_at=report.pop("pending"))
                    # Exceptions are code-only by adapter contract; provider response
                    # bodies and messages never enter the journal or report.
                    report["last_error"] = {
                        "code": exc.code if isinstance(exc, CatalogInterpretationError) else str(exc),
                        **observer.diagnostic,
                    }
                    report["costs"] = _costs(report)
                    _journal_write(stream, report)
                    return report
                report["providers"][name]["rows"].append(_outcome(case, result, time.perf_counter() - start))
                report.pop("pending")
                # If a provider reports usage above a documented reserve, do
                # not submit further calls even if the observed result is valid.
                if result.input_tokens > MAX_INPUT_TOKENS or (
                    name == "openai" and result.output_tokens > MAX_OPENAI_OUTPUT_TOKENS
                ):
                    report.update(status="provider_limit_exceeded", stopped_at={"provider": name, "case": case["id"]})
                    report["costs"] = _costs(report)
                    _journal_write(stream, report)
                    return report
                _journal_write(stream, report)
        for name, details in report["providers"].items():
            rows = details["rows"]
            incoming = sum(row["input_tokens"] for row in rows)
            outgoing = sum(row["output_tokens"] for row in rows)
            details.update(
                cases=len(rows),
                correct=sum(row["joint_correct"] for row in rows),
                input_tokens=incoming,
                output_tokens=outgoing,
                estimated_max_usd=str(
                    (incoming * JEV_INPUT if name == "jev" else incoming * OPENAI_INPUT + outgoing * OPENAI_OUTPUT)
                    / MILLION
                ),
            )
        report["status"] = "completed"
        report["costs"] = _costs(report)
        _journal_write(stream, report)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-usd")
    parser.add_argument("--max-cases", type=int, default=61)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--prior-journal", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        result = asyncio.run(
            evaluate(
                live=args.live,
                limit=args.max_cases,
                offset=args.offset,
                budget=Decimal(args.max_usd) if args.max_usd else None,
                jev_key=os.getenv("TYPESAFE_API_KEY"),
                openai_key=os.getenv("MEU_BRACO_DIREITO_OPENAI_API_KEY"),
                journal=args.journal,
                prior_journals=args.prior_journal,
            )
        )
    except (ValueError, InvalidOperation, FileExistsError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
