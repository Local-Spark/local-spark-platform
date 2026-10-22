import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4, uuid5

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import JsonFormatter, configure_logging, request_id, request_id_context
from app.core.security import decode_actor
from app.db.session import Database
from app.schemas.business import BusinessCreate
from app.services.business import fingerprint


def access_token(settings, actor=None, **overrides):
    now = datetime.now(UTC)
    actor = actor or uuid4()
    return jwt.encode(
        {
            "sub": str(actor),
            "sid": str(uuid5(actor, "test-session")),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            **overrides,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def test_jwt_identity(settings):
    actor = uuid4()
    assert decode_actor(access_token(settings, actor), settings) == actor


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": 1},
        {"aud": "other-api"},
        {"iss": "untrusted"},
        {"sub": "not-a-uuid"},
    ],
)
def test_invalid_jwt(settings, claims):
    with pytest.raises(jwt.InvalidTokenError):
        decode_actor(access_token(settings, **claims), settings)


def test_unsigned_token_rejected(settings):
    token = jwt.encode({"sub": str(uuid4())}, key="", algorithm="none")
    with pytest.raises(jwt.InvalidTokenError):
        decode_actor(token, settings)


@pytest.mark.parametrize(
    "changes",
    [
        {"database_url": "sqlite:///test.db"},
        {"jwt_secret": "short"},
        {"pool_size": 0},
        {"environment": "production", "jwt_secret": "development-secret-long-enough-for-testing", "temporal_tls": True},
        {"environment": "production", "temporal_tls": False},
        {"environment": "production", "temporal_tls": True},
        {"environment": "production", "temporal_tls": True, "public_web_url": "https://meu-braco-direito.example"},
        {
            "environment": "production",
            "temporal_tls": True,
            "public_web_url": "https://meu-braco-direito.example",
            "auth_encryption_key": "c2VjdXJlLXRlc3Qta2V5LTAwMDAwMDAwMDAwMDAwMDA=",
            "smtp_starttls": False,
        },
    ],
)
def test_invalid_configuration(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**settings.model_dump(), **changes})


def test_safe_production_configuration(settings):
    value = Settings(
        _env_file=None,
        **{
            **settings.model_dump(),
            "environment": "production",
            "temporal_tls": True,
            "public_web_url": "https://meu-braco-direito.example",
            "auth_encryption_key": "c2VjdXJlLXRlc3Qta2V5LTAwMDAwMDAwMDAwMDAwMDA=",
            "smtp_starttls": True,
            "smtp_username": "test",
            "smtp_password": "unit-test-password",
        },
    )
    assert value.environment == "production"
    assert settings.jwt_secret.get_secret_value() not in repr(value)


@pytest.mark.parametrize(
    "changes",
    [
        {"phone_verify_mode": "twilio"},
        {
            "phone_verify_mode": "twilio",
            "twilio_verify_service_sid": "invalid",
            "twilio_api_key": "SKtest",
            "twilio_api_secret": "private",
        },
    ],
)
def test_phone_provider_rejects_incomplete_configuration(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**settings.model_dump(), **changes})


def test_phone_provider_accepts_complete_configuration(settings):
    configured = Settings(
        _env_file=None,
        **{
            **settings.model_dump(),
            "phone_verify_mode": "twilio",
            "twilio_verify_service_sid": "VA" + "a" * 32,
            "twilio_api_key": "SK" + "b" * 32,
            "twilio_api_secret": "private",
        },
    )
    assert configured.phone_verify_mode == "twilio"


@pytest.mark.parametrize(
    "changes",
    [
        {"meta_access_token": "token"},
        {"meta_graph_version": "v25.0"},
        {"material_storage_access_key": "key"},
        {"material_storage_secret_key": "secret"},
    ],
)
def test_material_provider_requires_paired_credentials(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**settings.model_dump(), **changes})


@pytest.mark.parametrize("field", ["material_storage_endpoint", "material_storage_public_endpoint"])
def test_material_endpoints_use_tls_outside_development(settings, field):
    base = {
        **settings.model_dump(),
        "environment": "staging",
        "temporal_tls": True,
        "public_web_url": "https://meu-braco-direito.example",
        "auth_database_url": settings.database_url,
        "auth_encryption_key": "c2VjdXJlLXRlc3Qta2V5LTAwMDAwMDAwMDAwMDAwMDA=",
        "smtp_starttls": True,
        "smtp_username": "test",
        "smtp_password": "unit-test-password",
    }
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**base, field: "http://storage.example"})
    assert Settings(_env_file=None, **{**base, field: "https://storage.example"}).environment == "staging"


@pytest.mark.parametrize(
    "environment,url,expected",
    [
        ("development", "http://localhost:5173", {"http://localhost:5173", "http://127.0.0.1:5173"}),
        ("testing", "http://127.0.0.1:5174", {"http://localhost:5174", "http://127.0.0.1:5174"}),
        ("development", "http://localhost", {"http://localhost", "http://127.0.0.1"}),
        ("development", "https://meu-braco-direito.example", {"https://meu-braco-direito.example"}),
        ("staging", "https://localhost:5173", {"https://localhost:5173"}),
        ("production", "https://127.0.0.1:5173", {"https://127.0.0.1:5173"}),
    ],
)
def test_auth_origins_only_expand_loopback_in_local_environments(settings, environment, url, expected):
    config = settings.model_copy(update={"environment": environment, "public_web_url": url})
    assert config.auth_origins == expected


def test_settings_cache(monkeypatch, settings):
    monkeypatch.setenv("MEU_BRACO_DIREITO_DATABASE_URL", settings.database_url.get_secret_value())
    monkeypatch.setenv("MEU_BRACO_DIREITO_JWT_SECRET", settings.jwt_secret.get_secret_value())
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    get_settings.cache_clear()


@pytest.mark.parametrize("name,timezone", [("  ", "UTC"), ("ok", "invalid/timezone"), ("ok", "/etc/passwd")])
def test_invalid_business(name, timezone):
    with pytest.raises(ValidationError):
        BusinessCreate(name=name, timezone=timezone)


def test_normalization_and_fingerprint():
    first = BusinessCreate(name="  Café  ")
    second = BusinessCreate(name="Café")
    assert fingerprint(first) == fingerprint(second)
    assert fingerprint(first) != fingerprint(BusinessCreate(name="Outro"))


def test_safe_json_logs():
    tenant = uuid4()
    record = logging.LogRecord("meu_braco_direito.worker", logging.INFO, "", 0, "operation.completed", (), None)
    record.tenant_id = tenant
    record.attempt = 2
    record.authorization = "secret-token"
    record.payload = "private-customer-message"
    record.signed_url = "https://example.com/?token=secret"
    record.provider = {"unsafe": "value"}
    token = request_id_context.set(str(uuid4()))
    try:
        data = json.loads(JsonFormatter().format(record))
    finally:
        request_id_context.reset(token)
    assert data["tenant_id"] == str(tenant)
    assert data["attempt"] == 2
    assert data["request_id"]
    assert not {"authorization", "payload", "signed_url", "provider"} & data.keys()


def test_exception_message_not_logged():
    try:
        raise ValueError("token=must-not-appear")
    except ValueError:
        import sys

        record = logging.LogRecord("meu_braco_direito", logging.ERROR, "", 0, "operation.failed", (), sys.exc_info())
    encoded = JsonFormatter().format(record)
    assert "must-not-appear" not in encoded
    assert json.loads(encoded)["exception_type"] == "ValueError"


def test_logging_configuration_does_not_add_handlers():
    configure_logging()
    configure_logging()
    assert len(logging.getLogger("meu_braco_direito").handlers) == 1


def test_request_ids():
    original = str(uuid4())
    assert request_id(original) == original
    for value in [None, "invalid\r\nheader", ""]:
        assert UUID(request_id(value))


def test_relay_requires_separate_connection(settings):
    value = settings.model_copy(update={"relay_database_url": None})
    with pytest.raises(ValueError, match="Database URL"):
        Database(value, relay=True)


def test_missing_migration_head_fails_readiness_configuration(monkeypatch):
    from unittest.mock import MagicMock

    from app.db import session as db_session

    db_session.current_schema_head.cache_clear()
    monkeypatch.setattr(db_session.ScriptDirectory, "from_config", lambda _: MagicMock(get_current_head=lambda: None))
    with pytest.raises(RuntimeError, match="No database migration head"):
        db_session.current_schema_head()
    db_session.current_schema_head.cache_clear()
