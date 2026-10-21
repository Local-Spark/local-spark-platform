"""Commercial access is explicit, tenant-scoped and independent from registration."""

from typing import Any, Literal
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.identity import Identity
from app.services.administration import require_staff
from app.services.business import AccessDenied, IdempotencyConflict, require_member


class BillingError(Exception):
    def __init__(self, code: str, status: int = 409) -> None:
        self.code, self.status = code, status
        super().__init__(code)


async def context(session: AsyncSession, tenant: UUID) -> None:
    await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(tenant)})


async def commercial_event(
    session: AsyncSession, tenant: UUID, operation: UUID, action: str, actor: UUID | None
) -> None:
    params = {
        "id": uuid5(operation, action),
        "tenant": tenant,
        "operation": operation,
        "action": action,
        "actor": actor,
    }
    await session.execute(
        text("""INSERT INTO billing_audit(id,tenant_id,operation_id,action,actor_id)
      VALUES(:id,:tenant,:operation,:action,:actor) ON CONFLICT(operation_id,action) DO NOTHING"""),
        params,
    )
    await session.execute(
        text("""INSERT INTO billing_outbox(id,tenant_id,operation_id,event_type)
      VALUES(:id,:tenant,:operation,:action) ON CONFLICT(operation_id,event_type) DO NOTHING"""),
        params,
    )


async def lock_commercial_change(session: AsyncSession, tenant: UUID) -> None:
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 1))"), {"tenant": str(tenant)})


async def status(
    session: AsyncSession, settings: Settings, tenant: UUID, actor: UUID, *, administrative: bool = False
) -> dict[str, Any]:
    await context(session, tenant)
    if administrative:
        await require_staff(session, actor, "admin.billing.read")
    else:
        await require_member(session, tenant, actor)
    role = await session.scalar(
        text("SELECT role FROM memberships WHERE tenant_id=:tenant AND actor_id=:actor AND active"),
        {"tenant": tenant, "actor": actor},
    )
    account = (
        (
            await session.execute(
                text("""SELECT a.status,a.paid_until,a.blocked,a.livemode,a.subscription_id,
      c.amount_minor AS checkout_amount,
      (a.status='active' AND NOT a.blocked AND a.paid_until>now()) AS active
      FROM billing_accounts a LEFT JOIN billing_checkouts c ON c.id=a.checkout_id AND c.status<>'expired'
      WHERE a.tenant_id=:tenant AND a.livemode=:live"""),
                {"tenant": tenant, "live": settings.environment == "production"},
            )
        )
        .mappings()
        .one_or_none()
    )
    grant = (
        (
            await session.execute(
                text("""SELECT id,starts_at,ends_at,revoked_at,
      (revoked_at IS NULL AND starts_at<=now()
        AND ends_at>now()) AS active
      FROM billing_sponsorships WHERE tenant_id=:tenant"""),
                {"tenant": tenant},
            )
        )
        .mappings()
        .one_or_none()
    )
    job = None
    quoted_amount = settings.billing_monthly_amount_minor
    if role == "owner" or administrative:
        record = (
            (
                await session.execute(
                    text("""SELECT id,state,result,amount_minor FROM billing_jobs
          WHERE tenant_id=:tenant AND kind='checkout' AND livemode=:live ORDER BY created_at DESC,id DESC LIMIT 1"""),
                    {"tenant": tenant, "live": settings.environment == "production"},
                )
            )
            .mappings()
            .one_or_none()
        )
        if record is not None:
            job = {name: record[name] for name in ("id", "state", "result")}
            quoted_amount = record["amount_minor"]
    if account is not None and account["checkout_amount"] is not None:
        quoted_amount = account["checkout_amount"]
    source = "none"
    if account is not None and account["active"]:
        source = "paid" if account["livemode"] else "test"
    if grant is not None and grant["active"]:
        source = "sponsored"
    existing_subscription = bool(
        account and account["subscription_id"] and account["status"] not in {"canceled", "incomplete_expired"}
    )
    return {
        "tenant_id": tenant,
        "mode": settings.billing_mode,
        "can_manage": role == "owner",
        "checkout_enabled": settings.billing_mode != "disabled"
        and role == "owner"
        and source == "none"
        and not existing_subscription,
        "access_source": source,
        "access_active": source != "none",
        "subscription": {name: account[name] for name in ("status", "paid_until", "blocked", "livemode", "active")}
        if account
        else None,
        "sponsorship": dict(grant) if grant else None,
        "checkout": job,
        "price": {"amount_minor": quoted_amount, "currency": "BRL", "interval": "month"}
        if settings.billing_mode != "disabled" and source == "none" and not existing_subscription
        else None,
    }


async def request_checkout(
    session: AsyncSession, settings: Settings, tenant: UUID, identity: Identity, key: str, origin: str | None = None
) -> dict[str, Any]:
    await context(session, tenant)
    await require_member(session, tenant, identity.actor_id)
    role = await session.scalar(
        text("SELECT role FROM memberships WHERE tenant_id=:tenant AND actor_id=:actor AND active"),
        {"tenant": tenant, "actor": identity.actor_id},
    )
    if role != "owner" or not identity.email_verified:
        raise AccessDenied
    if settings.billing_mode == "disabled":
        raise BillingError("BILLING_UNAVAILABLE", 503)
    return_origin = settings.public_web_url if origin is None else origin
    if return_origin not in settings.auth_origins:
        raise BillingError("ORIGIN_REJECTED", 403)
    await lock_commercial_change(session, tenant)
    previous = (
        (
            await session.execute(
                text("""SELECT id,state,result FROM billing_jobs WHERE livemode=:live AND dedupe_key=:key"""),
                {"live": settings.billing_mode == "live", "key": f"checkout:{tenant}:{identity.actor_id}:{key}"},
            )
        )
        .mappings()
        .one_or_none()
    )
    if previous:
        return dict(previous)
    active = await session.scalar(
        text("""SELECT EXISTS(SELECT 1 FROM billing_sponsorships
      WHERE tenant_id=:tenant AND revoked_at IS NULL AND starts_at<=now() AND ends_at>now())"""),
        {"tenant": tenant},
    )
    if active:
        raise BillingError("SPONSORSHIP_ACTIVE")
    job_id = uuid4()
    await session.execute(
        text("""INSERT INTO billing_jobs
      (id,tenant_id,actor_id,livemode,kind,dedupe_key,price_id,amount_minor,return_origin)
      VALUES(:id,:tenant,:actor,:live,'checkout',:key,:price,:amount,:return_origin)"""),
        {
            "id": job_id,
            "tenant": tenant,
            "actor": identity.actor_id,
            "live": settings.billing_mode == "live",
            "key": f"checkout:{tenant}:{identity.actor_id}:{key}",
            "price": settings.stripe_price_id,
            "amount": settings.billing_monthly_amount_minor,
            "return_origin": return_origin,
        },
    )
    return {"id": job_id, "state": "pending", "result": None}


async def sponsor(session: AsyncSession, tenant: UUID, actor: UUID, key: str, reason: str) -> dict[str, Any]:
    await require_staff(session, actor, "admin.sponsorship.request")
    await context(session, tenant)
    if not await session.scalar(text("SELECT id FROM tenants WHERE id=:tenant"), {"tenant": tenant}):
        raise BillingError("ORGANIZATION_NOT_FOUND", 404)
    await lock_commercial_change(session, tenant)
    previous = (
        (await session.execute(text("SELECT * FROM billing_sponsorships WHERE tenant_id=:tenant"), {"tenant": tenant}))
        .mappings()
        .one_or_none()
    )
    if previous is not None:
        if previous["idempotency_key"] != key or previous["reason"] != reason:
            raise IdempotencyConflict
        return {**dict(previous), "replayed": True}
    obligation = await session.scalar(
        text("""SELECT
      EXISTS(SELECT 1 FROM billing_jobs WHERE tenant_id=:tenant AND kind='checkout'
        AND state IN ('pending','leased','dispatched'))
      OR EXISTS(SELECT 1 FROM billing_accounts WHERE tenant_id=:tenant AND status
        NOT IN ('inactive','canceled','incomplete_expired'))
      OR EXISTS(SELECT 1 FROM billing_checkouts WHERE tenant_id=:tenant AND status IN ('pending','open'))"""),
        {"tenant": tenant},
    )
    if obligation:
        raise BillingError("BILLING_OBLIGATION_EXISTS")
    grant_id = uuid4()
    grant = (
        (
            await session.execute(
                text("""INSERT INTO billing_sponsorships(id,tenant_id,actor_id,idempotency_key,reason)
      VALUES(:id,:tenant,:actor,:key,:reason) RETURNING *"""),
                {"id": grant_id, "tenant": tenant, "actor": actor, "key": key, "reason": reason},
            )
        )
        .mappings()
        .one()
    )
    await commercial_event(session, tenant, grant_id, "sponsorship.granted", actor)
    return {**dict(grant), "replayed": False}


async def revoke_sponsorship(session: AsyncSession, tenant: UUID, actor: UUID) -> None:
    await require_staff(session, actor, "admin.sponsorship.revoke")
    grant = await session.scalar(
        text("""UPDATE billing_sponsorships SET revoked_at=now()
      WHERE tenant_id=:tenant AND revoked_at IS NULL RETURNING id"""),
        {"tenant": tenant},
    )
    if grant is not None:
        await commercial_event(session, tenant, grant, "sponsorship.revoked", actor)


async def overview(session: AsyncSession, actor: UUID) -> dict[str, Any]:
    await require_staff(session, actor, "admin.billing.overview")
    row = (
        (
            await session.execute(
                text("""SELECT
      (SELECT count(*) FROM billing_accounts WHERE livemode AND status='active' AND NOT blocked
        AND paid_until>now()) AS paying,
      (SELECT count(*) FROM billing_accounts WHERE NOT livemode AND status='active' AND NOT blocked
        AND paid_until>now()) AS testing,
      (SELECT count(*) FROM billing_sponsorships WHERE revoked_at IS NULL AND starts_at<=now()
        AND ends_at>now()) AS sponsored,
      (SELECT count(*) FROM billing_jobs WHERE state IN ('pending','leased','dispatched')) AS pending,
      (SELECT count(*) FROM billing_jobs WHERE state='failed') AS failed""")
            )
        )
        .mappings()
        .one()
    )
    return {**dict(row), "mrr_available": False}


async def opportunities(
    session: AsyncSession,
    settings: Settings,
    actor: UUID,
    state: Literal["open", "expired"],
    limit: int,
    after: UUID | None,
) -> dict[str, Any]:
    await require_staff(session, actor, "admin.billing.opportunities.read")
    before_at = None
    if after is not None:
        before_at = await session.scalar(
            text("SELECT created_at FROM billing_jobs WHERE id=:id AND kind='checkout'"), {"id": after}
        )
        if before_at is None:
            return {"items": [], "next_cursor": None}
    rows = (
        (
            await session.execute(
                text("""SELECT j.id,j.created_at,t.id AS tenant_id,t.name AS business_name,
          u.email AS contact_email,p.phone AS contact_phone,p.phone_verified,
          c.status AS checkout_status,c.expires_at,a.livemode
          FROM billing_jobs j
          JOIN billing_checkouts c ON c.id=j.id
          JOIN billing_accounts a ON a.checkout_id=c.id AND a.tenant_id=c.tenant_id
          JOIN tenants t ON t.id=c.tenant_id
          JOIN user_accounts u ON u.id=j.actor_id
          LEFT JOIN LATERAL (
            SELECT phone,phone_verified FROM business_profiles
            WHERE tenant_id=t.id ORDER BY business_id LIMIT 1
          ) p ON true
          WHERE j.kind='checkout' AND a.livemode=:live AND c.status=:state
            AND (CAST(:before_at AS timestamptz) IS NULL OR
              (j.created_at,j.id)<(:before_at,:after))
            AND (:state<>'open' OR c.expires_at>now())
            AND NOT (a.status='active' AND NOT a.blocked AND a.paid_until>now())
            AND (a.subscription_id IS NULL OR a.status IN ('canceled','incomplete_expired'))
            AND NOT EXISTS (
              SELECT 1 FROM billing_sponsorships s WHERE s.tenant_id=t.id
                AND s.revoked_at IS NULL AND s.starts_at<=now() AND s.ends_at>now()
            )
          ORDER BY j.created_at DESC,j.id DESC LIMIT :limit"""),
                {
                    "live": settings.environment == "production",
                    "state": state,
                    "before_at": before_at,
                    "after": after,
                    "limit": limit + 1,
                },
            )
        )
        .mappings()
        .all()
    )
    items = [dict(row) for row in rows[:limit]]
    return {"items": items, "next_cursor": str(items[-1]["id"]) if len(rows) > limit else None}
