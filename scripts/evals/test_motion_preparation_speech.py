"""Real speech service with synthetic adapter; one-shot private preparation evidence."""

import json
import stat
from uuid import uuid4, uuid5

import pytest

from app.tests.conftest import settings  # noqa: F401
from app.tests.unit.test_motion_speech_recognition import local_case  # noqa: F401
from scripts.evals import motion_preparation_speech as preparation


async def test_local_asr_uses_product_service_and_retains_claim_and_result_once(local_case, tmp_path, monkeypatch):  # noqa: F811
    c = local_case
    monkeypatch.setattr(preparation, "LocalMotionSpeech", lambda _: c.recognizer)
    operation = uuid4()
    folder = tmp_path / "speech"
    result = await preparation.prepare_speech(c.prepared, c.settings, operation, folder)
    claim = json.loads((folder / "claim.json").read_bytes())
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert claim["operation_id"] == receipt["operation_id"] == str(uuid5(operation, "speech:0"))
    assert result.context["speech_result"]["provenance"] == "local_asr_unreviewed"
    assert result.context["speech_result"]["source_sha256"] == c.prepared.context["source"]["sha256"]
    assert receipt["result"] == c.recognizer.transcribe.return_value and receipt["estimated_usd_micros"] == 0
    assert stat.S_IMODE((folder / "receipt.json").stat().st_mode) == 0o600
    assert stat.S_IMODE(folder.stat().st_mode) == 0o700
    before = (folder / "claim.json").read_bytes()
    with pytest.raises(FileExistsError):
        await preparation.prepare_speech(c.prepared, c.settings, operation, folder)
    c.recognizer.transcribe.assert_awaited_once()
    assert (folder / "claim.json").read_bytes() == before


async def test_failure_and_changed_operation_cannot_fabricate_a_receipt(local_case, tmp_path, monkeypatch):  # noqa: F811
    c = local_case
    folder = tmp_path / "failed"
    operation = uuid4()
    c.recognizer.transcribe.side_effect = ValueError("synthetic decode failure")
    monkeypatch.setattr(preparation, "LocalMotionSpeech", lambda _: c.recognizer)
    with pytest.raises(ValueError, match="decode failure"):
        await preparation.prepare_speech(c.prepared, c.settings, operation, folder)
    assert (folder / "claim.json").exists() and not (folder / "receipt.json").exists()
    journal = preparation.PreparationSpeechJournal(c.settings, folder)
    with pytest.raises(ValueError, match="OPERATION_CHANGED"):
        await journal.received({"operation_id": operation}, uuid4(), uuid4(), {}, 0)
    assert not (folder / "receipt.json").exists()


async def test_disabled_policy_performs_no_io(local_case, tmp_path):  # noqa: F811
    c = local_case
    c.prepared.context.pop("speech_recognition")
    folder = tmp_path / "absent"
    assert await preparation.prepare_speech(c.prepared, c.settings, uuid4(), folder) is c.prepared
    assert not folder.exists()
