"""Dedicated Temporal worker and narrow outbox relay for private rehearsals."""

import asyncio
from uuid import uuid4

from temporalio.worker import Worker

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.entrypoints.worker import connect_temporal
from app.services.outbox import dispatch_once
from app.workflows.creation_lab_activities import CreationLabActivities, CreationLabProductionActivities
from app.workflows.creation_lab_production import CreationLabProductionWorkflow
from app.workflows.creation_lab_retention import CreationLabRetentionWorkflow


async def run() -> None:
    configure_logging()
    settings = get_settings()
    if not settings.relay_database_url or settings.creation_lab_task_queue == settings.temporal_task_queue:
        raise RuntimeError("CREATION_LAB_ISOLATED_RUNTIME_REQUIRED")
    database, relay = Database(settings), Database(settings, relay=True)
    try:
        client = await connect_temporal(settings)
        production = CreationLabProductionActivities(settings, database)
        worker = Worker(
            client,
            task_queue=settings.creation_lab_task_queue,
            workflows=[CreationLabProductionWorkflow, CreationLabRetentionWorkflow],
            activities=[production.run, production.fail, CreationLabActivities(database).expire_trace],
            max_concurrent_activities=2,
        )
        owner = uuid4()
        async with worker:
            while True:
                await dispatch_once(relay, client, settings, owner, lab_only=True)
                await asyncio.sleep(2)
    finally:
        await relay.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(run())
