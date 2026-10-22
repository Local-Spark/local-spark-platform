import asyncio
import json
from unittest.mock import AsyncMock, Mock
from urllib.parse import unquote

import jwt
import pyotp
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.auth import ZERO, AuthError, digest, now
from app.services.auth_mail import deliver_once

pytestmark = pytest.mark.integration
PASSWORD = "A long test password 2026!"
EMAIL = "ana@example.com"


async def mail_token(admin, service, purpose):
    async with admin.connect() as db:
        ciphertext = await db.scalar(
            text("""SELECT m.ciphertext FROM auth_mail m JOIN auth_actions a ON a.digest=m.action_digest
        WHERE a.purpose=:purpose ORDER BY a.expires_at DESC LIMIT 1"""),
            {"purpose": purpose},
        )
    payload = json.loads(service.cipher.decrypt(ciphertext.encode()))
    return unquote(payload["body"].split("#token=")[1].splitlines()[0])


@pytest.fixture
async def registered(auth_service, admin):
    await auth_service.register(EMAIL, "Ana Silva", PASSWORD)
    await auth_service.consume_action(await mail_token(admin, auth_service, "verify"), "verify")
    return auth_service


async def test_register_verify_login_refresh_logout_http(native_api, admin, auth_service):
    payload = {"email": "Ana@EXAMPLE.com", "display_name": "Ana Silva", "password": PASSWORD}
    first = await native_api.post("/api/v1/auth/register", json=payload)
    duplicate = await native_api.post("/api/v1/auth/register", json=payload)
    assert first.status_code == duplicate.status_code == 202
    assert first.json() == duplicate.json()
    token = await mail_token(admin, auth_service, "verify")
    assert (await native_api.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 200
    assert (await native_api.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 400
    bad = await native_api.post("/api/v1/auth/login", json={"email": EMAIL, "password": "wrong"})
    assert bad.status_code == 401
    logged = await native_api.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert logged.status_code == 200 and "_refresh" not in logged.json()
    assert "httponly" in logged.headers.get_list("set-cookie")[0].lower()
    headers = {"Authorization": "Bearer " + logged.json()["access_token"]}
    view = await native_api.post("/api/v1/session", headers=headers)
    assert view.status_code == 200 and view.json()["user"]["email_verified"] and not view.json()["is_staff"]
    assert (await native_api.get("/api/v1/admin/overview", headers=headers)).status_code == 403
    csrf = native_api.cookies["meu-braco-direito-csrf"]
    assert (await native_api.post("/api/v1/auth/refresh")).status_code == 403
    refreshed = await native_api.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert refreshed.status_code == 200
    assert (await native_api.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})).status_code == 204
    assert (await native_api.get("/api/v1/me", headers=headers)).status_code == 401
    assert (await native_api.post("/api/v1/auth/refresh")).status_code == 401
    assert (
        await native_api.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": EMAIL, "password": PASSWORD},
        )
    ).status_code == 403
    invalid = await native_api.post("/api/v1/auth/register", json={**payload, "password": "private-short-value"[:4]})
    assert invalid.status_code == 422 and "private-short-value" not in invalid.text
    assert (
        await native_api.post("/api/v1/auth/register", json={**payload, "email": "not-an-email"})
    ).status_code == 422


async def test_register_verify_and_login_from_loopback_alias(native_api, admin, auth_service):
    headers = {"Origin": "http://127.0.0.1:5173"}
    payload = {"email": EMAIL, "display_name": "Ana Silva", "password": PASSWORD}
    response = await native_api.post("/api/v1/auth/register", headers=headers, json=payload)
    assert response.status_code == 202
    token = await mail_token(admin, auth_service, "verify")
    verified = await native_api.post("/api/v1/auth/verify-email", headers=headers, json={"token": token})
    assert verified.status_code == 200
    logged = await native_api.post("/api/v1/auth/login", headers=headers, json=payload)
    assert logged.status_code == 200 and logged.cookies["meu-braco-direito-refresh"]
    csrf = native_api.cookies["meu-braco-direito-csrf"]
    refreshed = await native_api.post("/api/v1/auth/refresh", headers={**headers, "X-CSRF-Token": csrf})
    assert refreshed.status_code == 200


@pytest.mark.parametrize(
    "origin",
    [
        None,
        "null",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://localhost:5173",
        "http://localhost.evil.example:5173",
        "http://127.0.0.1.evil.example:5173",
    ],
)
async def test_local_origin_alias_does_not_allow_other_origins(native_api, origin):
    native_api.headers.pop("Origin")
    headers = {} if origin is None else {"Origin": origin}
    response = await native_api.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"email": EMAIL, "display_name": "Ana Silva", "password": PASSWORD},
    )
    assert response.status_code == 403 and response.json() == {"error_code": "ORIGIN_REJECTED"}


async def test_atomic_refresh_conflict_then_reuse_revokes_family(registered, admin):
    initial = await registered.login(EMAIL, PASSWORD)

    async def renew():
        try:
            return await registered.refresh(initial["_refresh"], initial["_csrf"])
        except AuthError as error:
            return error

    results = await asyncio.gather(*(renew() for _ in range(5)))
    successes = [result for result in results if isinstance(result, dict)]
    errors = [result for result in results if isinstance(result, AuthError)]
    assert len(successes) == 1 and len(errors) == 4
    assert all(error.code == "REFRESH_CONFLICT" for error in errors)
    await registered.authenticate(successes[0]["access_token"])
    with pytest.raises(AuthError, match="CSRF_FAILED"):
        await registered.refresh(successes[0]["_refresh"], "wrong-csrf")
    async with admin.begin() as db:
        await db.execute(
            text("UPDATE auth_refresh_tokens SET used_at=now()-interval '11 seconds' WHERE digest=:digest"),
            {"digest": digest(initial["_refresh"])},
        )
    with pytest.raises(AuthError, match="INVALID_SESSION"):
        await renew_or_raise(registered, initial)
    with pytest.raises(jwt.InvalidTokenError):
        await registered.authenticate(successes[0]["access_token"])
    with pytest.raises(AuthError, match="INVALID_SESSION"):
        await registered.refresh(successes[0]["_refresh"], initial["_csrf"])


async def renew_or_raise(service, result):
    return await service.refresh(result["_refresh"], result["_csrf"])


async def test_expired_missing_disabled_sessions(registered, admin):
    with pytest.raises(AuthError):
        await registered.refresh("missing", "csrf")
    result = await registered.login(EMAIL, PASSWORD)
    async with admin.begin() as db:
        await db.execute(text("UPDATE auth_sessions SET expires_at=now()-interval '1 second'"))
    with pytest.raises(AuthError):
        await renew_or_raise(registered, result)
    result = await registered.login(EMAIL, PASSWORD)
    async with admin.begin() as db:
        await db.execute(text("UPDATE user_accounts SET active=false"))
    with pytest.raises(AuthError):
        await registered.login(EMAIL, PASSWORD)
    with pytest.raises(AuthError):
        await renew_or_raise(registered, result)
    with pytest.raises(jwt.InvalidTokenError):
        await registered.authenticate(result["access_token"])


async def test_reset_is_one_use_and_revokes_access(registered, admin, native_api):
    old = await registered.login(EMAIL, PASSWORD)
    assert (await native_api.post("/api/v1/auth/password-reset-request", json={"email": EMAIL})).status_code == 202
    token = await mail_token(admin, registered, "reset")
    with pytest.raises(AuthError):
        await registered.consume_action(token, "verify")
    response = await native_api.post("/api/v1/auth/reset-password", json={"token": token, "password": PASSWORD + "new"})
    assert response.status_code == 200
    with pytest.raises(jwt.InvalidTokenError):
        await registered.authenticate(old["access_token"])
    with pytest.raises(AuthError):
        await registered.login(EMAIL, PASSWORD)
    assert (await registered.login(EMAIL, PASSWORD + "new"))["access_token"]
    assert (
        await native_api.post("/api/v1/auth/reset-password", json={"token": token, "password": PASSWORD})
    ).status_code == 400


async def test_unknown_and_unverified_accounts_and_generic_actions(auth_service, admin, native_api):
    for email in [EMAIL, "missing@example.com"]:
        assert (await native_api.post("/api/v1/auth/verification-request", json={"email": email})).status_code == 202
    with pytest.raises(AuthError):
        await auth_service.login(EMAIL, PASSWORD)
    await auth_service.register(EMAIL, "Ana", PASSWORD)
    initial = await auth_service.login(EMAIL, PASSWORD)
    assert not (await auth_service.authenticate(initial["access_token"])).email_verified
    await auth_service.request_action(EMAIL, "verify")
    token = await mail_token(admin, auth_service, "verify")
    async with admin.begin() as db:
        await db.execute(text("UPDATE auth_actions SET expires_at=now()-interval '1 second'"))
    with pytest.raises(AuthError):
        await auth_service.consume_action(token, "verify")
    await auth_service.request_action(EMAIL, "verify")
    token = await mail_token(admin, auth_service, "verify")
    async with admin.begin() as db:
        await db.execute(text("UPDATE user_accounts SET active=false"))
    with pytest.raises(AuthError):
        await auth_service.consume_action(token, "verify")
    await auth_service.request_action(EMAIL, "reset")
    await auth_service.logout("missing", "csrf")


async def test_concurrent_action_only_consumed_once(registered, admin):
    await registered.request_action(EMAIL, "reset")
    token = await mail_token(admin, registered, "reset")

    async def consume():
        try:
            await registered.consume_action(token, "reset", PASSWORD + "new")
            return True
        except AuthError:
            return False

    results = await asyncio.gather(consume(), consume())
    assert sum(results) == 1


async def test_password_change_during_hash_check_cannot_login(registered, admin, monkeypatch):
    original = registered.passwords.verify

    async def verify(*args):
        result = await original(*args)
        async with admin.begin() as db:
            await db.execute(text("UPDATE auth_credentials SET version=version+1"))
        return result

    monkeypatch.setattr(registered.passwords, "verify", verify)
    with pytest.raises(AuthError):
        await registered.login(EMAIL, PASSWORD)


async def grant_staff(admin):
    async with admin.begin() as db:
        await db.execute(text("INSERT INTO platform_staff(actor_id) SELECT id FROM user_accounts"))


async def test_staff_totp_enrollment_recovery_and_revocation(registered, admin, native_api):
    before = await registered.login(EMAIL, PASSWORD)
    await grant_staff(admin)
    with pytest.raises(jwt.InvalidTokenError):
        await registered.authenticate(before["access_token"])
    with pytest.raises(AuthError):
        await renew_or_raise(registered, before)
    challenge = await registered.login(EMAIL, PASSWORD)
    assert challenge["mfa_required"] and challenge["setup_secret"]
    with pytest.raises(AuthError):
        await registered.verify_mfa(challenge["challenge"], "bad-code")
    code = pyotp.TOTP(challenge["setup_secret"]).now()
    proved = await registered.verify_mfa(challenge["challenge"], code)
    assert len(proved["recovery_codes"]) == 8
    await registered.authenticate(proved["access_token"])
    await renew_or_raise(registered, proved)
    with pytest.raises(AuthError):
        await registered.verify_mfa(challenge["challenge"], code)
    next_login = await registered.login(EMAIL, PASSWORD)
    assert next_login["setup_secret"] is None
    with pytest.raises(AuthError):
        await registered.verify_mfa(next_login["challenge"], code)
    next_code = pyotp.TOTP(challenge["setup_secret"]).at(now().timestamp() + 30)
    assert (await registered.verify_mfa(next_login["challenge"], next_code))["recovery_codes"] == []
    again = await registered.login(EMAIL, PASSWORD)
    recovery = proved["recovery_codes"][0]
    recovered = await native_api.post("/api/v1/auth/mfa/verify", json={"token": again["challenge"], "code": recovery})
    assert recovered.status_code == 200 and recovered.json()["recovery_codes"] == []
    again = await registered.login(EMAIL, PASSWORD)
    with pytest.raises(AuthError):
        await registered.verify_mfa(again["challenge"], recovery)
    # A password reset must never clear the second factor.
    await registered.request_action(EMAIL, "reset")
    await registered.consume_action(await mail_token(admin, registered, "reset"), "reset", PASSWORD + "new")
    assert (await registered.login(EMAIL, PASSWORD + "new"))["setup_secret"] is None
    async with admin.begin() as db:
        await db.execute(text("UPDATE platform_staff SET active=false"))
    result = await registered.login(EMAIL, PASSWORD + "new")
    assert result["access_token"]


async def test_invalid_expired_and_superseded_mfa_challenges(registered, admin):
    await grant_staff(admin)
    with pytest.raises(AuthError):
        await registered.verify_mfa("missing", "000000")
    first, second = await registered.login(EMAIL, PASSWORD), await registered.login(EMAIL, PASSWORD)
    await registered.verify_mfa(first["challenge"], pyotp.TOTP(first["setup_secret"]).now())
    with pytest.raises(AuthError):
        await registered.verify_mfa(second["challenge"], pyotp.TOTP(second["setup_secret"]).now())
    challenge = await registered.login(EMAIL, PASSWORD)
    async with admin.begin() as db:
        await db.execute(text("UPDATE auth_credentials SET version=version+1"))
    with pytest.raises(AuthError):
        await registered.verify_mfa(challenge["challenge"], "000000")
    challenge = await registered.login(EMAIL, PASSWORD)
    async with admin.begin() as db:
        await db.execute(text("UPDATE user_accounts SET active=false"))
    with pytest.raises(AuthError):
        await registered.verify_mfa(challenge["challenge"], "000000")


async def test_shared_rate_limits_are_committed(auth_service, auth_database):
    async def attempt():
        try:
            await auth_service.throttle("login", "127.0.0.1", "ana@example.com")
            return True
        except AuthError as error:
            assert error.status == 429
            return False

    results = await asyncio.gather(*(attempt() for _ in range(15)))
    assert sum(results) == 10
    async with auth_database.transaction(ZERO, ZERO) as db:
        assert await db.scalar(text("SELECT max(attempts) FROM auth_limits")) == 15


async def test_auth_role_cannot_access_tenant_data_or_grant_staff(registered, auth_database, database):
    for sql in [
        "SELECT * FROM businesses",
        "INSERT INTO platform_staff(actor_id) SELECT id FROM user_accounts",
        "UPDATE user_accounts SET active=true",
    ]:
        with pytest.raises(DBAPIError):
            async with auth_database.transaction(ZERO, ZERO) as db:
                await db.execute(text(sql))
    with pytest.raises(DBAPIError):
        async with database.transaction(ZERO, ZERO) as db:
            await db.execute(text("SELECT * FROM auth_credentials"))


async def test_mail_is_encrypted_retried_and_fenced(auth_service, auth_database, admin, settings, monkeypatch):
    await auth_service.register(EMAIL, "Ana", PASSWORD)
    sender = Mock(side_effect=RuntimeError("SMTP private data must never be logged"))
    monkeypatch.setattr("app.services.auth_mail.send_mail", sender)
    assert await deliver_once(auth_database, settings)
    async with admin.begin() as db:
        row = (await db.execute(text("SELECT state,attempts,ciphertext FROM auth_mail"))).one()
        assert row.state == "pending" and row.attempts == 1 and EMAIL not in row.ciphertext
        await db.execute(text("UPDATE auth_mail SET available_at=now()"))
    sender.side_effect = None
    assert await deliver_once(auth_database, settings)
    assert not await deliver_once(auth_database, settings)
    await auth_service.request_action(EMAIL, "verify")
    async with admin.begin() as db:
        await db.execute(text("UPDATE auth_mail SET attempts=7 WHERE state='pending'"))
    sender.side_effect = RuntimeError()
    assert await deliver_once(auth_database, settings)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM auth_mail WHERE state='failed'")) == 1
    await auth_service.request_action(EMAIL, "verify")

    async def expired_lease(*args):
        async with admin.begin() as db:
            await db.execute(text("UPDATE auth_mail SET lease_until=now()-interval '1 second' WHERE state='leased'"))

    monkeypatch.setattr("app.services.auth_mail.asyncio.to_thread", expired_lease)
    assert await deliver_once(auth_database, settings)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM auth_mail WHERE state='leased'")) == 1
    async with admin.begin() as db:
        await db.execute(text("UPDATE auth_mail SET attempts=8 WHERE state='leased'"))
    assert not await deliver_once(auth_database, settings)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM auth_mail WHERE state='failed'")) == 2


async def test_register_failure_rolls_back_identity_and_mail(auth_service, admin, monkeypatch):
    monkeypatch.setattr(auth_service, "action", AsyncMock(side_effect=RuntimeError("failure")))
    with pytest.raises(RuntimeError):
        await auth_service.register(EMAIL, "Ana", PASSWORD)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM user_accounts")) == 0


async def test_serial_replay_renewal_logout_and_verified_resend(registered, admin, native_api):
    await registered.register(EMAIL, "Attempted rename", "a different password value")
    await registered.request_action(EMAIL, "verify")
    initial = await registered.login(EMAIL, PASSWORD)
    renewed = await renew_or_raise(registered, initial)
    await registered.logout(renewed["_refresh"], renewed["_csrf"])
    with pytest.raises(jwt.InvalidTokenError):
        await registered.authenticate(renewed["access_token"])
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM user_accounts")) == 1
        assert await db.scalar(text("SELECT count(*) FROM auth_actions")) == 0
    await grant_staff(admin)
    result = await native_api.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert result.json()["mfa_required"] and "access_token" not in result.json()
    assert not result.headers.get_list("set-cookie")


async def test_rate_limit_applies_to_a_serial_call(auth_service):
    await auth_service.throttle("serial", "127.0.0.1", EMAIL)
