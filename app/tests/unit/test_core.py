import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

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
    return jwt.encode(
        {
            "sub": str(actor or uuid4()),
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
    ],
)
def test_invalid_configuration(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**settings.model_dump(), **changes})


def test_safe_production_configuration(settings):
    value = Settings(_env_file=None, **{**settings.model_dump(), "environment": "production", "temporal_tls": True})
    assert value.environment == "production"
    assert settings.jwt_secret.get_secret_value() not in repr(value)


def test_settings_cache(monkeypatch, settings):
    monkeypatch.setenv("LOCAL_SPARK_DATABASE_URL", settings.database_url.get_secret_value())
    monkeypatch.setenv("LOCAL_SPARK_JWT_SECRET", settings.jwt_secret.get_secret_value())
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
    record = logging.LogRecord("local_spark.worker", logging.INFO, "", 0, "operation.completed", (), None)
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

        record = logging.LogRecord("local_spark", logging.ERROR, "", 0, "operation.failed", (), sys.exc_info())
    encoded = JsonFormatter().format(record)
    assert "must-not-appear" not in encoded
    assert json.loads(encoded)["exception_type"] == "ValueError"


def test_logging_configuration_does_not_add_handlers():
    configure_logging()
    configure_logging()
    assert len(logging.getLogger("local_spark").handlers) == 1


def test_request_ids():
    original = str(uuid4())
    assert request_id(original) == original
    for value in [None, "invalid\r\nheader", ""]:
        assert UUID(request_id(value))


def test_relay_requires_separate_connection(settings):
    value = settings.model_copy(update={"relay_database_url": None})
    with pytest.raises(ValueError, match="Relay database URL"):
        Database(value, relay=True)
