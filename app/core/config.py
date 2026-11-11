"""Typed environment configuration, following the Spotlight app/core convention."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEU_BRACO_DIREITO_",
        env_file=".env",
        extra="ignore",
        env_ignore_empty=True,
        hide_input_in_errors=True,
    )

    environment: Literal["development", "testing", "staging", "production"] = "development"
    # Development/test migration switch; production must enforce the agreement.
    service_agreement_required: bool = False
    project_name: str = "Meu Braço Direito API"
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
    phone_verify_mode: Literal["disabled", "twilio"] = "disabled"
    phone_verify_channel: Literal["sms", "whatsapp"] = "sms"
    twilio_verify_service_sid: str | None = None
    twilio_api_key: str | None = None
    twilio_api_secret: SecretStr | None = None
    meta_webhook_mode: Literal["disabled", "cloud"] = "disabled"
    meta_database_url: SecretStr | None = None
    correlator_database_url: SecretStr | None = None
    meta_verify_token: SecretStr | None = None
    meta_app_secret: SecretStr | None = None
    meta_waba_id: str | None = None
    meta_phone_number_id: str | None = None
    meta_public_phone: str | None = None
    meta_encryption_key: SecretStr | None = None
    meta_access_token: SecretStr | None = None
    meta_reply_enabled: bool = False
    meta_daily_message_limit: int = Field(default=0, ge=0)
    meta_graph_version: str | None = Field(default=None, pattern=r"^v\d+\.\d+$")
    material_storage_bucket: str | None = None
    material_storage_region: str = "us-east-1"
    material_storage_endpoint: str | None = None
    material_storage_public_endpoint: str | None = None
    material_storage_access_key: SecretStr | None = None
    material_storage_secret_key: SecretStr | None = None
    audio_transcription_mode: Literal["disabled", "openai"] = "disabled"
    openai_api_key: SecretStr | None = None
    audio_daily_seconds_limit: int = Field(default=0, ge=0)
    editorial_ai_mode: Literal["disabled", "openai"] = "disabled"
    editorial_ai_model: str = "gpt-5-mini"
    editorial_creative_experimental: bool = False
    editorial_daily_token_limit: int = Field(default=0, ge=0)
    intent_ai_mode: Literal["disabled", "jev"] = "disabled"
    reference_discovery_mode: Literal["disabled", "fake"] = "disabled"
    reference_fixture_hmac_key: SecretStr | None = None
    reference_geocoding_enabled: bool = False
    reference_google_api_key: SecretStr | None = None
    reference_provider_hmac_key: SecretStr | None = None
    reference_provider_key_version: str = ""
    reference_google_credential_version: str = ""
    reference_provider_pilot_id: UUID | None = None
    reference_geocoding_tariff_version: str = ""
    reference_geocoding_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    reference_discovery_execution_enabled: bool = False
    reference_google_tariff_version: str = ""
    reference_google_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    reference_jev_tariff_version: str = ""
    reference_jev_credential_version: str = ""
    reference_jev_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    reference_apify_api_token: SecretStr | None = None
    reference_apify_actor_id: str = ""
    reference_apify_actor_build: str = ""
    reference_apify_tariff_version: str = ""
    reference_apify_credential_version: str = ""
    reference_apify_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    reference_learning_execution_enabled: bool = False
    reference_feed_actor_build: str = ""
    reference_feed_tariff_version: str = ""
    reference_feed_credential_version: str = ""
    reference_feed_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    reference_post_reserved_usd_micros: int = Field(default=0, ge=0, le=5_000_000)
    typesafe_api_key: SecretStr | None = Field(default=None, validation_alias="TYPESAFE_API_KEY")
    intent_ai_model: str = "jev-1.14.0"
    intent_ai_daily_budget_usd_micros: int = Field(default=0, ge=0)
    # The reviewed Jev price may be raised conservatively, never understated.
    intent_ai_input_rate_usd_micros: int = Field(default=42_000, ge=42_000)
    visual_ai_mode: Literal["disabled", "fake", "openai"] = "disabled"
    visual_ai_execution_enabled: bool = False
    visual_skill_experiment_enabled: bool = False
    visual_ai_reservation_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    visual_ai_monthly_budget_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    visual_ai_global_monthly_budget_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    # Qualification is deliberately limited to explicitly configured synthetic inputs.
    # Existing image/service agreements do not authorize production video processing.
    motion_ai_mode: Literal["disabled", "fake", "openai"] = "disabled"
    motion_execution_enabled: bool = False
    motion_local_qualification_business_id: UUID | None = None
    motion_local_qualification_asset_ids: tuple[UUID, ...] = ()
    motion_ai_model: str = ""
    motion_ai_max_output_tokens: int = Field(default=16000, ge=1024, le=64000)
    motion_ai_input_usd_micros_per_million_tokens: int = Field(default=0, ge=0)
    motion_ai_output_usd_micros_per_million_tokens: int = Field(default=0, ge=0)
    motion_ai_reservation_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    motion_request_budget_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    motion_speech_mode: Literal["disabled", "local"] = "disabled"
    motion_speech_model_directory: str = ""
    motion_speech_model_sha256: str = ""
    motion_speech_language: str = Field(default="pt", pattern=r"^[a-z]{2,3}$")
    motion_speech_threads: int = Field(default=2, ge=1, le=4)
    motion_speech_timeout_seconds: int = Field(default=180, ge=10, le=300)
    motion_storyboard_enabled: bool = False
    motion_illustrations_enabled: bool = False
    motion_illustration_reservation_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    motion_illustration_budget_usd_micros: int = Field(default=0, ge=0, le=1_000_000_000_000)
    motion_max_corrections: int = Field(default=1, ge=0, le=2)
    motion_renderer_image: str = ""
    motion_renderer_docker_executable: str = ""
    motion_renderer_docker_socket: str = ""
    motion_renderer_scratch_directory: str = ""
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = "meu-braco-direito-local"
    jwt_audience: str = "meu-braco-direito-api"
    public_web_url: str = "http://localhost:5173"
    auth_encryption_key: SecretStr = SecretStr("MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
    password_concurrency: int = Field(default=4, ge=1, le=32)
    smtp_host: str = "localhost"
    smtp_port: int = 11025
    smtp_starttls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    mail_from: str = "hello@meu-braco-direito.local"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "meu-braco-direito-foundation"
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
            if self.reference_discovery_mode != "disabled":
                raise ValueError("Reference discovery simulation is limited to local development and testing")
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
    def service_agreement_safety(self) -> "Settings":
        if self.environment == "production" and not self.service_agreement_required:
            raise ValueError("Production requires service agreement enforcement")
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

    @model_validator(mode="after")
    def phone_verify_safety(self) -> "Settings":
        if self.phone_verify_mode == "twilio":
            if not self.twilio_verify_service_sid or not self.twilio_api_key or not self.twilio_api_secret:
                raise ValueError("Twilio Verify requires service SID and API key credentials")
            if not self.twilio_verify_service_sid.startswith("VA"):
                raise ValueError("Invalid Twilio Verify service SID")
        return self

    @model_validator(mode="after")
    def meta_webhook_safety(self) -> "Settings":
        if self.meta_webhook_mode == "cloud":
            if not all(
                (
                    self.meta_database_url,
                    self.meta_verify_token,
                    self.meta_app_secret,
                    self.meta_waba_id,
                    self.meta_phone_number_id,
                    self.meta_encryption_key,
                )
            ):
                raise ValueError("Meta webhook requires isolated storage and provider credentials")
            from cryptography.fernet import Fernet

            try:
                Fernet(self.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
            except (ValueError, TypeError) as exc:
                raise ValueError("Invalid Meta inbox encryption key") from exc
        return self

    @model_validator(mode="after")
    def material_safety(self) -> "Settings":
        if self.audio_transcription_mode == "openai" and (
            not self.openai_api_key or not self.audio_daily_seconds_limit or not self.meta_encryption_key
        ):
            raise ValueError("Audio transcription requires a provider key, encryption key and daily seconds limit")
        if bool(self.meta_access_token) != bool(self.meta_graph_version):
            raise ValueError("Meta media access token and Graph version must be configured together")
        if self.meta_reply_enabled and (
            not self.meta_encryption_key
            or not self.meta_access_token
            or not self.meta_phone_number_id
            or self.meta_daily_message_limit < 1
        ):
            raise ValueError("Meta replies require Cloud API credentials and a daily message limit")
        if bool(self.material_storage_access_key) != bool(self.material_storage_secret_key):
            raise ValueError("Object storage access key and secret must be configured together")
        if self.environment in {"staging", "production"}:
            if self.material_storage_endpoint and not self.material_storage_endpoint.startswith("https://"):
                raise ValueError("Object storage endpoint must use HTTPS outside development")
            if self.material_storage_public_endpoint and not self.material_storage_public_endpoint.startswith(
                "https://"
            ):
                raise ValueError("Public object storage endpoint must use HTTPS outside development")
        return self

    @model_validator(mode="after")
    def editorial_ai_safety(self) -> "Settings":
        if self.visual_ai_mode == "fake" and self.environment not in {"development", "testing"}:
            raise ValueError("Fake visual AI is restricted to development and testing")
        if self.visual_ai_mode == "openai":
            if self.environment not in {"development", "testing"}:
                raise ValueError("Visual AI is restricted to development and testing")
            if (
                not self.openai_api_key
                or not self.openai_api_key.get_secret_value().strip()
                or self.visual_ai_monthly_budget_usd_micros <= 0
            ):
                raise ValueError("Visual AI requires explicit credentials and a monthly budget")
        if self.visual_ai_execution_enabled and not self.visual_execution_ready():
            raise ValueError(
                "Visual execution requires development/testing, OpenAI credentials, encryption, "
                "service agreement and explicit per-attempt, tenant and aggregate budgets"
            )
        if self.editorial_creative_experimental and self.environment not in {"development", "testing"}:
            raise ValueError("Experimental editorial copy is restricted to development and testing")
        if self.intent_ai_mode == "jev":
            if self.environment not in {"development", "testing"}:
                raise ValueError("Intent interpretation is restricted to development and testing")
            if not self.typesafe_api_key or not self.meta_encryption_key or self.intent_ai_daily_budget_usd_micros <= 0:
                raise ValueError("Intent interpretation requires explicit credentials and a daily budget")
            if self.intent_ai_model != "jev-1.14.0":
                raise ValueError("Intent model requires a reviewed versioned pricing configuration")
        if self.editorial_ai_mode == "openai" and (not self.openai_api_key or self.editorial_daily_token_limit < 30000):
            raise ValueError("Editorial AI requires a provider key and daily token reservation limit")
        if not self.editorial_ai_model or len(self.editorial_ai_model) > 80:
            raise ValueError("Invalid editorial model")
        return self

    def reference_geocoding_ready(self) -> bool:
        """Explicit credentials and ledger configuration gate charged address resolution."""
        return bool(
            self.reference_geocoding_enabled
            and self.environment in {"development", "testing"}
            and self.correlator_database_url
            and self.reference_google_api_key
            and self.reference_google_api_key.get_secret_value().strip()
            and self.reference_provider_hmac_key
            and len(self.reference_provider_hmac_key.get_secret_value()) >= 32
            and self.reference_provider_key_version
            and self.reference_google_credential_version
            and self.reference_provider_pilot_id
            and self.reference_geocoding_tariff_version
            and self.reference_geocoding_reserved_usd_micros > 0
        )

    def reference_discovery_ready(self) -> bool:
        """One default-off gate shared by the owner API, relay and worker."""
        return bool(
            self.reference_discovery_execution_enabled
            and self.environment in {"development", "testing"}
            and self.correlator_database_url
            and self.reference_google_api_key
            and self.reference_google_api_key.get_secret_value().strip()
            and self.reference_provider_hmac_key
            and len(self.reference_provider_hmac_key.get_secret_value().encode()) >= 32
            and self.reference_provider_key_version
            and self.reference_google_credential_version
            and self.reference_provider_pilot_id
            and self.reference_google_tariff_version
            and self.reference_google_reserved_usd_micros > 0
            and self.typesafe_api_key
            and self.typesafe_api_key.get_secret_value().strip()
            and self.reference_jev_tariff_version
            and self.reference_jev_credential_version
            and self.reference_jev_reserved_usd_micros > 0
            and self.reference_apify_api_token
            and self.reference_apify_api_token.get_secret_value().strip()
            and self.reference_apify_actor_id
            and self.reference_apify_actor_build
            and self.reference_apify_tariff_version
            and self.reference_apify_credential_version
            and self.reference_apify_reserved_usd_micros >= 500_000
        )

    def reference_learning_ready(self) -> bool:
        """Feed analysis is independent of Google discovery and remains default-off."""
        return bool(
            self.reference_learning_execution_enabled
            and self.environment in {"development", "testing"}
            and self.correlator_database_url
            and self.reference_provider_hmac_key
            and len(self.reference_provider_hmac_key.get_secret_value().encode()) >= 32
            and self.reference_provider_key_version
            and self.reference_provider_pilot_id
            and self.typesafe_api_key
            and self.typesafe_api_key.get_secret_value().strip()
            and self.reference_jev_tariff_version
            and self.reference_jev_credential_version
            and self.reference_post_reserved_usd_micros > 0
            and self.reference_apify_api_token
            and self.reference_apify_api_token.get_secret_value().strip()
            and self.reference_feed_actor_build
            and self.reference_feed_tariff_version
            and self.reference_feed_credential_version
            and self.reference_feed_reserved_usd_micros > 0
        )

    def motion_execution_ready(self) -> bool:
        return bool(
            self.motion_execution_enabled
            and self.environment in {"development", "testing"}
            and self.motion_ai_mode in {"fake", "openai"}
            and self.motion_local_qualification_business_id
            and self.motion_local_qualification_asset_ids
            and self.meta_encryption_key
            and self.correlator_database_url
            and self.motion_renderer_image
            and self.motion_renderer_docker_executable
            and self.motion_renderer_docker_socket
            and self.material_storage_bucket
            and self.motion_ai_reservation_usd_micros > 0
            and self.motion_request_budget_usd_micros >= 2 * self.motion_ai_reservation_usd_micros
            and self.visual_ai_monthly_budget_usd_micros > 0
            and (
                self.motion_ai_mode == "fake"
                or (
                    self.openai_api_key
                    and self.motion_ai_model
                    and self.motion_ai_input_usd_micros_per_million_tokens > 0
                    and self.motion_ai_output_usd_micros_per_million_tokens > 0
                    and self.visual_ai_global_monthly_budget_usd_micros > 0
                )
            )
        )

    def visual_execution_ready(self) -> bool:
        """One technical configuration rule for API, dispatch and worker wiring."""
        return bool(
            self.visual_ai_execution_enabled
            and self.environment in {"development", "testing"}
            and self.visual_ai_mode == "openai"
            and self.openai_api_key
            and self.openai_api_key.get_secret_value().strip()
            and self.meta_encryption_key
            and self.meta_encryption_key.get_secret_value().strip()
            and self.service_agreement_required
            and 0
            < self.visual_ai_reservation_usd_micros
            <= min(self.visual_ai_monthly_budget_usd_micros, self.visual_ai_global_monthly_budget_usd_micros)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
