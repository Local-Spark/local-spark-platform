"""Lease proposal intents and start deterministic Temporal workflows."""

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

logger = logging.getLogger("meu_braco_direito.editorial_dispatch")


@dataclass(frozen=True)
class ProposalClaim:
    id: UUID
    owner: UUID
    fence: int


async def claim_proposals(database: Database, owner: UUID, limit: int = 10) -> list[ProposalClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
          SELECT id FROM editorial_proposals WHERE state='pending' OR
            (state='dispatching' AND dispatch_lease_until<now())
          ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
          UPDATE editorial_proposals p SET state='dispatching',dispatch_owner=:owner,
            dispatch_lease_until=now()+interval '60 seconds',dispatch_fence=p.dispatch_fence+1,
            updated_at=now() FROM due WHERE p.id=due.id
          RETURNING p.id,p.dispatch_fence"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  SELECT tenant_id,actor_id,id,'editorial.proposal_dispatching',business_id
                  FROM editorial_proposals WHERE id=:id
                  ON CONFLICT DO NOTHING"""),
                {"id": row["id"]},
            )
        return [ProposalClaim(row["id"], owner, row["dispatch_fence"]) for row in rows]


async def finish_proposal_dispatch(database: Database, claim: ProposalClaim, accepted: bool) -> None:
    async with database.sessions() as session, session.begin():
        await session.execute(
            text("""UPDATE editorial_proposals SET
          state=CASE WHEN :accepted THEN 'dispatching' ELSE 'pending' END,
          dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
          WHERE id=:id AND dispatch_owner=:owner AND dispatch_fence=:fence AND state='dispatching'"""),
            {"id": claim.id, "owner": claim.owner, "fence": claim.fence, "accepted": accepted},
        )


async def dispatch_proposals(database: Database, client: Client, settings: Settings, owner: UUID) -> int:
    claims = await claim_proposals(database, owner)
    for claim in claims:
        accepted = True
        try:
            await client.start_workflow(
                "EditorialProposalWorkflow",
                str(claim.id),
                id=f"editorial-proposal/{claim.id}",
                task_queue=settings.temporal_task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            accepted = False
            logger.warning("editorial.dispatch_retry", extra={"proposal_id": str(claim.id)})
        await finish_proposal_dispatch(database, claim, accepted)
    return len(claims)
