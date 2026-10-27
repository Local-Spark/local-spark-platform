"""Synthetic adapter comparison; tests use only mock HTTP transports."""

import json
from decimal import Decimal

import httpx
import pytest

from scripts import evaluate_intent_comparison as evals


def choice(selected, options):
    return {
        "type": "choice",
        "choice": selected,
        "confidence": 1.0,
        "probabilities": {key: float(key == selected) for key in options},
    }


def jev_handler(request):
    data = json.loads(request.content)
    state = json.loads(data["state"])
    case = next(item for item in evals.cases() if item["message"] == state["message"])
    intent, decision, fmt = case["expected"]
    choices = data["questions"]["offering"]["criteria"]
    formats = data["questions"]["format"]["criteria"]
    item_name = case.get("expected_candidate") or (case["candidates"][0]["name"] if decision == "selected" else None)
    index = next((i for i, candidate in enumerate(case["candidates"]) if candidate["name"] == item_name), None)
    offering = f"item_{index}" if index is not None else "clarify"
    format_choice = "unsupported" if case["id"] == "video" else (fmt or "unspecified")
    return httpx.Response(
        200,
        json={
            "model": evals.JEV_MODEL,
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "answers": {
                "intent": choice(intent, data["questions"]["intent"]["criteria"]),
                "offering": choice(offering, choices),
                "format": choice(format_choice, formats),
            },
        },
    )


def openai_handler(request):
    data = json.loads(request.content)
    assert data["model"] == evals.OPENAI_MODEL and data["store"] is False and data["tools"] == []
    assert data["reasoning"] == {"effort": "none"} and data["max_output_tokens"] == 1024
    state = json.loads(data["input"][1]["content"])
    case = next(item for item in evals.cases() if item["message"] == state["message"])
    intent, decision, fmt = case["expected"]
    item_name = case.get("expected_candidate") or (case["candidates"][0]["name"] if decision == "selected" else None)
    item = next((candidate["id"] for candidate in state["candidates"] if candidate["name"] == item_name), None)
    draft = {"intent": intent, "decision": decision or "clarify", "offering_id": item, "format": fmt}
    return httpx.Response(
        200,
        json={
            "status": "completed",
            "usage": {"input_tokens": 200, "output_tokens": 30},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(draft)}]}],
        },
    )


async def test_offline_does_not_access_network_or_require_credentials(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_a, **_k: pytest.fail("offline must not access network"))
    report = await evals.evaluate()
    assert report["status"] == "not_run" and len(report["planned_cases"]) == 61
    assert report["provider_settings"]["openai"] == {
        "reasoning_effort": "none",
        "max_output_tokens": 1024,
        "service_tier": "default",
        "store": False,
    }
    assert not report["independent_holdout"] and "not_conversation" in report["scope"]


@pytest.mark.parametrize(
    "budget,jev,openai",
    [
        (None, "x", "y"),
        (Decimal("NaN"), "x", "y"),
        (Decimal("1.01"), "x", "y"),
        (Decimal("0.001"), "x", "y"),
        (Decimal("1"), None, "y"),
        (Decimal("1"), "x", None),
    ],
)
async def test_no_call_without_safe_budget_and_both_keys(budget, jev, openai, tmp_path):
    with pytest.raises(ValueError):
        await evals.evaluate(live=True, budget=budget, jev_key=jev, openai_key=openai, journal=tmp_path / "journal")
    assert not (tmp_path / "journal").exists()


async def test_mocked_comparison_uses_same_cases_and_tracks_cost_without_content(tmp_path):
    journal = tmp_path / "journal.json"
    report = await evals.evaluate(
        live=True,
        limit=11,
        budget=Decimal("1"),
        jev_key="synthetic-jev-key",
        openai_key="synthetic-openai-key",
        journal=journal,
        jev_transport=httpx.MockTransport(jev_handler),
        openai_transport=httpx.MockTransport(openai_handler),
    )
    assert report["status"] == "completed" and Decimal(report["reserved_max_usd"]) == Decimal("0.1325632")
    assert all(item["cases"] == item["correct"] == 11 for item in report["providers"].values())
    assert Decimal(report["providers"]["jev"]["estimated_max_usd"]) == Decimal("0.0000462")
    assert Decimal(report["providers"]["openai"]["estimated_max_usd"]) == Decimal("0.000484")
    saved = journal.read_text()
    assert "synthetic-jev-key" not in saved and "synthetic-openai-key" not in saved
    assert "Dog da Casa" not in saved and "Unhas em gel" not in saved
    assert json.loads(saved)["status"] == "completed"
    with pytest.raises(FileExistsError):
        await evals.evaluate(live=True, budget=Decimal("1"), jev_key="x", openai_key="y", journal=journal)


async def test_uncertain_result_stops_all_providers_and_preserves_pending_effect(tmp_path):
    calls = []

    def timeout(request):
        calls.append(request.url.host)
        raise httpx.ReadTimeout("private provider response", request=request)

    journal = tmp_path / "journal"
    report = await evals.evaluate(
        live=True,
        budget=Decimal("1"),
        jev_key="fake",
        openai_key="fake",
        journal=journal,
        jev_transport=httpx.MockTransport(timeout),
        openai_transport=httpx.MockTransport(openai_handler),
    )
    assert report["status"] == "uncertain" and calls == ["api.typesafe.ai"]
    assert report["stopped_at"] == {"provider": "jev", "case": "foto"}
    assert "private provider response" not in journal.read_text()


async def test_live_rejects_missing_journal_and_tampered_fixture(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="journal"):
        await evals.evaluate(live=True, budget=Decimal("1"), jev_key="a", openai_key="b")
    modified = tmp_path / "modified.json"
    modified.write_text("{}")
    monkeypatch.setattr(evals, "CASES", modified)
    with pytest.raises(ValueError, match="checksum"):
        await evals.evaluate()


async def test_prior_journal_prevents_any_case_replay_and_counts_uncertain_cost(tmp_path):
    prior, current = tmp_path / "prior.json", tmp_path / "current.json"

    def declined(_request):
        return httpx.Response(400, json={"error": {"code": "unsupported_value", "message": "PRIVATE RESPONSE"}})

    first = await evals.evaluate(
        live=True,
        limit=2,
        budget=Decimal("1"),
        jev_key="fake",
        openai_key="fake",
        journal=prior,
        jev_transport=httpx.MockTransport(jev_handler),
        openai_transport=httpx.MockTransport(declined),
    )
    assert first["status"] == "uncertain" and first["stopped_at"]["case"] == "foto"
    assert first["last_error"] == {
        "code": "CATALOG_INTERPRETER_UNCERTAIN",
        "http_status": 400,
        "provider_code": "unsupported_value",
    }
    assert Decimal(first["costs"]["known_estimated_upper_usd"]) == Decimal("0.0000042")
    assert Decimal(first["costs"]["uncertain_reserved_usd"]) == evals.OPENAI_RESERVE
    assert "PRIVATE RESPONSE" not in prior.read_text()
    with pytest.raises(ValueError, match="already submitted"):
        await evals.evaluate(
            live=True,
            limit=1,
            budget=Decimal("1"),
            jev_key="fake",
            openai_key="fake",
            journal=current,
            prior_journals=[prior],
        )
    assert not current.exists()
    second = await evals.evaluate(
        live=True,
        offset=1,
        limit=1,
        budget=Decimal("1"),
        jev_key="fake",
        openai_key="fake",
        journal=current,
        prior_journals=[prior],
        jev_transport=httpx.MockTransport(jev_handler),
        openai_transport=httpx.MockTransport(openai_handler),
    )
    assert second["status"] == "completed" and second["providers"]["jev"]["rows"][0]["id"] == "story"
    assert Decimal(second["prior_incurred_upper_usd"]) == Decimal(first["costs"]["incurred_upper_usd"])
    with pytest.raises(ValueError, match="all earlier journals"):
        await evals.evaluate(
            live=True,
            offset=2,
            limit=1,
            budget=Decimal("1"),
            jev_key="fake",
            openai_key="fake",
            journal=tmp_path / "third.json",
            prior_journals=[current],
        )


async def test_incomplete_200_records_only_safe_reason_and_reported_cost(tmp_path):
    def incomplete(_request):
        return httpx.Response(
            200,
            json={
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "usage": {"input_tokens": 200, "output_tokens": 320},
                "message": "PRIVATE",
            },
        )

    report = await evals.evaluate(
        live=True,
        limit=1,
        budget=Decimal("1"),
        jev_key="fake",
        openai_key="fake",
        journal=tmp_path / "case.json",
        jev_transport=httpx.MockTransport(jev_handler),
        openai_transport=httpx.MockTransport(incomplete),
    )
    assert report["last_error"]["reason"] == "max_output_tokens"
    assert report["last_error"]["code"] == "CATALOG_INTERPRETER_INVALID"
    assert report["last_error"]["usage"] == {"input_tokens": 200, "output_tokens": 320}
    assert Decimal(report["costs"]["uncertain_reserved_usd"]) == 0
    assert Decimal(report["costs"]["known_estimated_upper_usd"]) == Decimal("0.0002077")
    assert "PRIVATE" not in json.dumps(report)


def test_previous_uncertain_reservations_use_their_historical_cap_and_default_legacy_to_320(tmp_path):
    base = {
        "fixtures": {"catalog": evals.CASES_SHA256, "histories": evals.HISTORIES_SHA256},
        "providers": {"jev": {"rows": []}, "openai": {"rows": []}},
        "status": "uncertain",
        "stopped_at": {"provider": "openai", "case": "foto"},
    }
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps(base))
    new = tmp_path / "new.json"
    new.write_text(
        json.dumps(
            {
                **base,
                "stopped_at": {"provider": "openai", "case": "story"},
                "provider_settings": {"openai": {"max_output_tokens": 1024}},
            }
        )
    )
    legacy_reserve = (evals.MAX_INPUT_TOKENS * evals.OPENAI_INPUT + 320 * evals.OPENAI_OUTPUT) / evals.MILLION
    submitted, prior_cost, _ = evals._previous([legacy, new])
    assert submitted == {"foto", "story"}
    assert prior_cost == legacy_reserve + evals.OPENAI_RESERVE
    assert legacy_reserve < evals.OPENAI_RESERVE


@pytest.mark.parametrize("cap", [0, True, "320", 1025])
def test_unknown_or_invalid_historical_cap_never_underestimates_cost(cap):
    report = {
        "providers": {"jev": {"rows": []}, "openai": {"rows": []}},
        "status": "uncertain",
        "stopped_at": {"provider": "openai", "case": "foto"},
        "provider_settings": {"openai": {"max_output_tokens": cap}},
    }
    with pytest.raises(ValueError, match="historical"):
        evals._costs(report)


def test_cli_offset_offline_and_live_continuation_requires_prior_journal(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys, "argv", ["compare", "--offset", "2", "--max-cases", "2"])
    evals.main()
    assert json.loads(capsys.readouterr().out)["planned_cases"] == ["video", "price"]
    monkeypatch.setenv("TYPESAFE_API_KEY", "fake")
    monkeypatch.setenv("MEU_BRACO_DIREITO_OPENAI_API_KEY", "fake")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compare",
            "--live",
            "--offset",
            "2",
            "--max-cases",
            "2",
            "--max-usd",
            "1",
            "--journal",
            str(tmp_path / "out"),
        ],
    )
    with pytest.raises(SystemExit):
        evals.main()
    assert not (tmp_path / "out").exists()
