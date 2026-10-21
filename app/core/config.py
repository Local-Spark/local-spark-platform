"""Typed environment configuration, following the Spotlight app/core convention."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOCAL_SPARK_", env_file=".env", extra="ignore", env_ignore_empty=True, hide_input_in_errors=True
    )

    environment: Literal["development", "testing", "staging", "production"] = "development"
    project_name: str = "Local Spark API"
    database_url: SecretStr
    relay_database_url: SecretStr | None = None
    auth_database_url: SecretStr | None = None
    billing_database_url: SecretStr | None = None
    billing_mode: Literal["disabled", "test", "live"] = "disabled"
    billing_live_enabled: bool = False
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None
    stripe_price_id: str | None = None
    billing_monthly_amount_minor: int | None = Field(default=None, gt=0)
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = "local-spark-local"
    jwt_audience: str = "local-spark-api"
    public_web_url: str = "http://localhost:5173"
    auth_encryption_key: SecretStr = SecretStr("MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
    password_concurrency: int = Field(default=4, ge=1, le=32)
    smtp_host: str = "localhost"
    smtp_port: int = 11025
    smtp_starttls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    mail_from: str = "hello@local-spark.local"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "local-spark-foundation"
    temporal_api_key: SecretStr | None = None
    temporal_tls: bool = False
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=5, ge=0, le=50)

    @property
    def auth_origins(self) -> set[str]:
        origins = {self.public_web_url}
        if self.environment in {"development", "testing"}:
            web = urlsplit(self.public_web_url)
            if web.hostname in {"localhost", "127.0.0.1"}:
                alias = "127.0.0.1" if web.hostname == "localhost" else "localhost"
                authority = f"{alias}:{web.port}" if web.port is not None else alias
                origins.add(web._replace(netloc=authority).geturl())
        return origins

    @model_validator(mode="after")
    def production_safety(self) -> "Settings":
        if not self.database_url.get_secret_value().startswith("postgresql+asyncpg://"):
            raise ValueError("Use PostgreSQL with the asyncpg driver")
        if self.environment in {"production", "staging"}:
            if "development" in self.jwt_secret.get_secret_value().lower():
                raise ValueError("Development signing secrets are not allowed outside development")
            if not self.temporal_tls:
                raise ValueError("Temporal TLS is required outside development")
            if not self.public_web_url.startswith("https://") or self.auth_database_url is None:
                raise ValueError("HTTPS web origin and dedicated auth database login are required")
            if self.auth_encryption_key.get_secret_value() == "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=":
                raise ValueError("A private auth encryption key is required")
            if not self.smtp_starttls or not self.smtp_username or self.smtp_password is None:
                raise ValueError("Authenticated TLS mail delivery is required")
        return self

    @model_validator(mode="after")
    def billing_safety(self) -> "Settings":
        if self.billing_mode != "disabled":
            if not all(
                (
                    self.billing_database_url,
                    self.stripe_secret_key,
                    self.stripe_webhook_secret,
                    self.stripe_price_id,
                    self.billing_monthly_amount_minor,
                )
            ):
                raise ValueError("Billing requires an isolated login, price, amount and provider credentials")
            if not self.stripe_secret_key.get_secret_value().startswith(f"sk_{self.billing_mode}_"):  # type: ignore[union-attr]
                raise ValueError("Stripe credential does not match billing mode")
            if self.billing_mode == "live" and (self.environment != "production" or not self.billing_live_enabled):
                raise ValueError("Live billing requires explicit production activation")
            if self.billing_mode == "test" and self.environment == "production":
                raise ValueError("Test billing is not allowed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
