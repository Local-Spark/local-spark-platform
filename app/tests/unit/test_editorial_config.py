"""Paid text generation stays disabled without explicit credentials and quota."""

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_editorial_provider_requires_key_and_daily_budget(settings):
    values = settings.model_dump()
    values.update(editorial_ai_mode="openai")
    with pytest.raises(ValidationError, match="Editorial AI requires"):
        Settings(_env_file=None, **values)
    values["openai_api_key"] = SecretStr("fake")
    with pytest.raises(ValidationError, match="Editorial AI requires"):
        Settings(_env_file=None, **values)
    values["editorial_daily_token_limit"] = 30000
    assert Settings(_env_file=None, **values).editorial_ai_mode == "openai"
    values["editorial_ai_model"] = ""
    with pytest.raises(ValidationError, match="Invalid editorial model"):
        Settings(_env_file=None, **values)
    values["editorial_ai_model"] = "x" * 81
    with pytest.raises(ValidationError, match="Invalid editorial model"):
        Settings(_env_file=None, **values)


def test_jev_requires_explicit_sandbox_credentials_budget_and_pinned_model(settings, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    values = settings.model_dump()
    values.pop("typesafe_api_key")
    values.update(intent_ai_mode="jev")
    with pytest.raises(ValidationError, match="Intent interpretation requires"):
        Settings(_env_file=None, **values)
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic")
    values.update(
        meta_encryption_key=SecretStr("test"),
        intent_ai_daily_budget_usd_micros=3000,
        intent_ai_model="unknown",
    )
    with pytest.raises(ValidationError, match="reviewed versioned pricing"):
        Settings(_env_file=None, **values)
    values["intent_ai_model"] = "jev-1.14.0"
    assert Settings(_env_file=None, **values).intent_ai_mode == "jev"
    values["intent_ai_input_rate_usd_micros"] = 1
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)
    values["intent_ai_input_rate_usd_micros"] = 42000
    values.update(
        environment="production",
        service_agreement_required=True,
        temporal_tls=True,
        public_web_url="https://example.test",
        jwt_secret=SecretStr("a" * 32),
        auth_database_url=values["database_url"],
        auth_encryption_key=SecretStr("private"),
        smtp_starttls=True,
        smtp_username="test",
        smtp_password=SecretStr("test"),
        material_storage_endpoint=None,
        material_storage_public_endpoint=None,
    )
    with pytest.raises(ValidationError, match="restricted to development"):
        Settings(_env_file=None, **values)
