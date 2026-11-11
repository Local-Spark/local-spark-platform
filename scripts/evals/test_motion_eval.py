"""Offline harness checks: no real provider or browser is used here."""

import json
from decimal import Decimal

import httpx
import pytest

from scripts.evals import motion_eval as m


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setenv("MEU_BRACO_DIREITO_OPENAI_API_KEY", "synthetic-test-key")
    body = m.json_bytes(
        {
            "model": "gpt-6.1-sol",
            "store": False,
            "reasoning": {"effort": "high"},
            "max_output_tokens": 32000,
            "text": {"format": {"type": "json_schema", "strict": True}},
        }
    )
    (tmp_path / "request.json").write_bytes(body)
    (tmp_path / "video.mp4").write_bytes(b"synthetic-video")
    (tmp_path / "LICENSE").write_text("Synthetic notice")
    config = {
        "version": 1,
        "synthetic_fixture": True,
        "id": "synthetic",
        "body_path": str(tmp_path / "request.json"),
        "body_sha256": m.digest(body),
        "width": 720,
        "height": 1280,
        "fps": 30,
        "duration_ms": 1000,
        "assets": [
            {
                "id": "video.mp4",
                "path": str(tmp_path / "video.mp4"),
                "sha256": m.digest(b"synthetic-video"),
                "mime": "video/mp4",
            }
        ],
        "reference": {"path": str(tmp_path / "video.mp4"), "sha256": m.digest(b"synthetic-video")},
        "tools": {key: "/synthetic/tool" for key in ("node", "playwright", "chromium", "ffmpeg", "ffprobe")},
        "reservation_usd": "0.75",
        "rights_files": [str(tmp_path / "LICENSE")],
    }
    destination = tmp_path / "case.json"
    destination.write_bytes(m.json_bytes(config))
    return destination


def answer():
    return {
        "concept": "Synthetic",
        "source_usage": [],
        "html": "<div>Local fixture</div>",
        "scene_init": "async () => {window.seek = async () => null}",
        "audio": {"mode": "silent", "tracks": []},
    }


def response(value=None):
    return {
        "status": "completed",
        "output": [{"content": [{"type": "output_text", "text": json.dumps(value or answer())}]}],
        "usage": {"input_tokens": 100, "output_tokens": 10, "output_tokens_details": {"reasoning_tokens": 4}},
    }


def fake_renderer(_node, config, output):
    data = json.loads(config.read_bytes())
    assert data["synthetic_fixture"] is True
    if output is not None:
        assert m.digest(m.path(data["html"]["path"]).read_bytes()) == data["html"]["sha256"]
        (output / "render.mp4").write_bytes(b"synthetic-render")
        (output / "trace.json").write_text('{"synthetic":true}')


def test_paid_mock_reserves_before_network_and_reuses_finished_request(case, tmp_path):
    runs = tmp_path / "runs"
    calls = []

    def transport(request):
        calls.append(request)
        assert str(request.url) == m.ENDPOINT
        assert request.headers["X-Client-Request-Id"]
        assert json.loads(next(runs.glob("*/ledger.jsonl")).read_text())["state"] == "reserved"
        return httpx.Response(200, json=response())

    run = m.execute(
        case,
        Decimal("0.75"),
        runs=runs,
        client=httpx.Client(transport=httpx.MockTransport(transport)),
        renderer=fake_renderer,
    )
    repeated = m.execute(case, Decimal("0.75"), runs=runs, renderer=lambda *_: pytest.fail("replay must reuse"))
    assert repeated == run and len(calls) == 1
    assert json.loads((run / "cost.json").read_bytes())["estimated_usd"] == "0.00035"
    assert (run / "report.html").exists() and (run / "rights-0-LICENSE").read_text() == "Synthetic notice"
    assert (run / "scene.html.txt").read_bytes() == (run / "scene.html").read_bytes()
    assert 'href="scene.html"' not in (run / "report.html").read_text()
    assert (run.stat().st_mode & 0o777) == 0o700
    assert b"synthetic-test-key" not in (run / "request.body").read_bytes()


@pytest.mark.parametrize("budget", [None, Decimal("0.74"), Decimal("0"), Decimal("NaN")])
def test_budget_rejected_before_network(case, tmp_path, budget):
    with pytest.raises(m.EvalError):
        m.execute(case, budget, runs=tmp_path / "runs", renderer=lambda *_: pytest.fail("must not start renderer"))


def test_network_failure_is_uncertain_and_never_retried(case, tmp_path):
    runs = tmp_path / "runs"
    calls = []

    def transport(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic")

    with pytest.raises(m.EvalError, match="uncertain"):
        m.execute(
            case,
            Decimal("0.75"),
            runs=runs,
            client=httpx.Client(transport=httpx.MockTransport(transport)),
            renderer=fake_renderer,
        )
    with pytest.raises(m.EvalError, match="already_started"):
        m.execute(case, Decimal("0.75"), runs=runs, renderer=fake_renderer)
    states = [json.loads(line)["state"] for line in next(runs.glob("*/ledger.jsonl")).read_text().splitlines()]
    assert states == ["reserved", "uncertain"] and len(calls) == 1


def test_offline_wrapper_has_zero_calls_and_no_api_key(case, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "api_key", lambda: pytest.fail("offline must not read credentials"))
    saved = tmp_path / "answer.json"
    saved.write_bytes(m.json_bytes(answer()))
    run = m.execute(case, None, cached=saved, runs=tmp_path / "runs", renderer=fake_renderer)
    summary = json.loads((run / "summary.json").read_bytes())
    assert summary["mode"] == "offline_response" and summary["estimated_usd"] == "0"
    assert (run / "response.body").read_bytes() == saved.read_bytes()
    page = (run / "report.html").read_text()
    assert page.count("<video ") == 2
    assert "<h2>Resultado</h2>" in page and "<h2>Referência v2</h2>" in page
    assert page.count("download>Baixar MP4") == 2


def test_extra_comparisons_are_frozen_before_network_and_report_labels_are_escaped(case, tmp_path):
    previous = tmp_path / "previous.mp4"
    previous.write_bytes(b"synthetic-previous")
    label = '<script>alert("previous")</script>'
    config = json.loads(case.read_bytes())
    config["reference"]["label"] = "V2 — piso"
    config["comparisons"] = [{"label": label, "path": str(previous), "sha256": m.digest(previous.read_bytes())}]
    case.write_bytes(m.json_bytes(config))
    runs = tmp_path / "runs"

    def transport(_request):
        frozen = json.loads(next(runs.glob("*/frozen-case.json")).read_bytes())
        assert m.path(frozen["comparisons"][0]["path"]).read_bytes() == b"synthetic-previous"
        previous.write_bytes(b"changed-after-snapshot")
        return httpx.Response(200, json=response())

    run = m.execute(
        case,
        Decimal("0.75"),
        runs=runs,
        client=httpx.Client(transport=httpx.MockTransport(transport)),
        renderer=fake_renderer,
    )
    frozen = json.loads((run / "frozen-case.json").read_bytes())
    comparison = frozen["comparisons"][0]
    assert m.path(comparison["path"]).is_relative_to(run)
    assert m.path(comparison["path"]).read_bytes() == b"synthetic-previous"
    assert comparison["sha256"] == config["comparisons"][0]["sha256"]
    assert json.loads((run / "case.json").read_bytes()) == config
    assert len(frozen["assets"]) == 1 and frozen["reference"]["label"] == "V2 — piso"
    page = (run / "report.html").read_text()
    assert page.count("<video ") == 3 and page.count("download>Baixar MP4") == 3
    assert "<h2>V2 — piso</h2>" in page and label not in page
    assert "&lt;script&gt;alert(&quot;previous&quot;)&lt;/script&gt;" in page
    assert 'src="assets/2-previous.mp4"' in page
    assert 'href="render/trace.json"' in page and 'href="summary.json"' in page


def test_tampered_comparison_rejects_before_renderer_or_credentials(case, tmp_path, monkeypatch):
    config = json.loads(case.read_bytes())
    config["comparisons"] = [{"label": "Previous", **config["reference"], "sha256": "0" * 64}]
    case.write_bytes(m.json_bytes(config))
    monkeypatch.setattr(m, "api_key", lambda: pytest.fail("must not read credentials"))
    with pytest.raises(m.EvalError, match="input_hash_mismatch"):
        m.execute(
            case,
            Decimal("0.75"),
            runs=tmp_path / "runs",
            renderer=lambda *_: pytest.fail("must not start renderer"),
        )
    assert not (tmp_path / "runs").exists()


def test_preflight_failure_prevents_credentials_reservation_and_network(case, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "api_key", lambda: pytest.fail("preflight first"))

    def fail(*_):
        raise m.EvalError("renderer_preflight_failed")

    with pytest.raises(m.EvalError, match="preflight"):
        m.execute(case, Decimal("0.75"), runs=tmp_path / "runs", renderer=fail)
    assert not list((tmp_path / "runs").glob("request-*"))


def test_structured_response_rejects_markdown_and_model_asset_paths(case, tmp_path):
    with pytest.raises(ValueError):
        m.parse_answer(
            m.json_bytes(
                {"status": "completed", "output": [{"content": [{"type": "output_text", "text": "```json\n{}\n```"}]}]}
            )
        )
    config, _ = m.load_case(case, None)
    value = answer()
    value["audio"] = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "/private/unknown.wav", "trim_start_ms": 0, "trim_end_ms": 500, "offset_ms": 0, "volume": 0.5}
        ],
    }
    with pytest.raises(m.EvalError, match="audio_asset"):
        m.assemble(config, m.Answer.model_validate(value), tmp_path)


def test_required_voice_cannot_be_silently_removed(case, tmp_path):
    config, _ = m.load_case(case, None)
    config["required_audio_ids"] = ["voice"]
    with pytest.raises(m.EvalError, match="required_audio_missing"):
        m.assemble(config, m.Answer.model_validate(answer()), tmp_path)


def test_tampered_input_is_rejected(case):
    config = json.loads(case.read_bytes())
    m.path(config["assets"][0]["path"]).write_bytes(b"changed")
    with pytest.raises(m.EvalError, match="hash"):
        m.load_case(case, None)


@pytest.mark.parametrize("extra", [{"tools": []}, {"store": True}])
def test_request_cannot_enable_tools_or_storage(case, extra):
    config = json.loads(case.read_bytes())
    body_path = m.path(config["body_path"])
    body = {**json.loads(body_path.read_bytes()), **extra}
    body_path.write_bytes(m.json_bytes(body))
    config["body_sha256"] = m.digest(body_path.read_bytes())
    case.write_bytes(m.json_bytes(config))
    with pytest.raises(m.EvalError, match="unsupported_request"):
        m.load_case(case, None)


def test_invalid_paid_output_preserves_response_usage_and_reservation(case, tmp_path):
    invalid = response()
    invalid["output"][0]["content"][0]["text"] = "invalid JSON"
    with pytest.raises(m.EvalError, match="invalid_response_saved"):
        m.execute(
            case,
            Decimal("0.75"),
            runs=tmp_path / "runs",
            renderer=fake_renderer,
            client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=invalid))),
        )
    cost = json.loads(next((tmp_path / "runs").glob("*/cost.json")).read_bytes())
    assert cost["estimated_usd"] == "0.00035" and cost["reservation_usd"] == "0.75"
    assert next((tmp_path / "runs").glob("*/response.body")).exists()


def test_render_uses_frozen_assets_when_original_changes_after_request(case, tmp_path):
    original = m.path(json.loads(case.read_bytes())["assets"][0]["path"])

    def transport(_):
        original.write_bytes(b"changed after request")
        return httpx.Response(200, json=response())

    run = m.execute(
        case,
        Decimal("0.75"),
        runs=tmp_path / "runs",
        renderer=fake_renderer,
        client=httpx.Client(transport=httpx.MockTransport(transport)),
    )
    frozen = json.loads((run / "frozen-case.json").read_bytes())
    assert m.path(frozen["assets"][0]["path"]).read_bytes() == b"synthetic-video"
    assert m.path(frozen["reference"]["path"]).read_bytes() == b"synthetic-video"


def rejected_quota(case, runs, payload=None, status=429):
    body = (
        payload
        if payload is not None
        else {"error": {"type": "insufficient_quota", "code": "credit_balance_exhausted"}}
    )
    with pytest.raises(m.EvalError, match="provider_http_status"):
        m.execute(
            case,
            Decimal("0.75"),
            runs=runs,
            renderer=fake_renderer,
            client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(status, json=body))),
        )
    return next(path for path in runs.iterdir() if path.is_dir())


@pytest.mark.parametrize("empty_usage", [False, True])
def test_explicit_quota_retry_keeps_old_records_and_uses_new_identity(case, tmp_path, empty_usage):
    runs = tmp_path / "runs"
    payload = {"error": {"type": "insufficient_quota", "code": "credit_balance_exhausted"}}
    if empty_usage:
        payload["usage"] = {}
    previous = rejected_quota(case, runs, payload)
    old = {path: path.read_bytes() for path in runs.rglob("*") if path.is_file()}
    with pytest.raises(m.EvalError, match="already_started"):
        m.execute(case, Decimal("0.75"), runs=runs, renderer=fake_renderer)
    result = m.execute(
        case,
        Decimal("0.75"),
        runs=runs,
        renderer=fake_renderer,
        retry_rejected=True,
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response()))),
    )
    assert result != previous and all(path.read_bytes() == data for path, data in old.items())
    first = json.loads((result / "ledger.jsonl").read_text().splitlines()[0])
    assert first["reservation_usd"] == "0.75"
    assert first["retry_of"]["operation_id"] == previous.name
    assert first["retry_of"]["reservation_usd_preserved"] == "0.75"
    assert len(list(runs.glob("request-*.json"))) == 2
    assert m.execute(case, Decimal("0.75"), runs=runs, renderer=fake_renderer) == result


@pytest.mark.parametrize(
    "change", ["rate_limit", "usage", "usage_null", "output", "incomplete", "tampered", "uncertain"]
)
def test_retry_rejects_every_other_response_or_ambiguous_state(case, tmp_path, change):
    runs = tmp_path / "runs"
    payload = {"error": {"type": "insufficient_quota", "code": "credit_balance_exhausted"}}
    if change == "rate_limit":
        payload["error"]["type"] = "rate_limit_exceeded"
    elif change == "usage":
        payload["usage"] = {"input_tokens": 1}
    elif change == "usage_null":
        payload["usage"] = None
    elif change == "output":
        payload["output"] = []
    elif change == "incomplete":
        payload["status"] = "incomplete"
    previous = rejected_quota(case, runs, payload)
    if change == "tampered":
        (previous / "response.body").write_bytes(b"{}")
    if change == "uncertain":
        m.event(previous, "uncertain")
    before = set(runs.iterdir())
    with pytest.raises(m.EvalError, match="recorded_quota_rejection"):
        m.execute(
            case,
            Decimal("0.75"),
            runs=runs,
            retry_rejected=True,
            renderer=lambda *_: pytest.fail("must reject before preflight or network"),
        )
    assert set(runs.iterdir()) == before


def test_retry_requires_existing_rejection_and_new_explicit_budget(case, tmp_path):
    with pytest.raises(m.EvalError, match="no_previous_quota_rejection"):
        m.execute(case, Decimal("0.75"), runs=tmp_path / "runs", retry_rejected=True)
    with pytest.raises(m.EvalError, match="explicit_budget"):
        m.execute(case, None, runs=tmp_path / "runs", retry_rejected=True)
