"""The optional synthetic evaluation is bounded, durable and fail-closed."""

import asyncio
import hashlib
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from pathlib import Path

import pytest

from app.adapters.visual_ai import VisualAIError, VisualResult
from scripts import evaluate_bl042_guarded as evaluation


def test_synthetic_request_is_pinned_and_non_customer():
    prepared = evaluation.synthetic_request()
    assert prepared.request.model == evaluation.MODEL
    assert prepared.request.size == "1024x1280"
    assert len(prepared.request.references) == 2
    assert hashlib.sha256(prepared.request.references[0].content).hexdigest() == evaluation.PHOTO_HASH
    assert hashlib.sha256(prepared.request.references[1].content).hexdigest() == evaluation.LOGO_HASH
    assert "FICTÍCIA" in prepared.request.prompt


def test_modified_fixture_is_rejected(tmp_path: Path):
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"untrusted-image")
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluation._checked(path, evaluation.PHOTO_HASH)


def _reserve_process(path: str) -> bool:
    return evaluation.reserve_once(Path(path), "a" * 64)


def test_only_one_concurrent_process_may_reserve(tmp_path: Path):
    ledger = tmp_path / "budget.sqlite3"
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_reserve_process, [str(ledger)] * 8))
    assert results.count(True) == 1
    with closing(sqlite3.connect(ledger)) as db, db:
        history, cap = db.execute("SELECT history,cap FROM policy").fetchone()
        total = db.execute("SELECT sum(hold) FROM attempts").fetchone()[0]
        assert (history, cap, total) == (500_000, 1_000_000, 500_000)
    assert not evaluation.reserve_once(ledger, "a" * 64)


def test_tampered_policy_or_symlink_cannot_authorize(tmp_path: Path):
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


@pytest.mark.asyncio
async def test_success_keeps_hold_and_replay_never_calls_provider(tmp_path: Path):
    class Stub:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            return VisualResult(b"image", "image/jpeg", "a" * 64, 1024, 1280, None, None)

    stub = Stub()
    ledger, image = tmp_path / "budget.sqlite3", tmp_path / "image.jpg"
    assert await evaluation.run_once(stub, ledger, image) == "completed_unreconciled"
    assert image.read_bytes() == b"image"
    assert await evaluation.run_once(stub, ledger, image) == "already_reserved_no_retry"
    assert stub.calls == 1
    with closing(sqlite3.connect(ledger)) as db, db:
        assert db.execute("SELECT hold,state FROM attempts").fetchone() == (500_000, "completed_unreconciled")


@pytest.mark.asyncio
async def test_uncertain_response_keeps_full_hold_and_blocks_retry(tmp_path: Path):
    class Stub:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            raise VisualAIError("VISUAL_PROVIDER_UNCERTAIN", uncertain=True)

    stub = Stub()
    ledger, image = tmp_path / "budget.sqlite3", tmp_path / "image.jpg"
    assert await evaluation.run_once(stub, ledger, image) == "uncertain"
    assert await evaluation.run_once(stub, ledger, image) == "already_reserved_no_retry"
    assert stub.calls == 1 and not image.exists()
    with closing(sqlite3.connect(ledger)) as db, db:
        assert db.execute("SELECT hold,state FROM attempts").fetchone() == (500_000, "uncertain")


@pytest.mark.asyncio
async def test_crash_after_reservation_never_retries(tmp_path: Path):
    class CrashingProvider:
        async def generate(self, request):
            raise asyncio.CancelledError

    ledger, image = tmp_path / "budget.sqlite3", tmp_path / "image.jpg"
    with pytest.raises(asyncio.CancelledError):
        await evaluation.run_once(CrashingProvider(), ledger, image)
    assert await evaluation.run_once(CrashingProvider(), ledger, image) == "already_reserved_no_retry"
    with closing(sqlite3.connect(ledger)) as db, db:
        assert db.execute("SELECT hold,state FROM attempts").fetchone() == (500_000, "submitted")
