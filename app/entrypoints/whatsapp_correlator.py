"""Run the restricted WhatsApp correlator separately from the public API."""

import asyncio
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.services.whatsapp_routing import route_once

logger = logging.getLogger("meu_braco_direito.whatsapp_correlator")


async def run_correlator() -> None:
    configure_logging()
    settings = get_settings()
    if settings.correlator_database_url is None or settings.meta_encryption_key is None:
        logger.info("whatsapp.correlator.disabled")
        return
    database = Database(settings, correlator=True)
    try:
        while True:
            count = await route_once(database, settings)
            if count:
                logger.info("whatsapp.material_routed", extra={"count": count})
            await asyncio.sleep(2)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(run_correlator())
