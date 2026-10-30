"""Fenced dispatch preserving legacy histories and one-shot visual effects."""

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
from app.services.auth import AuthError
from app.services.editorial_proposals import _audit
from app.services.visual_execution import require_visual_execution

logger = logging.getLogger("meu_braco_direito.media_dispatch")


@dataclass(frozen=True)
class PreviewClaim:
    id: UUID
    owner: UUID
    fence: int
    attempt: int
    generation_mode: str = "local"


async def claim_previews(
    database: Database, owner: UUID, limit: int = 10, *, visual_enabled: bool = False
) -> list[PreviewClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
                      SELECT id FROM media_previews WHERE
                        (state='pending' OR (state='rendering' AND dispatch_lease_until<now()
                          AND generation_mode<>'visual_ai'))
                        AND (generation_mode<>'visual_ai' OR :visual_enabled)
                        AND (generation_mode<>'local' OR mime_type='video/mp4')
                        AND (generation_mode NOT IN ('visual_fake','visual_ai') OR visual_recipe='full_piece_v1')
                        AND attempts<3 AND expires_at>now()
                      ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE media_previews p SET state='rendering',attempts=p.attempts+1,
                        dispatch_owner=:owner,dispatch_lease_until=now()+CASE
                          WHEN p.generation_mode='visual_ai' THEN interval '12 minutes'
                          ELSE interval '3 minutes' END,
                        dispatch_fence=p.dispatch_fence+1,updated_at=now()
                      FROM due WHERE p.id=due.id
                      RETURNING p.id,p.dispatch_fence,p.attempts,p.generation_mode"""),
                    {"owner": owner, "limit": limit, "visual_enabled": visual_enabled},
                )
            )
            .mappings()
            .all()
        )
        return [
            PreviewClaim(row["id"], owner, row["dispatch_fence"], row["attempts"], row["generation_mode"])
            for row in rows
        ]


async def finish_preview_dispatch(database: Database, claim: PreviewClaim, accepted: bool) -> None:
    if accepted or claim.generation_mode == "visual_ai":
        # A failed start acknowledgement can still mean Temporal accepted the
        # execution. Keep its exact ID/fence and never enqueue another effect.
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
    try:
        require_visual_execution(settings)
        visual_enabled = True
    except AuthError:
        visual_enabled = False
    claims = await claim_previews(database, owner, visual_enabled=visual_enabled)
    for claim in claims:
        accepted = True
        try:
            await client.start_workflow(
                "VisualGenerationWorkflow" if claim.generation_mode == "visual_ai" else "StaticPreviewWorkflow",
                args=[str(claim.id), claim.fence],
                id=f"visual-preview/{claim.id}"
                if claim.generation_mode == "visual_ai"
                else f"media-preview/{claim.id}/{claim.attempt}",
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
                    text("""UPDATE media_previews SET state='failed',error_code=CASE
                      WHEN generation_mode='visual_ai' THEN 'VISUAL_OUTCOME_UNCERTAIN'
                      ELSE 'PREVIEW_WORKER_TIMEOUT' END,
                      dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                      WHERE state='rendering' AND (attempts>=3 OR generation_mode='visual_ai')
                        AND dispatch_lease_until<now()
                      RETURNING *"""),
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await _audit(session, row, "media.preview_failed")
        return len(rows)
