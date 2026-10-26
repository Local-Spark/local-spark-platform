"""Send durable material intents to Temporal with deterministic workflow IDs."""

import asyncio
import logging
from time import monotonic
from uuid import uuid4

import httpx

from app.adapters.material_media import MaterialStore
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.entrypoints.worker import connect_temporal
from app.services.audio_transcription import reconcile_stale_audio
from app.services.content_deliveries import reconcile_publications
from app.services.content_dispatch import dispatch_publications
from app.services.editorial_dispatch import dispatch_proposals
from app.services.editorial_proposals import reconcile_stale_proposals
from app.services.media_dispatch import dispatch_previews, reconcile_stale_previews
from app.services.media_retention import purge_expired_previews
from app.services.whatsapp_processing import dispatch_materials
from app.services.whatsapp_replies import dispatch_reply
from app.services.whatsapp_retention import purge_once

logger = logging.getLogger("meu_braco_direito.whatsapp_dispatcher")


async def run_dispatcher() -> None:
    configure_logging()
    settings = get_settings()
    if settings.correlator_database_url is None:
        logger.info("whatsapp.dispatcher.disabled")
        return
    database = Database(settings, correlator=True)
    owner = uuid4()
    try:
        client = await connect_temporal(settings)
        store = MaterialStore(settings)
        last_purge = 0.0
        async with httpx.AsyncClient() as http:
            while True:
                count = (
                    await dispatch_materials(database, client, settings, owner) if settings.meta_encryption_key else 0
                )
                proposals = await dispatch_proposals(database, client, settings, owner)
                previews = await dispatch_previews(database, client, settings, owner)
                publications = (
                    await dispatch_publications(database, client, settings, owner)
                    if settings.meta_encryption_key
                    else 0
                )
                if settings.meta_encryption_key:
                    await dispatch_reply(database, settings, http)
                if count:
                    logger.info("whatsapp.material_dispatched", extra={"count": count})
                if proposals:
                    logger.info("editorial.proposals_dispatched", extra={"count": proposals})
                if previews:
                    logger.info("media.previews_dispatched", extra={"count": previews})
                if publications:
                    logger.info("content.publications_dispatched", extra={"count": publications})
                if monotonic() - last_purge >= 10:
                    if settings.meta_encryption_key:
                        await reconcile_stale_audio(database)
                    await reconcile_stale_proposals(database)
                    await reconcile_stale_previews(database)
                    if settings.meta_encryption_key:
                        await reconcile_publications(database)
                    await purge_expired_previews(database, store, owner)
                    purged = await purge_once(database, store, owner) if settings.meta_encryption_key else 0
                    if purged:
                        logger.info("whatsapp.materials_purged", extra={"count": purged})
                    last_purge = monotonic()
                await asyncio.sleep(2)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(run_dispatcher())
