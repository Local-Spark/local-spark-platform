"""Private Giz snapshots, local replay and sampled evidence; no provider calls."""

from __future__ import annotations

import base64
import json
import math
import sys
import uuid
from fractions import Fraction
from pathlib import Path
from typing import Any

from scripts.evals import motion_declarative_render as media
from scripts.evals import motion_eval as base
from scripts.evals import motion_review_eval as review
from scripts.evals.motion_review_evidence import extract_evidence

PROPOSAL = base.ROOT / ".local/evals/motion-creative-review-giz-proposal-2026-11-08"
PROPOSAL_SHA = "486f5a2467b704cb488416fccbd6b72d639aadea5fcbfa3df073d3fff03f7d0d"
INVENTORY = base.ROOT / ".local/evals/motion-creative-review-giz-preparation-2026-11-08/baseline-text-inventory.json"
RUNS = base.ROOT / ".local/evals/motion-feedback-review-runs"
CASE = "giz"
SAMPLE_TIMES = [
    0,
    500,
    1500,
    2500,
    2782,
    2882,
    2982,
    3082,
    3182,
    4000,
    5500,
    7000,
    8000,
    8253,
    8353,
    8453,
    8553,
    8753,
    10000,
    11166,
]
ACTIVE_CODE = (
    "scripts/evals/motion_feedback_review_eval.py",
    "scripts/evals/motion_feedback_inputs.py",
    "scripts/evals/motion_feedback_contracts.py",
    "scripts/evals/motion_eval.py",
    "scripts/evals/motion_review_eval.py",
    "scripts/evals/motion_review_evidence.py",
    "scripts/evals/motion_declarative_render.py",
    "scripts/evals/motion_render.cjs",
    "scripts/evals/motion_audio.cjs",
    "uv.lock",
)


def verify_proposal(proposal: Path) -> dict[str, Any]:
    raw = (proposal / "manifest.json").read_bytes()
    if base.digest(raw) != PROPOSAL_SHA or (proposal / "manifest.sha256").read_text().split() != [
        PROPOSAL_SHA,
        "manifest.json",
    ]:
        raise base.EvalError("feedback_proposal_changed")
    manifest: dict[str, Any] = json.loads(raw)
    names: set[str] = set()
    for item in manifest["files"]:
        file = review.local(proposal, item["path"])
        if (
            item["path"] in names
            or (proposal / item["path"]).is_symlink()
            or file.stat().st_size != item["bytes"]
            or base.digest(file.read_bytes()) != item["sha256"]
        ):
            raise base.EvalError("feedback_proposal_file_changed")
        names.add(item["path"])
    return manifest


def verify_renderer(source: Path) -> None:
    trace = review.read_json(source / "baseline/render/trace.json")
    for path, key in (
        (base.RENDERER, "executor_sha256"),
        (base.RENDERER.with_name("motion_audio.cjs"), "audio_module_sha256"),
    ):
        if base.digest(path.read_bytes()) != trace[key]:
            raise base.EvalError("feedback_historical_renderer_changed")


def prepare(proposal: Path = PROPOSAL, *, runs: Path = RUNS, extractor: Any = extract_evidence) -> Path:
    manifest = verify_proposal(proposal)
    verify_renderer(proposal)
    runs.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = runs / f"proposal-{PROPOSAL_SHA}.json"
    if marker.exists():
        run = Path(review.read_json(marker)["run"]).resolve()
        if run.parent != runs.resolve():
            raise base.EvalError("feedback_preparation_identity_invalid")
        if not all((run / name).is_file() for name in ("manifest.json", "manifest.sha256", "pins.json")):
            raise base.EvalError(f"feedback_preparation_incomplete_preserved; run={run}")
        review.verify_inputs(run)
        return run
    run = runs / str(uuid.uuid4())
    run.mkdir(mode=0o700)
    base.immutable(marker, base.json_bytes({"run": str(run.resolve())}))
    source = run / "source"
    source.mkdir(mode=0o700)
    for item in manifest["files"]:
        target = review.local(source, item["path"])
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        review.snapshot(review.local(proposal, item["path"]), target, item["sha256"])
    review.snapshot(proposal / "manifest.json", source / "manifest.json")
    baseline = run / CASE / "v0"
    baseline.mkdir(mode=0o700, parents=True)
    for origin, name in (
        ("render/render.mp4", "render.mp4"),
        ("render/trace.json", "trace.json"),
        ("answer.json", "answer.json"),
    ):
        review.snapshot(source / "baseline" / origin, baseline / name)
    answer = base.Answer.model_validate(review.read_json(baseline / "answer.json"))
    trace = review.read_json(baseline / "trace.json")
    if (
        trace["output"]["sha256"] != base.digest((baseline / "render.mp4").read_bytes())
        or trace["html_sha256"] != base.digest(answer.html.encode())
        or trace["scene_sha256"] != base.digest(answer.scene_init.encode())
    ):
        raise base.EvalError("feedback_baseline_binding_invalid")
    case = review.read_json(source / "baseline/frozen-case.json")
    assets = review.read_json(source / "execution-assets.json")
    if len(assets["assets"]) != 6 or assets["reference_assets_allowed"] is not False:
        raise base.EvalError("feedback_asset_allowlist_invalid")
    for key in ("width", "height", "fps", "duration_ms"):
        if case[key] != assets[key]:
            raise base.EvalError("feedback_profile_changed")
    original_assets = [{k: v for k, v in item.items() if k != "path"} for item in case["assets"]]
    if original_assets != [{k: v for k, v in item.items() if k != "path"} for item in assets["assets"]]:
        raise base.EvalError("feedback_asset_allowlist_changed")
    case["assets"] = []
    for item in assets["assets"]:
        if not item["path"].startswith("baseline/assets/"):
            raise base.EvalError("reference_not_executable")
        case["assets"].append({**item, "path": str(review.local(source, item["path"]))})
    case["comparisons"] = []
    case["reference"] = {"path": str(baseline / "render.mp4"), "sha256": trace["output"]["sha256"]}
    case["body_path"] = str(source / "baseline/request.body")
    case["body_sha256"] = base.digest((source / "baseline/request.body").read_bytes())
    case["rights_files"] = [str(p) for p in sorted((source / "baseline").glob("rights-*"))]
    if answer.audio.model_dump() != base.Audio.model_validate(assets["frozen_audio"]).model_dump():
        raise base.EvalError("feedback_baseline_audio_changed")
    base.immutable(run / CASE / "case.json", base.json_bytes(case))
    context = {
        "experiment_type": "feedback_guided_creative_refinement",
        "original_generation_instructions": (source / "context-original/generation-instructions.txt").read_text(),
        "original_full_input_text": (source / "context-original/full-input-text.md").read_text(),
        "original_structured_context": review.read_json(source / "context-original/structured-case.json"),
        "later_feedback": review.read_json(source / "feedback/additional-context.json"),
        "new_visual_reference_context": review.read_json(source / "references/reference-context.json"),
        "requirements": review.read_json(source / "proposed-review-requirements.json"),
        "attribution": (
            "Feedback e quadros da Intensa são intervenções posteriores, não prova de erro do briefing original."
        ),
    }
    base.immutable(run / CASE / "context.json", base.json_bytes(context))
    inventory = review.read_json(INVENTORY)
    for name, sha in inventory["source_sha256"].items():
        if base.digest(review.local(source, name).read_bytes()) != sha:
            raise base.EvalError("feedback_text_inventory_source_changed")
    review.snapshot(INVENTORY, run / "baseline-text-inventory.json")
    review.snapshot(source / "baseline/cost.json", run / CASE / "historical-cost.json")
    review.snapshot(review.RUBRIC, run / "rubric.json")
    base.immutable(
        run / "sampling.json",
        base.json_bytes({"times_ms": SAMPLE_TIMES, "timestamp_semantics": "requested_seek_not_measured_pts"}),
    )
    extractor(
        baseline / "render.mp4",
        trace["output"]["sha256"],
        case["tools"],
        baseline / "evidence",
        extra_times_ms=SAMPLE_TIMES,
    )
    pins = {str(p.relative_to(run)): base.digest(p.read_bytes()) for p in run.rglob("*") if p.is_file()}
    base.immutable(run / "pins.json", base.json_bytes(pins))
    plan = {
        "experiment_id": run.name,
        "kind": "feedback_guided_creative_refinement",
        "context_version": 2,
        "max_corrections": 1,
        "maximum_reservations_usd": "1.25",
        "maximum_paid_calls": 2,
        "source_proposal": str(proposal.resolve()),
        "proposal_sha256": PROPOSAL_SHA,
        "pins_sha256": base.digest(base.json_bytes(pins)),
        "cases": [
            {
                "id": CASE,
                "label": "Giz — refinamento com feedback humano posterior",
                "baseline_cost_note": "US$ 0,2203975 da geração histórica registrada; não é fatura nem COGS completo.",
                "evaluation_context": {
                    "type": "feedback_guided_creative_refinement",
                    "statement": context["attribution"],
                    "requirements": [o["id"] for o in context["requirements"]["observables"]],
                    "references": "Intensa: seis quadros novos nesta revisão; v2 não enviada ao modelo.",
                    "approval": "pending_human_creative_review",
                },
            }
        ],
    }
    base.immutable(run / "manifest.json", base.json_bytes(plan))
    base.immutable(run / "manifest.sha256", base.digest(base.json_bytes(plan)).encode())
    base.event(run, "prepared", experiment_id=run.name)
    review.update_summary(run, "prepared", None, None)
    return run


def sampled_evidence(run: Path, version: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    evidence = review.version_evidence(run, CASE, version)
    times = review.read_json(run / "sampling.json")["times_ms"]
    frames = [frame for frame in evidence["frames"] if frame["timestamp_ms"] in times]
    if [frame["timestamp_ms"] for frame in frames] != times:
        raise base.EvalError("feedback_sampling_missing")
    projected = {
        **evidence,
        "frames": frames,
        "sampling_scope": "only selected frames are provided; seek times, not PTS",
    }
    content = [{"type": "input_text", "text": f"VERSÃO {version}; evidências fornecidas:\n" + json.dumps(projected)}]
    mapping = {}
    for frame in frames:
        identifier = f"{version}:{frame['frame_id']}"
        mapping[identifier] = frame["timestamp_ms"]
        content.extend(
            image_content(
                review.local(run / CASE / version / "evidence", frame["path"]), identifier, frame["sha256"], "image/png"
            )
        )
    return content, mapping


def image_content(file: Path, label: str, sha: str, mime: str) -> list[dict[str, Any]]:
    data = file.read_bytes()
    if base.digest(data) != sha:
        raise base.EvalError("feedback_image_changed")
    return [
        {"type": "input_text", "text": label},
        {
            "type": "input_image",
            "image_url": f"data:{mime};base64," + base64.b64encode(data).decode(),
            "detail": "high",
        },
    ]


def reference_content(run: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    source = run / "source"
    trace = review.read_json(source / "references/intensa/provenance/trace.json")
    streams = [s for s in trace["output"]["metadata"]["streams"] if s.get("codec_type") == "video"]
    try:
        fps = Fraction(streams[0]["avg_frame_rate"])
        if len(streams) != 1 or not 1 <= fps <= 120 or len(trace["snapshots"]) < 6:
            raise ValueError
    except (ValueError, IndexError, ZeroDivisionError) as error:
        raise base.EvalError("feedback_reference_profile_invalid") from error
    if base.digest((source / "references/intensa/reference.mp4").read_bytes()) != trace["output"]["sha256"]:
        raise base.EvalError("feedback_reference_video_changed")
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                "REFERÊNCIA NOVA: Intensa; seis screenshots JPEG históricos anteriores ao encode, sem "
                "vídeo contínuo/áudio. Tempos de render solicitados, não PTS. Fora da allowlist "
                "executável. V2 não fornecida."
            ),
        }
    ]
    mapping = {}
    for index, frame in enumerate(trace["snapshots"][:6]):
        identifier = f"ref:intensa:f{index:04d}"
        timestamp = round(frame["frame"] * 1000 / fps)
        if frame["state"]["time_ms"] != timestamp:
            raise base.EvalError("feedback_reference_timestamp_mismatch")
        mapping[identifier] = timestamp
        content.extend(
            image_content(
                source / "references/intensa/historical-frames" / frame["file"],
                f"{identifier}; render solicitado {timestamp} ms",
                frame["sha256"],
                "image/jpeg",
            )
        )
    return content, mapping


def original_source_content(run: Path) -> list[dict[str, Any]]:
    source = run / "source"
    content = []
    for frame in review.read_json(source / "context-original/image-provenance.json")["images"]:
        content.extend(
            image_content(
                review.local(source, frame["path"]),
                "MATERIAL ORIGINAL (não é referência criativa): " + frame["original_label"],
                frame["sha256"],
                "image/png",
            )
        )
    return content


def binding(run: Path) -> dict[str, Any]:
    manifest = review.verify_inputs(run)
    verify_renderer(run / "source")
    tools = review.read_json(run / CASE / "case.json")["tools"]
    if Path(tools["playwright"]).resolve() != media.PLAYWRIGHT.resolve():
        raise base.EvalError("feedback_playwright_changed")
    return {
        "manifest_sha256": base.digest((run / "manifest.json").read_bytes()),
        "pins_sha256": manifest["pins_sha256"],
        "tools": media.verify_tools(tools),
        "code": {name: base.digest((base.ROOT / name).read_bytes()) for name in ACTIVE_CODE},
        "python": {"version": sys.version, "executable_sha256": base.digest(Path(sys.executable).read_bytes())},
    }


def render(run: Path, target: Path, answer: base.Answer, *, renderer: Any = base.run_renderer) -> None:
    before = binding(run)
    case = review.read_json(run / CASE / "case.json")
    config = base.assemble(case, answer, target)
    output = target / "render"
    output.mkdir(mode=0o700)
    renderer(case["tools"]["node"], config, output)
    trace = review.read_json(output / "trace.json")
    original = review.read_json(run / "source/baseline/render/trace.json")
    if (
        trace["html_sha256"] != base.digest(answer.html.encode())
        or trace["scene_sha256"] != base.digest(answer.scene_init.encode())
        or any(trace[k] != original[k] for k in ("executor_sha256", "audio_module_sha256"))
        or trace["frame_count"] != math.ceil(case["duration_ms"] * case["fps"] / 1000)
        or trace["assets"] != [{"id": a["id"], "sha256": a["sha256"]} for a in case["assets"]]
        or trace.get("denied_requests") != 0
        or trace.get("browser_sandbox") is not True
        or "assets/video.mp4" not in trace["served_assets"]
        or not set(trace["served_assets"]).issubset({a["id"] for a in case["assets"]})
        or base.digest((output / "render.mp4").read_bytes()) != trace["output"]["sha256"]
    ):
        raise base.EvalError("feedback_render_binding_invalid")
    proof = media.freeze_audio(
        run / CASE / "v0/render.mp4", output / "render.mp4", target / "render.mp4", case["tools"]
    )
    base.immutable(target / "audio-preservation.json", base.json_bytes(proof))
    review.snapshot(output / "trace.json", target / "trace.json")
    base.immutable(
        target / "render-provenance.json",
        base.json_bytes(
            {
                "raw_video": {"path": "render/render.mp4", "sha256": trace["output"]["sha256"]},
                "raw_trace": "render/trace.json",
                "final_video": {"path": "render.mp4", "sha256": proof["output_sha256"]},
                "relationship": "Raw trace describes raw MP4; final MP4 copies baseline AAC without video re-encoding.",
            }
        ),
    )
    if binding(run) != before:
        raise base.EvalError("feedback_inputs_changed_during_render")
