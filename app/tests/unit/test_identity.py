import secrets
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest

from app.core.identity import actor_for_subject
from app.core.passwords import Passwords
from app.services.auth import AuthError, AuthService
from app.tests.unit.test_core import access_token


def test_legacy_actor_ids_are_stable_and_namespaced():
    assert actor_for_subject("issuer", "subject") == actor_for_subject("issuer", "subject")
    assert actor_for_subject("issuer", "subject") != actor_for_subject("other", "subject")


async def test_password_hash_and_mismatch():
    passwords = Passwords()
    password = secrets.token_urlsafe(20)
    hashed = await passwords.hash(password)
    assert hashed.startswith("$argon2id$")
    assert await passwords.verify(password, hashed)
    assert not await passwords.verify("wrong", hashed)
    assert not await passwords.verify(password, None)
    assert not await passwords.verify(password, "invalid stored hash")


@pytest.mark.parametrize(
    "changes", [{"type": "refresh"}, {"sid": "bad-uuid"}, {"sub": "bad-uuid"}, {"aud": "wrong"}, {"exp": 1}]
)
async def test_native_token_rejects_invalid_claims(settings, fake_database, changes):
    auth = AuthService(settings, fake_database)
    with pytest.raises(jwt.InvalidTokenError):
        await auth.authenticate(access_token(settings, **changes))


def test_auth_error_is_sanitized():
    assert str(AuthError("INVALID_ACTION", 400)) == "INVALID_ACTION"


@pytest.mark.parametrize("tls", [False, True])
def test_smtp_security_and_headers(settings, monkeypatch, tls):
    from unittest.mock import MagicMock

    from pydantic import SecretStr

    from app.services.auth_mail import send_mail

    smtp = MagicMock()
    monkeypatch.setattr("app.services.auth_mail.smtplib.SMTP", smtp)
    config = settings.model_copy(
        update={
            "smtp_starttls": tls,
            "smtp_username": "test-user" if tls else None,
            "smtp_password": SecretStr("test-password"),
        }
    )
    send_mail(config, {"to": "test@example.com", "subject": "Confirmar e-mail", "body": "Local test body"})
    connection = smtp.return_value.__enter__.return_value
    assert connection.starttls.called == tls and connection.login.called == tls
    message = connection.send_message.call_args.args[0]
    assert message["To"] == "test@example.com"


async def test_mfa_challenge_consumed_during_credential_lock(settings, fake_database):
    from unittest.mock import MagicMock

    import pyotp

    auth = AuthService(settings, fake_database)
    secret = pyotp.random_base32()
    challenge = {"user_id": uuid4(), "version": 1, "setup_secret": auth.cipher.encrypt(secret.encode()).decode()}
    credential = {"active": True, "version": 1, "mfa_secret": None, "mfa_step": -1, "recovery_hashes": []}
    first, second = MagicMock(), MagicMock()
    first.mappings.return_value.one_or_none.return_value = challenge
    second.mappings.return_value.one.return_value = credential
    db = AsyncMock()
    db.execute.side_effect = [first, second]
    db.scalar.return_value = None
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def transaction(*args):
        yield db

    fake_database.transaction = transaction
    with pytest.raises(AuthError, match="INVALID_MFA"):
        await auth.verify_mfa("test-challenge", pyotp.TOTP(secret).now())


def test_https_cookies_are_host_only_secure_and_http_only(settings):
    from types import SimpleNamespace

    from fastapi import Request

    from app.api.v1.auth import reply

    request = Request(
        {
            "type": "http",
            "app": SimpleNamespace(
                state=SimpleNamespace(settings=settings.model_copy(update={"public_web_url": "https://spark.example"}))
            ),
            "headers": [],
        }
    )
    response = reply(request, {"access_token": "test-access", "_refresh": "test-refresh", "_csrf": "test-csrf"})
    cookies = response.headers.getlist("set-cookie")
    assert cookies[0].startswith("__Host-spark-refresh=") and "Secure" in cookies[0] and "HttpOnly" in cookies[0]
    assert "Domain=" not in cookies[0]
    assert "HttpOnly" not in cookies[1]
