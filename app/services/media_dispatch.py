"""Fenced, bounded dispatch of static preview requests to Temporal."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import text
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core.config import Settings
from app.db.session import Database
from app.services.editorial_proposals import _audit

logger = logging.getLogger("meu_braco_direito.media_dispatch")


@dataclass(frozen=True)
class PreviewClaim:
    id: UUID
    owner: UUID
    fence: int
    attempt: int


async def claim_previews(database: Database, owner: UUID, limit: int = 10) -> list[PreviewClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
                      SELECT id FROM media_previews WHERE
                        (state='pending' OR (state='rendering' AND dispatch_lease_until<now()))
                        AND attempts<3 AND expires_at>now()
                      ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE media_previews p SET state='rendering',attempts=p.attempts+1,
                        dispatch_owner=:owner,dispatch_lease_until=now()+interval '3 minutes',
                        dispatch_fence=p.dispatch_fence+1,updated_at=now()
                      FROM due WHERE p.id=due.id RETURNING p.id,p.dispatch_fence,p.attempts"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [PreviewClaim(row["id"], owner, row["dispatch_fence"], row["attempts"]) for row in rows]


async def finish_preview_dispatch(database: Database, claim: PreviewClaim, accepted: bool) -> None:
    if accepted:
        return
    async with database.sessions() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("""UPDATE media_previews SET
                      state=CASE WHEN attempts<3 THEN 'pending' ELSE 'failed' END,
                      error_code='TEMPORAL_UNAVAILABLE',dispatch_owner=NULL,
                      dispatch_lease_until=NULL,updated_at=now()
                      WHERE id=:id AND state='rendering' AND dispatch_owner=:owner
                        AND dispatch_fence=:fence RETURNING *"""),
                    {"id": claim.id, "owner": claim.owner, "fence": claim.fence},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is not None and row["state"] == "failed":
            await _audit(session, row, "media.preview_failed")


async def dispatch_previews(database: Database, client: Client, settings: Settings, owner: UUID) -> int:
    claims = await claim_previews(database, owner)
    for claim in claims:
        accepted = True
        try:
            await client.start_workflow(
                "StaticPreviewWorkflow",
                args=[str(claim.id), claim.fence],
                id=f"media-preview/{claim.id}/{claim.attempt}",
                task_queue=settings.temporal_task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            accepted = False
            logger.warning("media.preview_dispatch_retry", extra={"preview_id": str(claim.id)})
        await finish_preview_dispatch(database, claim, accepted)
    return len(claims)


async def reconcile_stale_previews(database: Database) -> int:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""UPDATE media_previews SET state='failed',error_code='PREVIEW_WORKER_TIMEOUT',
                      dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                      WHERE state='rendering' AND attempts>=3 AND dispatch_lease_until<now()
                      RETURNING *"""),
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await _audit(session, row, "media.preview_failed")
        return len(rows)
