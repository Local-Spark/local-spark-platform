"""Stripe Checkout + canonical reads. Card data never crosses our API."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import stripe

from app.core.config import Settings
from app.services.billing import BillingError

EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
    "charge.refunded",
    "charge.dispute.created",
}


@dataclass(frozen=True)
class Reference:
    order_id: UUID | None = None
    subscription_id: str | None = None
    customer_id: str | None = None
    hold: bool = False


def verify_webhook(settings: Settings, body: bytes, signature: str) -> dict[str, str] | None:
    if settings.billing_mode == "disabled" or settings.stripe_webhook_secret is None:
        raise BillingError("BILLING_UNAVAILABLE", 503)
    try:
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            body, signature, settings.stripe_webhook_secret.get_secret_value(), tolerance=300
        )
        if event["livemode"] is not (settings.billing_mode == "live"):
            raise ValueError("Wrong mode")
        event_id, event_type, object_id = event["id"], event["type"], event["data"]["object"]["id"]
        if not all(isinstance(value, str) and 0 < len(value) <= 128 for value in (event_id, event_type, object_id)):
            raise ValueError("Invalid event references")
    except (ValueError, KeyError, TypeError, stripe.SignatureVerificationError) as exc:
        raise BillingError("INVALID_WEBHOOK", 400) from exc
    if event_type not in EVENTS:
        return None
    return {"event_id": event_id, "event_type": event_type, "object_id": object_id}


class StripeBilling:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http = stripe.HTTPXClient(timeout=10)
        self.client = stripe.StripeClient(
            settings.stripe_secret_key.get_secret_value() if settings.stripe_secret_key else "sk_test_disabled",
            http_client=self.http,
            max_network_retries=2,
        )

    async def close(self) -> None:
        await self.http.close_async()  # type: ignore[no-untyped-call]

    async def checkout(self, order: dict[str, Any]) -> dict[str, Any]:
        if order["session_id"]:
            response = await self.client.v1.checkout.sessions.retrieve_async(order["session_id"])
        else:
            price = await self.client.v1.prices.retrieve_async(order["price_id"])
            recurring = price.get("recurring")
            if (
                not price["active"]
                or price["livemode"] != order["livemode"]
                or price["currency"] != "brl"
                or price["unit_amount"] != order["amount_minor"]
                or not recurring
                or recurring["interval"] != "month"
                or recurring["interval_count"] != 1
            ):
                raise BillingError("PRICE_MISMATCH", 422)
            response = await self.client.v1.checkout.sessions.create_async(
                {
                    "mode": "subscription",
                    "payment_method_types": ["card"],
                    "locale": "pt-BR",
                    "line_items": [{"price": order["price_id"], "quantity": 1}],
                    "client_reference_id": str(order["id"]),
                    "metadata": {"order_id": str(order["id"])},
                    "subscription_data": {"metadata": {"order_id": str(order["id"])}},
                    "success_url": f"{order['origin']}/app/billing?organization={order['tenant_id']}&return=success",
                    "cancel_url": f"{order['origin']}/app/billing?organization={order['tenant_id']}&return=cancel",
                    "expires_at": int(order["expires_at"].timestamp()),
                },
                options={"idempotency_key": f"local-spark-checkout/{order['id']}"},
            )
        result = dict(response)
        if (
            result["livemode"] != order["livemode"]
            or result["client_reference_id"] != str(order["id"])
            or result["metadata"].get("order_id") != str(order["id"])
        ):
            raise BillingError("CHECKOUT_MISMATCH", 422)
        return result

    async def reference(self, event_type: str, object_id: str) -> Reference:
        record: Any
        if event_type.startswith("charge."):
            if event_type == "charge.dispute.created":
                dispute = await self.client.v1.disputes.retrieve_async(object_id)
                object_id = dispute["charge"]
            charge = await self.client.v1.charges.retrieve_async(object_id)
            return Reference(customer_id=charge.get("customer"), hold=True)
        if event_type.startswith("checkout."):
            record = await self.client.v1.checkout.sessions.retrieve_async(object_id)
            subscription = record.get("subscription")
        elif event_type.startswith("invoice."):
            invoice = await self.client.v1.invoices.retrieve_async(object_id)
            parent = invoice.get("parent") or {}
            subscription = parent.get("subscription_details", {}).get("subscription")
            if not subscription:
                return Reference()
            record = await self.client.v1.subscriptions.retrieve_async(subscription)
        else:
            subscription = object_id
            record = await self.client.v1.subscriptions.retrieve_async(subscription)
        order = record.get("metadata", {}).get("order_id")
        return Reference(order_id=UUID(order) if order else None, subscription_id=subscription)

    async def subscription(self, subscription_id: str, order: dict[str, Any]) -> dict[str, Any]:
        result = await self.client.v1.subscriptions.retrieve_async(subscription_id, {"expand": ["latest_invoice"]})
        items = result["items"]["data"]
        if (
            result["livemode"] != order["livemode"]
            or result["metadata"].get("order_id") != str(order["id"])
            or len(items) != 1
            or items[0]["price"]["id"] != order["price_id"]
            or items[0]["quantity"] != 1
        ):
            raise BillingError("SUBSCRIPTION_MISMATCH", 422)
        invoice = result.get("latest_invoice") or {}
        paid = (
            invoice.get("status") == "paid"
            and invoice.get("currency") == "brl"
            and invoice.get("amount_paid", 0) >= order["amount_minor"]
        )
        return {
            "status": result["status"],
            "subscription_id": result["id"],
            "customer_id": result["customer"],
            "paid_until": datetime.fromtimestamp(items[0]["current_period_end"], UTC) if paid else None,
        }
