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
