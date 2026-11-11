"""Offline integration of review orchestration with synthetic fixtures and mock HTTP."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from PIL import Image

from scripts.evals import motion_eval as base
from scripts.evals import motion_review_eval as review
from scripts.evals.motion_review_evidence import LIMITATIONS


def put(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base.json_bytes(obj))


def fake_extract(video: Path, sha: str, _tools: dict, output: Path) -> dict:
    assert base.digest(video.read_bytes()) == sha
    output.mkdir(parents=True)
    frames = []
    for number, timestamp in enumerate((0, 500, 966)):
        name = f"f{number:04}.png"
        Image.new("RGB", (64, 96), (number, 0, 0)).save(output / name)
        frames.append(
            {
                "frame_id": name[:-4],
                "path": name,
                "timestamp_ms": timestamp,
                "sha256": base.digest((output / name).read_bytes()),
            }
        )
    manifest = {
        "version": 1,
        "video_sha256": sha,
        "duration_ms": 1000,
        "width": 64,
        "height": 96,
        "fps": 30,
        "frames": frames,
        "technical": {"audio_present": False, "decode_ok": True, "audio_mean_db": None, "audio_peak_db": None},
        "limitations": LIMITATIONS,
    }
    put(output / "evidence.json", manifest)
    return manifest


def fake_renderer(_node: str, config: Path, output: Path | None) -> None:
    if output is None:
        return
    data = json.loads(config.read_bytes())
    content = ("video:" + data["scene_init"]["sha256"]).encode()
    (output / "render.mp4").write_bytes(content)
    put(
        output / "trace.json",
        {
            "synthetic_fixture": True,
            "html_sha256": data["html"]["sha256"],
            "scene_sha256": data["scene_init"]["sha256"],
            "output": {"sha256": base.digest(content)},
        },
    )


def make_answer(revision: int = 0) -> dict:
    return {
        "concept": "fixture",
        "source_usage": [],
        "html": f"<div>Teste {revision}</div>",
        "scene_init": f"async () => {{window.seek = async () => {revision}}}",
        "audio": {"mode": "silent", "tracks": []},
    }


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setenv("MEU_BRACO_DIREITO_OPENAI_API_KEY", "fixture-secret-do-not-log")
    rubric = tmp_path / "rubric.json"
    put(rubric, {"version": 1, "description": "rubric fixture"})
    monkeypatch.setattr(review, "RUBRIC", rubric)
    source = tmp_path / "baseline"
    (source / "render").mkdir(parents=True)
    original = b"synthetic baseline mp4"
    (source / "render/render.mp4").write_bytes(original)
    (source / "asset.mp4").write_bytes(b"synthetic asset")
    (source / "rights.txt").write_text("synthetic rights")
    request = {
        "model": "gpt-6.1-sol",
        "instructions": "Instruções sintéticas do render",
        "store": False,
        "reasoning": {"effort": "high"},
        "max_output_tokens": 32000,
        "text": {"format": {"type": "json_schema", "strict": True}},
        "input": [{"role": "user", "content": [{"type": "input_text", "text": '{"facts": ["fixture"]}'}]}],
    }
    put(source / "request.body", request)
    answer = make_answer()
    put(source / "answer.json", answer)
    put(source / "rights.json", [{"copy": "rights.txt", "sha256": base.digest(b"synthetic rights")}])
    put(source / "cost.json", {"estimated_usd": "0.1"})
    (source / "response.body").write_bytes(b"synthetic response")
    put(
        source / "render/trace.json",
        {
            "synthetic_fixture": True,
            "html_sha256": base.digest(answer["html"].encode()),
            "scene_sha256": base.digest(answer["scene_init"].encode()),
            "output": {"sha256": base.digest(original)},
        },
    )
    case = {
        "version": 1,
        "synthetic_fixture": True,
        "id": "fixture",
        "body_path": str(source / "request.body"),
        "body_sha256": base.digest((source / "request.body").read_bytes()),
        "width": 64,
        "height": 96,
        "fps": 30,
        "duration_ms": 1000,
        "assets": [
            {
                "id": "a",
                "path": str(source / "asset.mp4"),
                "sha256": base.digest(b"synthetic asset"),
                "mime": "video/mp4",
            }
        ],
        "reference": {"path": str(source / "render/render.mp4"), "sha256": base.digest(original)},
        "tools": {key: "/synthetic/tool" for key in ("node", "playwright", "chromium", "ffmpeg", "ffprobe")},
        "reservation_usd": "0.75",
        "rights_files": [str(source / "rights.txt")],
    }
    put(source / "frozen-case.json", case)
    manifest = {
        "version": 1,
        "synthetic_fixture": True,
        "max_corrections": 2,
        "cases": [
            {
                "id": "fixture",
                "label": "Caso fictício",
                "baseline_run": str(source),
                "video_sha256": base.digest(original),
                "baseline_cost_note": "histórico fictício",
            }
        ],
    }
    path = tmp_path / "manifest.json"
    put(path, manifest)
    run = review.prepare(path, runs=tmp_path / "runs", extractor=fake_extract)
    return run, source


def criticism(
    run: Path, version: str, overall: str, prefer: str, *, issue_ref: str | None = None, case_id: str = "fixture"
) -> dict:
    sha = base.digest((run / case_id / version / "render.mp4").read_bytes())
    criteria = [
        {
            "criterion": c,
            "status": "uncertain" if c == "audio" else "pass",
            "evidence_ids": [] if c == "audio" else [f"{version}:f0000"],
            "observation": "mock",
        }
        for c in sorted(review.CRITERIA)
    ]
    issues = []
    if overall == "needs_correction":
        next(c for c in criteria if c["criterion"] == "legibility")["status"] = "fail"
        issues = [
            {
                "id": "i1",
                "criterion": "legibility",
                "severity": "major",
                "evidence_ids": [issue_ref or f"{version}:f0000"],
                "start_ms": 0,
                "end_ms": 0,
                "problem": "legenda pequena",
                "correction": "aumentar legenda",
                "actionable": True,
            }
        ]
    return {
        "version_id": version,
        "video_sha256": sha,
        "overall": overall,
        "criteria": criteria,
        "issues": issues,
        "preference": {
            "version_id": prefer,
            "reason": "mock",
            "evidence_ids": [f"{version}:f0000"] + ([f"v{int(version[1:]) - 1}:f0000"] if version != "v0" else []),
        },
        "limitations": ["mock"],
    }


def fake_provider(run: Path, states: list[tuple[str, str]], calls: list[str], *, mode: str = "") -> httpx.MockTransport:
    def respond(request: httpx.Request) -> httpx.Response:
        operation = request.headers["X-Client-Request-Id"]
        binding = json.loads((run / "operations" / operation / "binding.json").read_bytes())
        entries = review.journal(run)
        assert entries[-1]["state"] == "reserved" and entries[-1]["operation_id"] == operation
        kind, version = binding["kind"], binding["version_id"]
        calls.append(f"{kind}:{version}")
        if mode == "timeout":
            raise httpx.ReadTimeout("mock timeout")
        if mode == "no_usage":
            return httpx.Response(200, json={"status": "completed"})
        if mode == "invalid_json":
            return httpx.Response(200, content=b"not-json")
        if mode == "http_error":
            return httpx.Response(429, json={"usage": {"input_tokens": 100, "output_tokens": 10}})
        if kind == "critique":
            overall, prefer = states[int(version[1:])]
            value = criticism(
                run,
                version,
                overall,
                prefer,
                issue_ref="v0:f9999" if mode == "wrong_evidence" else None,
                case_id=binding["case_id"],
            )
        else:
            answer = make_answer(int(version[1:]))
            if mode == "changed_audio":
                answer["audio"]["mode"] = "mix"
            value = {
                "addressed_issue_ids": ["i99" if mode == "wrong_issue" else "i1"],
                "changes": "fixture",
                "composition": answer,
            }
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [{"content": [{"type": "output_text", "text": json.dumps(value)}]}],
                "usage": {"input_tokens": 100, "output_tokens": 10},
            },
        )

    return httpx.MockTransport(respond)


def execute(run: Path, transport: httpx.MockTransport) -> dict:
    return review.execute(run, Decimal("2.25"), transport=transport, renderer=fake_renderer, extractor=fake_extract)


@pytest.mark.parametrize(
    ("states", "expected", "winner", "reason"),
    [
        ([("adequate", "v0")], ["critique:v0"], "v0", "no_relevant_actionable_defect"),
        (
            [("needs_correction", "v0"), ("needs_correction", "v0")],
            ["critique:v0", "correction:v1", "critique:v1"],
            "v0",
            "no_demonstrated_improvement",
        ),
        (
            [("needs_correction", "v0"), ("adequate", "v1")],
            ["critique:v0", "correction:v1", "critique:v1"],
            "v1",
            "no_relevant_actionable_defect",
        ),
        (
            [("needs_correction", "v0"), ("needs_correction", "v1"), ("needs_correction", "v2")],
            ["critique:v0", "correction:v1", "critique:v1", "correction:v2", "critique:v2"],
            "v2",
            "correction_limit",
        ),
    ],
)
def test_full_offline_cycles(experiment, states, expected, winner, reason):
    run, source = experiment
    original = (source / "render/render.mp4").read_bytes()
    calls = []
    summary = execute(run, fake_provider(run, states, calls))
    assert calls == expected
    assert summary["cases"][0]["recommended_version"] == winner
    assert summary["cases"][0]["stop_reason"] == reason
    assert summary["human_review"] == "pending"
    assert (run / "fixture/v0/render.mp4").read_bytes() == original == (source / "render/render.mp4").read_bytes()
    assert (run / "report.html").is_file()
    assert review.execute(run, Decimal("2.25"), renderer=fake_renderer) == summary
    assert calls == expected


@pytest.mark.parametrize(
    "mode", ["timeout", "no_usage", "invalid_json", "wrong_evidence", "changed_audio", "wrong_issue", "http_error"]
)
def test_fail_closed_without_retry(experiment, mode):
    run, _ = experiment
    calls = []
    transport = fake_provider(run, [("needs_correction", "v0")], calls, mode=mode)
    with pytest.raises(base.EvalError, match="experiment_stopped_results_preserved"):
        execute(run, transport)
    assert len(calls) == (2 if mode in {"changed_audio", "wrong_issue"} else 1)
    summary = review.read_json(run / "summary.json")
    assert summary["status"] == "stopped"
    # No critique was accepted for v0 in these failures, except correction failures
    # that occur after the initial critique completed.
    if mode not in {"changed_audio", "wrong_issue"}:
        assert summary["cases"][0]["recommended_version"] is None
    assert not (run / "fixture/v1/render.mp4").exists()
    assert review.execute(run, Decimal("2.25"), transport=transport, renderer=fake_renderer) == summary
    assert len(calls) == (2 if mode in {"changed_audio", "wrong_issue"} else 1)
    if mode in {"timeout", "no_usage", "invalid_json"}:
        assert summary["unknown_cost_operations"]


def test_tampered_input_rejected_before_network(experiment):
    run, _ = experiment
    (run / "fixture/v0/answer.json").write_text("{}")
    calls = []
    with pytest.raises(base.EvalError, match="frozen_input_changed"):
        execute(run, fake_provider(run, [("adequate", "v0")], calls))
    assert not calls


def test_tampered_evidence_rejected_before_network(experiment):
    run, _ = experiment
    (run / "fixture/v0/evidence/f0000.png").write_bytes(b"bad")
    calls = []
    with pytest.raises(base.EvalError, match="frozen_input_changed"):
        execute(run, fake_provider(run, [("adequate", "v0")], calls))
    assert not calls


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_version", "critique_binding_invalid"),
        ("wrong_hash", "critique_binding_invalid"),
        ("unknown_evidence", "critique_unknown_evidence"),
        ("empty_evidence", "critique_without_evidence"),
        ("audio_pass", "perceptual_audio_not_observed"),
        ("invalid_interval", "issue_invalid_interval"),
        ("unobserved_interval", "actionable_issue_without_current_frame"),
        ("not_failed", "actionable_issue_requires_failed_criterion"),
        ("adequate_with_issue", "adequate_with_blocking_issue"),
    ],
)
def test_critique_evidence_and_intervals_are_enforced(experiment, mutation, message):
    run, _ = experiment
    data = criticism(run, "v0", "needs_correction", "v0")
    if mutation == "wrong_version":
        data["version_id"] = "v1"
    elif mutation == "wrong_hash":
        data["video_sha256"] = "0" * 64
    elif mutation == "unknown_evidence":
        data["issues"][0]["evidence_ids"] = ["v0:f9999"]
    elif mutation == "empty_evidence":
        next(c for c in data["criteria"] if c["criterion"] == "brand")["evidence_ids"] = []
    elif mutation == "audio_pass":
        audio = next(c for c in data["criteria"] if c["criterion"] == "audio")
        audio.update(status="pass", evidence_ids=["v0:f0000"])
    elif mutation == "invalid_interval":
        data["issues"][0].update(start_ms=600, end_ms=500)
    elif mutation == "unobserved_interval":
        data["issues"][0].update(start_ms=100, end_ms=200)
    elif mutation == "not_failed":
        next(c for c in data["criteria"] if c["criterion"] == "legibility")["status"] = "pass"
    elif mutation == "adequate_with_issue":
        data["overall"] = "adequate"
    with pytest.raises(base.EvalError, match=message):
        review.validate_critique(run, "fixture", "v0", "v0", review.Critique.model_validate(data))


def test_budget_rejected_before_any_network_or_renderer(experiment):
    run, _ = experiment
    calls = []
    transport = fake_provider(run, [("adequate", "v0")], calls)
    with pytest.raises(base.EvalError, match="budget_below_frozen_plan"):
        review.execute(run, Decimal("2.24"), transport=transport, renderer=lambda *_: pytest.fail("must not run"))
    assert not calls and not (run / "started.json").exists()


def test_budget_reserves_final_critique_before_correction(experiment):
    run, _ = experiment
    calls = []
    transport = fake_provider(run, [("needs_correction", "v0")], calls)
    review.run_case(
        run, {"id": "fixture"}, Decimal("1.00"), 2, transport=transport, renderer=fake_renderer, extractor=fake_extract
    )
    assert calls == ["critique:v0"]
    assert review.journal(run)[-1]["reason"] == "budget_before_correction"
    assert not (run / "fixture/v1").exists()


def test_prepare_rejects_modified_baseline_lineage(experiment, tmp_path):
    run, source = experiment
    source_manifest = review.read_json(run / "sources.json")
    source_manifest["cases"][0]["video_sha256"] = "0" * 64
    altered = tmp_path / "bad-manifest.json"
    put(altered, source_manifest)
    with pytest.raises(base.EvalError, match="baseline_lineage_mismatch"):
        review.prepare(altered, runs=tmp_path / "bad-runs", extractor=fake_extract)
    assert (source / "render/render.mp4").read_bytes() == b"synthetic baseline mp4"


def test_no_secret_in_logs_or_saved_requests(experiment, capsys):
    run, _ = experiment
    calls = []
    execute(run, fake_provider(run, [("adequate", "v0")], calls))
    output = capsys.readouterr()
    assert "fixture-secret-do-not-log" not in output.out + output.err
    assert b"fixture-secret-do-not-log" not in next((run / "operations").glob("*/request.json")).read_bytes()


def test_derived_evidence_manifest_cannot_be_replaced_after_render(experiment, monkeypatch):
    run, _ = experiment
    original = review.version_evidence
    tampered = False

    def replace_evidence(run_dir, case_id, version_id):
        nonlocal tampered
        if version_id == "v1" and not tampered:
            tampered = True
            evidence_dir = run_dir / case_id / version_id / "evidence"
            image = evidence_dir / "f0000.png"
            Image.new("RGB", (64, 96), (255, 255, 255)).save(image)
            manifest = review.read_json(evidence_dir / "evidence.json")
            manifest["frames"][0]["sha256"] = base.digest(image.read_bytes())
            put(evidence_dir / "evidence.json", manifest)
        return original(run_dir, case_id, version_id)

    monkeypatch.setattr(review, "version_evidence", replace_evidence)
    calls = []
    with pytest.raises(base.EvalError, match="experiment_stopped_results_preserved"):
        execute(run, fake_provider(run, [("needs_correction", "v0"), ("adequate", "v1")], calls))
    assert calls == ["critique:v0", "correction:v1"]
    summary = review.read_json(run / "summary.json")
    assert summary["status"] == "stopped"
    assert summary["stop_reason"] == "render_evidence_changed"


def test_improvement_requires_comparative_frame_evidence(experiment):
    run, _ = experiment
    target = run / "fixture/v1"
    target.mkdir()
    video = target / "render.mp4"
    video.write_bytes(b"revised fixture")
    fake_extract(video, base.digest(video.read_bytes()), {}, target / "evidence")
    base.event(
        run,
        "rendered",
        case_id="fixture",
        version_id="v1",
        evidence_sha256=base.digest((target / "evidence/evidence.json").read_bytes()),
    )
    data = criticism(run, "v1", "adequate", "v1")
    data["preference"]["evidence_ids"] = ["v1:f0000"]
    with pytest.raises(base.EvalError, match="preference_requires_comparative_evidence"):
        review.validate_critique(run, "fixture", "v1", "v0", review.Critique.model_validate(data))
    data["preference"]["evidence_ids"].append("v0:f0000")
    review.validate_critique(run, "fixture", "v1", "v0", review.Critique.model_validate(data))


def test_prepared_context_preserves_creative_direction_and_original_instructions():
    original = {
        "facts": ["fato"],
        "user_feedback": ["faça mais dinâmica"],
        "own_skill": {"name": "skill-reel", "content": "composição orientada por estilo"},
        "creative_direction_proposal": {"motion": "movimento contínuo", "visual": "contraste"},
        "target": {"format": "reel"},
        "profile": {"brand": "ficção"},
    }
    request = {
        "instructions": "Preserve o movimento da referência e os princípios da skill.",
        "input": [{"role": "user", "content": [{"type": "input_text", "text": "Contexto:\n" + json.dumps(original)}]}],
    }
    context = review.prepared_context(request)
    for key, value in original.items():
        assert context[key] == value
    assert context["generation_instructions"] == request["instructions"]


def completed_parent(experiment):
    run, _ = experiment
    calls = []
    execute(run, fake_provider(run, [("adequate", "v0")], calls))
    assert calls == ["critique:v0"]
    return run


def continuation_manifest(parent: Path, destination: Path, **changes) -> Path:
    sources = review.read_json(parent / "sources.json")
    sources.update({"continuation_of": str(parent), "max_corrections": 1}, **changes)
    put(destination, sources)
    return destination


def test_continuation_imports_costs_and_keeps_group_ceiling(experiment, tmp_path):
    parent = completed_parent(experiment)
    original_ledger = (parent / "ledger.jsonl").read_bytes()
    sources = continuation_manifest(parent, tmp_path / "continuation.json")
    child = review.prepare(sources, runs=tmp_path / "runs", extractor=fake_extract)
    child_manifest = review.read_json(child / "manifest.json")
    assert child_manifest["previous_run"] == str(parent)
    assert (child / "prior-ledger.jsonl").read_bytes() == original_ledger
    assert child_manifest["prior_ledger_sha256"] == base.digest(original_ledger)
    known, committed, unknown = review.spending(child)
    assert known == Decimal("0.00035") and committed == Decimal("0.25") and not unknown
    calls = []
    result = review.execute(
        child,
        Decimal("2.25"),
        transport=fake_provider(child, [("needs_correction", "v0"), ("adequate", "v1")], calls),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    assert calls == ["critique:v0", "correction:v1", "critique:v1"]
    reservations = [e for e in review.journal(child) if e["state"] == "reserved"]
    assert len(reservations) == 4
    assert sum(e["kind"] == "critique" for e in reservations) == 3
    assert sum(e["kind"] == "correction" for e in reservations) == 1
    assert sum(Decimal(e["reservation_usd"]) for e in reservations) == Decimal("1.5")
    assert result["cases"][0]["recommended_version"] == "v1"
    assert result["previous_run"] == str(parent)
    assert Decimal(result["known_estimated_usd"]) == Decimal("0.0014")
    assert Decimal(result["cases"][0]["costs"]["incremental_estimated_usd"]) == Decimal("0.0014")
    scopes = [operation["context_scope"] for operation in result["cases"][0]["operations"]]
    assert scopes.count("initial_incomplete_context") == 1
    assert scopes.count("creative_context_v2") == 3
    assert (parent / "ledger.jsonl").read_bytes() == original_ledger


def test_continuation_rejects_unfinished_or_unknown_parent(experiment, tmp_path):
    parent, _ = experiment
    manifest = continuation_manifest(parent, tmp_path / "continuation.json")
    with pytest.raises(base.EvalError, match="invalid_continuation"):
        review.prepare(manifest, runs=tmp_path / "bad-before", extractor=fake_extract)
    completed_parent(experiment)
    base.event(
        parent,
        "reserved",
        operation_id="uncertain-parent",
        case_id="fixture",
        version_id="v0",
        kind="critique",
        reservation_usd="0.25",
    )
    with pytest.raises(base.EvalError, match="invalid_continuation"):
        review.prepare(manifest, runs=tmp_path / "bad-unknown", extractor=fake_extract)


@pytest.mark.parametrize("mismatch", ["id", "video", "max_corrections"])
def test_continuation_rejects_different_parent_cases_or_limit(experiment, tmp_path, mismatch):
    parent = completed_parent(experiment)
    manifest = continuation_manifest(parent, tmp_path / "continuation.json")
    sources = review.read_json(manifest)
    if mismatch == "id":
        sources["cases"][0]["id"] = "different"
    elif mismatch == "video":
        sources["cases"][0]["video_sha256"] = "0" * 64
    else:
        sources["max_corrections"] = 2
    put(manifest, sources)
    with pytest.raises(base.EvalError, match="invalid_continuation"):
        review.prepare(manifest, runs=tmp_path / "bad", extractor=fake_extract)


@pytest.mark.parametrize(
    ("count", "prior_case", "prior_kind", "next_kind"),
    [
        (3, "fixture", "critique", "critique"),
        (2, "fixture", "correction", "correction"),
        (15, "other", "critique", "critique"),
    ],
)
def test_paid_call_caps_are_checked_before_network(experiment, count, prior_case, prior_kind, next_kind):
    run, _ = experiment
    for index in range(count):
        op_id = f"old-{index}"
        case_id = f"{prior_case}-{index}" if prior_case == "other" else prior_case
        base.event(
            run,
            "reserved",
            operation_id=op_id,
            case_id=case_id,
            version_id="v0",
            kind=prior_kind,
            reservation_usd="0.25",
        )
        base.event(run, "cost_recorded", operation_id=op_id, estimated_usd="0.001")
    before = (run / "ledger.jsonl").read_bytes()
    transport = httpx.MockTransport(lambda _: pytest.fail("call limit must prevent network"))
    with pytest.raises(base.EvalError, match="authorized_call_limit"):
        review.call_model(run, "fixture", "v0", next_kind, {"fixture": True}, Decimal("100"), transport=transport)
    assert (run / "ledger.jsonl").read_bytes() == before


def test_continuation_claim_prevents_second_child_from_calling_provider(experiment, tmp_path):
    parent = completed_parent(experiment)
    first_manifest = continuation_manifest(parent, tmp_path / "first.json")
    second_manifest = continuation_manifest(parent, tmp_path / "second.json")
    second_sources = review.read_json(second_manifest)
    second_sources["cases"][0]["label"] = "mesmo caso, outro rótulo"
    put(second_manifest, second_sources)
    first = review.prepare(first_manifest, runs=tmp_path / "first-runs", extractor=fake_extract)
    second = review.prepare(second_manifest, runs=tmp_path / "second-runs", extractor=fake_extract)
    first_calls = []
    execute(first, fake_provider(first, [("adequate", "v0")], first_calls))
    assert first_calls == ["critique:v0"]
    second_calls = []
    with pytest.raises(base.EvalError, match="continuation_already_claimed"):
        execute(second, fake_provider(second, [("adequate", "v0")], second_calls))
    assert not second_calls
    assert not (second / "started.json").exists()


def independent_parent(experiment, tmp_path):
    """Three completed v1 reviews followed by one ambiguous v2 request."""
    import shutil

    _, source = experiment
    items = []
    for name in ("intensa", "dog", "luma"):
        local = tmp_path / f"source-{name}"
        shutil.copytree(source, local)
        media = f"synthetic-{name}".encode()
        (local / "render/render.mp4").write_bytes(media)
        trace = review.read_json(local / "render/trace.json")
        trace["output"]["sha256"] = base.digest(media)
        put(local / "render/trace.json", trace)
        case = review.read_json(local / "frozen-case.json")
        case["reference"] = {"path": str(local / "render/render.mp4"), "sha256": base.digest(media)}
        put(local / "frozen-case.json", case)
        items.append(
            {
                "id": name,
                "label": name,
                "baseline_run": str(local),
                "video_sha256": base.digest(media),
                "baseline_cost_note": "synthetic",
            }
        )
    sources = {"version": 1, "synthetic_fixture": True, "max_corrections": 2, "cases": items}
    original_path = tmp_path / "all-cases.json"
    put(original_path, sources)
    original = review.prepare(original_path, runs=tmp_path / "all-runs", extractor=fake_extract)
    calls = []
    review.execute(
        original,
        Decimal("6.75"),
        transport=fake_provider(original, [("adequate", "v0")], calls),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    assert len(calls) == 3
    continuation_path = continuation_manifest(original, tmp_path / "v2.json", context_version=2)
    v2 = review.prepare(continuation_path, runs=tmp_path / "all-runs", extractor=fake_extract)
    with pytest.raises(base.EvalError, match="experiment_stopped_results_preserved"):
        review.execute(
            v2,
            Decimal("6.75"),
            transport=fake_provider(v2, [], [], mode="timeout"),
            renderer=fake_renderer,
            extractor=fake_extract,
        )
    return v2


def independent_manifest(parent, destination):
    sources = review.read_json(parent / "sources.json")
    sources.pop("continuation_of")
    sources["independent_continuation_of"] = str(parent)
    put(destination, sources)
    return destination


def test_independent_continuation_preserves_uncertainty_and_processes_only_untouched(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    parent_ledger = (parent / "ledger.jsonl").read_bytes()
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "all-runs", extractor=fake_extract)
    manifest = review.verify_inputs(run)
    assert manifest["eligible_case_ids"] == ["dog", "luma"]
    assert manifest["blocked_case_ids"] == ["intensa"]
    assert manifest["maximum_reservations_usd"] == "3.50"
    assert (run / "prior-ledger.jsonl").read_bytes() == parent_ledger
    assert review.spending(run)[1] == Decimal("1.00")
    unknown = review.spending(run)[2]
    assert len(unknown) == 1
    calls = []
    result = review.execute(
        run,
        Decimal("6.75"),
        transport=fake_provider(run, [("adequate", "v0")], calls),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    assert calls == ["critique:v0", "critique:v0"]
    assert result["unknown_cost_operations"] == unknown
    by_id = {x["id"]: x for x in result["cases"]}
    assert by_id["intensa"]["status"] == "blocked_uncertain"
    assert by_id["intensa"]["costs"]["estimated_total_usd"] is None
    assert by_id["dog"]["status"] == by_id["luma"]["status"] == "review_complete_human_pending"
    assert result["paid_calls"] == 6
    assert (parent / "ledger.jsonl").read_bytes() == parent_ledger
    assert (
        review.execute(
            run,
            Decimal("6.75"),
            transport=fake_provider(run, [], calls),
            renderer=fake_renderer,
            extractor=fake_extract,
        )
        == result
    )
    assert len(calls) == 2


def test_independent_continuation_refuses_budget_fork_and_mutated_ledger(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    first = review.prepare(source, runs=tmp_path / "first-runs", extractor=fake_extract)
    second = review.prepare(source, runs=tmp_path / "second-runs", extractor=fake_extract)
    with pytest.raises(base.EvalError, match="budget_above_authorized_limit"):
        review.execute(first, Decimal("6.76"), transport=fake_provider(first, [], []), renderer=fake_renderer)
    with pytest.raises(base.EvalError, match="budget_below_frozen_plan"):
        review.execute(first, Decimal("3.49"), transport=fake_provider(first, [], []), renderer=fake_renderer)
    review.execute(
        first,
        Decimal("6.75"),
        transport=fake_provider(first, [("adequate", "v0")], []),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    calls = []
    with pytest.raises(base.EvalError, match="continuation_already_claimed"):
        review.execute(second, Decimal("6.75"), transport=fake_provider(second, [], calls), renderer=fake_renderer)
    assert calls == []
    ledger = (first / "ledger.jsonl").read_bytes().splitlines(keepends=True)
    (first / "ledger.jsonl").write_bytes(b"".join(ledger[1:]))
    with pytest.raises(base.EvalError, match="imported_ledger_changed"):
        review.verify_inputs(first)


def test_independent_rejects_changes_or_parent_with_additional_unknown(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    value = review.read_json(source)
    value["cases"][1]["video_sha256"] = "0" * 64
    put(source, value)
    with pytest.raises(base.EvalError, match="invalid_independent_continuation"):
        review.prepare(source, runs=tmp_path / "bad", extractor=fake_extract)
    independent_manifest(parent, source)
    base.event(
        parent,
        "reserved",
        operation_id="second-unknown",
        case_id="dog",
        version_id="v0",
        kind="critique",
        reservation_usd="0.25",
        request_sha256="0" * 64,
    )
    with pytest.raises(base.EvalError, match="invalid_independent_continuation"):
        review.prepare(source, runs=tmp_path / "bad2", extractor=fake_extract)


def test_independent_two_children_race_claim_has_single_winner(experiment, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, local

    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    children = [review.prepare(source, runs=tmp_path / f"race-{i}", extractor=fake_extract) for i in range(2)]
    gate = Barrier(2, timeout=10)
    worker = local()
    all_calls = [[], []]

    def renderer(node, config, output):
        if output is None and not getattr(worker, "waited", False):
            worker.waited = True
            gate.wait()
        return fake_renderer(node, config, output)

    def execute_child(index):
        child = children[index]
        try:
            review.execute(
                child,
                Decimal("6.75"),
                transport=fake_provider(child, [("adequate", "v0")], all_calls[index]),
                renderer=renderer,
                extractor=fake_extract,
            )
            return "completed"
        except base.EvalError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute_child, (0, 1)))
    assert sorted(results) == ["completed", "continuation_already_claimed"]
    assert sorted(len(calls) for calls in all_calls) == [0, 2]


def test_independent_crash_after_claim_is_fail_closed(experiment, tmp_path, monkeypatch):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "crash-runs", extractor=fake_extract)
    original = base.immutable

    def crash_before_started(path, data):
        if path == run / "started.json":
            raise OSError("simulated process interruption")
        return original(path, data)

    monkeypatch.setattr(base, "immutable", crash_before_started)
    calls = []
    with pytest.raises(OSError):
        review.execute(run, Decimal("6.75"), transport=fake_provider(run, [], calls), renderer=fake_renderer)
    assert (parent / "continuation.json").exists() and not (run / "started.json").exists()
    monkeypatch.setattr(base, "immutable", original)
    with pytest.raises(base.EvalError, match="continuation_already_claimed"):
        review.execute(run, Decimal("6.75"), transport=fake_provider(run, [], calls), renderer=fake_renderer)
    assert not calls


def test_new_uncertain_effect_stops_other_independent_case(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "new-unknown", extractor=fake_extract)
    calls = []
    with pytest.raises(base.EvalError, match="experiment_stopped_results_preserved"):
        review.execute(
            run,
            Decimal("6.75"),
            transport=fake_provider(run, [], calls, mode="timeout"),
            renderer=fake_renderer,
            extractor=fake_extract,
        )
    assert calls == ["critique:v0"] and len(review.spending(run)[2]) == 2
    with pytest.raises(base.EvalError, match="unresolved_operation_no_new_effect"):
        review.call_model(
            run, "luma", "v0", "critique", {"fixture": True}, Decimal("6.75"), transport=fake_provider(run, [], calls)
        )
    assert calls == ["critique:v0"]


def test_independent_only_one_correction_and_two_critiques_per_untouched_case(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "corrected", extractor=fake_extract)
    calls = []
    result = review.execute(
        run,
        Decimal("6.75"),
        transport=fake_provider(run, [("needs_correction", "v0"), ("adequate", "v1")], calls),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    assert calls == ["critique:v0", "correction:v1", "critique:v1"] * 2
    assert result["paid_calls"] == 10
    assert result["committed_usd"] == "3.50"
    for case in result["cases"]:
        if case["id"] == "intensa":
            assert case["status"] == "blocked_uncertain"
        else:
            assert case["recommended_version"] == "v1"
            assert len([x for x in case["operations"] if x["kind"] == "critique"]) == 3
            assert len([x for x in case["operations"] if x["kind"] == "correction"]) == 1


def test_independent_never_repeats_a_previously_closed_case(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    base.event(parent, "case_stopped", case_id="dog", reason="previously_closed", recommended_version="v0")
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "closed", extractor=fake_extract)
    manifest = review.verify_inputs(run)
    assert manifest["eligible_case_ids"] == ["luma"]
    assert manifest["blocked_case_ids"] == ["dog", "intensa"]
    calls = []
    result = review.execute(
        run,
        Decimal("6.75"),
        transport=fake_provider(run, [("adequate", "v0")], calls),
        renderer=fake_renderer,
        extractor=fake_extract,
    )
    by_id = {x["id"]: x for x in result["cases"]}
    assert calls == ["critique:v0"]
    assert by_id["dog"]["status"] == "blocked_prior_case"
    assert by_id["intensa"]["status"] == "blocked_uncertain"


def test_independent_cannot_hide_unknown_request_or_send_arbitrary_body(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "unauthorized-body", extractor=fake_extract)
    base.immutable(parent / "continuation.json", base.json_bytes({"run": str(run.resolve())}))
    base.immutable(run / "started.json", base.json_bytes({"budget_usd": "6.75", "experiment_id": run.name}))
    original_body = review.read_json(next((parent / "operations").glob("*/request.json")))
    calls = []
    transport = fake_provider(run, [], calls)
    with pytest.raises(base.EvalError, match="unresolved_request_no_retry"):
        review.call_model(run, "dog", "v0", "critique", original_body, Decimal("6.75"), transport=transport)
    with pytest.raises(base.EvalError, match="independent_request_changed"):
        review.call_model(run, "dog", "v0", "critique", {"arbitrary": "content"}, Decimal("6.75"), transport=transport)
    assert calls == []


def test_independent_reuses_frozen_historical_cost_and_rights(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    item = review.read_json(parent / "sources.json")["cases"][1]
    old_source = Path(item["baseline_run"])
    (old_source / "cost.json").write_bytes(base.json_bytes({"estimated_usd": "999"}))
    (old_source / "response.body").write_bytes(b"altered response")
    (old_source / "rights.json").write_bytes(base.json_bytes([]))
    (old_source / "rights.txt").write_bytes(b"altered rights")
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "frozen", extractor=fake_extract)
    assert (run / "dog/historical-cost.json").read_bytes() == (parent / "dog/historical-cost.json").read_bytes()
    assert (run / "dog/historical-response.body").read_bytes() == (parent / "dog/historical-response.body").read_bytes()
    assert (run / "dog/rights.json").read_bytes() == (parent / "dog/rights.json").read_bytes()
    assert (run / "dog/rights.txt").read_bytes() == (parent / "dog/rights.txt").read_bytes()


def test_imported_unknown_cannot_be_cleared_by_appending_fake_cost(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "fake-reconcile", extractor=fake_extract)
    unknown = review.spending(run)[2][0]
    base.event(run, "cost_recorded", operation_id=unknown, estimated_usd="0")
    with pytest.raises(base.EvalError, match="imported_ledger_changed"):
        review.verify_inputs(run)


def test_directory_sync_failure_after_claim_stops_before_network(experiment, tmp_path, monkeypatch):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "sync-failure", extractor=fake_extract)
    monkeypatch.setattr(review, "sync_directory", lambda _: (_ for _ in ()).throw(OSError("sync failed")))
    calls = []
    with pytest.raises(OSError):
        review.execute(run, Decimal("6.75"), transport=fake_provider(run, [], calls), renderer=fake_renderer)
    assert (parent / "continuation.json").exists() and not calls


def test_same_child_concurrent_effects_have_one_reservation(experiment, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "same-child-race", extractor=fake_extract)
    base.immutable(parent / "continuation.json", base.json_bytes({"run": str(run.resolve())}))
    base.immutable(run / "started.json", base.json_bytes({"budget_usd": "6.75", "experiment_id": run.name}))
    request = review.review_request(run, "dog", "v0", "v0")
    gate = Barrier(2, timeout=10)
    calls = []

    def submit(_):
        gate.wait()
        try:
            review.call_model(
                run,
                "dog",
                "v0",
                "critique",
                request,
                Decimal("6.75"),
                transport=fake_provider(run, [("adequate", "v0")], calls),
            )
            return "completed"
        except base.EvalError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, (0, 1)))
    assert sorted(outcomes) == ["completed", "independent_effect_already_started_or_invalid"]
    assert calls == ["critique:v0"]
    assert (
        sum(
            x["state"] == "reserved" and x.get("case_id") == "dog" and not x.get("source_run")
            for x in review.journal(run)
        )
        == 1
    )


def test_cross_case_reservation_is_serialized_and_no_lock_held_during_http(experiment, tmp_path):
    import fcntl
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "cross-case", extractor=fake_extract)
    base.immutable(parent / "continuation.json", base.json_bytes({"run": str(run.resolve())}))
    base.immutable(run / "started.json", base.json_bytes({"budget_usd": "6.75", "experiment_id": run.name}))
    requests = {case: review.review_request(run, case, "v0", "v0") for case in ("dog", "luma")}
    entered = Event()
    finish = Event()

    def slow_transport(request):
        fd = os.open(run / ".effects.lock", os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        entered.set()
        assert finish.wait(10)
        return httpx.Response(200, json={"usage": {"input_tokens": 100, "output_tokens": 10}})

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(
            review.call_model,
            run,
            "dog",
            "v0",
            "critique",
            requests["dog"],
            Decimal("6.75"),
            transport=httpx.MockTransport(slow_transport),
        )
        assert entered.wait(10)
        try:
            with pytest.raises(base.EvalError, match="unresolved_operation_no_new_effect"):
                review.call_model(
                    run,
                    "luma",
                    "v0",
                    "critique",
                    requests["luma"],
                    Decimal("6.75"),
                    transport=httpx.MockTransport(lambda _: pytest.fail("must not dispatch")),
                )
        finally:
            finish.set()
        first.result(timeout=10)
    assert len([x for x in review.journal(run) if x["state"] == "reserved" and not x.get("source_run")]) == 1


def test_independent_budget_must_match_started(experiment, tmp_path):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "pinned-budget", extractor=fake_extract)
    base.immutable(parent / "continuation.json", base.json_bytes({"run": str(run.resolve())}))
    base.immutable(run / "started.json", base.json_bytes({"budget_usd": "3.50", "experiment_id": run.name}))
    with pytest.raises(base.EvalError, match="independent_budget_changed"):
        review.call_model(
            run,
            "dog",
            "v0",
            "critique",
            {},
            Decimal("6.75"),
            transport=httpx.MockTransport(lambda _: pytest.fail("must not dispatch")),
        )


def test_response_directory_sync_failure_is_unknown_not_received(experiment, tmp_path, monkeypatch):
    parent = independent_parent(experiment, tmp_path)
    source = independent_manifest(parent, tmp_path / "independent.json")
    run = review.prepare(source, runs=tmp_path / "response-sync", extractor=fake_extract)
    original_sync = review.sync_directory

    def fail_after_response(path):
        if (path / "response.body").is_file():
            raise OSError("simulated failure syncing response directory")
        return original_sync(path)

    monkeypatch.setattr(review, "sync_directory", fail_after_response)
    calls = []
    with pytest.raises(base.EvalError, match="experiment_stopped_results_preserved"):
        review.execute(
            run,
            Decimal("6.75"),
            transport=fake_provider(run, [("adequate", "v0")], calls),
            renderer=fake_renderer,
            extractor=fake_extract,
        )
    entries = review.journal(run)
    own = [x for x in entries if x["state"] == "reserved" and not x.get("source_run")]
    assert len(own) == 1 and calls == ["critique:v0"]
    operation_id = own[0]["operation_id"]
    assert any(x["state"] == "uncertain" and x.get("operation_id") == operation_id for x in entries)
    assert not any(
        x["state"] in {"received", "cost_recorded"} and x.get("operation_id") == operation_id for x in entries
    )
    assert operation_id in review.spending(run)[2]
