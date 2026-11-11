"""One synthetic motion evaluation: offline plan, one paid response, render/report.

No automatic retries or installs. A repeated paid request reuses a finished run;
an uncertain request cannot be sent again. Provider output and intervention files
remain separate. This local harness is not the production application.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import signal
import subprocess
import sys
import time
import uuid
import webbrowser
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "https://api.openai.com/v1/responses"
RENDERER = ROOT / "scripts/evals/motion_render.cjs"
RUNS = ROOT / ".local/evals/motion-runs"


class EvalError(ValueError):
    pass


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SourceUsage(StrictModel):
    source: str
    functions: list[str]
    adaptations: str


class AudioTrack(StrictModel):
    asset_id: str
    trim_start_ms: int = Field(ge=0)
    trim_end_ms: int = Field(gt=0)
    offset_ms: int = Field(ge=0)
    volume: float = Field(ge=0, le=1)


class Audio(StrictModel):
    mode: str
    tracks: list[AudioTrack] = Field(max_length=16)


class Answer(StrictModel):
    concept: str
    source_usage: list[SourceUsage]
    html: str = Field(min_length=1, max_length=1_000_000)
    scene_init: str = Field(min_length=1, max_length=1_000_000)
    audio: Audio


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path(value: str) -> Path:
    result = Path(value)
    return result if result.is_absolute() else ROOT / result


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def immutable(destination: Path, data: bytes) -> None:
    with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def event(run: Path, state: str, **fields: Any) -> None:
    data = json.dumps({"state": state, **fields}, sort_keys=True).encode() + b"\n"
    with os.fdopen(os.open(run / "ledger.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "ab") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def verified_file(item: dict[str, Any]) -> Path:
    source = path(item["path"])
    if digest(source.read_bytes()) != item["sha256"]:
        raise EvalError("input_hash_mismatch")
    return source


def load_case(case_path: Path, budget: Decimal | None) -> tuple[dict[str, Any], bytes]:
    case = json.loads(case_path.read_bytes())
    if case.get("version") != 1 or case.get("synthetic_fixture") is not True:
        raise EvalError("synthetic_case_required")
    reserve = Decimal(case["reservation_usd"])
    if budget is not None and (not budget.is_finite() or budget <= 0):
        raise EvalError("positive_budget_required")
    if not reserve.is_finite() or reserve <= 0 or (budget is not None and reserve > budget):
        raise EvalError("budget_exceeded")
    body = verified_file({"path": case["body_path"], "sha256": case["body_sha256"]}).read_bytes()
    request = json.loads(body)
    allowed = {"input", "instructions", "model", "reasoning", "service_tier", "store", "text", "max_output_tokens"}
    if (
        not set(request).issubset(allowed)
        or request.get("store") is not False
        or request.get("model") != "gpt-6.1-sol"
        or request.get("reasoning", {}).get("effort") != "high"
        or request.get("service_tier", "default") != "default"
        or type(request.get("max_output_tokens")) is not int
        or not 1 <= request["max_output_tokens"] <= 32000
        or request.get("text", {}).get("format", {}).get("type") != "json_schema"
        or request["text"]["format"].get("strict") is not True
    ):
        raise EvalError("unsupported_request")
    if not 1 <= case["duration_ms"] <= 60000 or case["fps"] != 30:
        raise EvalError("unsupported_profile")
    comparisons = case.get("comparisons", [])
    if not isinstance(comparisons, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("label"), str) or not item["label"].strip()
        for item in comparisons
    ):
        raise EvalError("invalid_comparisons")
    for item in [*case["assets"], case["reference"], *comparisons]:
        verified_file(item)
    return case, body


def renderer_config(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "synthetic_fixture": True,
        "executable_paths": {
            name: str(path(case["tools"][name])) for name in ("playwright", "chromium", "ffmpeg", "ffprobe")
        },
    }


def run_renderer(node: str, config: Path, output: Path | None) -> None:
    args = [str(path(node)), str(RENDERER)]
    args += ["--preflight", str(config)] if output is None else [str(config), str(output)]
    process = subprocess.Popen(
        args,
        env={"PATH": "/usr/bin:/bin", "TMPDIR": os.getenv("TMPDIR", "/tmp"), "LANG": "C.UTF-8"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=120 if output is None else 960)
    except subprocess.TimeoutExpired as error:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise EvalError("renderer_timeout") from error
    if process.returncode:
        diagnostic = (output if output is not None else config.parent) / "renderer-error.log"
        immutable(diagnostic, stdout[-16000:] + b"\n" + stderr[-16000:])
        raise EvalError("renderer_preflight_failed" if output is None else "renderer_failed")


def parse_answer(raw: bytes) -> tuple[Answer, dict[str, Any]]:
    value = json.loads(raw)
    if set(value) == set(Answer.model_fields):
        return Answer.model_validate(value), {}
    if value.get("status") != "completed":
        raise EvalError("provider_not_completed")
    texts = [
        part["text"]
        for output in value.get("output", [])
        for part in output.get("content", [])
        if part.get("type") == "output_text"
    ]
    if len(texts) != 1:
        raise EvalError("missing_structured_output")
    return Answer.model_validate_json(texts[0]), value.get("usage", {})


def assemble(case: dict[str, Any], answer: Answer, run: Path) -> Path:
    if answer.audio.mode not in {"silent", "mix"} or (answer.audio.mode == "mix") != bool(answer.audio.tracks):
        raise EvalError("invalid_audio_mode")
    audio_ids = {item["audio_id"] for item in case["assets"] if "audio_id" in item}
    if not set(case.get("required_audio_ids", [])).issubset({track.asset_id for track in answer.audio.tracks}):
        raise EvalError("required_audio_missing")
    for track in answer.audio.tracks:
        if (
            track.asset_id not in audio_ids
            or track.trim_end_ms <= track.trim_start_ms
            or track.offset_ms + track.trim_end_ms - track.trim_start_ms > case["duration_ms"]
        ):
            raise EvalError("invalid_audio_asset_or_interval")
    config = renderer_config(case)
    config.update({name: case[name] for name in ("width", "height", "fps", "duration_ms")})
    config["assets"] = [{**item, "path": str(verified_file(item))} for item in case["assets"]]
    config["audio"] = answer.audio.model_dump()
    for name, content, filename in [("html", answer.html, "scene.html"), ("scene_init", answer.scene_init, "scene.js")]:
        data = content.encode()
        immutable(run / filename, data)
        immutable(run / f"{filename}.txt", data)
        config[name] = {"path": str(run / filename), "sha256": digest(data)}
    destination = run / "render-config.json"
    immutable(destination, json_bytes(config))
    return destination


def api_key() -> str:
    key = os.getenv("MEU_BRACO_DIREITO_OPENAI_API_KEY")
    if not key:
        key = dotenv_values(ROOT / ".env").get("MEU_BRACO_DIREITO_OPENAI_API_KEY")
    if not key:
        raise EvalError("missing_configured_api_key")
    return key


def report(run: Path, case: dict[str, Any], summary: dict[str, Any]) -> None:
    title = html.escape(str(case["id"]))
    videos = [("Resultado", "render/render.mp4")]
    for item in [case["reference"], *case.get("comparisons", [])]:
        videos.append((str(item.get("label", "Referência v2")), os.path.relpath(verified_file(item), run)))
    players = "".join(
        f"<section><h2>{html.escape(label)}</h2>"
        f'<video aria-label="{html.escape(label)}" src="{html.escape(source)}" controls playsinline></video>'
        f'<p><a href="{html.escape(source)}">Abrir MP4</a> · '
        f'<a href="{html.escape(source)}" download>Baixar MP4</a></p></section>'
        for label, source in videos
    )
    frames = "".join(
        f'<img src="render/{html.escape(frame.name)}" alt="Quadro {index}">'
        for index, frame in enumerate(sorted((run / "render").glob("quadro-*.jpg")))
    )
    body = f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Motion — {title}</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:30px auto;padding:0 16px}}
.videos{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:24px}}
.videos section{{min-width:0}}video{{width:100%;max-height:70vh;background:#111}}
h2{{font-size:1.2rem}}.frames img{{width:130px;max-width:20%}}</style>
<h1>{title}</h1><p>Modo: {html.escape(summary["mode"])}. Replay offline não é nova direção por modelo.</p>
<p>Estimativa desta execução: US$ {html.escape(str(summary["estimated_usd"]))}; não é fatura.</p>
<div class="videos">{players}</div>
<div class="frames">{frames}</div>
<p><a href="render/trace.json">Trace do render</a> · <a href="response.body">Resposta bruta</a> ·
<a href="answer.json">Direção</a> · <a href="summary.json">Custo/estado</a></p>
<p><a href="scene.html.txt">HTML como texto</a> · <a href="scene.js.txt">Código da animação</a> ·
<a href="request.body">Pedido/modelo</a> · <a href="ledger.jsonl">Etapas</a></p>
<p><a href="rights.json">Fontes, licenças e avisos preservados</a></p>
<p>Ensaio sintético privado. Compare movimento, fala, legibilidade e referência antes do aceite final.</p>"""
    immutable(run / "report.html", body.encode())


def quota_rejection(previous: Path, request_sha256: str) -> dict[str, Any]:
    """Recognize only a recorded quota rejection, never infer it from absent usage."""
    try:
        ledger = (previous / "ledger.jsonl").read_bytes()
        entries = [json.loads(line) for line in ledger.splitlines()]
        raw = (previous / "response.body").read_bytes()
        response = json.loads(raw)
        if (
            [entry["state"] for entry in entries] != ["reserved", "received", "rejected"]
            or entries[0]["operation_id"] != previous.name
            or entries[0]["request_sha256"] != request_sha256
            or digest((previous / "request.body").read_bytes()) != request_sha256
            or entries[1]["http_status"] != 429
            or entries[1]["response_sha256"] != digest(raw)
            or entries[2].get("reason") != "provider_http_status"
            or set(response) not in ({"error"}, {"error", "usage"})
            or ("usage" in response and response["usage"] != {})
            or response["error"]["type"] != "insufficient_quota"
            or response["error"]["code"] != "credit_balance_exhausted"
        ):
            raise EvalError("retry_requires_recorded_quota_rejection_without_usage_or_output")
        return {
            "operation_id": previous.name,
            "run": str(previous),
            "ledger_sha256": digest(ledger),
            "response_sha256": digest(raw),
            "reservation_usd_preserved": entries[0]["reservation_usd"],
        }
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise EvalError("retry_requires_recorded_quota_rejection_without_usage_or_output") from error


def execute(
    case_path: Path,
    budget: Decimal | None,
    *,
    cached: Path | None = None,
    runs: Path = RUNS,
    client: httpx.Client | None = None,
    renderer: Any = run_renderer,
    retry_rejected: bool = False,
) -> Path:
    case, body = load_case(case_path, budget)
    if cached is None and budget is None:
        raise EvalError("explicit_budget_required")
    if retry_rejected and (cached is not None or budget is None):
        raise EvalError("retry_requires_paid_execution_and_new_budget")
    runs.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = runs / f"request-{digest(body)}.json"
    retry_of = None
    visited = set()
    while cached is None and marker.exists():
        if marker in visited:
            raise EvalError("invalid_retry_chain")
        visited.add(marker)
        previous = Path(json.loads(marker.read_bytes())["run"])
        if (previous / "summary.json").exists() and (previous / "report.html").exists():
            print(f"Reuso sem nova chamada: {previous}", flush=True)
            return previous
        successor = runs / f"request-{digest(body)}-after-{previous.name}.json"
        if not retry_rejected and not successor.exists():
            raise EvalError("request_already_started_use_saved_response_offline")
        retry_of = quota_rejection(previous, digest(body))
        marker = successor
    if retry_rejected and retry_of is None:
        raise EvalError("no_previous_quota_rejection")
    if retry_of is not None and not retry_rejected:
        raise EvalError("request_already_started_use_saved_response_offline")
    operation = str(uuid.uuid4())
    run = runs / operation
    run.mkdir(mode=0o700)
    print(f"RUN: {run}", flush=True)
    immutable(run / "case.json", json_bytes(case))
    immutable(run / "request.body", body)
    if retry_of is not None:
        immutable(run / "retry-intent.json", json_bytes({"retry_of": retry_of, "new_budget_usd": str(budget)}))
    asset_dir = run / "assets"
    asset_dir.mkdir(mode=0o700)
    frozen = []
    asset_count = len(case["assets"])
    for index, item in enumerate([*case["assets"], case["reference"], *case.get("comparisons", [])]):
        data = path(item["path"]).read_bytes()
        if digest(data) != item["sha256"]:
            raise EvalError("input_hash_mismatch")
        destination = asset_dir / f"{index}-{path(item['path']).name}"
        immutable(destination, data)
        frozen.append({**item, "path": str(destination)})
    case = {
        **case,
        "assets": frozen[:asset_count],
        "reference": frozen[asset_count],
        "comparisons": frozen[asset_count + 1 :],
    }
    immutable(run / "frozen-case.json", json_bytes(case))
    rights = []
    for index, source in enumerate(case.get("rights_files", [])):
        data = path(source).read_bytes()
        filename = f"rights-{index}-{path(source).name}"
        immutable(run / filename, data)
        rights.append({"source": source, "copy": filename, "sha256": digest(data)})
    immutable(run / "rights.json", json_bytes(rights))
    preflight = run / "preflight.json"
    immutable(preflight, json_bytes(renderer_config(case)))
    print("Etapa: preflight local do renderer", flush=True)
    renderer(case["tools"]["node"], preflight, None)
    usage: dict[str, Any] = {}
    if cached is not None:
        print("Etapa: resposta local offline; nenhuma chamada ao modelo", flush=True)
        raw = cached.read_bytes()
        immutable(run / "response.body", raw)
        event(run, "offline_response", source_sha256=digest(raw), reservation_usd="0")
    else:
        if retry_of is not None and quota_rejection(Path(retry_of["run"]), digest(body)) != retry_of:
            raise EvalError("prior_rejection_changed")
        key = api_key()
        try:
            immutable(marker, json_bytes({"run": str(run), "operation_id": operation}))
        except FileExistsError as error:
            raise EvalError("request_already_started") from error
        event(
            run,
            "reserved",
            operation_id=operation,
            reservation_usd=case["reservation_usd"],
            request_sha256=digest(body),
            **({"retry_of": retry_of} if retry_of is not None else {}),
        )
        if retry_of is not None and quota_rejection(Path(retry_of["run"]), digest(body)) != retry_of:
            event(run, "not_sent", reason="prior_rejection_changed")
            raise EvalError("prior_rejection_changed")
        started = time.monotonic()
        print(f"Etapa: modelo; uma chamada, operação {operation}", flush=True)
        try:
            with client or httpx.Client(
                transport=httpx.HTTPTransport(retries=0, trust_env=False),
                trust_env=False,
                follow_redirects=False,
                timeout=httpx.Timeout(600, connect=30),
            ) as http:
                response = http.post(
                    ENDPOINT,
                    content=body,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "X-Client-Request-Id": operation,
                    },
                    follow_redirects=False,
                )
            raw = response.content
            immutable(run / "response.body", raw)
            event(
                run,
                "received",
                http_status=response.status_code,
                response_sha256=digest(raw),
                seconds=time.monotonic() - started,
            )
        except Exception as error:
            event(run, "uncertain", reason="transport_or_recording_failed")
            raise EvalError("request_uncertain_no_retry") from error
    try:
        decoded = json.loads(raw)
        usage = decoded.get("usage", {}) if isinstance(decoded, dict) else {}
    except (ValueError, TypeError):
        usage = {}
    measured = isinstance(usage, dict) and all(
        type(usage.get(name)) is int and usage[name] >= 0 for name in ("input_tokens", "output_tokens")
    )
    estimated = (
        Decimal(0)
        if cached
        else (
            (Decimal(usage["input_tokens"]) * Decimal("2.50") + Decimal(usage["output_tokens"]) * Decimal("10"))
            / Decimal(1_000_000)
            if measured
            else None
        )
    )
    cost = {
        "operation_id": operation,
        "mode": "offline_response" if cached else "paid",
        "usage": usage,
        "estimated_usd": str(estimated) if estimated is not None else None,
        "invoice_verified": False,
        "estimate_basis": "All input charged conservatively at $2.50/M; output $10/M includes reasoning.",
        "reservation_usd": "0" if cached else case["reservation_usd"],
    }
    immutable(run / "cost.json", json_bytes(cost))
    if cached is None and response.status_code != 200:
        event(run, "rejected", reason="provider_http_status")
        raise EvalError("provider_http_status_no_retry")
    try:
        answer, _ = parse_answer(raw)
        immutable(run / "answer.json", json_bytes(answer.model_dump()))
        config = assemble(case, answer, run)
    except (ValueError, KeyError, TypeError) as error:
        event(run, "rejected", reason="invalid_response_or_assets")
        raise EvalError("invalid_response_saved_no_retry") from error
    output = run / "render"
    output.mkdir(mode=0o700)
    print("Etapa: render local do MP4 e quadros", flush=True)
    try:
        renderer(case["tools"]["node"], config, output)
    except Exception as error:
        event(run, "render_failed", reason="use_saved_response_offline")
        raise EvalError("render_failed_response_and_cost_saved") from error
    event(run, "completed", response_sha256=digest(raw), estimated_usd=str(estimated))
    immutable(run / "summary.json", json_bytes({**cost, "state": "completed"}))
    report(run, case, cost)
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--budget-usd", type=Decimal)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--execute", action="store_true")
    group.add_argument("--from-response", type=Path)
    group.add_argument("--render-only", type=Path, metavar="CONFIG_JSON")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--retry-rejected", action="store_true")
    args = parser.parse_args()
    try:
        if args.retry_rejected and (not args.execute or args.budget_usd is None):
            raise EvalError("retry_requires_execute_and_new_budget")
        if args.budget_usd is not None and (not args.budget_usd.is_finite() or args.budget_usd <= 0):
            raise EvalError("positive_budget_required")
        if args.render_only:
            config = json.loads(args.render_only.read_bytes())
            if config.get("synthetic_fixture") is not True:
                raise EvalError("synthetic_case_required")
            if not args.case:
                raise EvalError("case_required_for_node_path")
            case, _ = load_case(args.case, args.budget_usd)
            output = RUNS / str(uuid.uuid4())
            output.mkdir(parents=True, mode=0o700)
            run_renderer(case["tools"]["node"], args.render_only, output)
            print(f"Render offline: {output}")
            return 0
        if not args.case:
            raise EvalError("case_required")
        case, body = load_case(args.case, args.budget_usd)
        print(
            json.dumps(
                {
                    "case": case["id"],
                    "model": "gpt-6.1-sol",
                    "effort": "high",
                    "planned_paid_calls": 0 if args.from_response else 1,
                    "mode": "offline" if args.from_response else ("execute" if args.execute else "preflight"),
                    "estimated_cost_usd": case.get("estimated_cost_usd"),
                    "request_bytes": len(body),
                    "reservation_usd": "0" if args.from_response else case["reservation_usd"],
                    "budget_usd": str(args.budget_usd) if args.budget_usd else None,
                    "estimate": "Not an invoice; reserve bounds admission, not provider billing.",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if not args.execute and args.from_response is None:
            print("Preflight offline. Para executar a chamada: --execute e --budget-usd explícitos.")
            return 0
        run = execute(args.case, args.budget_usd, cached=args.from_response, retry_rejected=args.retry_rejected)
        print(f"Resultado e trace: {run / 'report.html'}")
        if args.open:
            webbrowser.open((run / "report.html").as_uri())
        return 0
    except (EvalError, ValidationError, KeyError, OSError, InvalidOperation, json.JSONDecodeError) as error:
        print(
            f"Motion eval interrompido: {error if isinstance(error, EvalError) else type(error).__name__}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
