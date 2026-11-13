"""Private one-shot preparation journal around the same speech service used by Temporal."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid5

from app.adapters.motion_local_speech import LocalMotionSpeech
from app.services.motion_speech_recognition import MotionSpeechRecognition


def write_once(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)


class PreparationSpeechJournal:
    """Local evidence for this inspection, never an admitted request or paid reservation."""

    def __init__(self, settings, folder):
        self.requests = SimpleNamespace(settings=settings)
        self.folder = folder
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)

    async def claim(self, row, token, operation, kind, payload):
        write_once(
            self.folder / "claim.json",
            {
                "operation_id": str(operation),
                "parent_operation_id": str(row["operation_id"]),
                "kind": kind,
                "payload": payload,
                "scope": "local_preparation_no_database_admission",
            },
        )

    async def received(self, row, token, operation, result, estimate):
        claim = json.loads((self.folder / "claim.json").read_bytes())
        if claim["operation_id"] != str(operation) or claim["parent_operation_id"] != str(row["operation_id"]):
            raise ValueError("PREPARATION_SPEECH_OPERATION_CHANGED")
        write_once(
            self.folder / "receipt.json",
            {
                "operation_id": str(operation),
                "result": result,
                "estimated_usd_micros": estimate,
                "scope": "new_local_asr_not_historical_injection",
            },
        )


async def prepare_speech(prepared, settings, operation_id: UUID, folder: Path):
    if prepared.context.get("speech_recognition") is None:
        return prepared
    effects = PreparationSpeechJournal(settings, folder)
    service = MotionSpeechRecognition(effects, LocalMotionSpeech(settings.motion_speech_model_directory))
    return await service.prepare({"operation_id": operation_id}, uuid5(operation_id, "preparation-speech"), prepared)
