"""Offline tests for the synthetic motion batch; never call providers or render."""

import json
import threading
import time
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.evals import motion_batch_eval as batch
from scripts.evals import motion_eval as single


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(single.json_bytes(value))


@pytest.fixture
def manifest(tmp_path):
    """Three distinct requests, all synthetic and backed by hash-checked inputs."""
    video = tmp_path / "synthetic.mp4"
    video.write_bytes(b"fixture-video")
    notice = tmp_path / "LICENSE"
    notice.write_text("Fixture license", encoding="utf-8")
    cases = []
    for i in range(3):
        body = single.json_bytes(
            {
                "model": "gpt-6.1-sol",
                "store": False,
                "reasoning": {"effort": "high"},
                "max_output_tokens": 32000,
                "text": {"format": {"type": "json_schema", "strict": True}},
                "input": f"fixture request {i}",
            }
        )
        request = tmp_path / f"request-{i}.json"
        request.write_bytes(body)
        config = {
            "version": 1,
            "synthetic_fixture": True,
            "id": f"fixture-{i}",
            "body_path": str(request),
            "body_sha256": single.digest(body),
            "width": 720,
            "height": 1280,
            "fps": 30,
            "duration_ms": 1000,
            "assets": [
                {
                    "id": "video.mp4",
                    "path": str(video),
                    "sha256": single.digest(video.read_bytes()),
                    "mime": "video/mp4",
                }
            ],
            "reference": {"path": str(video), "sha256": single.digest(video.read_bytes())},
            "tools": {k: "/synthetic/tool" for k in ("node", "playwright", "chromium", "ffmpeg", "ffprobe")},
            "reservation_usd": "0.75",
            "rights_files": [str(notice)],
        }
        case = tmp_path / f"case-{i}.json"
        _write_json(case, config)
        cases.append({"label": f"Caso {i}", "case_path": str(case)})
    refs = []
    for i in range(2):
        path = tmp_path / f"reference-{i}.mp4"
        path.write_bytes(f"reference {i}".encode())
        refs.append(
            {
                "label": "V2 <script>alert(1)</script>" if i == 0 else "Intensa",
                "path": str(path),
                "sha256": single.digest(path.read_bytes()),
            }
        )
    result = tmp_path / "manifest.json"
    _write_json(result, {"version": 1, "id": "synthetic-batch", "cases": cases, "references": refs})
    return result


def test_budget_cap_and_distinct_requests_checked_before_dispatch(manifest, monkeypatch):
    monkeypatch.setattr(single, "api_key", lambda: pytest.fail("credentials must not be read"))
    monkeypatch.setattr(single, "execute", lambda *a, **k: pytest.fail("must not dispatch"))
    with pytest.raises((ValueError, TypeError), match="budget"):
        batch.plan_manifest(manifest, Decimal("2.24"))
    valid = batch.plan_manifest(manifest, Decimal("2.25"))
    assert Decimal(valid["total_reservation_usd"]) == Decimal("2.25")
    assert len({c["request_sha256"] for c in valid["cases"]}) == 3


def test_duplicate_request_hash_fails_before_any_effect(manifest, monkeypatch):
    doc = json.loads(manifest.read_bytes())
    first = json.loads(Path(doc["cases"][0]["case_path"]).read_bytes())
    second_path = Path(doc["cases"][1]["case_path"])
    second = json.loads(second_path.read_bytes())
    second["body_path"], second["body_sha256"] = first["body_path"], first["body_sha256"]
    _write_json(second_path, second)
    monkeypatch.setattr(single, "execute", lambda *a, **k: pytest.fail("must not dispatch"))
    with pytest.raises((ValueError, TypeError), match="duplicate"):
        batch.plan_manifest(manifest, Decimal("2.25"))


def test_changed_reference_after_preflight_fails_before_dispatch(manifest, tmp_path):
    plan = batch.plan_manifest(manifest, Decimal("2.25"))
    Path(plan["references"][0]["path"]).write_bytes(b"changed-after-planning")
    calls = []

    def child(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("tampered reference must prevent all dispatch")

    with pytest.raises((ValueError, OSError)):
        batch.run_batch(plan, tmp_path / "batches", child)
    assert calls == []


def _successful_run(runs: Path, name: str) -> Path:
    run = runs / name
    run.mkdir(parents=True, mode=0o700)
    render = run / "render"
    render.mkdir()
    (render / "render.mp4").write_bytes(b"local-mp4")
    (render / "trace.json").write_text("{}", encoding="utf-8")
    cost = {"estimated_usd": "0.12", "reservation_usd": "0.75", "mode": "paid", "invoice_verified": False}
    _write_json(run / "cost.json", cost)
    _write_json(run / "summary.json", {**cost, "state": "completed"})
    (run / "report.html").write_text("local", encoding="utf-8")
    return run


def test_frozen_reference_escaped_labels_and_uncertain_outcome(manifest, tmp_path, monkeypatch):
    plan = batch.plan_manifest(manifest, Decimal("2.25"))
    original = Path(plan["references"][0]["path"])
    gate = threading.Lock()
    called = []
    monkeypatch.setattr(single, "run_renderer", lambda *_: None)

    def child(case_path, reserve, *, runs, renderer):
        assert reserve == Decimal("0.75")
        number = Path(case_path).stem.split("-")[-1]
        with gate:
            called.append(number)
            # The comparison bytes must already exist inside the batch before a child starts.
            frozen = list((runs.parent / "assets").rglob("*"))
            assert any(p.is_file() and p.read_bytes() == b"reference 0" for p in frozen)
            original.write_bytes(b"mutated-after-freeze")
        if number == "1":
            run = runs / "uncertain-fixture"
            run.mkdir(parents=True)
            renderer("/unused", run / "preflight.json", None)
            (run / "ledger.jsonl").write_text('{"state":"reserved"}\n{"state":"uncertain"}\n', encoding="utf-8")
            raise single.EvalError("request_uncertain_no_retry")
        return _successful_run(runs, "success-" + number)

    round_dir = batch.run_batch(plan, tmp_path / "batches", child)
    assert sorted(called) == ["1", "2", "3"]
    result = json.loads((round_dir / "results.json").read_bytes())
    assert sorted(x["state"] for x in result["results"]) == ["completed", "completed", "uncertain"]
    uncertain = next(x for x in result["results"] if x["state"] == "uncertain")
    assert uncertain["estimated_usd"] is None
    assert result["estimated_total_usd"] is None
    assert uncertain["run"] is not None
    assert any(p.is_file() and p.read_bytes() == b"reference 0" for p in (round_dir / "assets").rglob("*"))
    page = (round_dir / "report.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert page.count("<video ") >= 4


def test_parallel_workers_serialize_renderer_calls(manifest, tmp_path, monkeypatch):
    plan = batch.plan_manifest(manifest, Decimal("2.25"))
    guard = threading.Lock()
    both_started = threading.Barrier(2, timeout=3)
    state = {"workers": 0, "max_workers": 0, "renderers": 0, "max_renderers": 0, "calls": 0}

    def mock_renderer(_node, _config, _output):
        with guard:
            state["renderers"] += 1
            state["max_renderers"] = max(state["max_renderers"], state["renderers"])
            state["calls"] += 1
        time.sleep(0.04)
        with guard:
            state["renderers"] -= 1

    monkeypatch.setattr(single, "run_renderer", mock_renderer)

    def child(case_path, _reserve, *, runs, renderer):
        with guard:
            state["workers"] += 1
            state["max_workers"] = max(state["max_workers"], state["workers"])
            should_wait = state["max_workers"] <= 2 and state["calls"] == 0
        if should_wait:
            both_started.wait()
        name = Path(case_path).stem
        run = _successful_run(runs, name)
        renderer("/unused", run / "preflight.json", None)
        renderer("/unused", run / "render-config.json", run / "render")
        with guard:
            state["workers"] -= 1
        return run

    result = batch.run_batch(plan, tmp_path / "batches", child)
    assert (result / "report.html").is_file()
    assert state["max_workers"] == 2
    assert state["max_renderers"] == 1
    assert state["calls"] == 6


@pytest.mark.parametrize("bad_budget", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_nonpositive_and_nonfinite_budget_rejected(manifest, bad_budget):
    with pytest.raises((ValueError, TypeError)):
        batch.plan_manifest(manifest, bad_budget)


def test_more_than_three_cases_rejected(manifest):
    doc = json.loads(manifest.read_bytes())
    doc["cases"].append(doc["cases"][0])
    _write_json(manifest, doc)
    with pytest.raises((ValueError, TypeError)):
        batch.plan_manifest(manifest, Decimal("3.00"))


def test_execute_cli_without_explicit_budget_stops_before_loading_or_dispatch(manifest, monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys, "argv", ["motion_batch_eval.py", "--manifest", str(manifest), "--execute"])
    monkeypatch.setattr(batch, "plan_manifest", lambda *_: pytest.fail("budget must be checked first"))
    monkeypatch.setattr(single, "execute", lambda *_a, **_k: pytest.fail("must not dispatch"))
    assert batch.main() == 1
    assert "explicit_budget_required" in capsys.readouterr().err


def test_second_batch_never_resends_registered_requests_after_uncertain(manifest, tmp_path, monkeypatch):
    plan = batch.plan_manifest(manifest, Decimal("2.25"))
    root = tmp_path / "batches"
    calls = []
    guard = threading.Lock()
    monkeypatch.setattr(single, "run_renderer", lambda *_: None)

    def child(case_path, _reserve, *, runs, renderer):
        with guard:
            calls.append(str(case_path))
        name = Path(case_path).stem
        if name == "case-1":
            run = runs / "uncertain"
            run.mkdir(parents=True)
            renderer("/unused", run / "preflight.json", None)
            (run / "ledger.jsonl").write_text('{"state":"reserved"}\n{"state":"uncertain"}\n', encoding="utf-8")
            raise single.EvalError("request_uncertain_no_retry")
        return _successful_run(runs, name)

    first = batch.run_batch(plan, root, child)
    result = json.loads((first / "results.json").read_bytes())
    assert any(item["state"] == "uncertain" for item in result["results"])
    assert len(calls) == 3
    with pytest.raises(single.EvalError, match="request_already_registered"):
        batch.run_batch(plan, root, child)
    assert len(calls) == 3
    assert len(list((root / "requests").glob("*.json"))) == 3


def test_previous_single_request_is_not_resent_by_batch(manifest, tmp_path, monkeypatch):
    plan = batch.plan_manifest(manifest, Decimal("2.25"))
    single_runs = tmp_path / "prior-single-runs"
    single_runs.mkdir()
    digest = plan["cases"][0]["request_sha256"]
    _write_json(single_runs / f"request-{digest}.json", {"run": str(single_runs / "prior-run")})
    monkeypatch.setattr(single, "RUNS", single_runs)
    calls = []

    def child(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("registered single request must not dispatch")

    with pytest.raises(single.EvalError, match="request_already_registered"):
        batch.run_batch(plan, tmp_path / "batches", child)
    assert calls == []
