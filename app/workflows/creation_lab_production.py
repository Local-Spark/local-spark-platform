"""Private entrypoint; one attempt per durable stage, no content in Temporal history."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.contracts import BusinessEvent


@workflow.defn
class CreationLabProductionWorkflow:
    @workflow.run
    async def run(self, event: BusinessEvent) -> str:
        try:
            return await workflow.execute_activity(
                "run_creation_lab_production",
                event,
                result_type=str,
                schedule_to_start_timeout=timedelta(minutes=5),
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception:
            await workflow.execute_activity(
                "fail_creation_lab_production",
                event,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )
            raise
