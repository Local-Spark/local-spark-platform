import logging
from datetime import timedelta

from sqlalchemy import text
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from app.core.config import Settings
from app.db.session import Database

logger = logging.getLogger("local_spark.billing")


async def enqueue_open_checkout_reconciliation(database: Database, settings: Settings) -> int:
    """Schedule bounded canonical reads for unresolved current checkouts.

    The time bucket deduplicates concurrent workers. A completed payment is still
    activated only by the processor's read from Stripe, never by this scheduler.
    """
    if settings.billing_mode == "disabled":
        return 0
    async with database.sessions() as db, db.begin():
        result = await db.execute(
            text("""WITH current_bucket AS (
              SELECT floor(extract(epoch FROM clock_timestamp()) / 300)::bigint AS value
            ), candidates AS (
              SELECT c.id,c.tenant_id,c.session_id,c.livemode,b.value,
                concat('poll:',c.id,':',b.value) AS dedupe_key
              FROM billing_checkouts c
              JOIN billing_accounts a ON a.checkout_id=c.id AND a.tenant_id=c.tenant_id
                AND a.livemode=c.livemode
              JOIN billing_jobs original ON original.id=c.id
              CROSS JOIN current_bucket b
              WHERE c.livemode=:live AND c.status='open' AND c.session_id IS NOT NULL
                AND c.expires_at>clock_timestamp()
                AND original.created_at<=clock_timestamp()-interval '30 seconds'
                AND NOT (a.status='active' AND NOT a.blocked AND a.paid_until>clock_timestamp())
                AND NOT EXISTS (
                  SELECT 1 FROM billing_jobs prior WHERE prior.livemode=c.livemode
                    AND prior.dedupe_key=concat('poll:',c.id,':',b.value)
                )
              ORDER BY original.created_at,c.id LIMIT 25 FOR UPDATE OF c SKIP LOCKED
            )
            INSERT INTO billing_jobs(id,tenant_id,livemode,kind,dedupe_key,event_type,object_id)
            SELECT gen_random_uuid(),tenant_id,livemode,'reconcile',dedupe_key,
              'checkout.session.completed',session_id FROM candidates
            ON CONFLICT(livemode,dedupe_key) DO NOTHING RETURNING id"""),
            {"live": settings.billing_mode == "live"},
        )
        return len(result.all())


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
