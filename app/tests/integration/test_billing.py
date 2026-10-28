import asyncio
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.stripe_billing import Reference, StripeBilling
from app.core.identity import Identity
from app.main import create_app
from app.schemas.onboarding import OnboardingCreate
from app.services import billing
from app.services.billing_delivery import dispatch_billing, enqueue_open_checkout_reconciliation
from app.services.billing_processor import BillingProcessor, enqueue_webhook
from app.services.business import AccessDenied, IdempotencyConflict
from app.services.onboarding import provision_initial_business
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.tests.unit.test_billing_provider import signed_event

pytestmark = pytest.mark.integration
ZERO = UUID(int=0)


@pytest.fixture
def billing_settings(settings):
    return settings.model_copy(
        update={
            "billing_database_url": SecretStr(os.environ["TEST_BILLING_DATABASE_URL"]),
            "billing_mode": "test",
            "stripe_secret_key": SecretStr("sk_test_unit_only"),
            "stripe_webhook_secret": SecretStr("whsec_unit_only"),
            "stripe_price_id": "price_unit",
            "billing_monthly_amount_minor": 9900,
        }
    )


@pytest.fixture
async def commercial(database, admin, settings):
    owner = Identity(uuid4(), "test", str(uuid4()), "Ana", "ana@example.com", True)
    staff = Identity(uuid4(), "test", str(uuid4()), "Operator", "operator@example.com", True)
    async with database.transaction(ZERO, owner.actor_id) as db:
        initial = await provision_initial_business(
            db,
            owner,
            OnboardingCreate(
                name="Ana Studio",
                category="Beleza",
                city="São Paulo",
                description="Unhas",
                phone="+5511999999999",
                accept_terms=True,
                accept_privacy=True,
            ),
        )
    async with admin.begin() as db:
        await db.execute(
            text(
                "INSERT INTO user_accounts(id,issuer,subject,display_name,email_verified) "
                "VALUES(:id,'test',:sub,'Operator',true)"
            ),
            {"id": staff.actor_id, "sub": staff.subject},
        )
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": staff.actor_id})
    await _accept_service(database, settings, initial.tenant_id, owner.actor_id)
    return initial.tenant_id, owner, staff


async def _accept_service(database, settings, tenant, actor):
    async with database.transaction(tenant, actor) as session:
        business = await session.scalar(text("SELECT id FROM businesses WHERE tenant_id=:tenant"), {"tenant": tenant})
    await ServiceAgreementService(settings, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )


@pytest.fixture
def provider():
    result = AsyncMock(spec=StripeBilling)
    result.checkout.return_value = {
        "id": "cs_test_local",
        "status": "open",
        "url": "https://checkout.stripe.com/c/pay/local",
    }
    result.subscription.return_value = {
        "status": "active",
        "paid_until": datetime.now(UTC) + timedelta(days=30),
        "subscription_id": "sub_local",
        "customer_id": "cus_local",
    }
    return result


async def request_job(database, settings, commercial, key="checkout-test"):
    tenant, owner, _ = commercial
    async with database.transaction(tenant, owner.actor_id) as db:
        return await billing.request_checkout(db, settings, tenant, owner, key)


async def test_checkout_requires_exact_service_agreement_before_payment(database, admin, billing_settings, commercial):
    tenant, owner, _ = commercial
    async with admin.begin() as session:
        await session.execute(
            text("UPDATE service_agreement_acceptances SET notice_hash=:hash WHERE tenant_id=:tenant"),
            {"tenant": tenant, "hash": "0" * 64},
        )
    with pytest.raises(billing.BillingError, match="SERVICE_AGREEMENT_REQUIRED"):
        await request_job(database, billing_settings, commercial)
    async with admin.connect() as session:
        assert await session.scalar(text("SELECT count(*) FROM billing_jobs")) == 0


async def test_unreceived_webhook_is_reconciled_from_canonical_stripe_state(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, owner, _ = commercial
    processor = BillingProcessor(billing_settings, billing_database, provider)
    job = await request_job(database, billing_settings, commercial)
    assert (await processor.run(job["id"]))["status"] == "open"
    async with admin.begin() as db:
        await db.execute(
            text("UPDATE billing_jobs SET created_at=now()-interval '40 seconds' WHERE id=:id"),
            {"id": job["id"]},
        )
        await db.execute(
            text("""UPDATE billing_accounts SET status='active',subscription_id='sub_previous',
              paid_until=now()-interval '1 day' WHERE tenant_id=:tenant AND livemode=false"""),
            {"tenant": tenant},
        )
    assert (
        await enqueue_open_checkout_reconciliation(
            billing_database, billing_settings.model_copy(update={"billing_mode": "disabled"})
        )
        == 0
    )
    scheduled = await asyncio.gather(
        *(enqueue_open_checkout_reconciliation(billing_database, billing_settings) for _ in range(4))
    )
    assert sum(scheduled) == 1
    assert await enqueue_open_checkout_reconciliation(billing_database, billing_settings) == 0
    async with admin.connect() as db:
        poll = (
            (
                await db.execute(
                    text("SELECT id,object_id FROM billing_jobs WHERE kind='reconcile' AND dedupe_key LIKE 'poll:%'")
                )
            )
            .mappings()
            .one()
        )
    assert poll["object_id"] == "cs_test_local"
    provider.reference.return_value = Reference(order_id=job["id"], subscription_id="sub_local")
    assert (await processor.run(poll["id"]))["status"] == "reconciled"
    async with database.transaction(tenant, owner.actor_id) as db:
        view = await billing.status(db, billing_settings, tenant, owner.actor_id)
        assert view["access_source"] == "test" and view["access_active"]
    assert await enqueue_open_checkout_reconciliation(billing_database, billing_settings) == 0


async def test_sponsorship_concurrent_replay_expiration_revoke_and_isolation(database, admin, commercial, settings):
    tenant, owner, staff = commercial

    async def grant():
        async with database.transaction(ZERO, staff.actor_id) as db:
            return await billing.sponsor(db, tenant, staff.actor_id, "youtube-six-months", "Participação no canal")

    results = await asyncio.gather(*(grant() for _ in range(5)))
    assert len({r["id"] for r in results}) == 1 and sum(not r["replayed"] for r in results) == 1
    async with database.transaction(tenant, owner.actor_id) as db:
        view = await billing.status(db, settings, tenant, owner.actor_id)
        assert view["access_source"] == "sponsored" and view["price"] is None
        assert view["checkout"] is None and not view["checkout_enabled"]
    async with admin.begin() as db:
        assert await db.scalar(text("SELECT ends_at=starts_at+interval '6 months' FROM billing_sponsorships"))
        assert await db.scalar(text("SELECT count(*) FROM billing_audit")) == 1
        assert await db.scalar(text("SELECT to_regclass('public.billing_outbox')")) is None
        await db.execute(
            text("UPDATE billing_sponsorships SET starts_at=now()-interval '7 months',ends_at=now()-interval '1 month'")
        )
    async with database.transaction(tenant, owner.actor_id) as db:
        assert not (await billing.status(db, settings, tenant, owner.actor_id))["access_active"]
    for _ in range(2):
        async with database.transaction(ZERO, staff.actor_id) as db:
            await billing.revoke_sponsorship(db, tenant, staff.actor_id)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM billing_audit")) == 2
    with pytest.raises(IdempotencyConflict):
        async with database.transaction(ZERO, staff.actor_id) as db:
            await billing.sponsor(db, tenant, staff.actor_id, "another-campaign", "Participação no canal")
    with pytest.raises(billing.BillingError, match="ORGANIZATION_NOT_FOUND"):
        async with database.transaction(ZERO, staff.actor_id) as db:
            await billing.sponsor(db, uuid4(), staff.actor_id, "not-existing", "Motivo")
    with pytest.raises(AccessDenied):
        async with database.transaction(ZERO, owner.actor_id) as db:
            await billing.sponsor(db, tenant, owner.actor_id, "not-allowed", "Motivo")


async def test_checkout_concurrent_replay_guards_and_real_status(database, billing_settings, commercial, admin):
    tenant, owner, staff = commercial
    results = await asyncio.gather(*(request_job(database, billing_settings, commercial) for _ in range(5)))
    assert len({row["id"] for row in results}) == 1
    async with database.transaction(tenant, owner.actor_id) as db:
        view = await billing.status(db, billing_settings, tenant, owner.actor_id)
        assert view["checkout"]["state"] == "pending" and view["price"]["amount_minor"] == 9900
    with pytest.raises(billing.BillingError, match="BILLING_OBLIGATION_EXISTS"):
        async with database.transaction(ZERO, staff.actor_id) as db:
            await billing.sponsor(db, tenant, staff.actor_id, "youtube-access", "Vídeo no canal")
    with pytest.raises(billing.BillingError, match="BILLING_UNAVAILABLE"):
        await request_job(database, billing_settings.model_copy(update={"billing_mode": "disabled"}), commercial)
    async with admin.begin() as db:
        await db.execute(text("UPDATE memberships SET role='editor' WHERE actor_id=:actor"), {"actor": owner.actor_id})
    with pytest.raises(AccessDenied):
        await request_job(database, billing_settings, commercial)
    async with database.transaction(tenant, owner.actor_id) as db:
        assert (await billing.status(db, billing_settings, tenant, owner.actor_id))["checkout"] is None


async def test_sponsored_checkout_blocked_and_no_cross_tenant_reads(database, billing_settings, commercial):
    tenant, owner, staff = commercial
    async with database.transaction(ZERO, staff.actor_id) as db:
        await billing.sponsor(db, tenant, staff.actor_id, "youtube-access", "Vídeo no canal")
    with pytest.raises(billing.BillingError, match="SPONSORSHIP_ACTIVE"):
        await request_job(database, billing_settings, commercial)
    with pytest.raises(AccessDenied):
        async with database.transaction(uuid4(), owner.actor_id) as db:
            await billing.status(db, billing_settings, uuid4(), owner.actor_id)


async def test_processor_checkout_and_payment_canonical_reconciliation(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, owner, staff = commercial
    processor = BillingProcessor(billing_settings, billing_database, provider)
    job = await request_job(database, billing_settings, commercial)
    result = await processor.run(job["id"])
    assert result["status"] == "open" and (await processor.run(job["id"])) == result
    assert provider.checkout.await_count == 1
    async with database.transaction(ZERO, staff.actor_id) as db:
        page = await billing.opportunities(db, billing_settings, staff.actor_id, "open", 25, None)
        assert [item["tenant_id"] for item in page["items"]] == [tenant]
        assert page["items"][0]["contact_email"] == owner.email
        assert page["items"][0]["contact_phone"] == "+5511999999999"
        assert page["items"][0]["phone_verified"] is False
        assert page["next_cursor"] is None
    provider.reference.return_value = Reference(order_id=job["id"], subscription_id="sub_local")
    event = {"event_id": "evt_invoice", "event_type": "invoice.paid", "object_id": "in_local"}
    await asyncio.gather(*(enqueue_webhook(billing_database, billing_settings, event) for _ in range(5)))
    async with admin.connect() as db:
        reconcile = await db.scalar(text("SELECT id FROM billing_jobs WHERE kind='reconcile'"))
    assert (await processor.run(reconcile))["status"] == "reconciled"
    async with database.transaction(tenant, owner.actor_id) as db:
        status = await billing.status(db, billing_settings, tenant, owner.actor_id)
        assert status["access_source"] == "test" and status["access_active"]
    async with database.transaction(ZERO, staff.actor_id) as db:
        summary = await billing.overview(db, staff.actor_id)
        assert summary["paying"] == 0 and summary["testing"] == 1 and not summary["mrr_available"]
        assert (await billing.opportunities(db, billing_settings, staff.actor_id, "open", 25, None))["items"] == []
    next_job = await request_job(database, billing_settings, commercial, "new-intent-key")
    assert (await processor.run(next_job["id"]))["status"] == "already_subscribed"
    provider.reference.return_value = Reference(customer_id="cus_local", hold=True)
    await enqueue_webhook(
        billing_database, billing_settings, {**event, "event_id": "evt_hold", "event_type": "charge.refunded"}
    )
    async with admin.connect() as db:
        hold = await db.scalar(text("SELECT id FROM billing_jobs WHERE event_type='charge.refunded'"))
    await processor.run(hold)
    # A later invoice cannot clear an existing financial hold.
    provider.reference.return_value = Reference(order_id=job["id"], subscription_id="sub_local")
    await enqueue_webhook(billing_database, billing_settings, {**event, "event_id": "evt_later"})
    async with admin.connect() as db:
        later = await db.scalar(text("SELECT id FROM billing_jobs WHERE dedupe_key='stripe:evt_later'"))
    await processor.run(later)
    async with database.transaction(tenant, owner.actor_id) as db:
        assert not (await billing.status(db, billing_settings, tenant, owner.actor_id))["access_active"]


async def test_admin_checkout_opportunities_are_paginated_audited_and_expired(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, owner, staff = commercial
    processor = BillingProcessor(billing_settings, billing_database, provider)
    first = await request_job(database, billing_settings, commercial)
    await processor.run(first["id"])
    other = Identity(uuid4(), "test", str(uuid4()), "Bia", "bia@example.com", True)
    async with database.transaction(ZERO, other.actor_id) as db:
        second_tenant = (
            await provision_initial_business(
                db,
                other,
                OnboardingCreate(
                    name="Bia Studio",
                    category="Beleza",
                    city="São Paulo",
                    description="Cabelos",
                    phone="+5511988888888",
                    accept_terms=True,
                    accept_privacy=True,
                ),
            )
        ).tenant_id
    provider.checkout.return_value = {
        "id": "cs_test_second",
        "status": "open",
        "url": "https://checkout.stripe.com/c/pay/second",
    }
    await _accept_service(database, billing_settings, second_tenant, other.actor_id)
    async with database.transaction(second_tenant, other.actor_id) as db:
        second = await billing.request_checkout(db, billing_settings, second_tenant, other, "second-checkout")
    await processor.run(second["id"])
    async with database.transaction(ZERO, staff.actor_id) as db:
        first_page = await billing.opportunities(db, billing_settings, staff.actor_id, "open", 1, None)
        assert [item["tenant_id"] for item in first_page["items"]] == [second_tenant]
        assert first_page["next_cursor"] == str(second["id"])
        next_page = await billing.opportunities(db, billing_settings, staff.actor_id, "open", 1, second["id"])
        assert [item["tenant_id"] for item in next_page["items"]] == [tenant]
        assert next_page["next_cursor"] is None
        assert (await billing.opportunities(db, billing_settings, staff.actor_id, "open", 1, uuid4()))["items"] == []
        assert (await billing.opportunities(db, billing_settings, staff.actor_id, "expired", 25, None))["items"] == []
        assert (
            await db.scalar(text("SELECT count(*) FROM platform_audit WHERE action='admin.billing.opportunities.read'"))
            == 4
        )
    with pytest.raises(AccessDenied):
        async with database.transaction(tenant, owner.actor_id) as db:
            await billing.opportunities(db, billing_settings, owner.actor_id, "open", 25, None)
    async with admin.begin() as db:
        await db.execute(
            text(
                "UPDATE billing_accounts SET subscription_id='sub_existing',status='active',blocked=true "
                "WHERE tenant_id=:tenant"
            ),
            {"tenant": second_tenant},
        )
    async with database.transaction(ZERO, staff.actor_id) as db:
        assert [
            item["tenant_id"]
            for item in (await billing.opportunities(db, billing_settings, staff.actor_id, "open", 25, None))["items"]
        ] == [tenant]
    async with admin.begin() as db:
        await db.execute(
            text(
                "UPDATE billing_accounts SET subscription_id=NULL,status='inactive',blocked=false "
                "WHERE tenant_id=:tenant"
            ),
            {"tenant": second_tenant},
        )
    provider.checkout.return_value = {"id": "cs_test_local", "status": "expired"}
    assert (await processor.run(first["id"], expire=True))["status"] == "expired"
    async with database.transaction(ZERO, staff.actor_id) as db:
        expired = await billing.opportunities(db, billing_settings, staff.actor_id, "expired", 25, None)
        assert [item["tenant_id"] for item in expired["items"]] == [tenant]
        assert expired["items"][0]["checkout_status"] == "expired"
        open_page = await billing.opportunities(db, billing_settings, staff.actor_id, "open", 25, None)
        assert [item["tenant_id"] for item in open_page["items"]] == [second_tenant]


async def test_billing_role_cannot_write_business_and_app_cannot_forge_paid_access(
    database, billing_database, commercial
):
    tenant, owner, _ = commercial
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, owner.actor_id) as db:
            await db.execute(
                text("INSERT INTO billing_accounts(tenant_id,livemode,status) VALUES(:tenant,true,'active')"),
                {"tenant": tenant},
            )
    with pytest.raises(DBAPIError):
        async with billing_database.sessions() as db, db.begin():
            await db.execute(text("UPDATE memberships SET role='owner'"))
    with pytest.raises(DBAPIError):
        async with billing_database.sessions() as db:
            await db.execute(text("SELECT * FROM auth_credentials"))


async def test_billing_http_contracts_permissions_and_signed_inbox(
    database, billing_database, billing_settings, commercial
):
    tenant, owner, staff = commercial
    app = create_app(billing_settings, database, billing_database=billing_database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test", headers={"Authorization": "Bearer test"}
        ) as api,
    ):
        verifier = AsyncMock(return_value=owner)
        app.state.identity_verifier.authenticate = verifier
        assert (await api.get("/health/ready")).status_code == 200
        assert (await api.get(f"/api/v1/billing/{tenant}")).status_code == 200
        assert (await api.get("/api/v1/admin/billing")).status_code == 403
        assert (await api.get("/api/v1/admin/billing/opportunities")).status_code == 403
        verifier.return_value = staff
        assert (await api.get("/api/v1/admin/billing/opportunities")).json() == {
            "items": [],
            "next_cursor": None,
        }
        assert (await api.get("/api/v1/admin/billing/opportunities?state=unknown")).status_code == 422
        assert (await api.get("/api/v1/admin/billing/opportunities?limit=51")).status_code == 422
        path = f"/api/v1/admin/organizations/{tenant}/sponsorship"
        headers = {"Idempotency-Key": "http-sponsorship"}
        assert (await api.post(path, headers=headers, json={"reason": "Vídeo no canal"})).status_code == 201
        assert (await api.post(path, headers=headers, json={"reason": "Vídeo no canal"})).status_code == 200
        assert (await api.get(f"/api/v1/admin/organizations/{tenant}/billing")).json()["access_source"] == "sponsored"
        assert (await api.get("/api/v1/admin/billing")).json()["sponsored"] == 1
        assert (await api.delete(path)).status_code == 204
        verifier.return_value = owner
        assert (
            await api.post(f"/api/v1/billing/{tenant}/checkout", headers={"Idempotency-Key": "http-checkout"})
        ).status_code == 202
        body, signature = signed_event(billing_settings)
        assert (
            await api.post("/api/v1/webhooks/stripe", content=body, headers={"stripe-signature": signature})
        ).status_code == 200
        assert (
            await api.post("/api/v1/webhooks/stripe", content=body, headers={"stripe-signature": signature})
        ).status_code == 200
        assert (await api.post("/api/v1/webhooks/stripe", content=body)).status_code == 400
        assert (await api.post("/api/v1/webhooks/stripe", content=b"x" * 262145)).status_code == 413
        ignored, sig = signed_event(billing_settings, type="customer.created")
        assert (
            await api.post("/api/v1/webhooks/stripe", content=ignored, headers={"stripe-signature": sig})
        ).status_code == 200
        app.state.billing_database = None
        assert (
            await api.post("/api/v1/webhooks/stripe", content=body, headers={"stripe-signature": signature})
        ).status_code == 503


async def test_checkout_expiry_recovers_existing_intent_and_unknown_network_result(
    database, billing_database, admin, billing_settings, commercial, provider
):
    processor = BillingProcessor(billing_settings, billing_database, provider)
    first = await request_job(database, billing_settings, commercial)
    provider.checkout.side_effect = ConnectionError("synthetic network failure")
    with pytest.raises(ConnectionError):
        await processor.run(first["id"])
    original = provider.checkout.call_args.args[0]["id"]
    provider.checkout.side_effect = None
    await processor.run(first["id"])
    assert provider.checkout.call_args.args[0]["id"] == original
    second = await request_job(database, billing_settings, commercial, "second-checkout")
    await processor.run(second["id"])
    assert provider.checkout.call_args.args[0]["id"] == original
    provider.checkout.return_value = {"id": "cs_test_local", "status": "expired"}
    assert (await processor.run(first["id"], expire=True))["status"] == "expired"
    third = await request_job(database, billing_settings, commercial, "third-checkout")
    provider.checkout.return_value = {"id": "cs_test_next", "status": "complete", "subscription": "sub_local"}
    assert (await processor.run(third["id"]))["status"] == "complete"
    assert provider.checkout.call_args.args[0]["id"] == third["id"]
    provider.subscription.assert_awaited_once()
    with pytest.raises(billing.BillingError, match="INVALID_BILLING_JOB"):
        await processor.run(uuid4())
    await processor.fail(third["id"], "PROVIDER_RECONCILIATION_REQUIRED")
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT state FROM billing_jobs WHERE id=:id"), {"id": third["id"]}) == "failed"


async def test_account_lease_prevents_concurrent_and_stale_commits(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, _, _ = commercial
    processor = BillingProcessor(billing_settings, billing_database, provider)
    job = await request_job(database, billing_settings, commercial)
    account = await processor.claim_account(tenant, False)
    with pytest.raises(billing.BillingError, match="BILLING_BUSY"):
        await processor.claim_account(tenant, False)
    async with admin.begin() as db:
        await db.execute(text("UPDATE billing_accounts SET lease_until=now()-interval '1 second'"))
    fresh = await processor.claim_account(tenant, False)
    await processor.release_account(account)
    with pytest.raises(billing.BillingError, match="BILLING_LEASE_LOST"):
        await processor.prepare_checkout({**await processor.job(job["id"])}, account)
    with pytest.raises(billing.BillingError, match="BILLING_LEASE_LOST"):
        await processor.save(await processor.job(job["id"]), account, {"status": "ignored"})
    await processor.release_account(fresh)

    async def expire_during_rpc(order):
        async with admin.begin() as db:
            await db.execute(text("UPDATE billing_accounts SET lease_until=now()-interval '1 second'"))
        return {"id": "cs_test_local", "status": "open", "url": "https://checkout.stripe.com/c/pay/local"}

    provider.checkout.side_effect = expire_during_rpc
    with pytest.raises(billing.BillingError, match="BILLING_LEASE_LOST"):
        await processor.run(job["id"])


async def test_reconciliation_ignores_unrelated_and_old_subscription_events(
    database, billing_database, admin, billing_settings, commercial, provider
):
    processor = BillingProcessor(billing_settings, billing_database, provider)
    first = await request_job(database, billing_settings, commercial)
    await processor.run(first["id"])
    for index, reference in enumerate(
        [
            Reference(),
            Reference(customer_id="unrelated", hold=True),
            Reference(order_id=first["id"]),
            Reference(order_id=first["id"], subscription_id="sub_previous"),
        ]
    ):
        if index == 3:
            async with admin.begin() as db:
                await db.execute(text("UPDATE billing_accounts SET checkout_id=NULL,subscription_id='sub_current'"))
        provider.reference.return_value = reference
        await enqueue_webhook(
            billing_database,
            billing_settings,
            {"event_id": f"evt_{index}", "event_type": "invoice.paid", "object_id": "in_local"},
        )
        async with admin.connect() as db:
            job_id = await db.scalar(
                text("SELECT id FROM billing_jobs WHERE dedupe_key=:key"), {"key": f"stripe:evt_{index}"}
            )
        result = await processor.run(job_id)
        assert result["status"] == ("ignored" if index < 2 else "reconciled")
    provider.subscription.assert_not_awaited()


@pytest.mark.parametrize("url", ["http://checkout.stripe.com/c/pay/x", "https://evil.example/pay"])
async def test_checkout_rejects_unsafe_redirect_and_owner_revocation(
    database, billing_database, admin, billing_settings, commercial, provider, url
):
    processor = BillingProcessor(billing_settings, billing_database, provider)
    job = await request_job(database, billing_settings, commercial)
    provider.checkout.return_value = {"id": "cs_test_local", "status": "open", "url": url}
    with pytest.raises(billing.BillingError, match="INVALID_CHECKOUT_URL"):
        await processor.run(job["id"])
    async with admin.begin() as db:
        await db.execute(text("UPDATE memberships SET active=false"))
    with pytest.raises(billing.BillingError, match="OWNER_REVOKED"):
        await processor.run(job["id"])
    provider.checkout.return_value = {"id": "cs_test_local", "status": "complete", "subscription": None}
    assert (await processor.run(job["id"], expire=True))["status"] == "complete"
    disabled = BillingProcessor(
        billing_settings.model_copy(update={"billing_mode": "disabled"}), billing_database, provider
    )
    # Completed jobs can still be read, but disabled processors cannot start new work.
    assert (await disabled.run(job["id"]))["status"] == "complete"
    with pytest.raises(billing.BillingError, match="BILLING_UNAVAILABLE"):
        await disabled.run(job["id"], expire=True)


async def test_live_paid_metrics_and_request_rejected_for_unverified_owner(
    database, billing_database, admin, billing_settings, commercial
):
    from dataclasses import replace

    tenant, owner, staff = commercial
    with pytest.raises(AccessDenied):
        async with database.transaction(tenant, owner.actor_id) as db:
            await billing.request_checkout(
                db, billing_settings, tenant, replace(owner, email_verified=False), "unverified-user"
            )
    async with admin.begin() as db:
        await db.execute(
            text(
                "INSERT INTO billing_accounts(tenant_id,livemode,status,paid_until) "
                "VALUES(:tenant,true,'active',now()+interval '1 day')"
            ),
            {"tenant": tenant},
        )
    production = billing_settings.model_copy(update={"environment": "production", "billing_mode": "live"})
    async with database.transaction(tenant, owner.actor_id) as db:
        assert (await billing.status(db, production, tenant, owner.actor_id))["access_source"] == "paid"
    async with database.transaction(ZERO, staff.actor_id) as db:
        assert (await billing.overview(db, staff.actor_id))["paying"] == 1
    with pytest.raises(billing.BillingError, match="BILLING_OBLIGATION_EXISTS"):
        async with database.transaction(ZERO, staff.actor_id) as db:
            await billing.sponsor(db, tenant, staff.actor_id, "paid-not-sponsored", "Participação no canal")


@pytest.mark.parametrize("outcome", ["success", "duplicate", "failure", "exhausted"])
async def test_durable_job_dispatch_retry_and_duplicate_start(
    database, billing_database, admin, billing_settings, commercial, outcome
):
    from temporalio.exceptions import WorkflowAlreadyStartedError

    job = await request_job(database, billing_settings, commercial)
    client = AsyncMock()
    if outcome == "duplicate":
        client.start_workflow.side_effect = WorkflowAlreadyStartedError("test-job", "BillingWorkflow")
    if outcome in {"failure", "exhausted"}:
        client.start_workflow.side_effect = ConnectionError("synthetic unavailable")
    if outcome == "exhausted":
        async with admin.begin() as db:
            await db.execute(text("UPDATE billing_jobs SET attempts=7"))
    assert await dispatch_billing(billing_database, client, billing_settings) == 1
    async with admin.connect() as db:
        state = await db.scalar(text("SELECT state FROM billing_jobs WHERE id=:id"), {"id": job["id"]})
    assert state == ("pending" if outcome == "failure" else "failed" if outcome == "exhausted" else "dispatched")
    assert (
        await dispatch_billing(
            billing_database, client, billing_settings.model_copy(update={"billing_mode": "disabled"})
        )
        == 0
    )


async def test_dispatch_fence_does_not_overwrite_job_finished_during_rpc(
    database, billing_database, admin, billing_settings, commercial
):
    job = await request_job(database, billing_settings, commercial)
    client = AsyncMock()

    async def finish(*args, **kwargs):
        async with admin.begin() as db:
            await db.execute(
                text("UPDATE billing_jobs SET state='completed',result='{}' WHERE id=:id"), {"id": job["id"]}
            )

    client.start_workflow.side_effect = finish
    await dispatch_billing(billing_database, client, billing_settings)
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT state FROM billing_jobs WHERE id=:id"), {"id": job["id"]}) == "completed"


@pytest.mark.temporal
async def test_real_billing_temporal_worker_executes_durable_job(
    database, billing_database, admin, billing_settings, commercial, provider
):
    from temporalio.client import Client
    from temporalio.worker import Worker

    from app.workflows.billing import BillingWorkflow
    from app.workflows.billing_activities import BillingActivities

    queue = f"test-billing-{uuid4()}"
    config = billing_settings.model_copy(update={"temporal_task_queue": queue})
    processor = BillingProcessor(config, billing_database, provider)
    provider.checkout.return_value = {"id": "cs_test_local", "status": "expired"}
    job = await request_job(database, config, commercial)
    activities = BillingActivities(processor)
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    async with Worker(
        client,
        task_queue=f"{queue}-billing",
        workflows=[BillingWorkflow],
        activities=[activities.process_billing_job, activities.expire_billing_checkout, activities.fail_billing_job],
    ):
        assert await dispatch_billing(billing_database, client, config) == 1
        assert await client.get_workflow_handle(f"billing/{job['id']}").result() == "completed"
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT state FROM billing_jobs WHERE id=:id"), {"id": job["id"]}) == "completed"


async def test_quote_is_frozen_and_reordered_events_do_not_restore_cancelled_subscription(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, owner, _ = commercial
    processor = BillingProcessor(billing_settings, billing_database, provider)
    job = await request_job(database, billing_settings, commercial)
    changed = billing_settings.model_copy(
        update={"billing_monthly_amount_minor": 19900, "stripe_price_id": "price_next"}
    )
    async with database.transaction(tenant, owner.actor_id) as db:
        assert (await billing.status(db, changed, tenant, owner.actor_id))["price"]["amount_minor"] == 9900
    await processor.run(job["id"])
    async with database.transaction(tenant, owner.actor_id) as db:
        assert (await billing.status(db, changed, tenant, owner.actor_id))["price"]["amount_minor"] == 9900
    provider.reference.return_value = Reference(order_id=job["id"], subscription_id="sub_local")
    provider.subscription.return_value = {
        "status": "canceled",
        "subscription_id": "sub_local",
        "customer_id": "cus_local",
        "paid_until": datetime.now(UTC) + timedelta(days=10),
    }
    for event_id, event_type in [("evt_cancel", "customer.subscription.deleted"), ("evt_old_paid", "invoice.paid")]:
        await enqueue_webhook(
            billing_database,
            billing_settings,
            {"event_id": event_id, "event_type": event_type, "object_id": "obj_local"},
        )
        async with admin.connect() as db:
            target = await db.scalar(
                text("SELECT id FROM billing_jobs WHERE dedupe_key=:key"), {"key": f"stripe:{event_id}"}
            )
        await processor.run(target)
        async with database.transaction(tenant, owner.actor_id) as db:
            view = await billing.status(db, billing_settings, tenant, owner.actor_id)
            assert not view["access_active"] and view["checkout_enabled"]
    async with admin.begin() as db:
        await db.execute(text("UPDATE billing_checkouts SET status='complete' WHERE id=:id"), {"id": job["id"]})
    fresh = await request_job(database, billing_settings, commercial, "restart-after-cancel")
    provider.checkout.return_value = {
        "id": "cs_test_restart",
        "status": "open",
        "url": "https://checkout.stripe.com/c/pay/new",
    }
    assert (await processor.run(fresh["id"]))["status"] == "open"
    assert provider.checkout.call_args.args[0]["id"] == fresh["id"]


async def test_delayed_checkout_cannot_start_after_sponsorship_was_granted(
    database, billing_database, admin, billing_settings, commercial, provider
):
    tenant, owner, staff = commercial
    job = await request_job(database, billing_settings, commercial)
    # Delivery exhausted before a workflow could create a hosted session.
    async with admin.begin() as db:
        await db.execute(text("UPDATE billing_jobs SET state='failed' WHERE id=:id"), {"id": job["id"]})
    async with database.transaction(ZERO, staff.actor_id) as db:
        await billing.sponsor(db, tenant, staff.actor_id, "youtube-after-failure", "Participação no canal")
    processor = BillingProcessor(billing_settings, billing_database, provider)
    with pytest.raises(billing.BillingError, match="SPONSORSHIP_ACTIVE"):
        await processor.run(job["id"])
    provider.checkout.assert_not_awaited()


@pytest.mark.parametrize(
    "environment,configured,origin,accepted",
    [
        ("development", "http://localhost:5173", "http://127.0.0.1:5173", True),
        ("testing", "http://127.0.0.1:5173", "http://localhost:5173", True),
        ("development", "http://localhost:5173", None, True),
        ("development", "http://localhost:5173", "http://localhost:5174", False),
        ("development", "http://localhost:5173", "https://localhost:5173", False),
        ("development", "http://localhost:5173", "https://untrusted.example", False),
        ("development", "http://localhost:5173", "null", False),
        ("staging", "https://meu-braco-direito.example", "https://meu-braco-direito.example", True),
        ("production", "http://localhost:5173", "http://127.0.0.1:5173", False),
    ],
)
async def test_http_checkout_freezes_only_authorized_return_origin(
    database, billing_database, billing_settings, commercial, provider, environment, configured, origin, accepted
):
    tenant, owner, _ = commercial
    config = billing_settings.model_copy(update={"environment": environment, "public_web_url": configured})
    app = create_app(config, database, billing_database=billing_database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as api,
    ):
        app.state.identity_verifier.authenticate = AsyncMock(return_value=owner)
        headers = {"Authorization": "Bearer test", "Idempotency-Key": "return-origin-test"}
        if origin is not None:
            headers["Origin"] = origin
        response = await api.post(f"/api/v1/billing/{tenant}/checkout", headers=headers)
        if not accepted:
            assert response.status_code == 403 and response.json()["error_code"] == "ORIGIN_REJECTED"
            async with billing_database.sessions() as db:
                assert await db.scalar(text("SELECT count(*) FROM billing_jobs")) == 0
            return
        assert response.status_code == 202
        job_id = UUID(response.json()["id"])
        # Deployment settings can change between admission and asynchronous processing.
        processor = BillingProcessor(
            config.model_copy(update={"public_web_url": "https://changed.example"}), billing_database, provider
        )
        assert (await processor.job(job_id))["return_origin"] == (origin or configured)
        await processor.run(job_id)
        assert provider.checkout.call_args.args[0]["origin"] == (origin or configured)
        # Replaying the operation from another allowed host preserves the original order.
        headers["Origin"] = configured
        replay = await api.post(f"/api/v1/billing/{tenant}/checkout", headers=headers)
        assert replay.json()["id"] == str(job_id)
        assert (await processor.job(job_id))["return_origin"] == (origin or configured)


async def test_legacy_checkout_job_uses_configured_return_origin(
    database, billing_database, billing_settings, commercial, provider, admin
):
    job = await request_job(database, billing_settings, commercial)
    async with admin.begin() as db:
        await db.execute(text("UPDATE billing_jobs SET return_origin=NULL WHERE id=:id"), {"id": job["id"]})
    processor = BillingProcessor(billing_settings, billing_database, provider)
    await processor.run(job["id"])
    assert provider.checkout.call_args.args[0]["origin"] == billing_settings.public_web_url
