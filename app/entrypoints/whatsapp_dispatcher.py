"""Send durable material intents to Temporal with deterministic workflow IDs."""

import asyncio
import logging
from time import monotonic
from uuid import uuid4

from app.adapters.material_media import MaterialStore
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.entrypoints.worker import connect_temporal
from app.services.whatsapp_processing import dispatch_materials
from app.services.whatsapp_retention import purge_once

logger = logging.getLogger("meu_braco_direito.whatsapp_dispatcher")


async def run_dispatcher() -> None:
    configure_logging()
    settings = get_settings()
    if settings.correlator_database_url is None or settings.meta_encryption_key is None:
        logger.info("whatsapp.dispatcher.disabled")
        return
    database = Database(settings, correlator=True)
    owner = uuid4()
    try:
        client = await connect_temporal(settings)
        store = MaterialStore(settings)
        last_purge = 0.0
        while True:
            count = await dispatch_materials(database, client, settings, owner)
            if count:
                logger.info("whatsapp.material_dispatched", extra={"count": count})
            if monotonic() - last_purge >= 10:
                purged = await purge_once(database, store, owner)
                if purged:
                    logger.info("whatsapp.materials_purged", extra={"count": purged})
                last_purge = monotonic()
            await asyncio.sleep(2)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(run_dispatcher())
