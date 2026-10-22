"""Owner-authorized channel proof; a typed phone or SMS alone never links WhatsApp."""

import hashlib
import hmac
import json
import secrets
from typing import Any
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.billing import status as billing_status
from app.services.phone_verification import e164
from app.services.whatsapp_ingest import sender_hash


class WhatsAppLinkService:
    def __init__(self, settings: Settings, database: Database, meta_database: Database | None) -> None:
        self.settings, self.database, self.meta_database = settings, database, meta_database

    async def _owner_phone(self, session: Any, tenant: UUID, business: UUID, actor: UUID) -> str:
        row = (
            (
                await session.execute(
                    text("""SELECT p.phone,p.phone_verified FROM business_profiles p
                      JOIN memberships m ON m.tenant_id=p.tenant_id AND m.actor_id=:actor
                      WHERE p.tenant_id=:tenant AND p.business_id=:business
                        AND m.active AND m.role='owner' FOR UPDATE OF p"""),
                    {"tenant": tenant, "business": business, "actor": actor},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("BUSINESS_OWNER_REQUIRED", 403)
        if not row["phone_verified"]:
            raise AuthError("PHONE_VERIFICATION_REQUIRED", 409)
        if not (await billing_status(session, self.settings, tenant, actor))["access_active"]:
            raise AuthError("PLAN_REQUIRED", 403)
        return e164(row["phone"])

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, Any]:
        async with self.database.transaction(tenant, actor) as session:
            # Status is visible to the owner before phone and plan are ready.
            owner = await session.scalar(
                text("""SELECT 1 FROM business_profiles p JOIN memberships m
                  ON m.tenant_id=p.tenant_id AND m.actor_id=:actor
                  WHERE p.tenant_id=:tenant AND p.business_id=:business AND m.active AND m.role='owner'"""),
                {"tenant": tenant, "business": business, "actor": actor},
            )
            if owner is None:
                raise AuthError("BUSINESS_OWNER_REQUIRED", 403)
            linked = await session.scalar(
                text("""SELECT active FROM whatsapp_channel_links
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            pending = await session.scalar(
                text("""SELECT EXISTS(SELECT 1 FROM whatsapp_link_challenges
                  WHERE tenant_id=:tenant AND business_id=:business AND state='pending' AND expires_at>now())"""),
                {"tenant": tenant, "business": business},
            )
        return {"enabled": self.settings.meta_webhook_mode == "cloud", "linked": bool(linked), "pending": pending}

    async def start(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, str]:
        if self.settings.meta_webhook_mode != "cloud" or self.meta_database is None:
            raise AuthError("WHATSAPP_UNAVAILABLE", 503)
        token = secrets.token_urlsafe(24)
        digest = hashlib.sha256(token.encode()).hexdigest()
        request = uuid4()
        async with self.database.transaction(tenant, actor) as session:
            phone = await self._owner_phone(session, tenant, business, actor)
            linked = await session.scalar(
                text("""SELECT active FROM whatsapp_channel_links
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            if linked:
                return {"status": "linked"}
            reserved = await session.scalar(
                text("""INSERT INTO whatsapp_link_challenges
                  (tenant_id,business_id,actor_id,request_id,token_hash,sender_hash,state,expires_at)
                  VALUES(:tenant,:business,:actor,:request,:digest,:sender,'pending',now()+interval '15 minutes')
                  ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                    actor_id=EXCLUDED.actor_id,request_id=EXCLUDED.request_id,
                    token_hash=EXCLUDED.token_hash,sender_hash=EXCLUDED.sender_hash,
                    state='pending',created_at=now(),expires_at=EXCLUDED.expires_at,linked_at=NULL
                  WHERE whatsapp_link_challenges.state<>'pending'
                    OR whatsapp_link_challenges.created_at<now()-interval '60 seconds'
                  RETURNING request_id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "request": request,
                    "digest": digest,
                    "sender": sender_hash(self.settings, phone),
                },
            )
            if reserved is not None:
                return {"status": "pending", "message": f"VINCULAR {token}"}
            raise AuthError("WHATSAPP_LINK_WAIT", 429)

    async def _find_proof(self, sender: str, created_at: Any, token_hash: str) -> UUID | None:
        assert self.meta_database is not None
        async with self.meta_database.sessions() as session:
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,ciphertext FROM whatsapp_inbox
                          WHERE sender_hash=:sender AND event_kind='message'
                            AND received_at>=:created AND expires_at>now()
                          ORDER BY received_at DESC,id DESC LIMIT 100"""),
                        {"sender": sender, "created": created_at},
                    )
                )
                .mappings()
                .all()
            )
        cipher = Fernet(self.settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
        for row in rows:
            try:
                message = json.loads(cipher.decrypt(row["ciphertext"].encode()))
            except (InvalidToken, ValueError, UnicodeDecodeError):
                continue
            if message.get("type") != "text" or not isinstance(message.get("text"), dict):
                continue
            body = message["text"].get("body")
            if not isinstance(body, str) or not body.startswith("VINCULAR "):
                continue
            candidate = body.removeprefix("VINCULAR ").strip()
            if hmac.compare_digest(hashlib.sha256(candidate.encode()).hexdigest(), token_hash):
                return UUID(str(row["id"]))
        return None

    async def confirm(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, str]:
        if self.settings.meta_webhook_mode != "cloud" or self.meta_database is None:
            raise AuthError("WHATSAPP_UNAVAILABLE", 503)
        async with self.database.transaction(tenant, actor) as session:
            phone = await self._owner_phone(session, tenant, business, actor)
            challenge = (
                (
                    await session.execute(
                        text("""SELECT request_id,token_hash,sender_hash,created_at FROM whatsapp_link_challenges
                          WHERE tenant_id=:tenant AND business_id=:business
                            AND state='pending' AND expires_at>now()"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if challenge is None:
                linked = await session.scalar(
                    text("""SELECT active FROM whatsapp_channel_links
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
                if linked:
                    return {"status": "linked"}
                raise AuthError("WHATSAPP_LINK_NOT_PENDING", 409)
            expected = sender_hash(self.settings, phone)
            if not hmac.compare_digest(challenge["sender_hash"], expected or ""):
                raise AuthError("WHATSAPP_LINK_RETRY", 409)
        proof = await self._find_proof(challenge["sender_hash"], challenge["created_at"], challenge["token_hash"])
        if proof is None:
            raise AuthError("WHATSAPP_PROOF_NOT_RECEIVED", 409)
        try:
            async with self.database.transaction(tenant, actor) as session:
                phone = await self._owner_phone(session, tenant, business, actor)
                if not hmac.compare_digest(challenge["sender_hash"], sender_hash(self.settings, phone) or ""):
                    raise AuthError("WHATSAPP_LINK_RETRY", 409)
                changed = await session.scalar(
                    text("""UPDATE whatsapp_link_challenges SET state='linked',linked_at=now()
                      WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request
                        AND token_hash=:digest AND state='pending' AND expires_at>now()
                      RETURNING request_id"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "request": challenge["request_id"],
                        "digest": challenge["token_hash"],
                    },
                )
                if changed is None:
                    raise AuthError("WHATSAPP_LINK_RETRY", 409)
                await session.execute(
                    text("""INSERT INTO whatsapp_channel_links
                      (tenant_id,business_id,actor_id,sender_hash,proof_event_id)
                      VALUES(:tenant,:business,:actor,:sender,:proof)
                      ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                        actor_id=EXCLUDED.actor_id,sender_hash=EXCLUDED.sender_hash,
                        proof_event_id=EXCLUDED.proof_event_id,active=true,linked_at=now()"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "actor": actor,
                        "sender": challenge["sender_hash"],
                        "proof": proof,
                    },
                )
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:request,'whatsapp.linked',:business)
                      ON CONFLICT(tenant_id,operation_id,action) DO NOTHING"""),
                    {"tenant": tenant, "actor": actor, "request": challenge["request_id"], "business": business},
                )
        except IntegrityError as exc:
            raise AuthError("WHATSAPP_SENDER_IN_USE", 409) from exc
        return {"status": "linked"}
