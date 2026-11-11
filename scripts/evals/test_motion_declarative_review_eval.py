"""Offline declarative review admission, provenance and correction contracts."""

from __future__ import annotations

import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.schemas.motion import MotionDirection
from app.tests.unit.test_motion_schema import direction
from scripts.evals import motion_declarative_review_eval as declarative
from scripts.evals import motion_eval as base
from scripts.evals import motion_review_eval as review
from scripts.evals.test_motion_review_eval import criticism, fake_extract, put


def fake_cost(proposal: Path) -> None:
    components, operations = [], []
    for identifier, operation, amount in (
        ("direction", "direction:reel", 105925),
        ("jev", "jev:reel", 32),
        ("transcription", "transcription:reel", 900),
        ("rejected", "jev:reel:prior-rejected-1b", 35),
    ):
        bindings = {}
        for name in ("request", "response"):
            path = proposal / "costs" / identifier / f"{name}.body"
            put(path, {"operation": operation, "kind": name})
            bindings[name + ".body"] = {
                "path": str(path.relative_to(proposal)),
                "sha256": base.digest(path.read_bytes()),
            }
        record = {
            "operation_id": identifier,
            "operation": operation,
            "estimated_usd_micros": amount,
            "request_sha256": bindings["request.body"]["sha256"],
            "response_sha256": bindings["response.body"]["sha256"],
        }
        component = {"operation_id": identifier, "operation": operation, "estimated_usd_micros_rounded_up": amount}
        if identifier != "rejected":
            component.update({"record_source": "costs/round-1c-audit.json", "bindings": bindings})
            operations.append(record)
        else:
            component.update({"record_source": "costs/rejected/cost.json", "binding_source": "costs/ledger.jsonl"})
            put(
                proposal / "costs/rejected/cost.json",
                {"estimated_usd_micros_rounded_up": amount, "source_response_sha256": record["response_sha256"]},
            )
            (proposal / "costs/ledger.jsonl").write_bytes(
                base.json_bytes({**record, "event": "completed", "outcome": "rejected"}).replace(b"\n", b"")
            )
        components.append(component)
    put(proposal / "costs/round-1c-audit.json", {"operations": operations})
    put(
        proposal / "computation.json",
        {
            "estimated_usd": "0.106892",
            "estimated_usd_micros_rounded_up": 106892,
            "invoice_verified": False,
            "no_new_paid_effects": True,
            "components": components,
            "audit_source_sha256": base.digest((proposal / "costs/round-1c-audit.json").read_bytes()),
        },
    )


def fake_prepare(_source: Path, trusted: dict) -> dict:
    return copy.deepcopy({key: trusted[key] for key in ("direction", "sources", "fonts")})


def fake_render(run: Path, target: Path, prepared: dict, _tools: dict) -> None:
    data = b"synthetic rendered video:" + base.json_bytes(prepared)
    (target / "render.mp4").write_bytes(data)
    put(target / "trace.json", {"synthetic_fixture": True, "output": {"sha256": base.digest(data)}})
    put(
        target / "audio-preservation.json",
        {
            "baseline_sha256": base.digest((run / declarative.CASE / "v0/render.mp4").read_bytes()),
            "output_sha256": base.digest(data),
            "aac_packets_and_timing_equal": True,
            "pcm_equal": True,
        },
    )


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setenv("MEU_BRACO_DIREITO_OPENAI_API_KEY", "synthetic-key-never-log")
    proposal = tmp_path / "proposal"
    (proposal / "baseline").mkdir(parents=True)
    baseline = b"synthetic historical first version"
    (proposal / "baseline/render.mp4").write_bytes(baseline)
    monkeypatch.setattr(declarative, "BASELINE_SHA", base.digest(baseline))
    monkeypatch.setattr(declarative.bridge, "verify_code", lambda _source: None)
    monkeypatch.setattr(declarative.bridge, "prepare_payload", fake_prepare)
    monkeypatch.setattr(
        declarative.bridge, "verify_tools", lambda tools: {k: {"path": v, "sha256": "f" * 64} for k, v in tools.items()}
    )
    monkeypatch.setattr(declarative.bridge, "video_signature", lambda _video, _tools: {"decoded_fixture": "same"})
    document = MotionDirection.model_validate(direction()).model_dump(mode="json")
    trusted = {"direction": document, "sources": [], "fonts": []}
    put(proposal / "baseline/direction-derived.json", {"direction": document})
    put(proposal / "baseline/render-trace.json", {"synthetic_fixture": True})
    put(proposal / "baseline/prepared.json", fake_prepare(proposal, trusted))
    put(proposal / "replay/trusted-manifest.json", trusted)
    put(proposal / "original/request.body", {"historical": "unmodified original request"})
    put(
        proposal / "context.json",
        {
            "historical_generation_instructions": "original complete instructions",
            "historical_request_context": {"request": "A pausa do café", "references": [], "kit": {"name": "Fictício"}},
            "historical_inputs_unmodified": True,
        },
    )
    fake_cost(proposal)
    put(proposal / "original/diagnosis.json", {"must_not_reach_critic": "expected fontsize 9999"})
    files = [
        {"path": str(p.relative_to(proposal)), "sha256": base.digest(p.read_bytes()), "bytes": p.stat().st_size}
        for p in proposal.rglob("*")
        if p.is_file()
    ]
    put(proposal / "manifest.json", {"files": files, "baseline_sha256": base.digest(baseline), "no_paid_effects": True})
    run = declarative.prepare(
        proposal, runs=tmp_path / "runs", tools={"ffmpeg": "/fixture/ffmpeg"}, extractor=fake_extract
    )
    return run, proposal


def qualify(run: Path) -> None:
    declarative.qualify(run, renderer=fake_render)


def start(run: Path, proposal: Path) -> None:
    put(run / "started.json", {"budget_usd": "1.25", "experiment_id": run.name})
    put(proposal / "declarative-execution.json", {"run": str(run.resolve())})


def correction(run: Path) -> dict:
    doc = review.read_json(run / declarative.CASE / "v0/answer.json")["direction"]
    doc["pages"][0]["captions"][0]["typography"]["font_size"] += 100
    return {"addressed_issue_ids": ["i1"], "changes": "Aumentar a legenda identificada na crítica", "direction": doc}


def provider(run: Path, calls: list[str], *, first: str = "needs_correction", prefer: str = "v1", mode: str = ""):
    def response(request: httpx.Request) -> httpx.Response:
        operation = request.headers["X-Client-Request-Id"]
        binding = review.read_json(run / "operations" / operation / "binding.json")
        kind, version = binding["kind"], binding["version_id"]
        calls.append(f"{kind}:{version}")
        assert review.journal(run)[-1]["state"] == "reserved"
        assert base.digest(request.content) == binding["request_sha256"]
        assert b"expected fontsize 9999" not in request.content
        if mode == "timeout":
            raise httpx.ReadTimeout("synthetic private transport error")
        if mode == "unknown_usage":
            return httpx.Response(200, json={"status": "completed"})
        if kind == "critique":
            value = criticism(
                run,
                version,
                first if version == "v0" else "adequate",
                "v0" if version == "v0" else prefer,
                case_id=declarative.CASE,
                issue_ref="v0:missing" if mode == "wrong_evidence" else None,
            )
        else:
            value = correction(run)
            if mode == "changed_audio":
                value["direction"]["pages"][0]["audio"]["tracks"][0]["gain_mdb"] = -1000
            elif mode == "invalid_units":
                value["direction"]["pages"][0]["captions"][0]["typography"]["font_size"] = "700px"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "usage": {"input_tokens": 100, "output_tokens": 10},
                "output": [{"content": [{"type": "output_text", "text": json.dumps(value)}]}],
            },
        )

    return httpx.MockTransport(response)


def test_prepare_keeps_original_and_context_and_is_idempotent(experiment):
    run, proposal = experiment
    assert (run / declarative.CASE / "v0/render.mp4").read_bytes() == (proposal / "baseline/render.mp4").read_bytes()
    assert (run / declarative.CASE / "context.json").read_bytes() == (proposal / "context.json").read_bytes()
    assert (
        declarative.prepare(proposal, runs=run.parent, tools={"ffmpeg": "/fixture/ffmpeg"}, extractor=fake_extract)
        == run
    )
    assert not (run / "operations").exists()
    assert not (proposal / "declarative-execution.json").exists()
    request = declarative.request_for(run, "critique", "v0")
    text = base.json_bytes(request)
    assert b"original complete instructions" in text and b"expected fontsize" not in text
    assert review.read_json(run / "summary.json")["cases"][0]["costs"]["historical_estimated_usd"] == "0.106892"


@pytest.mark.parametrize("change", ["source", "baseline", "duplicate", "escape", "symlink", "size"])
def test_proposal_tampering_rejected(experiment, change):
    _run, proposal = experiment
    manifest = review.read_json(proposal / "manifest.json")
    if change in {"source", "baseline"}:
        (proposal / ("context.json" if change == "source" else "baseline/render.mp4")).write_bytes(b"changed")
    elif change == "duplicate":
        manifest["files"].append(manifest["files"][0])
    elif change == "escape":
        manifest["files"][0]["path"] = "../outside"
    elif change == "symlink":
        original = proposal / "context.json"
        alternate = proposal / "context-copy.json"
        alternate.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(alternate)
    else:
        manifest["files"][0]["bytes"] += 1
    put(proposal / "manifest.json", manifest)
    with pytest.raises(base.EvalError):
        declarative.verified_proposal(proposal)


def test_qualification_required_before_claim_or_transport(experiment):
    run, proposal = experiment
    calls = []
    with pytest.raises(base.EvalError, match="qualification_required"):
        declarative.execute(run, declarative.LIMIT, transport=provider(run, calls))
    assert calls == [] and not (run / "started.json").exists()
    assert not (proposal / "declarative-execution.json").exists()


def test_qualification_checks_all_pixels_and_preserves_baseline(experiment, monkeypatch):
    run, _ = experiment
    baseline = (run / declarative.CASE / "v0/render.mp4").read_bytes()
    signatures = iter(({"pixels": "before"}, {"pixels": "after"}))
    monkeypatch.setattr(declarative.bridge, "video_signature", lambda _v, _t: next(signatures))
    with pytest.raises(base.EvalError, match="pixels_or_timing_changed"):
        qualify(run)
    assert not (run / "qualification.json").exists()
    assert (run / declarative.CASE / "v0/render.mp4").read_bytes() == baseline


@pytest.mark.parametrize("change", ["artifact", "tools", "marker"])
def test_qualification_tampering_prevents_paid_calls(experiment, monkeypatch, change):
    run, _ = experiment
    qualify(run)
    if change == "artifact":
        (run / "qualification/replay/render.mp4").write_bytes(b"changed")
    elif change == "tools":
        monkeypatch.setattr(declarative.bridge, "verify_tools", lambda _t: {"changed": "tool identity"})
    else:
        (run / "qualification.json").write_text("{}")
    calls = []
    with pytest.raises(base.EvalError, match="qualification"):
        declarative.execute(run, declarative.LIMIT, transport=provider(run, calls))
    assert calls == [] and not (run / "operations").exists()


@pytest.mark.parametrize("budget", ["NaN", "Infinity", "-1", "0", "1.24", "1.26", "6.75"])
def test_budget_is_exact_finite_plan_and_checked_before_effects(experiment, budget):
    run, proposal = experiment
    calls = []
    with pytest.raises(base.EvalError, match="explicit_budget"):
        declarative.execute(run, Decimal(budget), transport=provider(run, calls))
    assert calls == [] and not (proposal / "declarative-execution.json").exists()


@pytest.mark.parametrize("first", ["adequate", "insufficient_evidence"])
def test_no_correction_without_detected_need(experiment, first):
    run, _ = experiment
    qualify(run)
    calls = []
    result = declarative.execute(
        run,
        declarative.LIMIT,
        transport=provider(run, calls, first=first),
        renderer=fake_render,
        extractor=fake_extract,
    )
    assert calls == ["critique:v0"]
    assert result["status"] == "completed_human_pending"
    assert not (run / declarative.CASE / "v1").exists()


@pytest.mark.parametrize("prefer", ["v0", "v1"])
def test_complete_three_call_cycle_keeps_both_versions_and_costs(experiment, prefer):
    run, proposal = experiment
    qualify(run)
    qualify(run)  # Pure verification, no duplicate replay.
    calls = []
    result = declarative.execute(
        run,
        declarative.LIMIT,
        transport=provider(run, calls, prefer=prefer),
        renderer=fake_render,
        extractor=fake_extract,
    )
    assert calls == ["critique:v0", "correction:v1", "critique:v1"]
    case = result["cases"][0]
    assert case["recommended_version"] == prefer
    assert [v["id"] for v in case["versions"]] == ["v0", "v1"]
    assert case["costs"]["paid_calls"] == 3 and case["costs"]["committed_usd"] == "1.25"
    assert Decimal(case["costs"]["estimated_total_usd"]) == Decimal("0.107942")
    assert (run / declarative.CASE / "v0/render.mp4").read_bytes() == (proposal / "baseline/render.mp4").read_bytes()
    assert result["status"] == "completed_human_pending"
    with pytest.raises(FileExistsError):
        declarative.execute(run, declarative.LIMIT, transport=provider(run, calls))
    assert len(calls) == 3


@pytest.mark.parametrize(
    "mode,count",
    [("timeout", 1), ("unknown_usage", 1), ("wrong_evidence", 1), ("changed_audio", 2), ("invalid_units", 2)],
)
def test_failure_is_preserved_without_repeat_or_manual_normalization(experiment, mode, count):
    run, _ = experiment
    qualify(run)
    calls = []
    with pytest.raises(base.EvalError, match="stopped_preserved"):
        declarative.execute(
            run,
            declarative.LIMIT,
            transport=provider(run, calls, mode=mode),
            renderer=fake_render,
            extractor=fake_extract,
        )
    assert len(calls) == count
    assert not (run / declarative.CASE / "v1/render.mp4").exists()
    if mode in {"timeout", "unknown_usage"}:
        known, committed, unknown = review.spending(run)
        assert known == 0 and committed == Decimal("0.25") and len(unknown) == 1
    with pytest.raises((base.EvalError, FileExistsError)):
        declarative.execute(run, declarative.LIMIT, transport=provider(run, calls))
    assert len(calls) == count


@pytest.mark.parametrize("change", ["text", "audio", "font", "source", "style", "page", "duration", "color"])
def test_only_authorized_visual_fields_can_change(experiment, change):
    run, _ = experiment
    payload = correction(run)
    doc, page = payload["direction"], payload["direction"]["pages"][0]
    if change == "text":
        page["captions"][0]["text"] = "Fato não autorizado"
    elif change == "audio":
        page["audio"]["tracks"][0]["gain_mdb"] = -1000
    elif change == "font":
        page["captions"][0]["typography"]["font_id"] = "other-font"
    elif change == "source":
        doc["sources"][0]["duration_ms"] += 1
    elif change == "style":
        doc["style"]["sha256"] = "f" * 64
    elif change == "page":
        page["id"] = "00000000-0000-0000-0000-000000000001"
    elif change == "duration":
        page["duration_ms"] += 1
    else:
        page["captions"][0]["typography"]["color"] = "#FF0000"
    critique = review.Critique.model_validate(criticism(run, "v0", "needs_correction", "v0", case_id=declarative.CASE))
    with pytest.raises((base.EvalError, ValidationError)):
        declarative.checked_correction(run, declarative.Correction.model_validate(payload), critique)


def test_allowed_typography_change_handles_optional_defaults(experiment):
    run, _ = experiment
    payload = correction(run)
    critique = review.Critique.model_validate(criticism(run, "v0", "needs_correction", "v0", case_id=declarative.CASE))
    # Simulate the historical source omitting optional null fields, without changing its meaning.
    source = review.read_json(run / declarative.CASE / "v0/answer.json")
    source["direction"]["pages"][0]["audio"].pop("omission_reason", None)
    put(run / declarative.CASE / "v0/answer.json", source)
    output = declarative.checked_correction(run, declarative.Correction.model_validate(payload), critique)
    assert output["direction"]["pages"][0]["captions"][0]["typography"]["font_size"] == 700
    payload["addressed_issue_ids"] = ["other"]
    with pytest.raises(base.EvalError, match="unbound"):
        declarative.checked_correction(run, declarative.Correction.model_validate(payload), critique)


@pytest.mark.parametrize("kind,version", [("critique", "v1"), ("correction", "v1"), ("critique", "v2")])
def test_out_of_order_calls_have_no_reservation(experiment, kind, version):
    run, proposal = experiment
    qualify(run)
    start(run, proposal)
    calls = []
    with pytest.raises(base.EvalError, match="out_of_order"):
        declarative.call(run, kind, version, declarative.LIMIT, transport=provider(run, calls))
    assert calls == [] and review.spending(run) == (Decimal(0), Decimal(0), [])


def test_crash_after_durable_effect_claim_never_reissues_request(experiment):
    run, proposal = experiment
    qualify(run)
    start(run, proposal)
    put(run / "effect-critique-v0.json", {"request_sha256": "f" * 64})
    calls = []
    with pytest.raises(FileExistsError):
        declarative.call(run, "critique", "v0", declarative.LIMIT, transport=provider(run, calls))
    assert calls == [] and not (run / "operations").exists()


def test_generic_executor_cannot_bypass_declarative_admission(experiment):
    run, _ = experiment
    calls = []
    with pytest.raises(base.EvalError, match="executor"):
        review.execute(
            run,
            declarative.LIMIT,
            transport=provider(run, calls),
            renderer=lambda *_: pytest.fail("generic preflight must not run"),
        )
    assert calls == [] and not (run / "started.json").exists()
    assert not (run / "operations").exists()


@pytest.mark.parametrize(
    "change", ["unqualified", "case", "budget", "no_intent", "intent", "request", "terminal", "dispatched"]
)
def test_shared_transport_cannot_bypass_declarative_admission(experiment, change):
    run, proposal = experiment
    if change != "unqualified":
        qualify(run)
    start(run, proposal)
    request = declarative.request_for(run, "critique", "v0")
    binding = {"request_sha256": base.digest(base.json_bytes(request))}
    if change != "no_intent":
        put(run / "effect-critique-v0.json", binding)
    if change == "intent":
        put(run / "effect-critique-v0.json", {"request_sha256": "f" * 64})
    elif change == "request":
        request["instructions"] += " Changed after local admission."
    elif change == "terminal":
        base.event(run, "completed_human_pending")
    elif change == "dispatched":
        put(run / "dispatch-critique-v0.json", binding)
    calls = []
    with pytest.raises((base.EvalError, FileExistsError)):
        review.call_model(
            run,
            "other" if change == "case" else declarative.CASE,
            "v0",
            "critique",
            request,
            Decimal("2") if change == "budget" else declarative.LIMIT,
            transport=provider(run, calls),
        )
    assert calls == [] and not (run / "operations").exists()
    assert review.spending(run) == (Decimal(0), Decimal(0), [])


def test_audio_divergence_stops_before_final_critique(experiment):
    run, _ = experiment
    qualify(run)
    calls = []

    def bad_render(run, target, prepared, tools):
        fake_render(run, target, prepared, tools)
        proof = review.read_json(target / "audio-preservation.json")
        proof["pcm_equal"] = False
        put(target / "audio-preservation.json", proof)

    with pytest.raises(base.EvalError, match="stopped_preserved"):
        declarative.execute(
            run, declarative.LIMIT, transport=provider(run, calls), renderer=bad_render, extractor=fake_extract
        )
    assert calls == ["critique:v0", "correction:v1"]
    assert not (run / declarative.CASE / "v1/critique.json").exists()


def test_request_correction_is_bound_to_critique_and_schema_units(experiment):
    run, _ = experiment
    critique = criticism(run, "v0", "needs_correction", "v0", case_id=declarative.CASE)
    path = run / declarative.CASE / "v0/critique.json"
    put(path, critique)
    with pytest.raises(base.EvalError, match="bound_actionable"):
        declarative.request_for(run, "correction", "v1")
    base.event(
        run,
        "version_reviewed",
        case_id=declarative.CASE,
        version_id="v0",
        critique_sha256=base.digest(path.read_bytes()),
    )
    request = declarative.request_for(run, "correction", "v1")
    assert "pontos-base" in request["instructions"]
    assert request["text"]["format"]["schema"]["properties"]["direction"]
    assert '"default"' not in json.dumps(request["text"]["format"])
    assert "DIREÇÃO ATUAL" in request["input"][0]["content"][-2]["text"]
    assert "CRÍTICA" in request["input"][0]["content"][-1]["text"]
    critique["issues"][0]["problem"] = "alterado posteriormente"
    put(path, critique)
    with pytest.raises(base.EvalError, match="bound_actionable"):
        declarative.request_for(run, "correction", "v1")


@pytest.mark.parametrize("change", ["sum", "component", "duplicate", "binding", "prior", "invoice"])
def test_historical_subtotal_includes_failed_call_and_is_source_bound(experiment, change):
    _run, proposal = experiment
    cost = review.read_json(proposal / "computation.json")
    if change == "sum":
        cost["estimated_usd"] = "0.105925"
    elif change == "component":
        cost["components"][0]["estimated_usd_micros_rounded_up"] += 1
    elif change == "duplicate":
        cost["components"][1] = cost["components"][0]
    elif change == "binding":
        cost["components"][0]["bindings"]["request.body"]["sha256"] = "f" * 64
    elif change == "prior":
        (proposal / "costs/rejected/response.body").write_bytes(b"different failed response")
    else:
        cost["invoice_verified"] = True
    put(proposal / "computation.json", cost)
    with pytest.raises(base.EvalError, match="historical"):
        declarative.verify_historical_cost(proposal)


@pytest.mark.parametrize("change", ["start", "claim", "inputs", "code", "stop"])
def test_readmission_rechecks_frozen_state_before_new_effect(experiment, monkeypatch, change):
    run, proposal = experiment
    qualify(run)
    start(run, proposal)
    if change == "start":
        put(run / "started.json", {"budget_usd": "1.26", "experiment_id": run.name})
    elif change == "claim":
        put(proposal / "declarative-execution.json", {"run": "a different run"})
    elif change == "inputs":
        (run / declarative.CASE / "context.json").write_text("{}")
    elif change == "code":
        monkeypatch.setattr(declarative, "ACTIVE_CODE", ("app/schemas/motion.py",))
    else:
        base.event(run, "stopped", reason="prior_failure")
    calls = []
    with pytest.raises(base.EvalError):
        declarative.call(run, "critique", "v0", declarative.LIMIT, transport=provider(run, calls))
    assert calls == [] and not (run / "operations").exists()


def test_same_effect_cannot_dispatch_twice_concurrently(experiment):
    run, proposal = experiment
    qualify(run)
    start(run, proposal)
    entered, release = threading.Event(), threading.Event()
    calls = []
    real_fake = provider(run, calls, first="adequate")

    def blocked(request):
        entered.set()
        assert release.wait(5)
        return real_fake.handle_request(request)

    transport = httpx.MockTransport(blocked)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(declarative.call, run, "critique", "v0", declarative.LIMIT, transport=transport)
        try:
            assert entered.wait(5)
            with pytest.raises(base.EvalError, match="out_of_order"):
                declarative.call(run, "critique", "v0", declarative.LIMIT, transport=transport)
        finally:
            release.set()
        assert review.structured_response(first.result(), review.Critique).overall == "adequate"
    assert calls == ["critique:v0"] and review.spending(run)[1] == Decimal("0.25")


def test_missing_final_evidence_blocks_third_paid_call(experiment):
    run, _ = experiment
    qualify(run)
    calls = []

    def changed_extract(video, sha, tools, output):
        evidence = fake_extract(video, sha, tools, output)
        (output / evidence["frames"][0]["path"]).write_bytes(b"corrupt frame")
        return evidence

    with pytest.raises(base.EvalError, match="stopped_preserved"):
        declarative.execute(
            run, declarative.LIMIT, transport=provider(run, calls), renderer=fake_render, extractor=changed_extract
        )
    assert calls == ["critique:v0", "correction:v1"]


def test_unchanged_direction_is_not_rendered(experiment):
    run, _ = experiment
    payload = correction(run)
    payload["direction"] = review.read_json(run / declarative.CASE / "v0/answer.json")["direction"]
    critique = review.Critique.model_validate(criticism(run, "v0", "needs_correction", "v0", case_id=declarative.CASE))
    with pytest.raises(base.EvalError, match="unchanged_composition"):
        declarative.checked_correction(run, declarative.Correction.model_validate(payload), critique)
