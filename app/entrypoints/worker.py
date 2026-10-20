import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.workflows.activities import FoundationActivities
from app.workflows.foundation import BusinessCreatedWorkflow


async def connect_temporal(settings: Settings) -> Client:
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        tls=settings.temporal_tls,
        api_key=settings.temporal_api_key.get_secret_value() if settings.temporal_api_key else None,
    )


async def run_worker() -> None:
    configure_logging()
    settings = get_settings()
    database = Database(settings)
    try:
        client = await connect_temporal(settings)
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[BusinessCreatedWorkflow],
            activities=[FoundationActivities(database).record_business_created],
            max_concurrent_activities=10,
        )
        await worker.run()
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
