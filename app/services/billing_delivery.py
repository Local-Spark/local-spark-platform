import logging
from datetime import timedelta

from sqlalchemy import text
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core.config import Settings
from app.db.session import Database

logger = logging.getLogger("local_spark.billing")


async def dispatch_billing(database: Database, client: Client, settings: Settings) -> int:
    if settings.billing_mode == "disabled":
        return 0
    async with database.sessions() as db, db.begin():
        jobs = (
            (
                await db.execute(
                    text("""WITH candidates AS (
          SELECT id FROM billing_jobs WHERE livemode=:live AND (state='pending'
            OR (state='leased' AND lease_until<=clock_timestamp()))
          ORDER BY created_at,id LIMIT 5 FOR UPDATE SKIP LOCKED)
          UPDATE billing_jobs j SET state='leased',lease_until=clock_timestamp()+interval '90 seconds',
            fencing_token=j.fencing_token+1,attempts=j.attempts+1 FROM candidates c WHERE j.id=c.id
          RETURNING j.id,j.fencing_token,j.attempts"""),
                    {"live": settings.billing_mode == "live"},
                )
            )
            .mappings()
            .all()
        )
    for job in jobs:
        state = "dispatched"
        try:
            await client.start_workflow(
                "BillingWorkflow",
                str(job["id"]),
                id=f"billing/{job['id']}",
                task_queue=f"{settings.temporal_task_queue}-billing",
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            state = "pending" if job["attempts"] < 8 else "failed"
            logger.warning(
                "billing.dispatch.retry", extra={"event_id": str(job["id"]), "error_code": "TEMPORAL_UNAVAILABLE"}
            )
        async with database.sessions() as db, db.begin():
            await db.execute(
                text("""UPDATE billing_jobs SET state=:state,lease_until=NULL
              WHERE id=:id AND fencing_token=:fencing_token AND state='leased' AND lease_until>clock_timestamp()"""),
                {**job, "state": state},
            )
    return len(jobs)
