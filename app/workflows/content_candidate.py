"""WhatsApp material to private candidate, with provider IO in activities only."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class ContentCandidateWorkflow:
    @workflow.run
    async def run(self, event_id: str) -> str:
        proposal_id = await workflow.execute_activity(
            "request_candidate_proposal",
            event_id,
            result_type=str,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        if proposal_id in {"skipped", "briefing_needs_clarification", "briefing_unavailable"}:
            return cast(str, proposal_id)
        for _ in range(60):
            state = await workflow.execute_activity(
                "candidate_proposal_state",
                proposal_id,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=20),
            )
            if state == "completed":
                break
            if state == "needs_fact":
                return cast(
                    str,
                    await workflow.execute_activity(
                        "deliver_candidate_clarification",
                        event_id,
                        result_type=str,
                        start_to_close_timeout=timedelta(seconds=30),
                    ),
                )
            if state == "failed":
                return "proposal_failed"
            await workflow.sleep(5)
        else:
            return "proposal_timeout"
        preview_id = await workflow.execute_activity(
            "request_candidate_preview",
            [event_id, proposal_id],
            result_type=str,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        if preview_id == "blocked":
            return "preview_blocked"
        for _ in range(60):
            state = await workflow.execute_activity(
                "candidate_preview_state",
                preview_id,
                result_type=str,
                start_to_close_timeout=timedelta(seconds=20),
            )
            if state == "completed":
                break
            if state == "failed":
                return "preview_failed"
            await workflow.sleep(5)
        else:
            return "preview_timeout"
        return cast(
            str,
            await workflow.execute_activity(
                "deliver_candidate_preview",
                [event_id, preview_id],
                result_type=str,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            ),
        )
