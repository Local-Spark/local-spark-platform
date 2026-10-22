"""MFA-gated operator invitations and immediate, audited revocation."""

import json
import secrets
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import Settings
from app.core.identity import Identity
from app.db.session import Database
from app.services.auth import ZERO, AuthError, audit, digest, now


class StaffService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database
        self.cipher = Fernet(settings.auth_encryption_key.get_secret_value().encode())

    async def require_operator(self, db: Any, actor: UUID) -> None:
        if not await db.scalar(text("SELECT public.is_platform_staff()")):
            raise AuthError("STAFF_REQUIRED", 403)
        # get_actor already checked that this access token belongs to an MFA session.
        if not await db.scalar(
            text("""SELECT 1 FROM auth_sessions WHERE user_id=:actor AND mfa_verified
              AND NOT revoked AND expires_at>now() LIMIT 1"""),
            {"actor": actor},
        ):
            raise AuthError("MFA_REQUIRED", 403)

    async def invite(self, actor: UUID, email: str, key: str) -> dict[str, Any]:
        invitation_id = uuid4()
        token = secrets.token_urlsafe(32)
        email = email.lower()
        async with self.database.transaction(ZERO, actor) as db:
            await self.require_operator(db, actor)
            await db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:email,7))"), {"email": email})
            previous = (
                (
                    await db.execute(
                        text(
                            "SELECT id,email,expires_at FROM staff_invitations "
                            "WHERE invited_by=:actor AND idempotency_key=:key"
                        ),
                        {"actor": actor, "key": key},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if previous:
                if previous["email"] != email:
                    raise AuthError("IDEMPOTENCY_CONFLICT", 409)
                return {**dict(previous), "replayed": True}
            if await db.scalar(
                text("""SELECT 1 FROM auth_credentials c JOIN platform_staff s ON s.actor_id=c.user_id
                  JOIN user_accounts u ON u.id=c.user_id
                  WHERE c.email=:email AND s.active AND u.active"""),
                {"email": email},
            ):
                raise AuthError("ALREADY_STAFF", 409)
            if await db.scalar(
                text("""SELECT 1 FROM staff_invitations WHERE email=:email AND accepted_at IS NULL
                  AND revoked_at IS NULL AND expires_at>now()"""),
                {"email": email},
            ):
                raise AuthError("INVITATION_PENDING", 409)
            expires_at = now() + timedelta(hours=48)
            await db.execute(
                text("""INSERT INTO staff_invitations
                  (id,invited_by,email,token_digest,idempotency_key,expires_at)
                  VALUES(:id,:actor,:email,:digest,:key,:expires)"""),
                {
                    "id": invitation_id,
                    "actor": actor,
                    "email": email,
                    "digest": digest(token),
                    "key": key,
                    "expires": expires_at,
                },
            )
            payload = {
                "to": email,
                "subject": "Convite para operar o Meu Braço Direito",
                "template": "staff_invite",
                "link": f"{self.settings.public_web_url}/staff-invite#token={token}",
                "body": (
                    f"Você recebeu um convite para a equipe Meu Braço Direito. Abra "
                    f"{self.settings.public_web_url}/staff-invite#token={token}\n"
                    "Entre com este e-mail e confirme sua conta antes de aceitar. "
                    "O link vale por 48 horas. Se não esperava o convite, ignore-o."
                ),
            }
            await db.execute(
                text("INSERT INTO auth_mail(staff_invitation_id,ciphertext) VALUES(:id,:body)"),
                {"id": invitation_id, "body": self.cipher.encrypt(json.dumps(payload).encode()).decode()},
            )
            await db.execute(
                text("INSERT INTO platform_audit(actor_id,action) VALUES(:actor,'admin.staff.invite')"),
                {"actor": actor},
            )
            await audit(db, "auth.staff.invited", actor)
            return {"id": invitation_id, "email": email, "expires_at": expires_at, "replayed": False}

    async def accept(self, identity: Identity, token: str) -> None:
        if not identity.email_verified or not identity.email:
            raise AuthError("VERIFIED_EMAIL_REQUIRED", 403)
        async with self.database.transaction(ZERO, identity.actor_id) as db:
            # The RLS policy permits reading only the exact invitation whose token
            # was presented for this transaction, so a wrong account can receive
            # a useful error without gaining invitation-list access.
            token_digest = digest(token)
            await db.execute(
                text("SELECT set_config('app.invitation_digest',:digest,true)"),
                {"digest": token_digest},
            )
            preview = (
                (
                    await db.execute(
                        text("""SELECT id,email FROM staff_invitations WHERE token_digest=:digest
                          AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>now()"""),
                        {"digest": token_digest},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if preview is None:
                raise AuthError("INVALID_INVITATION", 400)
            if preview["email"] != identity.email.lower():
                raise AuthError("INVITATION_EMAIL_MISMATCH", 403)
            row = (
                (
                    await db.execute(
                        text("""SELECT id,email FROM staff_invitations WHERE id=:id
                          AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>now()
                          FOR UPDATE"""),
                        {"id": preview["id"]},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("INVALID_INVITATION", 400)
            if await db.scalar(
                text("SELECT 1 FROM platform_staff WHERE actor_id=:actor AND active"),
                {"actor": identity.actor_id},
            ):
                raise AuthError("ALREADY_STAFF", 409)
            await db.execute(
                text("""INSERT INTO platform_staff(actor_id,active) VALUES(:actor,true)
                  ON CONFLICT(actor_id) DO UPDATE SET active=true"""),
                {"actor": identity.actor_id},
            )
            await db.execute(text("UPDATE staff_invitations SET accepted_at=now() WHERE id=:id"), {"id": row["id"]})
            await db.execute(
                text("UPDATE auth_sessions SET revoked=true WHERE user_id=:actor"), {"actor": identity.actor_id}
            )
            await db.execute(text("DELETE FROM auth_challenges WHERE user_id=:actor"), {"actor": identity.actor_id})
            await audit(db, "auth.staff.invitation.accepted", identity.actor_id)
            await db.execute(
                text("INSERT INTO platform_audit(actor_id,action) VALUES(:actor,'admin.staff.invite.accepted')"),
                {"actor": identity.actor_id},
            )

    async def access_state(self, identity: Identity) -> dict[str, bool]:
        async with self.database.transaction(ZERO, identity.actor_id) as db:
            pending = bool(
                await db.scalar(
                    text("""SELECT 1 FROM staff_invitations WHERE email=:email
                  AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>now() LIMIT 1"""),
                    {"email": identity.email.lower() if identity.email else ""},
                )
            )
            revoked = await db.scalar(
                text("SELECT active=false FROM platform_staff WHERE actor_id=:actor"),
                {"actor": identity.actor_id},
            )
            return {"pending": pending, "revoked": bool(revoked)}

    async def overview(self, actor: UUID) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as db:
            await self.require_operator(db, actor)
            operators = (
                (
                    await db.execute(
                        text("""SELECT s.actor_id,u.display_name,u.email,s.active
                          FROM platform_staff s JOIN user_accounts u ON u.id=s.actor_id
                          ORDER BY u.display_name,s.actor_id LIMIT 100""")
                    )
                )
                .mappings()
                .all()
            )
            invitations = (
                (
                    await db.execute(
                        text("""SELECT id,email,created_at,expires_at,accepted_at,revoked_at,
                          CASE WHEN accepted_at IS NOT NULL THEN 'accepted'
                            WHEN revoked_at IS NOT NULL THEN 'revoked'
                            WHEN expires_at<=now() THEN 'expired' ELSE 'pending' END AS status
                          FROM staff_invitations ORDER BY created_at DESC,id DESC LIMIT 50""")
                    )
                )
                .mappings()
                .all()
            )
            await db.execute(
                text("INSERT INTO platform_audit(actor_id,action) VALUES(:actor,'admin.staff.read')"),
                {"actor": actor},
            )
            return {"operators": [dict(row) for row in operators], "invitations": [dict(row) for row in invitations]}

    async def revoke_invitation(self, actor: UUID, invitation_id: UUID) -> None:
        async with self.database.transaction(ZERO, actor) as db:
            await self.require_operator(db, actor)
            row = (
                (
                    await db.execute(
                        text("SELECT accepted_at,revoked_at FROM staff_invitations WHERE id=:id FOR UPDATE"),
                        {"id": invitation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("INVITATION_NOT_FOUND", 404)
            if row["accepted_at"] is not None:
                raise AuthError("INVITATION_ALREADY_ACCEPTED", 409)
            if row["revoked_at"] is None:
                await db.execute(
                    text("UPDATE staff_invitations SET revoked_at=now() WHERE id=:id"), {"id": invitation_id}
                )
                await db.execute(
                    text("DELETE FROM auth_mail WHERE staff_invitation_id=:id AND state<>'sent'"),
                    {"id": invitation_id},
                )
                await db.execute(
                    text("INSERT INTO platform_audit(actor_id,action) VALUES(:actor,'admin.staff.invite.revoked')"),
                    {"actor": actor},
                )
                await audit(db, "auth.staff.invitation.revoked", actor)

    async def revoke_operator(self, actor: UUID, target: UUID) -> None:
        if actor == target:
            raise AuthError("CANNOT_REVOKE_SELF", 409)
        async with self.database.transaction(ZERO, actor) as db:
            await self.require_operator(db, actor)
            await db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('staff-revoke',7))"))
            active = await db.scalar(
                text("SELECT active FROM platform_staff WHERE actor_id=:target FOR UPDATE"),
                {"target": target},
            )
            if active is None:
                raise AuthError("OPERATOR_NOT_FOUND", 404)
            if not active:
                return
            if await db.scalar(text("SELECT count(*) FROM platform_staff WHERE active")) <= 1:
                raise AuthError("LAST_OPERATOR", 409)
            await db.execute(text("UPDATE platform_staff SET active=false WHERE actor_id=:target"), {"target": target})
            await db.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:target"), {"target": target})
            await db.execute(text("DELETE FROM auth_challenges WHERE user_id=:target"), {"target": target})
            await db.execute(
                text("INSERT INTO platform_audit(actor_id,action) VALUES(:actor,'admin.staff.revoked')"),
                {"actor": actor},
            )
            await audit(db, "auth.staff.revoked", target)
