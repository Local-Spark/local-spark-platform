"""Typed environment configuration, following the Spotlight app/core convention."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOCAL_SPARK_", env_file=".env", extra="ignore")

    environment: Literal["development", "testing", "staging", "production"] = "development"
    project_name: str = "Local Spark API"
    database_url: SecretStr
    relay_database_url: SecretStr | None = None
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = "local-spark-local"
    jwt_audience: str = "local-spark-api"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "local-spark-foundation"
    temporal_api_key: SecretStr | None = None
    temporal_tls: bool = False
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=5, ge=0, le=50)

    @model_validator(mode="after")
    def production_safety(self) -> "Settings":
        if not self.database_url.get_secret_value().startswith("postgresql+asyncpg://"):
            raise ValueError("Use PostgreSQL with the asyncpg driver")
        if self.environment in {"production", "staging"}:
            if "development" in self.jwt_secret.get_secret_value().lower():
                raise ValueError("Development signing secrets are not allowed outside development")
            if not self.temporal_tls:
                raise ValueError("Temporal TLS is required outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
