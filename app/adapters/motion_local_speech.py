"""Run local ASR with a killable timeout, bounded output and offline environment."""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from app.adapters.material_media import FetchedMedia
from app.adapters.motion_html_renderer import MotionRenderError, _command
from app.adapters.motion_media import inspect_and_extract_motion_audio
from app.services.auth import AuthError


class LocalMotionSpeech:
    def __init__(self, directory: str):
        self.directory = directory

    async def transcribe(self, source: bytes, sha256: str, policy: dict[str, Any]) -> dict[str, Any]:
        info, audio = await inspect_and_extract_motion_audio(FetchedMedia(source, "video/mp4", sha256))
        if audio is None or info.duration_seconds > 60:
            raise AuthError("MOTION_SPEECH_SOURCE_INVALID", 409)
        with tempfile.TemporaryDirectory(prefix="motion-speech-") as folder:
            wav = Path(folder) / "source.wav"
            wav.write_bytes(audio)
            try:
                raw = await _command(
                    [
                        sys.executable,
                        "-m",
                        "app.adapters.motion_local_speech_worker",
                        str(wav),
                        self.directory,
                        policy["model_sha256"],
                        policy["language"],
                        str(policy["threads"]),
                    ],
                    env={
                        "PATH": os.defpath,
                        "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                        "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1",
                        "TOKENIZERS_PARALLELISM": "false",
                        "OMP_NUM_THREADS": str(policy["threads"]),
                    },
                    timeout=policy["timeout_seconds"],
                    limit=256 * 1024,
                )
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError
                return result
            except (MotionRenderError, ValueError) as exc:
                raise AuthError("MOTION_SPEECH_EXECUTION_FAILED", 409) from exc
