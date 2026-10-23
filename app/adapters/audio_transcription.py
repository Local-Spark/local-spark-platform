"""Bounded audio normalization and one-shot speech-to-text provider call."""

import asyncio
import math
import tempfile
from pathlib import Path
from uuid import UUID

import httpx

from app.adapters.material_media import MaterialError
from app.core.config import Settings


async def _command(*args: str) -> bytes:
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
    except (FileNotFoundError, TimeoutError) as exc:
        if process is not None and process.returncode is None:
            process.kill()
            await process.communicate()
        raise MaterialError("AUDIO_CONVERSION_UNAVAILABLE") from exc
    if process.returncode != 0:
        raise MaterialError("AUDIO_INVALID")
    return stdout


async def normalize_audio(data: bytes) -> tuple[bytes, int]:
    """Reject long/invalid audio before reserving any paid usage."""
    with tempfile.TemporaryDirectory(prefix="transcribe-") as folder:
        source, target = Path(folder) / "input", Path(folder) / "audio.wav"
        source.write_bytes(data)
        raw = await _command(
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(source),
        )
        try:
            duration = float(raw.strip())
        except ValueError as exc:
            raise MaterialError("AUDIO_INVALID") from exc
        if not math.isfinite(duration) or duration <= 0 or duration > 180:
            raise MaterialError("AUDIO_DURATION_INVALID")
        await _command(
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "wav",
            str(target),
        )
        if target.stat().st_size > 25_000_000:
            raise MaterialError("AUDIO_SIZE_EXCEEDED")
        return target.read_bytes(), math.ceil(duration)


class OpenAIAudioTranscriber:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(self, audio: bytes, event: UUID) -> str:
        key = self.settings.openai_api_key
        if self.settings.audio_transcription_mode != "openai" or key is None:
            raise MaterialError("AUDIO_PROVIDER_DISABLED")
        async with httpx.AsyncClient(timeout=90, follow_redirects=False, trust_env=False) as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {key.get_secret_value()}", "X-Client-Request-Id": str(event)},
                    data={"model": "gpt-transcribe"},
                    files={"file": ("audio.wav", audio, "audio/wav")},
                )
                response.raise_for_status()
                body = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise MaterialError("AUDIO_PROVIDER_UNCERTAIN") from exc
        transcript = body.get("text") if isinstance(body, dict) else None
        if not isinstance(transcript, str) or not transcript.strip() or len(transcript) > 16000:
            raise MaterialError("AUDIO_PROVIDER_INVALID")
        return transcript.strip()
