"""Synthetic script eval stays offline by default and caps provider calls."""

import csv
import json
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from app.services.editorial_proposals import EditorialProposalService
from scripts import evaluate_editorial as editorial_eval


async def test_script_eval_baseline_and_review_sheet(settings, monkeypatch, tmp_path):
    monkeypatch.setattr(editorial_eval, "Settings", lambda: settings)
    report = await editorial_eval.evaluate(False)
    cases = json.loads(editorial_eval.CASES.read_text())
    assert len(report["cases"]) == len(cases)
    assert report["release_decision"] == "blocked_pending_semantic_review_and_staging"
    assert all(item["baseline_storyboard_valid"] and item["human_review"] == "pending" for item in report["cases"])
    assert sum(item["status"] == "needs_confirmed_fact" for item in report["cases"]) == sum(
        not case["facts"] for case in cases
    )
    assert all(item["safe"] for item in report["cases"])
    case = cases[0]
    data, _ = editorial_eval.inputs(case)
    draft = EditorialProposalService._baseline(data)
    wrong_fact = draft.script[0].model_copy(update={"voiceover": "Resultado garantido."})
    assert not editorial_eval.storyboard_valid(
        draft.model_copy(update={"script": [wrong_fact, *draft.script[1:]]}), case["facts"], None
    )
    target = tmp_path / "review.csv"
    editorial_eval.write_review_sheet(report, target)
    with target.open() as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == len(cases)
    assert all(row["candidate"] == "baseline-v1" and not row["factual_error"] for row in rows)


async def test_script_eval_live_cap_is_explicit_and_never_calls_real_provider(settings, monkeypatch, tmp_path):
    cases = json.loads(editorial_eval.CASES.read_text())
    cases = [cases[0], cases[1], cases[4]]
    corpus = tmp_path / "cases.json"
    corpus.write_text(json.dumps(cases))
    monkeypatch.setattr(editorial_eval, "CASES", corpus)
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    monkeypatch.setattr(editorial_eval, "Settings", lambda: configured)
    fake = AsyncMock()
    fake.propose.side_effect = lambda data, _operation: (EditorialProposalService._baseline(data), 10, 5)
    monkeypatch.setattr(editorial_eval, "OpenAIEditorialProvider", lambda _settings: fake)
    report = await editorial_eval.evaluate(True, 1)
    assert [item["status"] for item in report["cases"]] == ["completed", "not_run_call_cap", "not_run_call_cap"]
    assert report["cases"][0]["storyboard_valid"] is True
    fake.propose.assert_awaited_once()
    target = tmp_path / "review.csv"
    editorial_eval.write_review_sheet(report, target)
    with target.open() as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 4
    assert rows[1]["candidate"] == configured.editorial_ai_model
    with pytest.raises(ValueError, match="call cap"):
        await editorial_eval.evaluate(False, 0)
