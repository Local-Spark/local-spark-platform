"""Tests for the isolated local motion review report."""

from __future__ import annotations

import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

from scripts.evals.motion_review_report import _asset, _critique, _label, render_report, write_report


def _summary() -> dict:
    return {
        "experiment_id": 'exp-1"<script>alert(1)</script>',
        "previous_run": "parent<fake>",
        "status": "finished",
        "stop_reason": None,
        "budget_usd": "2.00",
        "known_estimated_usd": "0.50",
        "committed_usd": "0.75",
        "unknown_cost_operations": ["failed-1"],
        "cases": [
            {
                "id": "case-1",
                "label": "Café & bolo",
                "baseline_cost_note": "custo histórico desconhecido",
                "costs": {
                    "historical_estimated_usd": "0.12",
                    "incremental_estimated_usd": "0.33",
                    "estimated_total_usd": "0.45",
                    "committed_usd": "1.00",
                    "unknown_operations": ["uncertain-op"],
                    "paid_calls": 2,
                },
                "operations": [
                    {
                        "version_id": "v1",
                        "kind": "correction",
                        "context_scope": "initial_incomplete_context",
                        "estimated_usd": None,
                        "reservation_usd": "0.75",
                        "seconds": None,
                        "status": "uncertain",
                    }
                ],
                "status": "done",
                "stop_reason": None,
                "recommended_version": "v1",
                "versions": [
                    {
                        "id": "v0",
                        "video_path": "mídia/v 0.mp4",
                        "video_sha256": "abc",
                        "round": 0,
                        "critique_path": None,
                        "evidence_path": "evidence.json",
                        "model_recommendation": None,
                        "stage_seconds": None,
                    },
                    {
                        "id": "v1",
                        "video_path": "mídia/v1.mp4",
                        "video_sha256": "def",
                        "round": 1,
                        "critique_path": "critique.json",
                        "evidence_path": "evidence.json",
                        "model_recommendation": "rever",
                        "stage_seconds": 2.4,
                        "operations": [
                            {
                                "kind": "correction",
                                "context_scope": "creative_context_v2",
                                "estimated_usd": None,
                                "reservation_usd": "0.75",
                                "seconds": None,
                                "status": "uncertain",
                            }
                        ],
                    },
                ],
            }
        ],
    }


def test_report_renders_video_critique_and_precise_costs(tmp_path: Path) -> None:
    (tmp_path / "mídia").mkdir()
    (tmp_path / "mídia/v 0.mp4").write_bytes(b"video")
    (tmp_path / "mídia/v1.mp4").write_bytes(b"video")
    (tmp_path / "evidence.json").write_text("{}")
    (tmp_path / "manifest.json").write_text("{}")
    critique = {
        "overall": "needs revision",
        "criteria": [{"criterion": "ritmo", "status": "fail", "observation": "<script>bad</script>"}],
        "issues": [{"id": "i1", "problem": "texto pequeno", "start_ms": 100, "end_ms": 900}],
        "preference": {"version_id": "v1", "reason": "ritmo"},
    }
    (tmp_path / "critique.json").write_text(json.dumps(critique), encoding="utf-8")
    target = write_report(tmp_path, _summary())
    html = target.read_text(encoding="utf-8")
    assert target == tmp_path / "report.html"
    assert html.count("<video controls") == 2
    assert 'src="m%C3%ADdia/v%200.mp4"' in html
    assert "&lt;script&gt;bad&lt;/script&gt;" in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>bad</script>" not in html
    assert all(value in html for value in ("0.50", "0.75", "failed-1", "texto pequeno", "900"))
    assert all(value in html for value in ("0.12", "0.33", "0.45", "uncertain-op", "uncertain"))
    assert "contexto criativo incompleto" in html
    assert "parent&lt;fake&gt;" in html
    assert "Avaliação inicial com contexto incompleto" in html and "Contexto criativo completo v2" in html
    assert "Aceitar a peça não autoriza publicação" in html
    assert 'data-criterion="audio"' in html and 'class="decision"' in html
    assert 'href="manifest.json"' in html
    assert 'href="ledger.jsonl"' not in html
    assert 'href="summary.json"' not in html
    assert "recomendação do modelo não é aprovação humana" in html
    assert "Áudio não foi avaliado perceptualmente" in html
    assert 'data-blind="A" data-identified="v0"' in html
    assert 'data-blind="B" data-identified="v1"' in html
    assert "a.download = 'human-review.json'" in html


def test_no_revision_or_dangerous_links(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-motion-review.mp4"
    outside.write_bytes(b"private")
    (tmp_path / "escape.mp4").symlink_to(outside)
    summary = _summary()
    version = summary["cases"][0]["versions"][0]
    summary["cases"][0]["versions"] = [version]
    version["video_path"] = "escape.mp4"
    version["evidence_path"] = "../outside-motion-review.mp4"
    html = render_report(tmp_path, summary)
    assert "Sem nova versão" in html
    assert "Vídeo indisponível" in html
    assert "Evidências indisponível" in html
    assert "outside-motion-review.mp4" not in html
    assert "escape.mp4" not in html
    for value in ("/etc/passwd", "https://example.com", "../file", "a\\b", "x?y", "x#y", "bad\x00path"):
        assert _asset(tmp_path, value) is None
    outside.unlink()


def test_unreadable_and_malformed_critique(tmp_path: Path) -> None:
    (tmp_path / "invalid.json").write_text("{")
    (tmp_path / "list.json").write_text("[]")
    assert "não pôde ser lida" in _critique(tmp_path, "invalid.json")
    assert "formato inesperado" in _critique(tmp_path, "list.json")
    assert "indisponível" in _critique(tmp_path, "missing.json")
    assert _label(25) == "Z"
    assert _label(26) == "AA"


def test_adequate_scope_and_limitations_are_escaped_without_changing_source(tmp_path: Path) -> None:
    source = {
        "overall": "adequate",
        "limitations": [
            "Quadros amostrados não comprovam o movimento inteiro.",
            '<img src=x onerror="alert(1)"> Áudio & sincronismo não avaliados.',
        ],
    }
    path = tmp_path / "critique.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    original = path.read_bytes()
    html = _critique(tmp_path, "critique.json")
    assert "nenhum outro defeito acionável identificado nas evidências avaliadas" in html
    assert "código original: <code>adequate</code>" in html
    assert "Quadros amostrados não comprovam o movimento inteiro." in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt; Áudio &amp; sincronismo não avaliados." in html
    assert "<img" not in html
    assert path.read_bytes() == original


@pytest.mark.parametrize("value", [None, "not a list", {"unexpected": "data"}, 42, [None, {}, 42, "", "  "]])
def test_malformed_limitations_are_identified_without_crashing(tmp_path: Path, value: object) -> None:
    path = tmp_path / "critique.json"
    path.write_text(json.dumps({"overall": "adequate", "limitations": value}), encoding="utf-8")
    html = _critique(tmp_path, "critique.json")
    assert "Há registros de limitações em formato inválido ou vazio, não exibidos." in html
    assert "Limitações não informadas." not in html
    assert "<code>adequate</code>" in html


@pytest.mark.parametrize(
    "source", [{"overall": "insufficient_evidence"}, {"overall": "needs_correction", "limitations": []}]
)
def test_absent_limitations_and_other_statuses_keep_their_meaning(tmp_path: Path, source: dict) -> None:
    (tmp_path / "critique.json").write_text(json.dumps(source), encoding="utf-8")
    html = _critique(tmp_path, "critique.json")
    assert f"Resultado: {source['overall']}" in html
    assert "nenhum outro defeito acionável" not in html
    assert "Limitações não informadas." in html


def test_valid_limitations_survive_malformed_neighbors(tmp_path: Path) -> None:
    (tmp_path / "critique.json").write_text(
        json.dumps(
            {"overall": '<script>alert("status")</script>', "limitations": ["Escuta pendente", None, ["invalid"]]}
        ),
        encoding="utf-8",
    )
    html = _critique(tmp_path, "critique.json")
    assert "<li>Escuta pendente</li>" in html
    assert "formato inválido ou vazio" in html
    assert "&lt;script&gt;alert(&quot;status&quot;)&lt;/script&gt;" in html
    assert "<script>" not in html


def test_critique_details_remain_hidden_during_blind_comparison(tmp_path: Path) -> None:
    (tmp_path / "critique.json").write_text(
        json.dumps({"overall": "adequate", "limitations": ["LIMITATION_ONLY_AFTER_REVEAL"]}), encoding="utf-8"
    )

    class Reader(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.hidden_depth = 0
            self.visible: list[str] = []
            self.identified: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "details" and (self.hidden_depth or "identified" in (dict(attrs).get("class") or "").split()):
                self.hidden_depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag == "details" and self.hidden_depth:
                self.hidden_depth -= 1

        def handle_data(self, data: str) -> None:
            (self.identified if self.hidden_depth else self.visible).append(data)

    reader = Reader()
    reader.feed(_critique(tmp_path, "critique.json"))
    assert "LIMITATION_ONLY_AFTER_REVEAL" in "".join(reader.identified)
    assert "adequate" in "".join(reader.identified)
    assert "".join(reader.visible).strip() == ""
    report = render_report(tmp_path, _summary())
    assert "A parada automática encerra as chamadas; o aceite criativo depende de avaliação humana." in report
    assert '<body class="blind">' in report


def test_report_refuses_symlink_destination(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere"
    target.write_text("preserve")
    (tmp_path / "report.html").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        write_report(tmp_path, _summary())
    assert target.read_text() == "preserve"


def test_browser_script_exports_selection_hashes_and_toggles(tmp_path: Path) -> None:
    """Exercise the actual inline JS with a tiny simulated DOM and Node."""
    report = render_report(tmp_path, _summary())
    script = report.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = (
        r"""
const assert = require('node:assert/strict');
const handlers = {};
let captured;
const toggleButton = {addEventListener: (_, fn) => {handlers.toggle = fn}, textContent: ''};
const download = {addEventListener: (_, fn) => {handlers.download = fn}};
const labeled = [{dataset: {blind:'A', identified:'v0'}, textContent:'A'}];
let isBlind = true;
const section = {dataset:{caseId:'case-1'}, querySelector: selector => (
  selector === '.choice' ? {value:'v0'} : selector === '.decision' ? {value:'accepted'} : {value:'motivo'}
), querySelectorAll: selector => selector === '.criterion-note' ?
  [{dataset:{criterion:'audio'},value:'escutado'}] : [{dataset:{id:'v0',sha256:'abc'}}]};
const link = {click(){}, remove(){}};
const document = {
  body: {classList:{toggle:()=>{isBlind = !isBlind; return isBlind}},appendChild(){}},
  getElementById: id => id === 'toggle' ? toggleButton : id === 'export' ? download : {dataset:{id:'exp-1'}},
  querySelectorAll: selector => selector === '.case' ? [section] : labeled,
  createElement: () => link
};
const URL = {createObjectURL: blob => {captured = blob; return 'blob:1'}, revokeObjectURL(){}};
"""
        + script
        + r"""
handlers.toggle();
assert.equal(labeled[0].textContent, 'v0');
handlers.toggle();
assert.equal(labeled[0].textContent, 'A');
handlers.download();
captured.text().then(text => {
  assert.deepEqual(JSON.parse(text), {experiment_id:'exp-1',cases:[{
    id:'case-1', selection:'v0', decision:'accepted', notes:'motivo',
    notes_by_criterion:{audio:'escutado'}, versions:[{id:'v0',video_sha256:'abc'}]
  }]});
  assert.equal(link.download, 'human-review.json');
});
"""
    )
    subprocess.run(["node", "-e", harness], check=True, capture_output=True, text=True)


def test_feedback_alignment_separates_requirement_and_reference_evidence(tmp_path: Path) -> None:
    critique = {
        "overall": "adequate",
        "alignment_status": "met",
        "human_approval": "pending",
        "brief_alignment": [
            {
                "requirement_id": "window_transformation",
                "status": "met",
                "evidence_ids": ["v0:f0000", "v1:f0001", "v1:f0003"],
                "reference_evidence_ids": ["ref:intensa:f0000"],
                "narrative_role": "<script>new unsafe text</script>",
                "reason": "convite",
            }
        ],
        "limitations": ["Seek solicitado, não PTS medido"],
    }
    (tmp_path / "critique.json").write_text(json.dumps(critique))
    rendered = _critique(tmp_path, "critique.json")
    assert "atendido nas amostras" in rendered and "Atendimento ao feedback posterior" in rendered
    assert "reference_evidence_ids" in rendered and "v0:f0000" in rendered and "ref:intensa:f0000" in rendered
    assert "avaliação humana dos vídeos completos" in rendered
    assert "&lt;script&gt;new unsafe text&lt;/script&gt;" in rendered
    assert "<script>new unsafe text</script>" not in rendered
    assert rendered.startswith('<details class="identified">')
    legacy = {k: v for k, v in critique.items() if k not in {"brief_alignment", "alignment_status", "human_approval"}}
    (tmp_path / "critique.json").write_text(json.dumps(legacy))
    assert "Atendimento ao feedback posterior" not in _critique(tmp_path, "critique.json")


@pytest.mark.parametrize("alignment", [None, "malformed", 4, {}, [None, "invalid", {}, {"reason": "<img onerror=x>"}]])
def test_malformed_optional_alignment_does_not_break_or_inject_markup(tmp_path: Path, alignment: object) -> None:
    (tmp_path / "critique.json").write_text(json.dumps({"brief_alignment": alignment, "alignment_status": ["<x>"]}))
    result = _critique(tmp_path, "critique.json")
    assert "<img onerror=x>" not in result and "<x>" not in result
    assert "código original" in result


def test_feedback_context_is_escaped_and_kept_in_identified_details(tmp_path: Path) -> None:
    summary = _summary()
    summary["cases"][0]["evaluation_context"] = {
        "type": "feedback_guided_creative_refinement",
        "statement": "Feedback posterior <script>bad</script>",
        "references": "Intensa: screenshots pré-encode; v2 não fornecida",
        "requirements": ["theme_change"],
        "approval": "pending_human_creative_review",
    }
    result = render_report(tmp_path, summary)
    start = result.index('<details class="identified"><summary>Contexto desta comparação')
    end = result.index("</details>", start)
    content = result[start:end]
    assert "Feedback posterior &lt;script&gt;bad&lt;/script&gt;" in content
    assert "pré-encode; v2 não fornecida" in content and "theme_change" in content
    assert "<script>bad</script>" not in result
    summary["cases"][0]["evaluation_context"] = "malformed"
    assert "Contexto desta comparação" not in render_report(tmp_path, summary)
