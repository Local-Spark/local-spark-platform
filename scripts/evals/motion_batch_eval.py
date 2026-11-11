"""Private synthetic motion batch: offline plan or explicit bounded execution.

No retries. Each paid operation and uncertain reservation remains in its child run.
The batch budget is an admission reserve, not a guarantee of provider billing.
Batch markers check the default individual registry, but individual execution
does not consult batch markers. It may resend a batch request later or concurrently.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import html
import importlib
import json
import os
import sys
import threading
import uuid
import webbrowser
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

single = importlib.import_module("scripts.evals.motion_eval" if __package__ else "motion_eval")

ROOT = single.ROOT
BATCHES = ROOT / ".local/evals/motion-batches"
ALLOWED_ERRORS = {
    "request_uncertain_no_retry",
    "provider_http_status_no_retry",
    "invalid_response_saved_no_retry",
    "render_failed_response_and_cost_saved",
    "renderer_preflight_failed",
    "renderer_timeout",
    "input_hash_mismatch",
    "request_already_started_use_saved_response_offline",
    "missing_configured_api_key",
}


def _budget(value: Decimal | None) -> Decimal | None:
    if value is not None and (not value.is_finite() or value <= 0):
        raise single.EvalError("positive_budget_required")
    return value


def _label(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise single.EvalError("invalid_label")
    return value


def plan_manifest(manifest_path: Path, budget_usd: Decimal | None) -> dict[str, Any]:
    budget = _budget(budget_usd)
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"version", "id", "cases", "references"}
        or manifest["version"] != 1
        or not isinstance(manifest["id"], str)
        or not manifest["id"].strip()
        or len(manifest["id"]) > 160
    ):
        raise single.EvalError("invalid_manifest")
    items, refs = manifest["cases"], manifest["references"]
    if not isinstance(items, list) or not 1 <= len(items) <= 3 or not isinstance(refs, list) or len(refs) != 2:
        raise single.EvalError("invalid_batch_size")
    cases = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"label", "case_path"} or not isinstance(item["case_path"], str):
            raise single.EvalError("invalid_manifest")
        case_path = single.path(item["case_path"]).resolve()
        case_bytes = case_path.read_bytes()
        case, body = single.load_case(case_path, budget)
        cases.append(
            {
                "label": _label(item["label"]),
                "case_path": str(case_path),
                "case_sha256": single.digest(case_bytes),
                "request_sha256": single.digest(body),
                "reservation_usd": str(Decimal(case["reservation_usd"])),
            }
        )
    if len({x["request_sha256"] for x in cases}) != len(cases):
        raise single.EvalError("duplicate_request")
    total = sum((Decimal(x["reservation_usd"]) for x in cases), Decimal(0))
    if budget is not None and total > budget:
        raise single.EvalError("budget_exceeded")
    references = []
    for item in refs:
        if (
            not isinstance(item, dict)
            or set(item) != {"label", "path", "sha256"}
            or not isinstance(item["path"], str)
            or not isinstance(item["sha256"], str)
        ):
            raise single.EvalError("invalid_manifest")
        reference = single.verified_file(item).resolve()
        references.append({"label": _label(item["label"]), "path": str(reference), "sha256": item["sha256"]})
    return {
        "version": 1,
        "id": manifest["id"],
        "manifest_path": str(manifest_path.resolve()),
        "manifest_sha256": single.digest(raw),
        "budget_usd": str(budget) if budget is not None else None,
        "total_reservation_usd": str(total),
        "cases": cases,
        "references": references,
    }


def _safe_error(error: BaseException) -> str:
    code = str(error) if isinstance(error, single.EvalError) else ""
    return code if code in ALLOWED_ERRORS else "execution_failed"


def _cost(run: Path | None) -> str | None:
    if run is None:
        return None
    try:
        value = json.loads((run / "cost.json").read_bytes()).get("estimated_usd")
        if value is None or not Decimal(str(value)).is_finite() or Decimal(str(value)) < 0:
            return None
        return str(value)
    except (OSError, ValueError, TypeError, InvalidOperation):
        return None


def _mode(run: Path | None) -> str | None:
    if run is None:
        return None
    try:
        value = json.loads((run / "cost.json").read_bytes()).get("mode")
        return value if value in {"paid", "offline_response"} else None
    except (OSError, ValueError, TypeError):
        return None


def _report(batch: Path, plan: dict[str, Any], references: list[dict[str, str]], results: list[dict[str, Any]]) -> None:
    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    panels = []
    for item in results:
        label, state, run = esc(item["label"]), esc(item["state"]), item["run"]
        estimate = item["estimated_usd"] if item["estimated_usd"] is not None else "desconhecida"
        mode = item.get("mode") or "desconhecido"
        panel = f"<section><h2>{label}</h2><p>Estado: {state}; modo: {esc(mode)}; estimativa: {esc(estimate)} USD.</p>"
        if run and (batch / run / "render/render.mp4").is_file():
            src = esc(run + "/render/render.mp4")
            panel += f'<video controls playsinline src="{src}"></video><p><a href="{src}" download>Baixar MP4</a></p>'
        if run:
            for name, title in [
                ("request.body", "Pedido"),
                ("response.body", "Resposta"),
                ("answer.json", "Direção"),
                ("cost.json", "Custo"),
                ("ledger.jsonl", "Ledger"),
                ("renderer-error.log", "Erro de pré-teste"),
                ("render/renderer-error.log", "Erro do render"),
                ("render/trace.json", "Trace"),
                ("rights.json", "Direitos"),
                ("report.html", "Relatório individual"),
            ]:
                if (batch / run / name).is_file():
                    panel += f'<a href="{esc(run + "/" + name)}">{title}</a> · '
        if item["error"]:
            panel += f"<p>Motivo: {esc(item['error'])}</p>"
        panels.append(panel + "</section>")
    for item in references:
        src = esc(item["copy"])
        panels.append(
            f'<section><h2>{esc(item["label"])}</h2><video controls playsinline src="{src}"></video>'
            f'<p><a href="{src}" download>Baixar referência</a></p></section>'
        )
    content = f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; media-src 'self'">
<title>Motion — {esc(plan["id"])}</title>
<style>
body{{font:16px system-ui;max-width:1300px;margin:30px auto;padding:0 16px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:22px}}
video{{width:100%;max-height:70vh;background:#111}}
</style>
<h1>{esc(plan["id"])}</h1>
<p>Ensaio sintético privado. Reserva total US$ {esc(plan["total_reservation_usd"])};
orçamento US$ {esc(plan["budget_usd"])}.</p>
<p>Valores são estimativas, não fatura; valor desconhecido permanece desconhecido. Sem retry automático.</p>
<main>{"".join(panels)}</main>
<p><a href="results.json">Resultados</a> · <a href="plan.json">Plano</a> ·
<a href="manifest.json">Manifesto</a></p>"""
    single.immutable(batch / "report.html", content.encode())


def run_batch(
    plan: dict[str, Any], output_root: Path, execute_child: Callable[..., Path], open_report: bool = False
) -> Path:
    if plan.get("budget_usd") is None:
        raise single.EvalError("explicit_budget_required")
    budget = _budget(Decimal(plan["budget_usd"]))
    assert budget is not None
    # Recheck all sources and the complete cap before any worker or provider access.
    current = plan_manifest(Path(plan["manifest_path"]), budget)
    if current != plan:
        raise single.EvalError("batch_plan_changed")
    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    batch = output_root / str(uuid.uuid4())
    batch.mkdir(mode=0o700)
    (batch / "assets").mkdir(mode=0o700)
    (batch / "cases").mkdir(mode=0o700)
    (batch / "runs").mkdir(mode=0o700)
    manifest_bytes = Path(plan["manifest_path"]).read_bytes()
    if single.digest(manifest_bytes) != plan["manifest_sha256"]:
        raise single.EvalError("input_hash_mismatch")
    single.immutable(batch / "manifest.json", manifest_bytes)
    single.immutable(batch / "plan.json", single.json_bytes(plan))
    frozen_refs = []
    for index, ref in enumerate(plan["references"]):
        data = Path(ref["path"]).read_bytes()
        if single.digest(data) != ref["sha256"]:
            raise single.EvalError("input_hash_mismatch")
        copy = f"assets/reference-{index + 1}.mp4"
        single.immutable(batch / copy, data)
        frozen_refs.append({"label": ref["label"], "copy": copy, "sha256": ref["sha256"]})
    single.immutable(batch / "references.json", single.json_bytes(frozen_refs))
    frozen_cases = []
    for index, case in enumerate(plan["cases"]):
        data = Path(case["case_path"]).read_bytes()
        if single.digest(data) != case["case_sha256"]:
            raise single.EvalError("input_hash_mismatch")
        target = batch / "cases" / f"case-{index + 1}.json"
        single.immutable(target, data)
        frozen_cases.append(target)
    # Batch-level durable markers prevent a later batch from silently resending
    # the same body, including when a prior outcome is uncertain. The short
    # filesystem lock is released before workers start and before any network.
    registry = output_root / "requests"
    registry.mkdir(mode=0o700, exist_ok=True)
    with (output_root / ".requests.lock").open("a+b") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        try:
            markers = [registry / (case["request_sha256"] + ".json") for case in plan["cases"]]
            individual = [single.RUNS / ("request-" + case["request_sha256"] + ".json") for case in plan["cases"]]
            if any(marker.exists() for marker in [*markers, *individual]):
                raise single.EvalError("request_already_registered")
            for case, marker in zip(plan["cases"], markers, strict=True):
                single.immutable(
                    marker,
                    single.json_bytes(
                        {"request_sha256": case["request_sha256"], "batch": str(batch), "state": "prepared"}
                    ),
                )
            directory = os.open(registry, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            fcntl.flock(guard.fileno(), fcntl.LOCK_UN)
    render_lock = threading.Lock()

    def one(index: int) -> dict[str, Any]:
        item = plan["cases"][index]
        found_run: Path | None = None

        def guarded_renderer(node: str, config: Path, output: Path | None) -> None:
            nonlocal found_run
            found_run = config.parent if output is None else output.parent
            with render_lock:
                single.run_renderer(node, config, output)

        state, error = "completed", None
        try:
            found_run = execute_child(
                frozen_cases[index], Decimal(item["reservation_usd"]), runs=batch / "runs", renderer=guarded_renderer
            )
        except Exception as exc:
            error = _safe_error(exc)
            state = "uncertain" if error == "request_uncertain_no_retry" else "failed"
        relative = None
        if found_run is not None:
            try:
                relative = str(found_run.resolve().relative_to(batch.resolve()))
            except ValueError:
                state, error, found_run = "failed", "execution_failed", None
        return {
            "label": item["label"],
            "state": state,
            "run": relative,
            "estimated_usd": _cost(found_run),
            "mode": _mode(found_run),
            "error": error,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(one, i) for i in range(len(frozen_cases))]
        results = [f.result() for f in futures]
    known = [Decimal(x["estimated_usd"]) for x in results if x["estimated_usd"] is not None]
    summary = {
        "results": results,
        "estimated_total_usd": str(sum(known, Decimal(0))) if len(known) == len(results) else None,
        "reservation_usd": plan["total_reservation_usd"],
        "invoice_verified": False,
    }
    single.immutable(batch / "results.json", single.json_bytes(summary))
    _report(batch, plan, frozen_refs, results)
    if open_report:
        webbrowser.open((batch / "report.html").resolve().as_uri())
    return batch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--budget-usd", type=Decimal)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    try:
        if args.execute and args.budget_usd is None:
            raise single.EvalError("explicit_budget_required")
        plan = plan_manifest(args.manifest, args.budget_usd)
        if not args.execute:
            print(json.dumps({"mode": "offline_preflight", **plan}, ensure_ascii=False, indent=2))
            return 0
        result = run_batch(plan, BATCHES, single.execute, open_report=args.open)
        print(f"Relatório privado: {result / 'report.html'}", flush=True)
        return 0
    except (single.EvalError, ValueError, KeyError, TypeError, OSError, InvalidOperation) as exc:
        code = str(exc) if isinstance(exc, single.EvalError) else "invalid_batch"
        print(f"Lote interrompido: {code}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
