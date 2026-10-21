"""Native authentication. All durable state uses the restricted authentication database role."""

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pyotp
from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.identity import Identity
from app.core.passwords import Passwords
from app.db.session import Database

ZERO = UUID(int=0)


def now() -> datetime:
    return datetime.now(UTC)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AuthError(Exception):
    def __init__(self, code: str = "INVALID_CREDENTIALS", status: int = 401) -> None:
        self.code, self.status = code, status
        super().__init__(code)


async def audit(db: AsyncSession, event: str, user: UUID | None = None) -> None:
    await db.execute(
        text("INSERT INTO auth_audit(user_id,event) VALUES (:user,:event)"), {"user": user, "event": event}
    )


def totp_step(secret: str, code: str, last_step: int) -> int | None:
    step = int(now().timestamp()) // 30
    otp = pyotp.TOTP(secret)
    for candidate in range(step - 1, step + 2):
        if candidate > last_step and secrets.compare_digest(otp.at(candidate * 30), code):
            return candidate
    return None


class AuthService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database
        self.passwords = Passwords(settings.password_concurrency)
        self.cipher = Fernet(settings.auth_encryption_key.get_secret_value().encode())

    async def throttle(self, operation: str, ip: str, identifier: str = "") -> None:
        bucket = int(now().timestamp()) // 600
        counts = []
        async with self.database.transaction(ZERO, ZERO) as db:
            for scope, value, limit in (("ip", ip, 100), ("account", identifier.lower(), 10)):
                key = hmac.new(
                    self.settings.jwt_secret.get_secret_value().encode(),
                    f"{operation}:{scope}:{value}:{bucket}".encode(),
                    "sha256",
                ).hexdigest()
                count = await db.scalar(
                    text("""
INSERT INTO auth_limits(key,attempts,expires_at) VALUES (:key,1,:expiry)
ON CONFLICT(key) DO UPDATE SET attempts=auth_limits.attempts+1 RETURNING attempts
"""),
                    {"key": key, "expiry": now() + timedelta(minutes=20)},
                )
                counts.append(count > limit)
        if any(counts):
            raise AuthError("RATE_LIMITED", 429)

    async def action(self, db: AsyncSession, user: UUID, email: str, purpose: str) -> None:
        token = secrets.token_urlsafe(32)
        deadline = now() + (timedelta(hours=24) if purpose == "verify" else timedelta(minutes=30))
        await db.execute(
            text(
                """
INSERT INTO auth_actions(digest,user_id,purpose,expires_at) VALUES
(:digest,:user,:purpose,:expires)
"""
            ),
            {"digest": digest(token), "user": user, "purpose": purpose, "expires": deadline},
        )
        path, subject = (
            ("verify-email", "Confirme seu e-mail na Local Spark")
            if purpose == "verify"
            else ("reset-password", "Defina sua senha na Local Spark")
        )
        payload = {
            "to": email,
            "subject": subject,
            "template": purpose,
            "link": f"{self.settings.public_web_url}/{path}#token={token}",
            "body": (
                f"Abra o link para continuar: {self.settings.public_web_url}/{path}#token={token}\n"
                "Se você não fez este pedido, ignore esta mensagem."
            ),
        }
        ciphertext = self.cipher.encrypt(json.dumps(payload).encode()).decode()
        await db.execute(
            text("INSERT INTO auth_mail(action_digest,ciphertext) VALUES (:digest,:body)"),
            {"digest": digest(token), "body": ciphertext},
        )
        await audit(db, f"auth.{purpose}.requested", user)

    async def register(self, email: str, name: str, password: str) -> None:
        hashed = await self.passwords.hash(password)
        email = email.lower()
        async with self.database.transaction(ZERO, ZERO) as db:
            # Serializes absence checks without exposing password work under a DB lock.
            await db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:email,1))"), {"email": email})
            if await db.scalar(text("SELECT user_id FROM auth_credentials WHERE email=:email"), {"email": email}):
                return
            user = uuid4()
            await db.execute(
                text("""
INSERT INTO user_accounts(id,issuer,subject,display_name,email,email_verified)
VALUES (:id,'local-spark',:subject,:name,:email,false)
"""),
                {"id": user, "subject": str(user), "name": name, "email": email},
            )
            await db.execute(
                text("INSERT INTO auth_credentials(user_id,email,password_hash) VALUES (:id,:email,:hash)"),
                {"id": user, "email": email, "hash": hashed},
            )
            await self.action(db, user, email, "verify")
            await audit(db, "auth.registered", user)

    async def lookup(self, db: AsyncSession, email: str) -> dict[str, Any] | None:
        result = (
            (
                await db.execute(
                    text("""
SELECT c.*,u.active FROM auth_credentials c JOIN user_accounts u ON u.id=c.user_id
WHERE c.email=:email
"""),
                    {"email": email.lower()},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(result) if result else None

    async def request_action(self, email: str, purpose: str) -> None:
        async with self.database.transaction(ZERO, ZERO) as db:
            record = await self.lookup(db, email)
            if record and record["active"]:
                verified = await db.scalar(
                    text("SELECT email_verified FROM user_accounts WHERE id=:id"), {"id": record["user_id"]}
                )
                if purpose == "reset" or not verified:
                    await self.action(db, record["user_id"], record["email"], purpose)

    async def consume_action(self, token: str, purpose: str, password: str | None = None) -> None:
        hashed = await self.passwords.hash(password) if password is not None else None
        async with self.database.transaction(ZERO, ZERO) as db:
            # Account lock is shared with login/MFA/reset: state cannot be resurrected after reset.
            user = await db.scalar(
                text("""
SELECT user_id FROM auth_actions WHERE digest=:digest AND purpose=:purpose AND
expires_at>now()
"""),
                {"digest": digest(token), "purpose": purpose},
            )
            if user is None:
                raise AuthError("INVALID_ACTION", 400)
            active = await db.scalar(
                text("""
SELECT u.active FROM auth_credentials c JOIN user_accounts u ON u.id=c.user_id
WHERE c.user_id=:id FOR UPDATE OF c
"""),
                {"id": user},
            )
            deleted = await db.scalar(
                text("DELETE FROM auth_actions WHERE digest=:digest AND expires_at>now() RETURNING user_id"),
                {"digest": digest(token)},
            )
            if not active or deleted is None:
                raise AuthError("INVALID_ACTION", 400)
            await db.execute(text("UPDATE user_accounts SET email_verified=true WHERE id=:id"), {"id": user})
            if hashed is not None:
                await db.execute(
                    text("UPDATE auth_credentials SET password_hash=:hash,version=version+1 WHERE user_id=:id"),
                    {"id": user, "hash": hashed},
                )
                await db.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:id"), {"id": user})
                await db.execute(text("DELETE FROM auth_challenges WHERE user_id=:id"), {"id": user})
            await db.execute(
                text("DELETE FROM auth_actions WHERE user_id=:id AND purpose=:purpose"),
                {"id": user, "purpose": purpose},
            )
            await audit(db, f"auth.{purpose}.completed", user)

    def access(self, user: UUID, session: UUID) -> str:
        return jwt.encode(
            {
                "sub": str(user),
                "sid": str(session),
                "type": "access",
                "iss": self.settings.jwt_issuer,
                "aud": self.settings.jwt_audience,
                "iat": now(),
                "exp": now() + timedelta(minutes=5),
            },
            self.settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )

    async def new_session(self, db: AsyncSession, user: UUID, mfa: bool = False) -> dict[str, Any]:
        session, refresh, csrf = uuid4(), secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        await db.execute(
            text(
                """
INSERT INTO auth_sessions(id,user_id,csrf_hash,expires_at,mfa_verified) VALUES
(:id,:user,:csrf,:expires,:mfa)
"""
            ),
            {"id": session, "user": user, "csrf": digest(csrf), "expires": now() + timedelta(days=30), "mfa": mfa},
        )
        await db.execute(
            text("INSERT INTO auth_refresh_tokens(digest,session_id) VALUES (:hash,:id)"),
            {"hash": digest(refresh), "id": session},
        )
        await audit(db, "auth.login.succeeded", user)
        return {
            "access_token": self.access(user, session),
            "token_type": "bearer",
            "expires_in": 300,
            "_refresh": refresh,
            "_csrf": csrf,
        }

    async def login(self, email: str, password: str) -> dict[str, Any]:
        async with self.database.transaction(ZERO, ZERO) as db:
            record = await self.lookup(db, email)
        valid = await self.passwords.verify(password, record["password_hash"] if record else None)
        if not valid or record is None or not record["active"]:
            async with self.database.transaction(ZERO, ZERO) as db:
                await audit(db, "auth.login.failed")
            raise AuthError()
        async with self.database.transaction(ZERO, record["user_id"]) as db:
            current = (
                (
                    await db.execute(
                        text("SELECT * FROM auth_credentials WHERE user_id=:id FOR UPDATE"), {"id": record["user_id"]}
                    )
                )
                .mappings()
                .one()
            )
            active = await db.scalar(text("SELECT active FROM user_accounts WHERE id=:id"), {"id": record["user_id"]})
            if current["version"] != record["version"] or not active:
                raise AuthError()
            staff = await db.scalar(text("SELECT public.is_platform_staff()"))
            if staff:
                raw = secrets.token_urlsafe(32)
                setup = pyotp.random_base32() if current["mfa_secret"] is None else None
                await db.execute(
                    text(
                        """
INSERT INTO auth_challenges(digest,user_id,version,setup_secret,expires_at) VALUES
(:digest,:user,:version,:secret,:expires)
"""
                    ),
                    {
                        "digest": digest(raw),
                        "user": record["user_id"],
                        "version": current["version"],
                        "secret": self.cipher.encrypt(setup.encode()).decode() if setup else None,
                        "expires": now() + timedelta(minutes=5),
                    },
                )
                return {
                    "mfa_required": True,
                    "challenge": raw,
                    "setup_secret": setup,
                    "provisioning_uri": pyotp.TOTP(setup).provisioning_uri(email, issuer_name="Local Spark")
                    if setup
                    else None,
                }
            return await self.new_session(db, record["user_id"])

    async def verify_mfa(self, token: str, code: str) -> dict[str, Any]:
        async with self.database.transaction(ZERO, ZERO) as db:
            challenge = (
                (
                    await db.execute(
                        text("SELECT * FROM auth_challenges WHERE digest=:digest AND expires_at>now()"),
                        {"digest": digest(token)},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if challenge is None:
                raise AuthError("INVALID_MFA")
            record = (
                (
                    await db.execute(
                        text(
                            """
SELECT c.*,u.active FROM auth_credentials c JOIN user_accounts u ON u.id=c.user_id
WHERE c.user_id=:id
FOR UPDATE OF c
"""
                        ),
                        {"id": challenge["user_id"]},
                    )
                )
                .mappings()
                .one()
            )
            if (
                not record["active"]
                or record["version"] != challenge["version"]
                or (challenge["setup_secret"] and record["mfa_secret"])
            ):
                raise AuthError("INVALID_MFA")
            encoded = record["mfa_secret"] or challenge["setup_secret"]
            secret = self.cipher.decrypt(encoded.encode()).decode()
            step = totp_step(secret, code, record["mfa_step"])
            recovery = digest(code) in record["recovery_hashes"]
            if step is None and not recovery:
                raise AuthError("INVALID_MFA")
            consumed = await db.scalar(
                text("DELETE FROM auth_challenges WHERE digest=:digest RETURNING user_id"), {"digest": digest(token)}
            )
            if consumed is None:
                raise AuthError("INVALID_MFA")
            codes = [secrets.token_hex(16) for _ in range(8)] if challenge["setup_secret"] else []
            hashes = (
                [digest(value) for value in codes]
                if codes
                else [value for value in record["recovery_hashes"] if value != digest(code)]
            )
            await db.execute(
                text(
                    """
UPDATE auth_credentials SET
mfa_secret=:secret,mfa_step=:step,recovery_hashes=CAST(:hashes AS jsonb) WHERE
user_id=:id
"""
                ),
                {
                    "secret": encoded,
                    "step": step if step is not None else record["mfa_step"],
                    "hashes": json.dumps(hashes),
                    "id": record["user_id"],
                },
            )
            await audit(db, "auth.mfa.verified", record["user_id"])
            result = await self.new_session(db, record["user_id"], True)
            result["recovery_codes"] = codes
            return result

    async def refresh(self, raw: str, csrf: str) -> dict[str, Any]:
        error = None
        result: dict[str, Any] = {}
        async with self.database.transaction(ZERO, ZERO) as db:
            token = (
                (
                    await db.execute(
                        text("SELECT * FROM auth_refresh_tokens WHERE digest=:hash FOR UPDATE"), {"hash": digest(raw)}
                    )
                )
                .mappings()
                .one_or_none()
            )
            if token is None:
                raise AuthError("INVALID_SESSION")
            record = (
                (
                    await db.execute(
                        text("SELECT * FROM auth_sessions WHERE id=:id FOR UPDATE"), {"id": token["session_id"]}
                    )
                )
                .mappings()
                .one()
            )
            if not secrets.compare_digest(record["csrf_hash"], digest(csrf)):
                raise AuthError("CSRF_FAILED", 403)
            active = await db.scalar(text("SELECT active FROM user_accounts WHERE id=:id"), {"id": record["user_id"]})
            if record["revoked"] or record["expires_at"] <= now() or not active:
                raise AuthError("INVALID_SESSION")
            await db.execute(text("SELECT set_config('app.actor_id',:actor,true)"), {"actor": str(record["user_id"])})
            staff = await db.scalar(text("SELECT public.is_platform_staff()"))
            if staff and not record["mfa_verified"]:
                raise AuthError("INVALID_SESSION")
            if token["used_at"] is not None:
                if (now() - token["used_at"]).total_seconds() <= 10:
                    error = AuthError("REFRESH_CONFLICT", 409)
                else:
                    await db.execute(text("UPDATE auth_sessions SET revoked=true WHERE id=:id"), {"id": record["id"]})
                    await audit(db, "auth.refresh.reuse", record["user_id"])
                    error = AuthError("INVALID_SESSION")
            else:
                replacement = secrets.token_urlsafe(32)
                await db.execute(
                    text("UPDATE auth_refresh_tokens SET used_at=now() WHERE digest=:hash"), {"hash": digest(raw)}
                )
                await db.execute(
                    text("INSERT INTO auth_refresh_tokens(digest,session_id) VALUES (:hash,:id)"),
                    {"hash": digest(replacement), "id": record["id"]},
                )
                result = {
                    "access_token": self.access(record["user_id"], record["id"]),
                    "token_type": "bearer",
                    "expires_in": 300,
                    "_refresh": replacement,
                    "_csrf": csrf,
                }
        if error:
            raise error
        return result

    async def logout(self, raw: str, csrf: str) -> None:
        async with self.database.transaction(ZERO, ZERO) as db:
            result = await db.scalar(
                text("""
UPDATE auth_sessions SET revoked=true WHERE id=(SELECT session_id FROM
auth_refresh_tokens WHERE digest=:hash)
AND csrf_hash=:csrf RETURNING user_id
"""),
                {"hash": digest(raw), "csrf": digest(csrf)},
            )
            if result:
                await audit(db, "auth.logout", result)

    async def authenticate(self, token: str) -> Identity:
        try:
            claims = jwt.decode(
                token,
                self.settings.jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                issuer=self.settings.jwt_issuer,
                audience=self.settings.jwt_audience,
                options={"require": ["sub", "sid", "type", "iss", "aud", "exp", "iat"]},
            )
            user, session = UUID(claims["sub"]), UUID(claims["sid"])
            if claims["type"] != "access":
                raise jwt.InvalidTokenError()
        except (ValueError, TypeError, AttributeError) as exc:
            raise jwt.InvalidTokenError() from exc
        async with self.database.transaction(ZERO, user) as db:
            record = (
                (
                    await db.execute(
                        text("""
SELECT u.* FROM user_accounts u JOIN auth_sessions s ON s.user_id=u.id
WHERE u.id=:user AND u.active AND s.id=:session AND NOT s.revoked AND
s.expires_at>now()
AND (NOT public.is_platform_staff() OR s.mfa_verified)
"""),
                        {"user": user, "session": session},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if record is None:
                raise jwt.InvalidTokenError()
            return Identity(
                user,
                record["issuer"],
                record["subject"],
                record["display_name"],
                record["email"],
                record["email_verified"],
            )
