"""Owner-authorized phone verification with a durable provider challenge."""

import re
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from app.adapters.twilio_verify import PhoneProviderError, TwilioVerify
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError


def e164(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("55") and len(digits) in {12, 13}:
        return f"+{digits}"
    if not phone.strip().startswith("+") and len(digits) in {10, 11}:
        return f"+55{digits}"
    raise AuthError("PHONE_FORMAT_UNSUPPORTED", 422)


class PhoneVerificationService:
    def __init__(self, settings: Settings, database: Database, provider: TwilioVerify) -> None:
        self.settings, self.database, self.provider = settings, database, provider

    async def profile(self, db: Any, tenant: UUID, business: UUID, actor: UUID) -> dict[str, Any]:
        row = (
            (
                await db.execute(
                    text("""SELECT p.phone,p.phone_verified FROM business_profiles p
                      JOIN memberships m ON m.tenant_id=p.tenant_id AND m.actor_id=:actor
                      WHERE p.tenant_id=:tenant AND p.business_id=:business
                        AND m.active AND m.role='owner'"""),
                    {"tenant": tenant, "business": business, "actor": actor},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("BUSINESS_OWNER_REQUIRED", 403)
        return dict(row)

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, Any]:
        async with self.database.transaction(tenant, actor) as db:
            profile = await self.profile(db, tenant, business, actor)
            state = await db.scalar(
                text("""SELECT state FROM phone_verification_requests
                  WHERE tenant_id=:tenant AND business_id=:business AND phone=:phone"""),
                {"tenant": tenant, "business": business, "phone": profile["phone"]},
            )
            try:
                destination = e164(profile["phone"])
            except AuthError:
                destination = None
            return {
                "enabled": self.settings.phone_verify_mode == "twilio",
                "phone": profile["phone"],
                "destination": destination,
                "verified": profile["phone_verified"],
                "state": state,
            }

    async def update_phone(self, tenant: UUID, business: UUID, actor: UUID, phone: str) -> dict[str, Any]:
        destination = e164(phone)
        async with self.database.transaction(tenant, actor) as db:
            await self.profile(db, tenant, business, actor)
            await db.execute(
                text("""UPDATE business_profiles SET phone=:phone,phone_verified=false
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business, "phone": destination},
            )
            await db.execute(
                text("""UPDATE phone_verification_requests SET state='failed',provider_sid=NULL
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            await db.execute(
                text("""UPDATE whatsapp_link_challenges SET state='cancelled'
                  WHERE tenant_id=:tenant AND business_id=:business AND state='pending'"""),
                {"tenant": tenant, "business": business},
            )
            await db.execute(
                text("""WITH unlinked AS (
                    UPDATE whatsapp_channel_links SET active=false
                    WHERE tenant_id=:tenant AND business_id=:business AND active
                    RETURNING business_id
                  )
                  INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  SELECT :tenant,:actor,:operation,'whatsapp.unlinked',business_id FROM unlinked"""),
                {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()},
            )
        return {"phone": destination, "destination": destination, "verified": False}

    async def start(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, str]:
        if self.settings.phone_verify_mode != "twilio":
            raise AuthError("PHONE_VERIFY_UNAVAILABLE", 503)
        request_id = uuid4()
        async with self.database.transaction(tenant, actor) as db:
            profile = await self.profile(db, tenant, business, actor)
            if profile["phone_verified"]:
                return {"status": "verified"}
            phone, target = profile["phone"], e164(profile["phone"])
            reserved = await db.scalar(
                text("""INSERT INTO phone_verification_requests
                  (tenant_id,business_id,actor_id,phone,e164,request_id,state,requested_at,expires_at)
                  VALUES(:tenant,:business,:actor,:phone,:e164,:request,'starting',now(),now()+interval '10 minutes')
                  ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                    actor_id=EXCLUDED.actor_id,phone=EXCLUDED.phone,e164=EXCLUDED.e164,
                    request_id=EXCLUDED.request_id,provider_sid=NULL,state='starting',
                    requested_at=now(),expires_at=now()+interval '10 minutes',attempts=0,verified_at=NULL
                  WHERE phone_verification_requests.requested_at<now()-interval '60 seconds'
                    OR phone_verification_requests.phone<>EXCLUDED.phone
                  RETURNING request_id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "phone": phone,
                    "e164": target,
                    "request": request_id,
                },
            )
            if reserved is None:
                raise AuthError("PHONE_VERIFY_WAIT", 429)
        try:
            sid = await self.provider.start(target)
        except PhoneProviderError as exc:
            async with self.database.transaction(tenant, actor) as db:
                await db.execute(
                    text("""UPDATE phone_verification_requests SET state='failed'
                      WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request"""),
                    {"tenant": tenant, "business": business, "request": request_id},
                )
            raise AuthError("PHONE_VERIFY_UNAVAILABLE", 503) from exc
        async with self.database.transaction(tenant, actor) as db:
            updated = await db.scalar(
                text("""UPDATE phone_verification_requests SET state='pending',provider_sid=:sid
                  WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request
                  AND state='starting' RETURNING request_id"""),
                {"tenant": tenant, "business": business, "request": request_id, "sid": sid},
            )
            if updated is None:
                raise AuthError("PHONE_VERIFY_RETRY", 409)
        return {"status": "pending"}

    async def confirm(self, tenant: UUID, business: UUID, actor: UUID, code: str) -> dict[str, str]:
        if self.settings.phone_verify_mode != "twilio":
            raise AuthError("PHONE_VERIFY_UNAVAILABLE", 503)
        if not re.fullmatch(r"\d{4,10}", code):
            raise AuthError("INVALID_PHONE_CODE", 400)
        async with self.database.transaction(tenant, actor) as db:
            profile = await self.profile(db, tenant, business, actor)
            if profile["phone_verified"]:
                return {"status": "verified"}
            row = (
                (
                    await db.execute(
                        text("""UPDATE phone_verification_requests SET attempts=attempts+1
                          WHERE tenant_id=:tenant AND business_id=:business AND state='pending'
                            AND expires_at>now() AND attempts<5 AND phone=:phone
                          RETURNING request_id,provider_sid,phone"""),
                        {"tenant": tenant, "business": business, "phone": profile["phone"]},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["provider_sid"] is None:
                raise AuthError("PHONE_VERIFY_NOT_PENDING", 409)
            request_id, sid, phone = row["request_id"], row["provider_sid"], row["phone"]
        try:
            approved = await self.provider.check(sid, code)
        except PhoneProviderError as exc:
            raise AuthError("PHONE_VERIFY_UNAVAILABLE", 503) from exc
        if not approved:
            raise AuthError("INVALID_PHONE_CODE", 400)
        async with self.database.transaction(tenant, actor) as db:
            await self.profile(db, tenant, business, actor)
            changed = await db.scalar(
                text("""UPDATE business_profiles SET phone_verified=true
                  WHERE tenant_id=:tenant AND business_id=:business AND phone=:phone
                  RETURNING phone_verified"""),
                {"tenant": tenant, "business": business, "phone": phone},
            )
            if not changed:
                raise AuthError("PHONE_VERIFY_RETRY", 409)
            await db.execute(
                text("""UPDATE phone_verification_requests SET state='approved',verified_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request"""),
                {"tenant": tenant, "business": business, "request": request_id},
            )
        return {"status": "verified"}
