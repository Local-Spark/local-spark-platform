"""Offline tests for the separately authorized synthetic brand-finishing eval."""

import asyncio
import hashlib
import io
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from pathlib import Path

import pytest
from PIL import Image

from app.adapters.visual_ai import VisualAIError, VisualResult
from scripts import evaluate_bl042_guarded_v2 as evaluation


def _scene() -> VisualResult:
    data = io.BytesIO()
    Image.new("RGB", (1024, 1280), "#ab9582").save(data, "PNG")
    raw = data.getvalue()
    return VisualResult(raw, "image/png", hashlib.sha256(raw).hexdigest(), 1024, 1280, None, None)


def _reserve_process(path: str) -> bool:
    return evaluation.reserve_once(Path(path), "a" * 64)


def test_fixed_request_uses_only_cc0_reference_and_fictitious_brand():
    prepared = evaluation.synthetic_request()
    assert prepared.request.model == evaluation.MODEL and prepared.request.output_format == "png"
    assert prepared.request.size == "1024x1280" and len(prepared.request.references) == 1
    assert hashlib.sha256(prepared.request.references[0].content).hexdigest() == evaluation.PHOTO_HASH
    assert prepared.logo.sha256 == evaluation.LOGO_HASH and prepared.kit.brand_name == "Café do Cedro"
    assert prepared.statement == "Croissant de manteiga · R$ 18"
    assert prepared.cta == "Peça informações pelo WhatsApp"
    assert "FICTÍCIO" in prepared.request.prompt and "Não mostre texto" in prepared.request.prompt


def test_fixed_fixture_cannot_be_replaced(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluation, "_checked", lambda *_: (_ for _ in ()).throw(ValueError("fixture rejected")))
    with pytest.raises(ValueError, match="fixture rejected"):
        evaluation.synthetic_request()
    assert not list(tmp_path.iterdir())


def test_only_one_process_can_reserve_the_full_additional_grant(tmp_path):
    ledger = tmp_path / "budget.sqlite3"
    with ProcessPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(_reserve_process, [str(ledger)] * 8))
    assert outcomes.count(True) == 1
    with closing(sqlite3.connect(ledger)) as db:
        assert db.execute("SELECT grant_id,cap FROM policy").fetchone() == (evaluation.EVAL_ID, 1_000_000)
        assert db.execute("SELECT hold,state FROM attempts").fetchone() == (1_000_000, "submitted")
    assert not evaluation.reserve_once(ledger, "a" * 64)


def test_invalid_policy_symlink_and_legacy_ledger_fail_closed(tmp_path):
    ledger = tmp_path / "budget.sqlite3"
    assert evaluation.reserve_once(ledger, "a" * 64)
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute("UPDATE policy SET cap=2000000")
    with pytest.raises(ValueError, match="policy"):
        evaluation.reserve_once(ledger, "a" * 64)
    link = tmp_path / "link.sqlite3"
    link.symlink_to(ledger)
    with pytest.raises(ValueError, match="symlink"):
        evaluation.reserve_once(link, "a" * 64)
    with pytest.raises(ValueError, match="legacy"):
        evaluation.reserve_once(evaluation.LEGACY_LEDGER, "a" * 64)
    with pytest.raises(ValueError, match="fingerprint"):
        evaluation.reserve_once(tmp_path / "other.sqlite3", "invalid")


async def test_response_saves_original_and_applies_brand_without_a_second_call(tmp_path):
    class Stub:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            return _scene()

    provider = Stub()
    ledger, output = tmp_path / "budget.sqlite3", tmp_path / "output"
    assert await evaluation.run_once(provider, ledger, output) == "completed_unreconciled"
    assert hashlib.sha256((output / "scene.png").read_bytes()).hexdigest() == _scene().sha256
    assert (output / "feed.png").read_bytes() != (output / "scene.png").read_bytes()
    with pytest.raises(ValueError, match="output already exists"):
        await evaluation.run_once(provider, ledger, output)
    assert provider.calls == 1
    with closing(sqlite3.connect(ledger)) as db:
        hold, state, result = db.execute("SELECT hold,state,result FROM attempts").fetchone()
    assert (hold, state) == (1_000_000, "completed_unreconciled")
    assert "feed_sha256" in result and "scene_sha256" in result


@pytest.mark.parametrize("crash", [False, True])
async def test_uncertain_or_cancelled_request_never_retries(tmp_path, crash):
    class Stub:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            if crash:
                raise asyncio.CancelledError
            raise VisualAIError("VISUAL_PROVIDER_UNCERTAIN", uncertain=True)

    provider = Stub()
    ledger, output = tmp_path / "budget.sqlite3", tmp_path / "output"
    if crash:
        with pytest.raises(asyncio.CancelledError):
            await evaluation.run_once(provider, ledger, output)
    else:
        assert await evaluation.run_once(provider, ledger, output) == "uncertain"
    assert await evaluation.run_once(provider, ledger, output) == "already_reserved_no_retry"
    assert provider.calls == 1 and not (output / "feed.png").exists()
    with closing(sqlite3.connect(ledger)) as db:
        state = db.execute("SELECT state FROM attempts").fetchone()[0]
    assert state == ("submitted" if crash else "uncertain")


async def test_postprocessing_failure_keeps_reservation_and_original_scene(tmp_path, monkeypatch):
    class Stub:
        async def generate(self, request):
            return _scene()

    def fail(*args, **kwargs):
        raise evaluation.BrandOverlayError("simulated failure")

    monkeypatch.setattr(evaluation, "render_brand_overlay", fail)
    ledger, output = tmp_path / "budget.sqlite3", tmp_path / "output"
    assert await evaluation.run_once(Stub(), ledger, output) == "postprocess_failed"
    assert (output / "scene.png").exists() and not (output / "feed.png").exists()
    with closing(sqlite3.connect(ledger)) as db:
        assert db.execute("SELECT state,hold FROM attempts").fetchone() == ("postprocess_failed", 1_000_000)
