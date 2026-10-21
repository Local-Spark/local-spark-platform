import asyncio
import logging

from temporalio.worker import Worker

from app.adapters.stripe_billing import StripeBilling
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.entrypoints.worker import connect_temporal
from app.services.billing_delivery import dispatch_billing
from app.services.billing_processor import BillingProcessor
from app.workflows.billing import BillingWorkflow
from app.workflows.billing_activities import BillingActivities


async def main() -> None:
    configure_logging()
    settings = get_settings()
    database = Database(settings, billing=True)
    provider = StripeBilling(settings)
    activities = BillingActivities(BillingProcessor(settings, database, provider))
    try:
        if settings.billing_mode == "disabled":
            logging.getLogger("local_spark.billing").info("billing.disabled")
            while True:
                await asyncio.sleep(30)
        client = await connect_temporal(settings)
        async with Worker(
            client,
            task_queue=f"{settings.temporal_task_queue}-billing",
            workflows=[BillingWorkflow],
            activities=[
                activities.process_billing_job,
                activities.expire_billing_checkout,
                activities.fail_billing_job,
            ],
            max_concurrent_activities=5,
            max_task_queue_activities_per_second=5,
        ):
            while True:
                await dispatch_billing(database, client, settings)
                await asyncio.sleep(2)
    finally:
        await provider.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
