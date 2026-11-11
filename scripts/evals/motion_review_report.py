"""Standalone, local human-review report for a motion evaluation run."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _asset(run: Path, value: object) -> tuple[str, Path] | None:
    """Only permit existing regular files inside the run, including resolved symlinks."""
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = Path(value)
    if path.is_absolute() or any(part in {"..", "."} for part in path.parts):
        return None
    if ":" in value or "?" in value or "#" in value:
        return None
    root = run.resolve()
    try:
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            return None
    except (OSError, RuntimeError, ValueError):
        return None
    return quote(path.as_posix(), safe="/"), resolved


def _link(run: Path, value: object, label: str) -> str:
    asset = _asset(run, value)
    if asset is None:
        return f'<span class="missing">{_escape(label)} indisponível</span>'
    return f'<a href="{_escape(asset[0])}" download>{_escape(label)}</a>'


def _critique(run: Path, value: object) -> str:
    asset = _asset(run, value)
    if asset is None:
        return '<p class="missing">Crítica indisponível.</p>'
    try:
        data = json.loads(asset[1].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return '<p class="missing">Crítica não pôde ser lida.</p>'
    if not isinstance(data, dict):
        return '<p class="missing">Crítica em formato inesperado.</p>'
    result = ['<details class="identified"><summary>Crítica do modelo</summary>']
    overall = data.get("overall", "não informado")
    if overall == "adequate":
        result.append(
            "<p>Resultado: nenhum outro defeito acionável identificado nas evidências avaliadas "
            "(código original: <code>adequate</code>).</p>"
        )
    else:
        result.append(f"<p>Resultado: {_escape(overall)}</p>")
    if "brief_alignment" in data:
        status = data.get("alignment_status", "não informado")
        label = {"met": "atendido nas amostras", "not_met": "não atendido", "uncertain": "incerto"}.get(
            str(status), "não informado"
        )
        result.append(
            f"<h4>Atendimento ao feedback posterior</h4><p>Resultado agregado: {_escape(label)} "
            f"(código original: {_escape(status)}). Movimento observado e atendimento ao briefing são avaliações "
            "distintas. Referências orientam a análise; não substituem evidências das versões comparadas. "
            "Aprovação criativa depende da avaliação humana dos vídeos completos.</p>"
        )
        if not isinstance(data["brief_alignment"], list):
            result.append('<p class="missing">Alinhamento em formato inesperado.</p>')
    raw_limitations = data.get("limitations", [])
    limitations = (
        [item for item in raw_limitations if isinstance(item, str) and item.strip()]
        if isinstance(raw_limitations, list)
        else []
    )
    result.append("<h4>Limitações desta avaliação</h4>")
    if limitations:
        result.append("<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in limitations) + "</ul>")
    if not isinstance(raw_limitations, list) or len(limitations) != len(raw_limitations):
        result.append('<p class="missing">Há registros de limitações em formato inválido ou vazio, não exibidos.</p>')
    elif not limitations:
        result.append('<p class="missing">Limitações não informadas.</p>')
    for key, title, fields in (
        ("criteria", "Critérios", ("criterion", "status", "evidence_ids", "observation")),
        (
            "issues",
            "Pontos de ajuste",
            ("id", "criterion", "severity", "evidence_ids", "start_ms", "end_ms", "problem", "correction"),
        ),
        (
            "brief_alignment",
            "Requisitos do feedback e evidências",
            ("requirement_id", "status", "evidence_ids", "reference_evidence_ids", "narrative_role", "reason"),
        ),
    ):
        if key == "brief_alignment" and key not in data:
            continue
        rows = data.get(key, [])
        if not isinstance(rows, list):
            continue
        result.append(f'<h4>{_escape(title)}</h4><div class="table-wrap"><table><thead><tr>')
        result.extend(f"<th>{_escape(field)}</th>" for field in fields)
        result.append("</tr></thead><tbody>")
        for row in rows:
            if isinstance(row, dict):
                result.append("<tr>")
                result.extend(f"<td>{_escape(row.get(field, ''))}</td>" for field in fields)
                result.append("</tr>")
        result.append("</tbody></table></div>")
    preference = data.get("preference")
    if isinstance(preference, dict):
        result.append(
            f"<p>Preferência sugerida: {_escape(preference.get('version_id', ''))} — "
            f"{_escape(preference.get('reason', ''))}</p>"
        )
    result.append("</details>")
    return "".join(result)


def _label(index: int) -> str:
    # Excel-like labels keep even unusually large comparison sets distinct.
    label = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label


def _cost(value: object) -> str:
    return "não informado" if value is None else f"US$ {_escape(value)}"


def _operations(operations: object, *, show_version: bool = False, feedback_context: bool = False) -> str:
    if not isinstance(operations, list) or not operations:
        return "<p>Sem operações registradas.</p>"
    rows = ['<div class="table-wrap"><table><thead><tr>']
    fields: tuple[tuple[str, str], ...] = (("version_id", "Versão"),) if show_version else ()
    fields += (
        ("kind", "Etapa"),
        ("context_scope", "Contexto"),
        ("status", "Estado"),
        ("estimated_usd", "Estimativa"),
        ("reservation_usd", "Reserva"),
        ("seconds", "Segundos"),
    )
    rows.extend(f"<th>{_escape(label)}</th>" for _, label in fields)
    rows.append("</tr></thead><tbody>")
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        rows.append("<tr>")
        for name, _ in fields:
            value = operation.get(name)
            if name == "context_scope" and isinstance(value, str):
                value = {
                    "initial_incomplete_context": "Avaliação inicial com contexto incompleto",
                    "creative_context_v2": "Feedback humano posterior + referência adicional"
                    if feedback_context
                    else "Contexto criativo completo v2",
                }.get(value, value)
            rendered = (
                _cost(value) if name.endswith("_usd") else _escape(value if value is not None else "não informado")
            )
            rows.append(f"<td>{rendered}</td>")
        rows.append("</tr>")
    rows.append("</tbody></table></div>")
    return "".join(rows)


def _version(run: Path, version: dict[str, Any], index: int, *, feedback_context: bool = False) -> str:
    version_id = str(version.get("id", ""))
    blind = _label(index)
    duration = version.get("stage_seconds")
    duration = duration if duration is not None else "não informado"
    asset = _asset(run, version.get("video_path"))
    video = (
        f'<video controls preload="metadata" src="{_escape(asset[0])}"></video>'
        if asset
        else '<p class="missing">Vídeo indisponível.</p>'
    )
    return "".join(
        (
            '<article class="version">',
            f'<h3 class="version-label" data-blind="{blind}" data-identified="{_escape(version_id)}">{blind}</h3>',
            video,
            f"<p>{_link(run, version.get('video_path'), 'Baixar vídeo')}</p>",
            f'<p class="identified">Rodada: {_escape(version.get("round", ""))} · Tempo: {_escape(duration)} s</p>',
            f'<p class="identified hash">SHA-256: {_escape(version.get("video_sha256", ""))}</p>',
            f'<p class="identified">Recomendação do modelo: '
            f"{_escape(version.get('model_recommendation') or 'nenhuma')}</p>",
            f'<p class="identified">{_link(run, version.get("evidence_path"), "Evidências")}</p>',
            '<details class="identified"><summary>Operações e custos desta versão</summary>',
            _operations(version.get("operations"), feedback_context=feedback_context),
            "</details>",
            _critique(run, version.get("critique_path")),
            "</article>",
        )
    )


def _case(run: Path, case: dict[str, Any]) -> str:
    case_id = str(case.get("id", ""))
    versions = [v for v in case.get("versions", []) if isinstance(v, dict)]
    parts = [
        f'<section class="case" data-case-id="{_escape(case_id)}">',
        f"<h2>{_escape(case.get('label', case_id))}</h2>",
        f"<p>Status: {_escape(case.get('status', ''))} · "
        f"Motivo de parada: {_escape(case.get('stop_reason') or 'nenhum')}</p>",
        f"<p>Custo da versão inicial: {_escape(case.get('baseline_cost_note', 'não informado'))}</p>",
        f'<p class="identified">Versão recomendada pelo modelo: '
        f"{_escape(case.get('recommended_version') or 'nenhuma')}</p>",
    ]
    context = case.get("evaluation_context")
    feedback_context = isinstance(context, dict) and context.get("type") == "feedback_guided_creative_refinement"
    if isinstance(context, dict):
        parts.append('<details class="identified"><summary>Contexto desta comparação</summary>')
        for key, label in (
            ("type", "Tipo"),
            ("statement", "Origem do contexto"),
            ("requirements", "Requisitos posteriores"),
            ("references", "Referências fornecidas"),
            ("approval", "Estado do aceite humano"),
        ):
            if key in context:
                parts.append(f"<p>{_escape(label)}: {_escape(context[key])}</p>")
        parts.append("</details>")
    costs = case.get("costs")
    if isinstance(costs, dict):
        unknown = costs.get("unknown_operations")
        unknown_text = ", ".join(map(str, unknown)) if isinstance(unknown, list) and unknown else "nenhuma"
        parts.extend(
            (
                f"<p>Estimativa histórica: {_cost(costs.get('historical_estimated_usd'))} · "
                f"Incremental: {_cost(costs.get('incremental_estimated_usd'))} · "
                f"Subtotal estimado das APIs registradas: {_cost(costs.get('estimated_total_usd'))} · "
                f"Comprometido: {_cost(costs.get('committed_usd'))} · "
                f"Tentativas de API: {_escape(costs.get('paid_calls', 'não informado'))}</p>",
                f"<p>Operações com custo desconhecido neste caso: {_escape(unknown_text)}</p>",
                '<details class="identified"><summary>Todas as operações deste caso</summary>',
                _operations(case.get("operations"), show_version=True, feedback_context=feedback_context),
                "</details>",
            )
        )
    if len(versions) < 2:
        parts.append("<p>Sem nova versão para comparar.</p>")
    parts.append('<div class="versions">')
    for index, version in enumerate(versions):
        parts.append(_version(run, version, index, feedback_context=feedback_context))
    parts.append("</div><fieldset><legend>Sua avaliação</legend>")
    parts.append('<label>Preferência <select class="choice"><option value="">Não avaliada</option>')
    for index, version in enumerate(versions):
        version_id = str(version.get("id", ""))
        parts.append(
            f'<option value="{_escape(version_id)}" data-blind="{_label(index)}" '
            f'data-identified="{_escape(version_id)}">{_label(index)}</option>'
        )
    parts.append('<option value="tie">Empate</option><option value="none">Nenhuma</option></select></label>')
    parts.append(
        '<label>Decisão sobre a peça <select class="decision"><option value="undecided">Pendente</option>'
        '<option value="accepted">Aceitar</option><option value="rejected">Rejeitar</option>'
        "</select></label><p>Aceitar a peça não autoriza publicação.</p>"
    )
    parts.append('<label>Observações gerais <textarea class="notes" rows="3"></textarea></label>')
    parts.append("<details><summary>Observações por critério</summary>")
    for criterion, label in (
        ("factuality", "Fidelidade factual"),
        ("brand", "Identidade da marca"),
        ("legibility", "Legibilidade"),
        ("composition", "Composição"),
        ("motion", "Narrativa e movimento"),
        ("technical", "Integridade técnica"),
        ("audio", "Fala, música e mix"),
    ):
        parts.append(
            f'<label>{label} <textarea class="criterion-note" data-criterion="{criterion}" rows="2"></textarea></label>'
        )
    parts.append("</details>")
    for version in versions:
        parts.append(
            f'<span hidden class="version-data" data-id="{_escape(version.get("id", ""))}" '
            f'data-sha256="{_escape(version.get("video_sha256", ""))}"></span>'
        )
    parts.append("</fieldset></section>")
    return "".join(parts)


def render_report(run: Path, summary: dict[str, Any]) -> str:
    """Render the report without external services or dependencies."""
    unknown = summary.get("unknown_cost_operations", [])
    cases = summary.get("cases", [])
    artifacts = " · ".join(
        _link(run, name, name) for name in ("manifest.json", "ledger.jsonl", "summary.json") if _asset(run, name)
    )
    body = [
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Revisão do experimento de motion</title>",
        "<style>",
        _CSS,
        '</style></head><body class="blind">',
        "<main><header><h1>Revisão do experimento de motion</h1>",
        f"<p>Experimento: {_escape(summary.get('experiment_id', ''))}</p>",
        f"<p>Status: {_escape(summary.get('status', ''))} · "
        f"Motivo de parada: {_escape(summary.get('stop_reason') or 'nenhum')}</p>",
        f"<p>Orçamento: US$ {_escape(summary.get('budget_usd', ''))} · "
        f"Estimativa conhecida: US$ {_escape(summary.get('known_estimated_usd', ''))} · "
        f"Comprometido: US$ {_escape(summary.get('committed_usd', ''))}</p>",
        f"<p>Operações com custo desconhecido: {_escape(', '.join(map(str, unknown)) if unknown else 'nenhuma')}</p>",
        "<p>Os custos incluem falhas registradas; estimativas e reservas não são fatura. "
        "A recomendação do modelo não é aprovação humana. Áudio não foi avaliado perceptualmente.</p>",
        "<p>Avalie os vídeos e o som antes de registrar sua decisão. "
        "Uma versão mantida sem correção não demonstra ganho de qualidade. "
        "A parada automática encerra as chamadas; o aceite criativo depende de avaliação humana.</p>",
        f"<p>{artifacts}</p>",
        '<button type="button" id="toggle">Mostrar identificação das versões</button> ',
        '<button type="button" id="export">Baixar avaliação humana</button>',
        "<p>A avaliação fica nesta página até você baixar o arquivo; "
        "não há aprovação automática nem envio.</p></header>",
    ]
    previous_run = summary.get("previous_run")
    if previous_run:
        body.insert(
            -1,
            "<p>Continuação de execuções anteriores. Os custos acumulados incluem as chamadas "
            "já registradas, inclusive a avaliação inicial com contexto criativo incompleto; "
            "operações incertas conservam sua reserva e não são tratadas como custo zero. "
            f"Execução anterior: {_escape(previous_run)}.</p>",
        )
    if isinstance(cases, list):
        body.extend(_case(run, case) for case in cases if isinstance(case, dict))
    body.extend(
        (
            f'<div id="experiment" hidden data-id="{_escape(summary.get("experiment_id", ""))}"></div>',
            "<script>",
            _JS,
            "</script></main></body></html>",
        )
    )
    return "".join(body)


def write_report(run: Path, summary: dict[str, Any]) -> Path:
    """Write report.html into the existing private run directory."""
    report = run / "report.html"
    if report.is_symlink():
        raise ValueError("report.html must not be a symlink")
    report.write_text(render_report(run, summary), encoding="utf-8")
    return report


_CSS = """
:root{font-family:system-ui,sans-serif;color:#182333;background:#f4f6f8;line-height:1.5;overflow-wrap:anywhere}
*{box-sizing:border-box}body{margin:0}
main{max-width:1400px;margin:auto;padding:clamp(1rem,3vw,2rem)}
header,.case{background:white;border-radius:14px;padding:1.2rem;margin-bottom:1rem;box-shadow:0 2px 10px #14203318}
h1,h2,h3{line-height:1.2}button,select,textarea{font:inherit}button{padding:.65rem;margin:.25rem 0;cursor:pointer}
.versions{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:1rem}
.version{border:1px solid #d7dfe6;border-radius:10px;padding:1rem;min-width:0}
video{width:100%;max-height:65vh;background:#111}fieldset{margin-top:1rem;border:1px solid #ccd5df;min-width:0}
select{max-width:100%}
label{display:block;margin:.7rem 0}textarea{display:block;width:100%;box-sizing:border-box}
.hash{overflow-wrap:anywhere;font-size:.85rem}.table-wrap{overflow-x:auto}
td,th{padding:.35rem;border:1px solid #ddd;text-align:left;vertical-align:top}
.missing{color:#704727}.blind .identified{display:none}a{color:#174f9b}
"""

_JS = """
const toggle = document.getElementById('toggle');
toggle.addEventListener('click', () => {
  const blind = document.body.classList.toggle('blind');
  document.querySelectorAll('[data-blind][data-identified]').forEach(el => {
    el.textContent = blind ? el.dataset.blind : el.dataset.identified;
  });
  toggle.textContent = blind ? 'Mostrar identificação das versões' : 'Ocultar identificação das versões';
});
document.getElementById('export').addEventListener('click', () => {
  const cases = Array.from(document.querySelectorAll('.case'), section => ({
    id: section.dataset.caseId,
    selection: section.querySelector('.choice').value || null,
    decision: section.querySelector('.decision').value,
    notes: section.querySelector('.notes').value,
    notes_by_criterion: Object.fromEntries(Array.from(section.querySelectorAll('.criterion-note'), item =>
      [item.dataset.criterion, item.value])),
    versions: Array.from(section.querySelectorAll('.version-data'), item => (
      {id:item.dataset.id, video_sha256:item.dataset.sha256}
    ))
  }));
  const review = {experiment_id: document.getElementById('experiment').dataset.id, cases};
  const url = URL.createObjectURL(new Blob([JSON.stringify(review, null, 2)], {type:'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'human-review.json';
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
"""
