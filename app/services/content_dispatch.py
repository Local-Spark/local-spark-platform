"""Dispatch explicitly approved local publications through Temporal."""

import logging
from datetime import timedelta
from uuid import UUID

from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core.config import Settings
from app.db.session import Database
from app.services.content_deliveries import claim_publications, finish_publication_dispatch

logger = logging.getLogger("meu_braco_direito.content_dispatch")


async def dispatch_publications(database: Database, client: Client, settings: Settings, owner: UUID) -> int:
    if settings.environment == "production":
        return 0
    claims = await claim_publications(database, owner)
    for delivery_id, fence in claims:
        accepted = True
        try:
            await client.start_workflow(
                "FakeContentPublicationWorkflow",
                args=[str(delivery_id), fence],
                id=f"fake-content-publish/{delivery_id}/{fence}",
                task_queue=settings.temporal_task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            accepted = False
            logger.warning("content.publication_dispatch_retry", extra={"delivery_id": str(delivery_id)})
        await finish_publication_dispatch(database, delivery_id, fence, accepted)
    return len(claims)
