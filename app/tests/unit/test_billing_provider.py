import hashlib
import hmac
import json
import os
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import stripe
from pydantic import SecretStr, ValidationError

from app.adapters.stripe_billing import Reference, StripeBilling, verify_webhook
from app.core.config import Settings
from app.services.billing import BillingError


@pytest.fixture
def config(settings):
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


def signed_event(config, *, timestamp=None, **changes):
    event = {
        "id": "evt_local",
        "type": "invoice.paid",
        "livemode": False,
        "data": {"object": {"id": "in_local"}},
        **changes,
    }
    raw = json.dumps(event).encode()
    ts = int(time.time()) if timestamp is None else timestamp
    signature = hmac.new(
        config.stripe_webhook_secret.get_secret_value().encode(), str(ts).encode() + b"." + raw, hashlib.sha256
    ).hexdigest()
    return raw, f"t={ts},v1={signature}"


@pytest.mark.parametrize(
    "changes",
    [
        {"billing_database_url": None},
        {"stripe_secret_key": None},
        {"stripe_webhook_secret": None},
        {"stripe_price_id": None},
        {"billing_monthly_amount_minor": None},
        {"stripe_secret_key": "sk_live_wrong_mode"},
        {"billing_mode": "live", "stripe_secret_key": "sk_live_test_only"},
    ],
)
def test_billing_configuration_fails_closed(config, changes):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **{**config.model_dump(), **changes})
    assert "unit_only" not in str(error.value)


def test_explicit_live_configuration_and_environment_isolation(config):
    safe = {
        **config.model_dump(),
        "environment": "production",
        "service_agreement_required": True,
        "temporal_tls": True,
        "public_web_url": "https://meu-braco-direito.example",
        "auth_encryption_key": "c2VjdXJlLXRlc3Qta2V5LTAwMDAwMDAwMDAwMDAwMDA=",
        "smtp_starttls": True,
        "smtp_username": "test",
        "smtp_password": "test-password",
        "billing_mode": "live",
        "stripe_secret_key": "sk_live_unit_only",
        "billing_live_enabled": True,
    }
    assert Settings(_env_file=None, **safe).billing_mode == "live"
    for changes in [
        {"billing_live_enabled": False},
        {"billing_mode": "test", "stripe_secret_key": "sk_test_unit_only"},
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{**safe, **changes})


def test_signed_webhooks_validate_time_mode_shape_and_supported_types(config):
    body, signature = signed_event(config)
    assert verify_webhook(config, body, signature) == {
        "event_id": "evt_local",
        "event_type": "invoice.paid",
        "object_id": "in_local",
    }
    assert verify_webhook(config, *signed_event(config, type="customer.created")) is None
    for kwargs in [{"livemode": True}, {"id": 1}, {"id": "x" * 129}, {"data": {}}, {"data": None}]:
        with pytest.raises(BillingError, match="INVALID_WEBHOOK"):
            verify_webhook(config, *signed_event(config, **kwargs))
    for raw, header in [
        (body, "invalid"),
        signed_event(config, timestamp=int(time.time()) - 600),
        (b"not-json", signature),
    ]:
        with pytest.raises(BillingError, match="INVALID_WEBHOOK"):
            verify_webhook(config, raw, header)
    for value in [
        config.model_copy(update={"billing_mode": "disabled"}),
        config.model_copy(update={"stripe_webhook_secret": None}),
    ]:
        with pytest.raises(BillingError, match="BILLING_UNAVAILABLE"):
            verify_webhook(value, body, signature)


@pytest.fixture
def order():
    return {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "price_id": "price_unit",
        "amount_minor": 9900,
        "livemode": False,
        "session_id": None,
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "origin": "http://localhost:5173",
    }


@pytest.fixture
async def adapter(config, order, monkeypatch):
    provider = StripeBilling(config)
    provider.client.v1.prices.retrieve_async = AsyncMock(
        return_value={
            "active": True,
            "livemode": False,
            "currency": "brl",
            "unit_amount": 9900,
            "recurring": {"interval": "month", "interval_count": 1},
        }
    )
    session = stripe.StripeObject.construct_from(
        {
            "id": "cs_test_local",
            "status": "open",
            "url": "https://checkout.stripe.com/c/pay/local",
            "livemode": False,
            "client_reference_id": str(order["id"]),
            "metadata": {"order_id": str(order["id"])},
            "subscription": "sub_local",
        },
        None,
    )
    provider.client.v1.checkout.sessions.create_async = AsyncMock(return_value=session)
    provider.client.v1.checkout.sessions.retrieve_async = AsyncMock(return_value=session)
    provider.client.v1.subscriptions.retrieve_async = AsyncMock(
        return_value={"metadata": {"order_id": str(order["id"])}}
    )
    provider.client.v1.invoices.retrieve_async = AsyncMock(
        return_value={"parent": {"subscription_details": {"subscription": "sub_local"}}}
    )
    provider.client.v1.charges.retrieve_async = AsyncMock(return_value={"customer": "cus_local"})
    provider.client.v1.disputes.retrieve_async = AsyncMock(return_value={"charge": "ch_local"})
    try:
        yield provider
    finally:
        await provider.close()


@pytest.mark.parametrize("prefix", ["local-spark-checkout", "meu-braco-direito-checkout"])
@pytest.mark.parametrize("return_origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
async def test_checkout_idempotency_uses_frozen_parameters_and_recovers_existing_session(
    adapter, order, settings, return_origin, prefix
):
    order["origin"] = return_origin
    order["provider_key_prefix"] = prefix
    await adapter.checkout(order)
    await adapter.checkout(order)
    calls = adapter.client.v1.checkout.sessions.create_async.call_args_list
    assert calls[0] == calls[1]
    assert calls[0].kwargs["options"]["idempotency_key"] == f"{prefix}/{order['id']}"
    assert calls[0].args[0]["mode"] == "subscription" and calls[0].args[0]["payment_method_types"] == ["card"]
    assert str(order["tenant_id"]) in calls[0].args[0]["success_url"]
    assert calls[0].args[0]["success_url"].startswith(f"{return_origin}/app/billing?")
    assert calls[0].args[0]["cancel_url"].startswith(f"{return_origin}/app/billing?")
    await adapter.checkout({**order, "session_id": "cs_test_local"})
    adapter.client.v1.checkout.sessions.retrieve_async.assert_awaited_once()
    disabled = StripeBilling(settings)
    await disabled.close()


@pytest.mark.parametrize(
    "changes",
    [
        {"active": False},
        {"livemode": True},
        {"currency": "usd"},
        {"unit_amount": 100},
        {"recurring": None},
        {"recurring": {"interval": "year", "interval_count": 1}},
        {"recurring": {"interval": "month", "interval_count": 2}},
    ],
)
async def test_checkout_rejects_provider_price_mismatch(adapter, order, changes):
    adapter.client.v1.prices.retrieve_async.return_value.update(changes)
    with pytest.raises(BillingError, match="PRICE_MISMATCH"):
        await adapter.checkout(order)


@pytest.mark.parametrize("changes", [{"livemode": True}, {"client_reference_id": "unrelated"}, {"metadata": {}}])
async def test_checkout_rejects_response_for_another_intent(adapter, order, changes):
    session = dict(adapter.client.v1.checkout.sessions.create_async.return_value)
    adapter.client.v1.checkout.sessions.create_async.return_value = stripe.StripeObject.construct_from(
        {**session, **changes}, None
    )
    with pytest.raises(BillingError, match="CHECKOUT_MISMATCH"):
        await adapter.checkout(order)


@pytest.mark.parametrize(
    "event_type",
    [
        "checkout.session.completed",
        "invoice.paid",
        "customer.subscription.updated",
        "charge.refunded",
        "charge.dispute.created",
    ],
)
async def test_canonical_references_are_resolved_without_using_webhook_metadata(adapter, order, event_type):
    result = await adapter.reference(event_type, "obj_local")
    if event_type.startswith("charge."):
        assert result == Reference(customer_id="cus_local", hold=True)
    else:
        assert result.order_id == order["id"] and result.subscription_id


async def test_unrelated_non_subscription_invoice_and_missing_metadata(adapter):
    adapter.client.v1.invoices.retrieve_async.return_value = {"parent": None}
    assert await adapter.reference("invoice.paid", "in_other") == Reference()
    adapter.client.v1.subscriptions.retrieve_async.return_value = {"metadata": {}}
    assert (await adapter.reference("customer.subscription.updated", "sub_other")).order_id is None


def subscription(order):
    return {
        "id": "sub_local",
        "customer": "cus_local",
        "status": "active",
        "livemode": False,
        "metadata": {"order_id": str(order["id"])},
        "items": {
            "data": [{"quantity": 1, "price": {"id": "price_unit"}, "current_period_end": int(time.time()) + 86400}]
        },
        "latest_invoice": {"status": "paid", "currency": "brl", "amount_paid": 9900},
    }


@pytest.mark.parametrize(
    "invoice",
    [
        {"status": "paid", "currency": "brl", "amount_paid": 9900},
        None,
        {},
        {"status": "open"},
        {"status": "paid", "currency": "usd"},
        {"status": "paid", "currency": "brl", "amount_paid": 0},
    ],
)
async def test_only_confirmed_paid_period_can_grant_access(adapter, order, invoice):
    value = subscription(order)
    value["latest_invoice"] = invoice
    adapter.client.v1.subscriptions.retrieve_async.return_value = value
    result = await adapter.subscription("sub_local", order)
    assert (result["paid_until"] is not None) == bool(invoice and invoice.get("amount_paid") == 9900)


@pytest.mark.parametrize("change", ["mode", "metadata", "items", "price", "quantity"])
async def test_subscription_is_bound_to_order_price_and_quantity(adapter, order, change):
    value = subscription(order)
    if change == "mode":
        value["livemode"] = True
    if change == "metadata":
        value["metadata"] = {}
    if change == "items":
        value["items"]["data"] = []
    if change == "price":
        value["items"]["data"][0]["price"]["id"] = "price_other"
    if change == "quantity":
        value["items"]["data"][0]["quantity"] = 2
    adapter.client.v1.subscriptions.retrieve_async.return_value = value
    with pytest.raises(BillingError, match="SUBSCRIPTION_MISMATCH"):
        await adapter.subscription("sub_local", order)
