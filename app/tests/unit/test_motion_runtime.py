"""Explicit runner wiring and unmistakably synthetic qualification output."""

from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.adapters.motion_ai import OpenAIMotionProvider
from app.adapters.motion_fixture import FixtureMotionProvider
from app.services import motion_runtime
from app.services.auth import AuthError
from app.services.motion_protocols import MotionModelRequest
from app.tests.unit.test_motion_ai import frame


def configured(settings, mode="fake"):
    return settings.model_copy(
        update={
            "motion_execution_enabled": True,
            "motion_ai_mode": mode,
            "motion_local_qualification_business_id": uuid4(),
            "motion_local_qualification_asset_ids": (uuid4(),),
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
            "correlator_database_url": SecretStr("postgresql+asyncpg://unused:unused@localhost/local_test"),
            "motion_renderer_image": "sha256:" + "a" * 64,
            "motion_renderer_docker_executable": "/private/test/docker",
            "motion_renderer_docker_socket": "/private/test/docker.sock",
            "material_storage_bucket": "private-test",
            "motion_ai_reservation_usd_micros": 100,
            "motion_request_budget_usd_micros": 200,
            "visual_ai_monthly_budget_usd_micros": 1000,
            "visual_ai_global_monthly_budget_usd_micros": 1000,
            "openai_api_key": SecretStr("test-key-not-a-credential"),
            "motion_ai_model": "configured-test-model",
            "motion_ai_input_usd_micros_per_million_tokens": 1,
            "motion_ai_output_usd_micros_per_million_tokens": 2,
        }
    )


def test_unconfigured_runner_fails_before_constructing_any_adapter(settings, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unconfigured execution must not construct adapters")

    monkeypatch.setattr(motion_runtime, "MaterialStore", forbidden)
    with pytest.raises(AuthError, match="MOTION_EXECUTION_NOT_CONFIGURED"):
        motion_runtime.build_motion_runner(settings, AsyncMock(), AsyncMock())


@pytest.mark.parametrize("mode", ["fake", "openai"])
@pytest.mark.parametrize("scratch", ["", "/shared/motion"])
def test_runner_wires_separate_cost_database_and_explicit_provider_without_io(settings, monkeypatch, mode, scratch):
    cfg = configured(settings, mode)
    cfg.motion_renderer_scratch_directory = scratch
    app_database, worker_database = AsyncMock(), AsyncMock()

    def forbidden(*args, **kwargs):
        pytest.fail("Runner construction must not submit, render, read media or connect to a database")

    monkeypatch.setattr(motion_runtime.MaterialStore, "get_video", forbidden)
    monkeypatch.setattr(motion_runtime.IsolatedMotionRenderer, "render", forbidden)
    monkeypatch.setattr(OpenAIMotionProvider, "submit", forbidden)
    monkeypatch.setattr(FixtureMotionProvider, "submit", forbidden)
    app_database.transaction.side_effect = forbidden
    worker_database.transaction.side_effect = forbidden
    runner = motion_runtime.build_motion_runner(cfg, app_database, worker_database)
    assert runner.requests.database is app_database
    assert runner.inputs.store is runner.store
    assert runner.store.settings is cfg
    assert runner.renderer.image == cfg.motion_renderer_image
    assert runner.renderer.docker_executable == Path(cfg.motion_renderer_docker_executable)
    assert runner.renderer.docker_socket == Path(cfg.motion_renderer_docker_socket)
    assert runner.renderer.scratch_directory == (Path(scratch) if scratch else None)
    assert isinstance(runner.provider, FixtureMotionProvider if mode == "fake" else OpenAIMotionProvider)
    assert runner.provider.model == ("motion-qualification-v1" if mode == "fake" else cfg.motion_ai_model)
    assert runner.effects.ledger.database is worker_database


@pytest.mark.parametrize("kind", ["generate", "correct"])
async def test_fixture_preserves_audio_and_escapes_brand_without_claiming_creative_quality(kind):
    audio = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1.0}
        ],
    }
    context = {"kit": {"overrides": {"brand_name": '<script>alert("bad")</script>&'}}, "authorized_audio": audio}
    request = MotionModelRequest(uuid4(), kind, context)
    provider = FixtureMotionProvider()
    payload = provider.build_request(request)
    assert payload == {"kind": kind, "context": context}
    result = await provider.submit(request, payload)
    assert result.estimated_usd_micros == 0 and result.review is None
    assert result.composition.audio.model_dump(mode="json") == audio
    assert "<script>" not in result.composition.html
    assert "&lt;script&gt;" in result.composition.html and "&amp;" in result.composition.html
    assert "not a creative benchmark" in result.composition.concept
    assert "window.seek" in result.composition.scene_init


async def test_fixture_review_identifies_synthetic_evidence_and_never_claims_audio_listening():
    frames = (frame(100), frame(900))
    provider = FixtureMotionProvider()
    request = MotionModelRequest(uuid4(), "review", {}, frames=frames)
    result = await provider.submit(request, provider.build_request(request))
    assert result.estimated_usd_micros == 0 and result.composition is None
    review = result.review
    assert review.preferred == "undetermined" and not review.preference_evidence
    assert "not quality assessment" in review.limitations[0]
    for criterion in review.criteria:
        if criterion.name == "audio":
            assert criterion.status == "uncertain" and not criterion.evidence
        else:
            assert len(criterion.evidence) == 1
            assert criterion.evidence[0].at_ms == frames[0].ms
            assert criterion.evidence[0].sha256 == frames[0].sha256
        assert "no human or model evaluation" in criterion.observation


def test_illustration_provider_is_explicit_and_constructing_it_does_not_generate(settings, monkeypatch):
    from app.adapters.visual_ai import OpenAIVisualProvider
    from app.tests.unit.test_motion_illustrations import art_settings

    generated = AsyncMock()
    monkeypatch.setattr(OpenAIVisualProvider, "generate", generated)
    runner = motion_runtime.build_motion_runner(art_settings(settings), AsyncMock(), AsyncMock())
    assert isinstance(runner.illustration_provider, OpenAIVisualProvider)
    generated.assert_not_awaited()


def test_runner_wires_optional_local_speech_without_loading_a_model(settings, tmp_path, monkeypatch):
    from app.adapters.motion_local_speech import LocalMotionSpeech

    cfg = configured(settings)
    cfg.motion_speech_mode = "local"
    cfg.motion_speech_model_directory = str(tmp_path)
    cfg.motion_speech_model_sha256 = "a" * 64

    def forbidden(*args, **kwargs):
        pytest.fail("Construction must not transcribe or load model weights")

    monkeypatch.setattr(LocalMotionSpeech, "transcribe", forbidden)
    runner = motion_runtime.build_motion_runner(cfg, AsyncMock(), AsyncMock())
    assert isinstance(runner.speech_recognizer, LocalMotionSpeech)
    assert runner.speech_recognizer.directory == str(tmp_path)
