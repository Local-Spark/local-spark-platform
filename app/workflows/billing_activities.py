from typing import Any
from uuid import UUID

import stripe
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.billing import BillingError
from app.services.billing_processor import BillingProcessor


class BillingActivities:
    def __init__(self, processor: BillingProcessor) -> None:
        self.processor = processor

    async def execute(self, job_id: str, *, expire: bool) -> dict[str, Any]:
        try:
            result = await self.processor.run(UUID(job_id), expire=expire)
            # Hosted payment links stay in the restricted DB, not Temporal history.
            return {key: result[key] for key in ("status", "expires_at") if key in result}
        except BillingError as exc:
            retryable = exc.code in {"BILLING_BUSY", "BILLING_LEASE_LOST", "BILLING_UNAVAILABLE"}
            raise ApplicationError(
                exc.code, type="BillingTransient" if retryable else "BillingRejected", non_retryable=not retryable
            ) from None
        except stripe.StripeError as exc:
            permanent = isinstance(
                exc, (stripe.AuthenticationError, stripe.PermissionError, stripe.InvalidRequestError)
            )
            raise ApplicationError(
                "PROVIDER_REQUEST_FAILED",
                type="BillingRejected" if permanent else "ProviderTransient",
                non_retryable=permanent,
            ) from None
        except (ValueError, KeyError, TypeError):
            raise ApplicationError("INVALID_PROVIDER_RESPONSE", type="BillingRejected", non_retryable=True) from None

    @activity.defn
    async def process_billing_job(self, job_id: str) -> dict[str, Any]:
        return await self.execute(job_id, expire=False)

    @activity.defn
    async def expire_billing_checkout(self, job_id: str) -> dict[str, Any]:
        return await self.execute(job_id, expire=True)

    @activity.defn
    async def fail_billing_job(self, job_id: str) -> None:
        await self.processor.fail(UUID(job_id), "PROVIDER_RECONCILIATION_REQUIRED")
