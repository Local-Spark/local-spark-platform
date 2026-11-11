"""Local ASR contract, durable effects and offline subprocess; synthetic words/audio only."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from pydantic import ValidationError

from app.adapters import motion_local_speech as adapter
from app.adapters import motion_local_speech_worker as worker
from app.adapters.motion_html_renderer import MotionRenderError, RenderAsset
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.motion_speech import speech_context, validate_speech_plan
from app.services.motion_speech_policy import speech_policy
from app.services.motion_speech_recognition import MotionSpeechRecognition, recognized_timing
from app.tests.unit.test_motion_inputs import video_info
from app.tests.unit.test_motion_plan import planned


def raw_result():
    return {
        "words": [{"text": "Café", "start": 0, "end": 0.3, "confidence": 0.95}],
        "language": "pt",
        "engine_version": "synthetic",
    }


def source():
    return {
        "asset_id": "assets/source.mp4",
        "sha256": hashlib.sha256(b"source").hexdigest(),
        "duration_ms": 1000,
        "has_audio": True,
    }


@pytest.fixture
def local_case(settings, tmp_path):
    settings = settings.model_copy(
        update={
            "motion_speech_mode": "local",
            "motion_speech_model_directory": str(tmp_path),
            "motion_speech_model_sha256": "a" * 64,
        }
    )
    policy = speech_policy(settings)
    effects = SimpleNamespace(requests=SimpleNamespace(settings=settings), claim=AsyncMock(), received=AsyncMock())
    recognizer = SimpleNamespace(transcribe=AsyncMock(return_value=raw_result()))
    ctx = {"source": source(), "speech_recognition": policy, "request": {}}
    prepared = PreparedMotionInput(
        ctx,
        (RenderAsset("assets/source.mp4", "video/mp4", b"source", source()["sha256"]),),
        (),
        1000,
        {"mode": "mix", "tracks": []},
    )
    return SimpleNamespace(
        settings=settings,
        policy=policy,
        effects=effects,
        recognizer=recognizer,
        service=MotionSpeechRecognition(effects, recognizer),
        prepared=prepared,
        row={"operation_id": uuid4()},
        token=uuid4(),
    )


def test_local_policy_requires_explicit_configuration_without_reading_models(settings, tmp_path):
    assert speech_policy(settings) is None
    for directory, digest in [("relative", "a" * 64), (str(tmp_path), "bad")]:
        with pytest.raises(AuthError, match="NOT_CONFIGURED"):
            speech_policy(
                settings.model_copy(
                    update={
                        "motion_speech_mode": "local",
                        "motion_speech_model_directory": directory,
                        "motion_speech_model_sha256": digest,
                    }
                )
            )


async def test_local_result_is_claimed_persisted_and_attached_without_changing_source_or_audio(local_case):
    c = local_case
    result = await c.service.prepare(c.row, c.token, c.prepared)
    op = uuid5(c.row["operation_id"], "speech:0")
    assert c.effects.claim.await_args.args[2:4] == (op, "generate")
    assert c.effects.claim.await_args.args[4]["purpose"] == "local_speech_recognition"
    assert c.effects.received.await_args.args == (c.row, c.token, op, raw_result(), 0)
    assert result.context["transcript"]["provenance"] == "local_asr_unreviewed"
    assert result.context["transcript"]["cues"][0]["start_ms"] == 0
    assert result.assets is c.prepared.assets and result.audio is c.prepared.audio
    assert "speech_result" not in c.prepared.context
    with pytest.raises(AuthError, match="FOCUS_MISSING"):
        validate_speech_plan(planned(), result.context)
    comp = planned().model_dump(mode="json")
    comp["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]["speech_cue_id"] = "word-1"
    validate_speech_plan(type(planned()).model_validate(comp), result.context)
    result.context["speech_result"]["cues"][0]["confidence"] = 0.4
    result.context["transcript"] = speech_context(result.context, source())
    with pytest.raises(AuthError, match="BEAT_INVALID"):
        validate_speech_plan(type(planned()).model_validate(comp), result.context)
    with pytest.raises(ValidationError):
        MotionRequest(
            operation_id=uuid4(),
            source_asset_id=uuid4(),
            instruction="Test",
            speech_timing=result.context["speech_result"],
        )


@pytest.mark.parametrize(
    "case", ["disabled", "reviewed", "no_audio", "no_words", "replay", "provider", "invalid", "policy", "missing"]
)
async def test_no_hidden_execution_retry_or_substitution(local_case, case):
    c = local_case
    if case == "disabled":
        c.prepared.context.pop("speech_recognition")
    elif case == "reviewed":
        c.prepared.context["request"]["speech_timing"] = {"provenance": "owner_reviewed"}
    elif case == "no_audio":
        c.prepared.context["source"]["has_audio"] = False
    elif case == "no_words":
        c.recognizer.transcribe.return_value = {"words": []}
    elif case == "replay":
        c.effects.claim.side_effect = AuthError("MOTION_EFFECT_ALREADY_CLAIMED", 409)
    elif case == "provider":
        c.recognizer.transcribe.side_effect = AuthError("MOTION_SPEECH_EXECUTION_FAILED", 409)
    elif case == "invalid":
        c.recognizer.transcribe.return_value = {"words": "bad"}
    elif case == "policy":
        c.settings.motion_speech_threads = 3
    else:
        c.service.recognizer = None
    if case in {"replay", "provider", "invalid", "policy", "missing"}:
        with pytest.raises(AuthError):
            await c.service.prepare(c.row, c.token, c.prepared)
    else:
        result = await c.service.prepare(c.row, c.token, c.prepared)
        if case == "no_words":
            assert result.context["transcript"]["cues"] == []
            validate_speech_plan(planned(), result.context)
        else:
            assert result is c.prepared
    if case not in {"provider", "invalid", "no_words"}:
        c.recognizer.transcribe.assert_not_awaited()
    else:
        c.recognizer.transcribe.assert_awaited_once()
    if case == "invalid":
        c.effects.received.assert_awaited_once()


@pytest.mark.parametrize(
    "words",
    [
        None,
        "bad",
        [{}],
        [None],
        [{"text": "a", "start": True, "end": 1, "confidence": 1}],
        [{"text": "a", "start": float("nan"), "end": 1, "confidence": 1}],
        [{"text": "a", "start": 0.4, "end": 0.4, "confidence": 1}],
        [{"text": "a", "start": 0, "end": 1.1, "confidence": 1}],
        [{"text": "a", "start": 0, "end": 0.2, "confidence": 0.2}],
        [{}] * 301,
    ],
)
def test_invalid_or_uncertain_times_are_not_redistributed(words):
    with pytest.raises(AuthError):
        recognized_timing({"words": words}, source())


@pytest.mark.parametrize("failure", [None, "no_audio", "long", "command", "json", "shape"])
async def test_adapter_uses_offline_bounded_process_and_cleans_temp_audio(monkeypatch, tmp_path, failure):
    inspect = AsyncMock(
        return_value=(
            video_info(seconds=61 if failure == "long" else 1),
            None if failure == "no_audio" else b"synthetic wav",
        )
    )
    monkeypatch.setattr(adapter, "inspect_and_extract_motion_audio", inspect)
    paths = []

    async def command(args, *, env, timeout, limit):
        paths.append(Path(args[3]))
        assert paths[-1].read_bytes() == b"synthetic wav"
        assert "HF_HUB_OFFLINE" in env and env["HF_HUB_OFFLINE"] == "1"
        assert "OPENAI_API_KEY" not in env
        assert timeout == 180 and limit == 256 * 1024
        if failure == "command":
            raise MotionRenderError("MOTION_RENDER_TIMEOUT")
        return b"bad" if failure == "json" else b"[]" if failure == "shape" else json.dumps(raw_result()).encode()

    monkeypatch.setattr(adapter, "_command", command)
    policy = {"model_sha256": "a" * 64, "language": "pt", "threads": 2, "timeout_seconds": 180}
    if failure:
        with pytest.raises(AuthError):
            await adapter.LocalMotionSpeech(str(tmp_path)).transcribe(b"source", source()["sha256"], policy)
    else:
        assert (
            await adapter.LocalMotionSpeech(str(tmp_path)).transcribe(b"source", source()["sha256"], policy)
            == raw_result()
        )
    assert all(not path.exists() for path in paths)


def bundle(tmp_path):
    for name in ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt"):
        (tmp_path / name).write_bytes(b"synthetic")
    return worker.bundle_hash(tmp_path)


@pytest.mark.parametrize(
    "failure", ["missing", "vocabulary", "oversize", "symlink", "changed", "words_missing", "too_many", None]
)
def test_worker_binds_complete_bundle_and_requests_real_word_timestamps(monkeypatch, tmp_path, failure):
    digest = bundle(tmp_path)
    monkeypatch.setattr(worker, "pcm_audio", lambda _: "synthetic pcm")
    word = SimpleNamespace(word=" Café ", start=0.1, end=0.4, probability=0.95)
    segment = SimpleNamespace(
        text=" Café ", words=[word] * 301 if failure == "too_many" else None if failure == "words_missing" else [word]
    )
    model = SimpleNamespace(transcribe=lambda *_a, **kw: ([segment], SimpleNamespace(language="pt")))

    def factory(directory, **kw):
        assert directory == str(tmp_path)
        assert kw == {
            "device": "cpu",
            "compute_type": "int8",
            "cpu_threads": 2,
            "num_workers": 1,
            "local_files_only": True,
        }
        return model

    monkeypatch.setattr(
        worker.importlib, "import_module", lambda _: SimpleNamespace(WhisperModel=factory, __version__="synthetic")
    )
    if failure == "missing":
        (tmp_path / "tokenizer.json").unlink()
    elif failure == "vocabulary":
        (tmp_path / "vocabulary.txt").unlink()
    elif failure == "oversize":
        with (tmp_path / "model.bin").open("wb") as f:
            f.truncate(513 * 1024 * 1024)
    elif failure == "symlink":
        (tmp_path / "extra.json").symlink_to(tmp_path / "config.json")
    elif failure == "changed":
        (tmp_path / "config.json").write_bytes(b"changed")
    if failure:
        with pytest.raises(ValueError):
            worker.transcribe(tmp_path / "audio.wav", tmp_path, digest, "pt", 2)
    else:
        assert worker.transcribe(tmp_path / "audio.wav", tmp_path, digest, "pt", 2)["words"][0]["text"] == "Café"
        segment.words = []
        segment.text = ""
        assert worker.transcribe(tmp_path / "audio.wav", tmp_path, digest, "pt", 2)["words"] == []
        monkeypatch.setattr(worker.sys, "argv", ["worker", "audio.wav", str(tmp_path), digest, "pt", "2"])
        worker.main()


def test_automatic_policy_cannot_send_an_untranscribed_audio_to_generation(local_case):
    from app.services.motion_speech import validate_speech_input

    with pytest.raises(AuthError, match="MOTION_SPEECH_RESULT_REQUIRED"):
        validate_speech_input(local_case.prepared.context)


@pytest.mark.parametrize("failure", [None, "stereo", "rate", "width", "empty", "long", "odd"])
def test_pcm_audio_is_bounded_and_passes_exact_samples_without_pyav(tmp_path, monkeypatch, failure):
    import wave
    from unittest.mock import MagicMock, patch

    path = tmp_path / "audio.wav"
    data = b"\x00\x80\x00\x00\xff\x7f"
    if failure == "empty":
        data = b""
    elif failure == "long":
        data = b"\0" * (16000 * 60 * 2 + 2)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(2 if failure == "stereo" else 1)
        audio.setsampwidth(1 if failure == "width" else 2)
        audio.setframerate(8000 if failure == "rate" else 16000)
        audio.writeframes(data)
    if failure == "odd":
        with patch.object(wave.Wave_read, "readframes", return_value=b"x"):
            with pytest.raises(ValueError, match="WAV_INVALID"):
                worker.pcm_audio(path)
    elif failure:
        with pytest.raises(ValueError, match="WAV_INVALID"):
            worker.pcm_audio(path)
    else:
        numpy = MagicMock()
        monkeypatch.setattr(worker.importlib, "import_module", lambda name: numpy if name == "numpy" else None)
        samples = numpy.frombuffer.return_value
        assert worker.pcm_audio(path) is samples.astype.return_value.__truediv__.return_value
        numpy.frombuffer.assert_called_once_with(data, dtype="<i2")
        samples.astype.assert_called_once_with(numpy.float32)
        samples.astype.return_value.__truediv__.assert_called_once_with(32768.0)
