import os
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import Settings
from app.main import create_app


class IntegrationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=(Path(__file__).parents[2] / ".env.test.example", Path(__file__).parents[2] / ".env.test"),
        extra="ignore",
    )

    admin_database_url: SecretStr
    database_url: SecretStr
    relay_database_url: SecretStr
    temporal_address: str


def pytest_configure():
    # Only test configuration is loaded here; the application's .env is never a DB fallback.
    config = IntegrationSettings()
    for field, value in config.model_dump().items():
        os.environ.setdefault(
            f"TEST_{field.upper()}", value.get_secret_value() if isinstance(value, SecretStr) else value
        )


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        environment="testing",
        database_url=os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost/unused"),
        relay_database_url=os.getenv("TEST_RELAY_DATABASE_URL"),
        jwt_secret="unit-test-secret-with-at-least-32-characters",
    )


@pytest.fixture
def fake_database():
    db = AsyncMock()
    db.ready.return_value = True

    @asynccontextmanager
    async def transaction(*args):
        yield AsyncMock()

    db.transaction = transaction
    return db


@pytest.fixture
def client(settings, fake_database):
    with TestClient(create_app(settings, fake_database), raise_server_exceptions=False) as result:
        yield result
