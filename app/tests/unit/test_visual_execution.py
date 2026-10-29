"""Real product execution needs explicit bounded configuration, even after copying settings."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.visual_execution import require_visual_execution


def configured(settings):
    return settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
            "service_agreement_required": True,
            "openai_api_key": SecretStr("synthetic-unusable-key"),
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )


def test_product_execution_is_explicit_and_does_not_grant_api_the_worker_login(settings):
    ready = configured(settings).model_copy(update={"correlator_database_url": None})
    assert ready.visual_execution_ready()
    require_visual_execution(ready)
    assert Settings(_env_file=None, **ready.model_dump()).visual_execution_ready()
    assert not settings.visual_ai_execution_enabled and settings.visual_ai_reservation_usd_micros == 0


@pytest.mark.parametrize(
    "change",
    [
        {"visual_ai_execution_enabled": False},
        {"environment": "production"},
        {"environment": "staging"},
        {"visual_ai_mode": "fake"},
        {"visual_ai_mode": "disabled"},
        {"openai_api_key": None},
        {"openai_api_key": SecretStr(" ")},
        {"meta_encryption_key": None},
        {"meta_encryption_key": SecretStr(" ")},
        {"service_agreement_required": False},
        {"visual_ai_reservation_usd_micros": 0},
        {"visual_ai_reservation_usd_micros": 101},
        {"visual_ai_monthly_budget_usd_micros": 69},
        {"visual_ai_global_monthly_budget_usd_micros": 69},
    ],
)
def test_configuration_cannot_be_bypassed_by_model_copy(settings, change):
    cfg = configured(settings).model_copy(update=change)
    assert not cfg.visual_execution_ready()
    with pytest.raises(AuthError, match="VISUAL_EXECUTION_DISABLED"):
        require_visual_execution(cfg)


def test_enabled_execution_startup_rejects_incomplete_limits(settings):
    cfg = configured(settings).model_dump()
    cfg["visual_ai_reservation_usd_micros"] = 0
    with pytest.raises(ValidationError, match="Visual execution requires"):
        Settings(_env_file=None, **cfg)


def test_real_mode_is_explicit_and_does_not_allow_legacy_adjustment_requests():
    request = PreviewRequest(operation_id=uuid4(), proposal_id=uuid4(), generation_mode="visual_ai")
    assert request.generation_mode == "visual_ai"
    with pytest.raises(ValidationError, match="VISUAL_ADJUSTMENT_UNAVAILABLE"):
        PreviewRequest(
            operation_id=uuid4(),
            proposal_id=uuid4(),
            generation_mode="visual_ai",
            parent_preview_id=uuid4(),
        )
