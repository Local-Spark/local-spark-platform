"""Offline safety and scoring tests for the synthetic Jev benchmark."""

import json
from decimal import Decimal

import httpx
import pytest

from scripts import evaluate_jev_intent as benchmark


def answer(choice, confidence=0.9, tokens=100, *, model="jev-1.14.0"):
    probabilities = {label: 0.1 for label in benchmark.LABELS}
    probabilities[choice] = 0.6
    return {
        "model": model,
        "answers": {
            "intent": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": probabilities}
        },
        "usage": {"input_tokens": tokens, "output_tokens": 40},
    }


async def test_offline_never_opens_network_and_uses_real_baseline(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("Offline evaluation cannot initialize an HTTP client")

    monkeypatch.setattr(benchmark.httpx, "AsyncClient", fail)
    report = await benchmark.evaluate()
    assert report["jev"]["status"] == "not_run"
    assert report["baseline"]["cases"] == 50
    assert report["baseline"]["answered"] < 50
    assert report["baseline_cost_usd"] is None
    assert report["release_decision"].startswith("blocked_")
    assert "mensagem" not in json.dumps(report, ensure_ascii=False)
    negative = next(row for row in report["baseline_cases"] if row["id"] == "other-10")
    assert negative["expected"] == "other"


def test_fixture_is_balanced_versioned_and_refuses_modified_data(tmp_path, monkeypatch):
    dataset, cases = benchmark.load_cases()
    assert dataset["synthetic"] is True and len(cases) == 50
    assert {item["expected"] for item in cases[:5]} == set(benchmark.LABELS)
    assert len(benchmark.load_cases("development")[1]) == 40
    assert len(benchmark.load_cases("holdout")[1]) == 10
    modified = tmp_path / "other.json"
    modified.write_text(json.dumps(dataset))
    monkeypatch.setattr(benchmark, "CASES", modified)
    with pytest.raises(ValueError, match="hash mismatch"):
        benchmark.load_cases()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"budget": None, "api_key": "synthetic-key"}, "positive explicit"),
        ({"budget": Decimal("0.10"), "api_key": None}, "TYPESAFE_API_KEY"),
        ({"budget": Decimal("0.0001"), "api_key": "synthetic-key"}, "conservative maximum"),
        ({"budget": Decimal("0.10"), "api_key": "synthetic-key", "model": "jev-latest"}, "pinned"),
    ],
)
async def test_paid_calls_require_explicit_credentials_budget_and_pinned_model(kwargs, message, monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("HTTP client must not be created before budget validation")

    monkeypatch.setattr(benchmark.httpx, "AsyncClient", fail)
    with pytest.raises(ValueError, match=message):
        await benchmark.evaluate(live=True, **kwargs)


async def test_mock_transport_compares_pinned_decisions_cost_abstention_and_calibration():
    dataset, cases = benchmark.load_cases()
    expected_by_message = {case["message"]: case["expected"] for case in cases}
    calls = []

    def handler(request):
        body = json.loads(request.content)
        assert request.url == httpx.URL(benchmark.ENDPOINT)
        assert request.headers["authorization"] == "Bearer synthetic-key"
        assert body["model"] == "jev-1.14.0"
        assert set(body["questions"]["intent"]["criteria"]) == set(benchmark.LABELS)
        calls.append(body["state"])
        choice = expected_by_message[body["state"]]
        return httpx.Response(200, json=answer(choice, confidence=0.2 if len(calls) == 1 else 0.9))

    report = await benchmark.evaluate(
        live=True, budget=Decimal("0.10"), api_key="synthetic-key", transport=httpx.MockTransport(handler)
    )
    result = report["jev"]
    assert dataset["synthetic"] and len(calls) == 5
    assert result["summary"]["coverage"] == 0.8
    assert result["summary"]["accuracy_answered"] == 1
    assert result["summary"]["reasons"] == {"low_confidence": 1, "classified": 4}
    assert result["calibration_by_selected_probability"][0]["average_probability"] == 0.6
    assert result["known_input_tokens"] == 500
    assert Decimal(result["known_cost_usd"]) == Decimal("0.000021")
    assert result["uncertain_billing_calls"] == 0
    assert not result["threshold_calibrated"]
    assert "synthetic-key" not in json.dumps(report)
    assert all(message not in json.dumps(report, ensure_ascii=False) for message in calls)


async def test_provider_errors_are_abstentions_and_spend_may_be_unknown():
    count = 0

    def handler(request):
        nonlocal count
        count += 1
        if count == 1:
            return httpx.Response(429, text="sensitive provider response must not leak")
        if count == 2:
            raise httpx.ReadTimeout("unknown outcome", request=request)
        if count == 3:
            result = answer("price")
            result["answers"]["intent"]["confidence"] = 2
            return httpx.Response(200, json=result)
        return httpx.Response(200, json={"model": "unexpected"})

    report = await benchmark.evaluate(
        live=True, max_cases=4, budget=Decimal("0.10"), api_key="synthetic-key", transport=httpx.MockTransport(handler)
    )
    result = report["jev"]
    assert count == 4 and result["summary"]["answered"] == 0
    assert result["summary"]["reasons"] == {"provider_http_error": 1, "provider_error": 1, "invalid_response": 2}
    assert result["uncertain_billing_calls"] == 3
    assert result["known_input_tokens"] == 100
    assert Decimal(result["estimated_upper_cost_usd"]) == benchmark.RATE * 100 + benchmark.MAX_CALL_USD * 3
    assert "sensitive provider response" not in json.dumps(report)


async def test_provider_exceeding_documented_context_limit_stops_remaining_calls():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=answer("price", tokens=benchmark.MAX_INPUT_TOKENS + 1))

    report = await benchmark.evaluate(
        live=True, budget=Decimal("0.10"), api_key="synthetic-key", transport=httpx.MockTransport(handler)
    )
    assert len(calls) == 1
    assert report["jev"]["status"] == "stopped_provider_limit"
    assert report["jev"]["unrun_cases"] == 4
    assert report["jev"]["known_input_tokens"] == benchmark.MAX_INPUT_TOKENS + 1


def test_probability_parser_rejects_invalid_and_mismatched_outputs():
    good = answer("price")
    assert benchmark.parse_answer(good, "jev-1.14.0", 0.5) == ("price", "price", 0.9, 0.6)
    assert benchmark.parse_answer(good, "jev-1.14.0", 0.95)[0] is None
    good["answers"]["intent"]["probabilities"]["price"] = 0.01
    with pytest.raises(ValueError, match="distribution"):
        benchmark.parse_answer(good, "jev-1.14.0", 0.5)
    with pytest.raises(ValueError, match="model"):
        benchmark.parse_answer(answer("price", model="jev-1.13.0"), "jev-1.14.0", 0.5)


async def test_malformed_probabilities_keep_paid_usage_and_report():
    payload = answer("price", tokens=123)
    payload["answers"]["intent"]["probabilities"] = list(benchmark.LABELS)
    report = await benchmark.evaluate(
        live=True,
        max_cases=1,
        budget=Decimal("0.10"),
        api_key="synthetic-key",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)),
    )
    result = report["jev"]
    assert result["summary"]["reasons"] == {"invalid_response": 1}
    assert result["known_input_tokens"] == 123 and result["uncertain_billing_calls"] == 0
    assert Decimal(result["known_cost_usd"]) == benchmark.RATE * 123
