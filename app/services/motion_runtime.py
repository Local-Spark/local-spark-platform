"""Construct explicit adapters; construction never dispatches an external effect."""

from pathlib import Path

from app.adapters.material_media import MaterialStore
from app.adapters.motion_ai import OpenAIMotionProvider
from app.adapters.motion_fixture import FixtureMotionProvider
from app.adapters.motion_html_renderer import IsolatedMotionRenderer
from app.adapters.motion_inputs import MotionInputLoader
from app.adapters.motion_local_speech import LocalMotionSpeech
from app.adapters.visual_ai import OpenAIVisualProvider
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.motion_illustration_policy import illustration_policy
from app.services.motion_orchestrator import MotionOrchestrator
from app.services.motion_protocols import MotionModelProvider
from app.services.motion_requests import MotionRequestService
from app.services.motion_speech_policy import speech_policy


def build_motion_runner(settings: Settings, database: Database, worker_database: Database) -> MotionOrchestrator:
    if not settings.motion_execution_ready():
        raise AuthError("MOTION_EXECUTION_NOT_CONFIGURED", 409)
    provider: MotionModelProvider
    if settings.motion_ai_mode == "fake":
        provider = FixtureMotionProvider()
    else:
        assert settings.openai_api_key is not None
        provider = OpenAIMotionProvider(
            settings.openai_api_key.get_secret_value(),
            model=settings.motion_ai_model,
            input_usd_micros_per_million_tokens=settings.motion_ai_input_usd_micros_per_million_tokens,
            output_usd_micros_per_million_tokens=settings.motion_ai_output_usd_micros_per_million_tokens,
            max_output_tokens=settings.motion_ai_max_output_tokens,
        )
    art_policy = illustration_policy(settings)
    store = MaterialStore(settings)
    return MotionOrchestrator(
        MotionRequestService(settings, database),
        worker_database,
        provider,
        IsolatedMotionRenderer(
            image=settings.motion_renderer_image,
            docker_executable=Path(settings.motion_renderer_docker_executable),
            docker_socket=Path(settings.motion_renderer_docker_socket),
            scratch_directory=Path(settings.motion_renderer_scratch_directory)
            if settings.motion_renderer_scratch_directory
            else None,
        ),
        MotionInputLoader(store),
        store,
        speech_recognizer=LocalMotionSpeech(settings.motion_speech_model_directory)
        if speech_policy(settings)
        else None,
        illustration_provider=OpenAIVisualProvider(settings.openai_api_key.get_secret_value())
        if art_policy is not None and settings.openai_api_key
        else None,
    )
