"""Durable provider jobs. Network IO happens between short, fenced transactions."""

import json
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from sqlalchemy import text

from app.adapters.stripe_billing import StripeBilling
from app.core.config import Settings
from app.db.session import Database
from app.services.billing import BillingError, commercial_event, lock_commercial_change


async def enqueue_webhook(database: Database, settings: Settings, event: dict[str, str]) -> None:
    async with database.sessions() as db, db.begin():
        await db.execute(
            text("""INSERT INTO billing_jobs(id,kind,livemode,dedupe_key,event_type,object_id)
          VALUES(:id,'reconcile',:live,:key,:event_type,:object_id) ON CONFLICT(livemode,dedupe_key) DO NOTHING"""),
            {
                "id": uuid4(),
                "live": settings.billing_mode == "live",
                "key": f"stripe:{event['event_id']}",
                "event_type": event["event_type"],
                "object_id": event["object_id"],
            },
        )


class BillingProcessor:
    def __init__(self, settings: Settings, database: Database, provider: StripeBilling) -> None:
        self.settings, self.database, self.provider = settings, database, provider

    async def job(self, job_id: UUID) -> dict[str, Any]:
        async with self.database.sessions() as db:
            row = (
                (await db.execute(text("SELECT * FROM billing_jobs WHERE id=:id"), {"id": job_id}))
                .mappings()
                .one_or_none()
            )
        if row is None or row["livemode"] != (self.settings.billing_mode == "live"):
            raise BillingError("INVALID_BILLING_JOB", 422)
        return dict(row)

    async def claim_account(self, tenant: UUID, live: bool) -> dict[str, Any]:
        async with self.database.sessions() as db, db.begin():
            await db.execute(
                text("""INSERT INTO billing_accounts(tenant_id,livemode)
              VALUES(:tenant,:live) ON CONFLICT DO NOTHING"""),
                {"tenant": tenant, "live": live},
            )
            row = (
                (
                    await db.execute(
                        text("""UPDATE billing_accounts SET fencing_token=fencing_token+1,
              lease_until=clock_timestamp()+interval '90 seconds' WHERE tenant_id=:tenant AND livemode=:live
              AND (lease_until IS NULL OR lease_until<=clock_timestamp()) RETURNING *"""),
                        {"tenant": tenant, "live": live},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise BillingError("BILLING_BUSY")
        return dict(row)

    async def release_account(self, account: dict[str, Any]) -> None:
        async with self.database.sessions() as db, db.begin():
            await db.execute(
                text("""UPDATE billing_accounts SET lease_until=NULL
              WHERE tenant_id=:tenant_id AND livemode=:livemode AND fencing_token=:fencing_token"""),
                account,
            )

    async def prepare_checkout(self, job: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
        async with self.database.sessions() as db, db.begin():
            existing = (
                (await db.execute(text("SELECT * FROM billing_checkouts WHERE id=:id"), {"id": account["checkout_id"]}))
                .mappings()
                .one_or_none()
            )
            if existing is not None and (
                existing["id"] == job["id"]
                or existing["status"] in {"pending", "open"}
                or (existing["status"] == "complete" and account["status"] not in {"canceled", "incomplete_expired"})
            ):
                return dict(existing)
            await db.execute(
                text("""INSERT INTO billing_checkouts(id,tenant_id,livemode,price_id,amount_minor,origin)
              VALUES(:id,:tenant_id,:livemode,:price_id,:amount_minor,:origin) ON CONFLICT DO NOTHING"""),
                {**job, "origin": self.settings.public_web_url},
            )
            updated = await db.scalar(
                text("""UPDATE billing_accounts SET checkout_id=:id
              WHERE tenant_id=:tenant_id AND livemode=:livemode AND fencing_token=:fencing_token
              AND lease_until>clock_timestamp() RETURNING tenant_id"""),
                {**account, "id": job["id"]},
            )
            if updated is None:
                raise BillingError("BILLING_LEASE_LOST")
            return dict(
                (await db.execute(text("SELECT * FROM billing_checkouts WHERE id=:id"), {"id": job["id"]}))
                .mappings()
                .one()
            )

    async def save(
        self,
        job: dict[str, Any],
        account: dict[str, Any],
        result: dict[str, Any],
        snapshot: dict[str, Any] | None = None,
        checkout: dict[str, Any] | None = None,
    ) -> None:
        values = {**account, **(snapshot or {})}
        async with self.database.sessions() as db, db.begin():
            updated = await db.scalar(
                text("""UPDATE billing_accounts SET status=:status,paid_until=:paid_until,
              subscription_id=:subscription_id,customer_id=:customer_id,blocked=:blocked,lease_until=NULL
              WHERE tenant_id=:tenant_id AND livemode=:livemode AND fencing_token=:fencing_token
              AND lease_until>clock_timestamp() RETURNING tenant_id"""),
                values,
            )
            if updated is None:
                raise BillingError("BILLING_LEASE_LOST")
            if checkout is not None:
                await db.execute(
                    text("""UPDATE billing_checkouts SET status=:status,session_id=:session_id,
                  url=:url WHERE id=:id"""),
                    checkout,
                )
            await db.execute(
                text("""UPDATE billing_jobs SET state='completed',result=CAST(:result AS jsonb),tenant_id=:tenant
              WHERE id=:id"""),
                {"id": job["id"], "tenant": account["tenant_id"], "result": json.dumps(result)},
            )
            await commercial_event(
                db,
                account["tenant_id"],
                job["id"],
                "billing.reconciled" if snapshot else f"billing.checkout.{result['status']}",
                job["actor_id"],
            )

    async def run(self, job_id: UUID, *, expire: bool = False) -> dict[str, Any]:
        job = await self.job(job_id)
        if job["state"] == "completed" and not expire:
            return dict(job["result"])
        if self.settings.billing_mode == "disabled":
            raise BillingError("BILLING_UNAVAILABLE", 503)
        if job["kind"] == "checkout":
            return await self.checkout(job, expire=expire)
        reference = await self.provider.reference(job["event_type"], job["object_id"])
        async with self.database.sessions() as db:
            if reference.hold:
                tenant = await db.scalar(
                    text("SELECT tenant_id FROM billing_accounts WHERE customer_id=:id AND livemode=:live"),
                    {"id": reference.customer_id, "live": job["livemode"]},
                )
                order = None
            else:
                record = (
                    (
                        await db.execute(
                            text("SELECT * FROM billing_checkouts WHERE id=:id AND livemode=:live"),
                            {"id": reference.order_id, "live": job["livemode"]},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                order = dict(record) if record else None
                tenant = order["tenant_id"] if order else None
        if tenant is None:
            # Unrelated events on the same provider account must never claim a tenant.
            async with self.database.sessions() as db, db.begin():
                await db.execute(
                    text(
                        "UPDATE billing_jobs SET state='completed',result='{" + '"status":"ignored"' + "}' WHERE id=:id"
                    ),
                    {"id": job_id},
                )
            return {"status": "ignored"}
        account = await self.claim_account(tenant, job["livemode"])
        try:
            if reference.hold:
                snapshot = {"blocked": True}
            elif (
                reference.order_id != account["checkout_id"] and reference.subscription_id != account["subscription_id"]
            ):
                snapshot = {}
            elif reference.subscription_id and order is not None:
                snapshot = await self.provider.subscription(reference.subscription_id, order)
            else:
                snapshot = {}
            result = {"status": "reconciled"}
            await self.save(job, account, result, snapshot)
            return result
        finally:
            await self.release_account(account)

    async def checkout(self, job: dict[str, Any], *, expire: bool) -> dict[str, Any]:
        async with self.database.sessions() as db, db.begin():
            await lock_commercial_change(db, job["tenant_id"])
            owner = await db.scalar(
                text("""SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id
              WHERE m.tenant_id=:tenant AND m.actor_id=:actor AND m.active AND m.role='owner'
                AND u.active AND u.email_verified"""),
                {"tenant": job["tenant_id"], "actor": job["actor_id"]},
            )
            if not expire:
                if not owner:
                    raise BillingError("OWNER_REVOKED", 403)
                sponsored = await db.scalar(
                    text("""SELECT EXISTS(SELECT 1 FROM billing_sponsorships
                  WHERE tenant_id=:tenant AND revoked_at IS NULL AND starts_at<=now() AND ends_at>now())"""),
                    {"tenant": job["tenant_id"]},
                )
                if sponsored:
                    raise BillingError("SPONSORSHIP_ACTIVE")
                await db.execute(text("UPDATE billing_jobs SET state='dispatched' WHERE id=:id"), {"id": job["id"]})
        account = await self.claim_account(job["tenant_id"], job["livemode"])
        try:
            if account["subscription_id"] and account["status"] not in {"canceled", "incomplete_expired"}:
                result: dict[str, Any] = {"status": "already_subscribed"}
                await self.save(job, account, result)
                return result
            order = await self.prepare_checkout(job, account)
            session = await self.provider.checkout(order)
            url = session.get("url") if session["status"] == "open" else None
            if url and (urlsplit(url).scheme != "https" or urlsplit(url).netloc != "checkout.stripe.com"):
                raise BillingError("INVALID_CHECKOUT_URL", 422)
            snapshot = None
            if session["status"] == "complete" and session.get("subscription"):
                snapshot = await self.provider.subscription(session["subscription"], order)
            result = {"status": session["status"], "checkout_url": url, "expires_at": order["expires_at"].isoformat()}
            await self.save(
                job,
                account,
                result,
                snapshot,
                {"id": order["id"], "status": session["status"], "session_id": session["id"], "url": url},
            )
            return result
        finally:
            await self.release_account(account)

    async def fail(self, job_id: UUID, code: str) -> None:
        async with self.database.sessions() as db, db.begin():
            await db.execute(
                text("UPDATE billing_jobs SET state='failed',result=CAST(:result AS jsonb) WHERE id=:id"),
                {"id": job_id, "result": json.dumps({"status": "failed", "error_code": code})},
            )
