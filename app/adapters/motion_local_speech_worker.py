"""Short-lived CPU inference process; offline model bundle, bounded words, no customer logs."""

import hashlib
import importlib
import json
import sys
import wave
from pathlib import Path
from typing import Any


def bundle_hash(directory: Path) -> str:
    """Bind weights AND tokenizer/config; required local tokenizer prevents remote fallback."""
    required = {"model.bin", "config.json", "tokenizer.json"}
    files = sorted(p for p in directory.iterdir() if p.suffix in {".bin", ".json", ".txt"})
    names = {p.name for p in files}
    if (
        not required <= names
        or not names & {"vocabulary.json", "vocabulary.txt"}
        or sum(p.stat().st_size for p in files) > 512 * 1024 * 1024
    ):
        raise ValueError("MOTION_SPEECH_MODEL_INVALID")
    digest = hashlib.sha256()
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("MOTION_SPEECH_MODEL_INVALID")
        with path.open("rb") as stream:
            digest.update(path.name.encode() + b"\0" + hashlib.file_digest(stream, "sha256").digest())
    return digest.hexdigest()


def pcm_audio(wav: Path) -> Any:
    """FFmpeg already produced bounded mono PCM; avoid a second PyAV decode."""
    with wave.open(str(wav), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
            raise ValueError("MOTION_SPEECH_WAV_INVALID")
        # Pipe WAV headers can declare an unknown frame count; cap the actual read.
        pcm = audio.readframes(16000 * 60 + 1)
    if not pcm or len(pcm) > 16000 * 60 * 2 or len(pcm) % 2:
        raise ValueError("MOTION_SPEECH_WAV_INVALID")
    numpy = importlib.import_module("numpy")
    return numpy.frombuffer(pcm, dtype="<i2").astype(numpy.float32) / 32768.0


def transcribe(wav: Path, directory: Path, expected_hash: str, language: str, threads: int) -> dict[str, Any]:
    if bundle_hash(directory) != expected_hash:
        raise ValueError("MOTION_SPEECH_MODEL_CHANGED")
    library = importlib.import_module("faster_whisper")
    model = library.WhisperModel(
        str(directory), device="cpu", compute_type="int8", cpu_threads=threads, num_workers=1, local_files_only=True
    )
    segments, info = model.transcribe(
        pcm_audio(wav),
        language=language,
        beam_size=5,
        word_timestamps=True,
        condition_on_previous_text=False,
        temperature=0.0,
        vad_filter=False,
    )
    words = []
    for segment in segments:
        if segment.text.strip() and not segment.words:
            raise ValueError("MOTION_SPEECH_WORDS_MISSING")
        for word in segment.words or ():
            words.append(
                {"text": word.word.strip(), "start": word.start, "end": word.end, "confidence": word.probability}
            )
            if len(words) > 300:
                raise ValueError("MOTION_SPEECH_WORD_LIMIT")
    return {"words": words, "language": info.language, "engine_version": library.__version__}


def main() -> None:
    result = transcribe(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5]))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
