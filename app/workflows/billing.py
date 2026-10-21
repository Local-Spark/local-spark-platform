from datetime import datetime, timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError


@workflow.defn
class BillingWorkflow:
    @workflow.run
    async def run(self, job_id: str) -> str:
        options: dict[str, Any] = {
            "start_to_close_timeout": timedelta(seconds=60),
            "schedule_to_close_timeout": timedelta(hours=1),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=8,
                non_retryable_error_types=["BillingRejected"],
            ),
        }
        try:
            result = await workflow.execute_activity("process_billing_job", job_id, result_type=dict, **options)
            if result.get("status") == "open":
                expires = datetime.fromisoformat(result["expires_at"])
                await workflow.sleep(max(timedelta(0), expires - workflow.now()))
                await workflow.execute_activity("expire_billing_checkout", job_id, **options)
        except ActivityError:
            await workflow.execute_activity("fail_billing_job", job_id, start_to_close_timeout=timedelta(seconds=15))
            return "failed"
        return "completed"
