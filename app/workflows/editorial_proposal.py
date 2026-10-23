"""One activity per proposal; paid attempts are fenced by the database ledger."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class EditorialProposalWorkflow:
    @workflow.run
    async def run(self, proposal_id: str) -> str:
        return cast(
            str,
            await workflow.execute_activity(
                "generate_editorial_proposal",
                proposal_id,
                result_type=str,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=1),
            ),
        )
