import asyncio
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.entrypoints.worker import connect_temporal
from app.services.outbox import dispatch_once


async def run_relay() -> None:
    configure_logging()
    settings = get_settings()
    database = Database(settings, relay=True)
    owner_id = uuid4()
    try:
        client = await connect_temporal(settings)
        while True:
            await dispatch_once(database, client, settings, owner_id)
            await asyncio.sleep(2)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(run_relay())
