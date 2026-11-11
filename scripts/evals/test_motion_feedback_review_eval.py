"""Synthetic two-effect flow: no model, browser or real media commands."""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from PIL import Image

from scripts.evals import motion_eval as base
from scripts.evals import motion_feedback_contracts as contracts
from scripts.evals import motion_feedback_inputs as inputs
from scripts.evals import motion_feedback_review_eval as feedback
from scripts.evals import motion_review_eval as review
from scripts.evals.motion_review_evidence import LIMITATIONS
from scripts.evals.test_motion_review_eval import criticism, make_answer, put


def extractor(video: Path, sha: str, _tools: dict, output: Path, *, extra_times_ms: list[int]) -> dict:
    assert base.digest(video.read_bytes()) == sha
    output.mkdir(parents=True)
    frames = []
    for index, timestamp in enumerate(sorted(set(range(0, 11167, 500)) | {11166} | set(extra_times_ms))):
        name = f"f{index:04}.png"
        Image.new("RGB", (64, 96), (index, 0, 0)).save(output / name)
        frames.append(
            {
                "frame_id": name[:-4],
                "path": name,
                "timestamp_ms": timestamp,
                "sha256": base.digest((output / name).read_bytes()),
            }
        )
    result = {
        "version": 1,
        "video_sha256": sha,
        "duration_ms": 11200,
        "width": 64,
        "height": 96,
        "fps": 30,
        "frames": frames,
        "limitations": LIMITATIONS,
        "technical": {"audio_present": True, "decode_ok": True, "audio_mean_db": -18, "audio_peak_db": -2},
    }
    put(output / "evidence.json", result)
    return result


def renderer(_node: str, config: Path, output: Path | None) -> None:
    if output is None:
        return
    value = review.read_json(config)
    video = ("video:" + value["scene_init"]["sha256"]).encode()
    (output / "render.mp4").write_bytes(video)
    put(
        output / "trace.json",
        {
            "html_sha256": value["html"]["sha256"],
            "scene_sha256": value["scene_init"]["sha256"],
            "executor_sha256": base.digest(base.RENDERER.read_bytes()),
            "audio_module_sha256": base.digest(base.RENDERER.with_name("motion_audio.cjs").read_bytes()),
            "frame_count": math.ceil(value["fps"] * value["duration_ms"] / 1000),
            "assets": [{"id": a["id"], "sha256": a["sha256"]} for a in value["assets"]],
            "denied_requests": 0,
            "browser_sandbox": True,
            "served_assets": ["assets/video.mp4"],
            "output": {"sha256": base.digest(video)},
        },
    )


def freeze(original: Path, video: Path, output: Path, _tools: dict) -> dict:
    output.write_bytes(video.read_bytes())
    return {
        "baseline_sha256": base.digest(original.read_bytes()),
        "output_sha256": base.digest(output.read_bytes()),
        "aac_packets_and_timing_equal": True,
        "pcm_equal": True,
    }


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setenv("MEU_BRACO_DIREITO_OPENAI_API_KEY", "synthetic-key-never-log")
    monkeypatch.setattr(inputs.media, "verify_tools", lambda tools: {"synthetic_tools": tools})
    monkeypatch.setattr(inputs.media, "freeze_audio", freeze)
    monkeypatch.setattr(inputs.media, "video_signature", lambda video, _tools: {"rgb": base.digest(video.read_bytes())})
    proposal = tmp_path / "proposal"
    answer = make_answer()
    answer["audio"] = {
        "mode": "mix",
        "tracks": [{"asset_id": "voice", "trim_start_ms": 0, "trim_end_ms": 11180, "offset_ms": 0, "volume": 1.0}],
    }
    put(proposal / "baseline/answer.json", answer)
    (proposal / "baseline/scene.html").write_text(answer["html"])
    (proposal / "baseline/scene.js").write_text(answer["scene_init"])
    put(proposal / "baseline/request.body", {"original": True})
    put(proposal / "baseline/cost.json", {"estimated_usd": "0.2203975"})
    (proposal / "baseline/rights-0.txt").write_text("synthetic rights")
    assets = []
    for index in range(6):
        relative = f"baseline/assets/{index}.bin"
        file = proposal / relative
        file.parent.mkdir(exist_ok=True)
        file.write_bytes(f"synthetic asset {index}".encode())
        item = {
            "id": "assets/video.mp4" if index == 0 else f"assets/fixture{index}",
            "path": relative,
            "mime": "video/mp4" if index == 0 else "application/octet-stream",
            "sha256": base.digest(file.read_bytes()),
        }
        if index == 1:
            item["audio_id"] = "voice"
        assets.append(item)
    profile = {"width": 64, "height": 96, "fps": 30, "duration_ms": 11180}
    tools = {k: "/synthetic/tool" for k in ("node", "chromium", "ffmpeg", "ffprobe")}
    tools["playwright"] = str(inputs.media.PLAYWRIGHT)
    put(
        proposal / "execution-assets.json",
        {**profile, "assets": assets, "frozen_audio": answer["audio"], "reference_assets_allowed": False},
    )
    case = {**profile, "assets": assets, "tools": tools, "synthetic_fixture": True}
    put(proposal / "baseline/frozen-case.json", case)
    target = proposal / "baseline/render"
    target.mkdir()
    config = tmp_path / "mock-config.json"
    put(
        config,
        {
            **profile,
            "assets": assets,
            "html": {"sha256": base.digest(answer["html"].encode())},
            "scene_init": {"sha256": base.digest(answer["scene_init"].encode())},
        },
    )
    renderer("", config, target)
    (proposal / "context-original").mkdir()
    (proposal / "context-original/generation-instructions.txt").write_text("ALL original generation instructions")
    (proposal / "context-original/full-input-text.md").write_text("ALL original full source, skill and context")
    put(proposal / "context-original/structured-case.json", {"original": "complete facts"})
    put(proposal / "feedback/additional-context.json", {"literal": "later human feedback, not original defect"})
    put(proposal / "references/reference-context.json", {"intensa": "new context", "v2": "not supplied"})
    put(
        proposal / "proposed-review-requirements.json",
        {"observables": [{"id": k} for k in sorted(contracts.REQUIREMENT_IDS)]},
    )
    sources, references = [], []
    for index in range(6):
        for directory, suffix in (("context-original/images", "png"), ("references/intensa/historical-frames", "jpg")):
            file = proposal / directory / f"frame{index}.{suffix}"
            file.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (64, 96), (index, 1, 1)).save(file)
            sha = base.digest(file.read_bytes())
            if suffix == "png":
                sources.append(
                    {"path": str(file.relative_to(proposal)), "original_label": f"Original {index}", "sha256": sha}
                )
            else:
                references.append(
                    {"file": file.name, "frame": index * 60, "sha256": sha, "state": {"time_ms": index * 2000}}
                )
    put(proposal / "context-original/image-provenance.json", {"images": sources})
    reference_video = b"synthetic reference video, never an executable asset"
    (proposal / "references/intensa/reference.mp4").write_bytes(reference_video)
    put(
        proposal / "references/intensa/provenance/trace.json",
        {
            "snapshots": references,
            "output": {
                "sha256": base.digest(reference_video),
                "metadata": {"streams": [{"codec_type": "video", "avg_frame_rate": "30/1"}]},
            },
        },
    )
    inventory = tmp_path / "inventory.json"
    put(
        inventory,
        {
            "purpose": "Local inspection only",
            "source_sha256": {
                name: base.digest((proposal / name).read_bytes())
                for name in ("baseline/answer.json", "baseline/scene.html", "baseline/scene.js")
            },
        },
    )
    monkeypatch.setattr(inputs, "INVENTORY", inventory)
    files = [
        {"path": str(p.relative_to(proposal)), "sha256": base.digest(p.read_bytes()), "bytes": p.stat().st_size}
        for p in proposal.rglob("*")
        if p.is_file()
    ]
    put(proposal / "manifest.json", {"files": files})
    sha = base.digest((proposal / "manifest.json").read_bytes())
    (proposal / "manifest.sha256").write_text(f"{sha}  manifest.json\n")
    monkeypatch.setattr(inputs, "PROPOSAL_SHA", sha)
    return inputs.prepare(proposal, runs=tmp_path / "runs", extractor=extractor), proposal


def authorize(run: Path) -> None:
    feedback.qualify(run, renderer=renderer)
    put(
        run / "authorization.json",
        {
            **feedback.authorization_binding(run, Decimal("1.25")),
            "decision": "authorized",
            "source": "synthetic user grant for this experiment",
        },
    )


def transport(run: Path, calls: list[str], *, mode: str = "") -> httpx.MockTransport:
    def respond(request: httpx.Request) -> httpx.Response:
        operation = request.headers["X-Client-Request-Id"]
        binding = review.read_json(run / "operations" / operation / "binding.json")
        kind = binding["kind"]
        calls.append(kind)
        assert review.journal(run)[-1]["state"] == "reserved"
        assert base.digest(request.content) == binding["request_sha256"]
        if mode == "timeout":
            raise httpx.ReadTimeout("synthetic private text")
        if mode == "no_usage":
            return httpx.Response(200, json={"status": "completed"})
        if mode == "invalid_json":
            return httpx.Response(200, content=b"invalid")
        if kind == "correction":
            answer = feedback.baseline(run).model_dump(mode="json")
            answer["scene_init"] += "; /* synthetic modified motion */"
            value = {
                "composition": answer,
                "changes": "New motion with narrative purpose",
                "addressed_requirement_ids": sorted(contracts.REQUIREMENT_IDS),
            }
            if mode == "changed_audio":
                answer["audio"]["tracks"][0]["volume"] = 0.5
        else:
            value = criticism(
                run, "v1", "needs_correction" if mode == "regression" else "adequate", "v1", case_id="giz"
            )
            value.update(
                {
                    "human_approval": "pending",
                    "alignment_status": "met",
                    "brief_alignment": [
                        {
                            "requirement_id": identifier,
                            "status": "met",
                            "evidence_ids": ["v0:f0000", "v1:f0000", "v1:f0001"],
                            "reference_evidence_ids": ["ref:intensa:f0000"],
                            "narrative_role": "Question to invitation",
                            "reason": "Synthetic",
                        }
                        for identifier in sorted(contracts.REQUIREMENT_IDS)
                    ],
                }
            )
            if mode == "unprovided_frame":
                value["brief_alignment"][0]["evidence_ids"] = ["v0:f0000", "v1:f0000", "v1:f0002"]
            elif mode == "reference_as_evidence":
                value["criteria"][0]["evidence_ids"] = ["ref:intensa:f0000"]
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "usage": {"input_tokens": 100, "output_tokens": 10},
                "output": [{"content": [{"type": "output_text", "text": json.dumps(value)}]}],
            },
        )

    return httpx.MockTransport(respond)


def refined(run: Path, calls: list[str]) -> None:
    authorize(run)
    feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))


def rendered(run: Path, calls: list[str]) -> None:
    refined(run, calls)
    feedback.inspect(run, "code", approved=True, reviewer="test operator", notes="Inspected source and credits")
    feedback.render_candidate(run, renderer=renderer, extractor=extractor)
    feedback.inspect(run, "artifact", approved=True, reviewer="test operator", notes="Inspected rendered content")


def test_prepare_keeps_sources_and_sampling_separate_without_credentials(experiment, monkeypatch):
    run, proposal = experiment
    monkeypatch.setattr(base, "api_key", lambda: pytest.fail("not during local preparation"))
    assert inputs.prepare(proposal, runs=run.parent, extractor=extractor) == run
    assert (run / "giz/v0/render.mp4").read_bytes() == (proposal / "baseline/render/render.mp4").read_bytes()
    assert (run / "source/context-original/full-input-text.md").read_bytes() == (
        proposal / "context-original/full-input-text.md"
    ).read_bytes()
    assert not (run / "operations").exists() and not (proposal / "feedback-execution.json").exists()
    request = feedback.request_for(run, "correction")
    content = request["input"][0]["content"]
    assert sum(c["type"] == "input_image" for c in content) == 32
    assert request["max_output_tokens"] == 32000 and request["store"] is False
    assert "ALL original generation instructions" in content[0]["text"]
    assert "ALL original full source, skill and context" in content[0]["text"]
    assert "HUMANO POSTERIOR" in request["instructions"]
    assert "met/not_met" not in request["instructions"]
    assert list(inputs.sampled_evidence(run, "v0")[1].values()) == inputs.SAMPLE_TIMES
    assets = review.read_json(run / "giz/case.json")["assets"]
    assert len(assets) == 6 and all("/source/baseline/assets/" in a["path"] for a in assets)
    assert review.read_json(run / "summary.json")["cases"][0]["costs"]["historical_estimated_usd"] == "0.2203975"


def test_two_calls_require_two_local_inspections_and_keep_human_pending(experiment):
    run, _ = experiment
    calls = []
    rendered(run, calls)
    request = feedback.request_for(run, "critique")
    assert sum(c["type"] == "input_image" for c in request["input"][0]["content"]) == 52
    assert request["max_output_tokens"] == 8000
    result = feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction", "critique"]
    assert result["status"] == "completed_human_pending"
    assert result["cases"][0]["recommended_version"] == "v1"
    assert (run / "giz/v1/render/render.mp4").exists() and (run / "giz/v1/render/trace.json").exists()
    assert (run / "giz/v0/critique.json").exists() is False
    for action in (
        lambda: feedback.execute(run, Decimal("1.25"), transport=transport(run, calls)),
        lambda: feedback.finish(run, Decimal("1.25"), transport=transport(run, calls)),
        lambda: feedback.call(run, "correction", Decimal("1.25"), transport=transport(run, calls)),
    ):
        with pytest.raises((base.EvalError, FileExistsError)):
            action()
    assert len(calls) == 2


@pytest.mark.parametrize("budget", ["0", "1.00", "1.26", "NaN", "Infinity"])
def test_budget_mismatch_has_zero_effects(experiment, budget):
    run, proposal = experiment
    calls = []
    with pytest.raises(base.EvalError, match="budget"):
        feedback.execute(run, Decimal(budget), transport=transport(run, calls))
    assert not calls and not (proposal / "feedback-execution.json").exists() and not (run / "started.json").exists()


def test_qualification_and_authorization_before_claim(experiment):
    run, proposal = experiment
    calls = []
    with pytest.raises(base.EvalError, match="qualification_required"):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
    feedback.qualify(run, renderer=renderer)
    with pytest.raises(FileNotFoundError):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
    put(run / "authorization.json", {"decision": "authorized", "source": "old unrelated grant"})
    with pytest.raises(base.EvalError, match="authorization_required"):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
    assert not calls and not (proposal / "feedback-execution.json").exists()


@pytest.mark.parametrize("mode", ["timeout", "no_usage", "invalid_json", "changed_audio"])
def test_failed_effect_stops_without_retry_and_preserves_response(experiment, mode):
    run, _ = experiment
    calls = []
    authorize(run)
    with pytest.raises(base.EvalError):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls, mode=mode))
    with pytest.raises(base.EvalError):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction"]
    assert len([e for e in review.journal(run) if e["state"] == "reserved"]) == 1
    assert review.read_json(run / "summary.json")["status"] == "stopped"
    if mode != "timeout":
        assert len(list((run / "operations").glob("*/response.body"))) == 1


def test_out_of_order_commands_and_uninspected_render_have_zero_new_effect(experiment):
    run, _ = experiment
    calls = []
    refined(run, calls)
    journal = (run / "ledger.jsonl").read_bytes()
    with pytest.raises(FileNotFoundError):
        feedback.render_candidate(run, renderer=renderer, extractor=extractor)
    with pytest.raises(FileNotFoundError):
        feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    with pytest.raises(base.EvalError, match="out_of_order"):
        feedback.call(run, "correction", Decimal("1.25"), transport=transport(run, calls))
    assert (run / "ledger.jsonl").read_bytes() == journal and calls == ["correction"]


@pytest.mark.parametrize("stage", ["code", "artifact"])
def test_rejected_local_inspection_stops_before_next_effect(experiment, stage):
    run, _ = experiment
    calls = []
    refined(run, calls)
    if stage == "artifact":
        feedback.inspect(run, "code", approved=True, reviewer="operator", notes="Reviewed code")
        feedback.render_candidate(run, renderer=renderer, extractor=extractor)
    feedback.inspect(run, stage, approved=False, reviewer="operator", notes="Factual text changed")
    with pytest.raises(base.EvalError, match="stopped"):
        feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction"]


@pytest.mark.parametrize("change", ["proposal", "context", "qualification", "artifact", "code", "tool"])
def test_qualification_tampering_blocks_before_payment(experiment, monkeypatch, change):
    run, proposal = experiment
    authorize(run)
    if change in {"code", "tool"}:
        original = inputs.binding
        monkeypatch.setattr(inputs, "binding", lambda r: {**original(r), change: "changed"})
    else:
        path = {
            "proposal": proposal / "feedback/additional-context.json",
            "context": run / "giz/context.json",
            "qualification": run / "qualification.json",
            "artifact": run / "qualification/replay/render.mp4",
        }[change]
        path.write_bytes(path.read_bytes() + b" ")
    calls = []
    with pytest.raises(base.EvalError):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
    assert not calls and not (run / "started.json").exists()


def test_replay_mismatch_never_qualifies(experiment, monkeypatch):
    run, _ = experiment
    monkeypatch.setattr(inputs.media, "video_signature", lambda path, _tools: {"different": str(path)})
    with pytest.raises(base.EvalError, match="replay_changed"):
        feedback.qualify(run, renderer=renderer)
    assert not (run / "qualification.json").exists()
    assert (run / "qualification/replay/render/render.mp4").exists()


@pytest.mark.parametrize("change", ["answer", "response", "inspection", "evidence", "audio"])
def test_changed_candidate_or_inspection_cannot_reach_paid_comparison(experiment, change):
    run, _ = experiment
    calls = []
    rendered(run, calls)
    file = {
        "answer": run / "giz/v1/answer.json",
        "response": next((run / "operations").glob("*/response.body")),
        "inspection": run / "inspection-artifact.json",
        "evidence": run / "giz/v1/evidence/f0000.png",
        "audio": run / "giz/v1/audio-preservation.json",
    }[change]
    if change in {"answer", "audio"}:
        value = review.read_json(file)
        value["concept" if change == "answer" else "pcm_equal"] = "Changed" if change == "answer" else False
        put(file, value)
    else:
        file.write_bytes(file.read_bytes() + b" ")
    with pytest.raises(ValueError):
        feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction"]


@pytest.mark.parametrize("mode", ["regression", "unprovided_frame", "reference_as_evidence"])
def test_comparison_regression_and_evidence_scope_are_enforced(experiment, mode):
    run, _ = experiment
    calls = []
    rendered(run, calls)
    if mode == "regression":
        summary = feedback.finish(run, Decimal("1.25"), transport=transport(run, calls, mode=mode))
        assert summary["cases"][0]["recommended_version"] == "v0"
    else:
        with pytest.raises(base.EvalError):
            feedback.finish(run, Decimal("1.25"), transport=transport(run, calls, mode=mode))
        assert not (run / "giz/v1/critique.json").exists()
    assert calls == ["correction", "critique"]


def test_only_one_concurrent_refinement_can_dispatch(experiment):
    run, _ = experiment
    calls = []
    authorize(run)

    def worker():
        try:
            feedback.execute(run, Decimal("1.25"), transport=transport(run, calls))
            return True
        except (base.EvalError, FileExistsError):
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sorted(results) == [False, True] and calls == ["correction"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("denied_requests", 1),
        ("browser_sandbox", False),
        ("frame_count", 335),
        ("served_assets", ["references/intensa/reference.mp4"]),
        ("scene_sha256", "0" * 64),
        ("executor_sha256", "0" * 64),
        ("assets", []),
    ],
)
def test_render_trace_must_match_allowlist_profile_and_current_code(experiment, field, value):
    run, _ = experiment
    calls = []
    refined(run, calls)
    feedback.inspect(run, "code", approved=True, reviewer="operator", notes="Source inspected")

    def altered(node, config, output):
        renderer(node, config, output)
        trace = review.read_json(output / "trace.json")
        trace[field] = value
        put(output / "trace.json", trace)

    with pytest.raises(base.EvalError, match="render_stopped"):
        feedback.render_candidate(run, renderer=altered, extractor=extractor)
    assert (run / "giz/v1/render/render.mp4").exists()
    assert not (run / "giz/v1/render.mp4").exists() and calls == ["correction"]


def test_freeze_audio_failure_preserves_raw_render_and_blocks_critique(experiment, monkeypatch):
    run, _ = experiment
    calls = []
    refined(run, calls)
    feedback.inspect(run, "code", approved=True, reviewer="operator", notes="Source inspected")

    def divergent(original, video, output, tools):
        return {**freeze(original, video, output, tools), "pcm_equal": False}

    monkeypatch.setattr(inputs.media, "freeze_audio", divergent)
    with pytest.raises(base.EvalError, match="render_stopped"):
        feedback.render_candidate(run, renderer=renderer, extractor=extractor)
    with pytest.raises(base.EvalError, match="stopped"):
        feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    assert (run / "giz/v1/render/render.mp4").exists() and calls == ["correction"]


def test_known_cost_above_reservation_blocks_remaining_call(experiment):
    run, _ = experiment
    calls = []
    rendered(run, calls)
    operation = next(e["operation_id"] for e in review.journal(run) if e["state"] == "reserved")
    # Local cost reconciliation may discover a charge greater than admission reserve.
    base.event(run, "cost_recorded", operation_id=operation, estimated_usd="1.10")
    with pytest.raises(base.EvalError, match="budget_for_remaining_effects_required"):
        feedback.finish(run, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction"] and not (run / "effect-critique-v1.json").exists()


def test_reference_png_and_manifest_mutation_cannot_be_sent(experiment):
    run, proposal = experiment
    file = proposal / "references/intensa/historical-frames/frame0.jpg"
    file.write_bytes(file.read_bytes() + b"changed")
    with pytest.raises(base.EvalError, match="proposal_file_changed"):
        inputs.verify_proposal(proposal)
    file = run / "source/references/intensa/historical-frames/frame0.jpg"
    file.write_bytes(file.read_bytes() + b"changed")
    with pytest.raises(base.EvalError, match="image_changed"):
        inputs.reference_content(run)


def test_frozen_request_cannot_change_after_offline_qualification(experiment, monkeypatch):
    run, _ = experiment
    authorize(run)
    original = feedback.request_for
    monkeypatch.setattr(feedback, "request_for", lambda r, k: {**original(r, k), "max_output_tokens": 123})
    with pytest.raises(base.EvalError, match="qualification_changed"):
        feedback.execute(run, Decimal("1.25"), transport=transport(run, []))
    assert not (run / "started.json").exists()


@pytest.mark.parametrize("filename", ["other.json", "../manifest.json", "/manifest.json", "manifest.json extra"])
def test_proposal_checksum_sidecar_requires_the_bound_filename(experiment, filename):
    _, proposal = experiment
    (proposal / "manifest.sha256").write_text(f"{inputs.PROPOSAL_SHA}  {filename}\n")
    with pytest.raises(base.EvalError, match="proposal_changed"):
        inputs.verify_proposal(proposal)


@pytest.mark.parametrize("change", ["fps", "time", "video"])
def test_reference_profile_and_screenshot_time_are_linked(experiment, change):
    run, _ = experiment
    path = run / "source/references/intensa/provenance/trace.json"
    trace = review.read_json(path)
    if change == "fps":
        trace["output"]["metadata"]["streams"][0]["avg_frame_rate"] = "60/1"
    elif change == "time":
        trace["snapshots"][1]["state"]["time_ms"] = 2001
    else:
        trace["output"]["sha256"] = "0" * 64
    put(path, trace)
    with pytest.raises(base.EvalError):
        inputs.reference_content(run)


def test_legacy_execute_rejects_feedback_run_before_preflight_or_claim(experiment):
    run, proposal = experiment
    calls = []
    with pytest.raises(base.EvalError, match="requires_its_own_executor"):
        review.execute(
            run,
            Decimal("1.25"),
            transport=transport(run, calls),
            renderer=lambda *_: pytest.fail("legacy renderer must not start"),
            extractor=extractor,
        )
    assert not calls and not (run / "started.json").exists() and not (proposal / "feedback-execution.json").exists()


@pytest.mark.parametrize("stage", ["prepared", "authorized", "missing_intent", "modified_request", "wrong_identity"])
def test_direct_shared_transport_cannot_bypass_admission(experiment, stage):
    run, proposal = experiment
    calls = []
    if stage != "prepared":
        authorize(run)
    if stage not in {"prepared", "authorized"}:
        put(proposal / "feedback-execution.json", {"run": str(run.resolve())})
        put(
            run / "started.json",
            {
                "experiment_id": run.name,
                "budget_usd": "1.25",
                "authorization_sha256": base.digest((run / "authorization.json").read_bytes()),
            },
        )
    request = feedback.request_for(run, "correction")
    if stage in {"modified_request", "wrong_identity"}:
        put(run / "effect-correction-v1.json", {"request_sha256": base.digest(base.json_bytes(request))})
    if stage == "modified_request":
        request["max_output_tokens"] = 64000
    with pytest.raises((ValueError, FileNotFoundError)):
        review.call_model(
            run,
            "giz",
            "v0" if stage == "wrong_identity" else "v1",
            "correction",
            request,
            Decimal("1.25"),
            transport=transport(run, calls),
        )
    assert not calls and not (run / "operations").exists()
    assert not (run / "dispatch-correction-v1.json").exists()


def test_direct_critique_without_inspection_is_blocked(experiment):
    run, _ = experiment
    calls = []
    refined(run, calls)
    feedback.inspect(run, "code", approved=True, reviewer="operator", notes="Code reviewed")
    feedback.render_candidate(run, renderer=renderer, extractor=extractor)
    request = feedback.request_for(run, "critique")
    put(run / "effect-critique-v1.json", {"request_sha256": base.digest(base.json_bytes(request))})
    with pytest.raises(FileNotFoundError):
        review.call_model(run, "giz", "v1", "critique", request, Decimal("1.25"), transport=transport(run, calls))
    assert calls == ["correction"] and not (run / "dispatch-critique-v1.json").exists()


def test_existing_dispatch_marker_prevents_direct_repeat_without_a_reservation(experiment):
    run, proposal = experiment
    authorize(run)
    put(proposal / "feedback-execution.json", {"run": str(run.resolve())})
    put(
        run / "started.json",
        {
            "experiment_id": run.name,
            "budget_usd": "1.25",
            "authorization_sha256": base.digest((run / "authorization.json").read_bytes()),
        },
    )
    request = feedback.request_for(run, "correction")
    marker = {"request_sha256": base.digest(base.json_bytes(request))}
    put(run / "effect-correction-v1.json", marker)
    put(run / "dispatch-correction-v1.json", marker)
    calls = []
    with pytest.raises(FileExistsError):
        review.call_model(run, "giz", "v1", "correction", request, Decimal("1.25"), transport=transport(run, calls))
    assert not calls and not (run / "operations").exists()


def test_incomplete_preparation_preserves_identity_and_reports_its_directory(experiment):
    run, proposal = experiment
    fresh_runs = run.parent.parent / "failed-preparation"

    def failed(*_args, **_kwargs):
        raise ValueError("synthetic extraction failure")

    with pytest.raises(ValueError, match="extraction failure"):
        inputs.prepare(proposal, runs=fresh_runs, extractor=failed)
    marker = fresh_runs / f"proposal-{inputs.PROPOSAL_SHA}.json"
    incomplete = Path(review.read_json(marker)["run"])
    assert (incomplete / "giz/v0/render.mp4").exists() and not (incomplete / "manifest.json").exists()
    with pytest.raises(base.EvalError, match="preparation_incomplete_preserved") as error:
        inputs.prepare(proposal, runs=fresh_runs, extractor=extractor)
    assert str(incomplete) in str(error.value)
    assert [p for p in fresh_runs.iterdir() if p.is_dir()] == [incomplete]
