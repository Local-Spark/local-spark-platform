"""Deterministic material workflow; provider and database IO remain in activities."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy

from app.workflows.content_candidate import ContentCandidateWorkflow


@workflow.defn
class WhatsAppMaterialWorkflow:
    @workflow.run
    async def run(self, event_id: str) -> str:
        try:
            result = cast(
                str,
                await workflow.execute_activity(
                    "process_whatsapp_material",
                    event_id,
                    result_type=str,
                    start_to_close_timeout=timedelta(minutes=3),
                    schedule_to_close_timeout=timedelta(minutes=12),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=4,
                        non_retryable_error_types=["MaterialInvalid"],
                    ),
                ),
            )
            if result == "processed":
                try:
                    await workflow.execute_activity(
                        "transcribe_whatsapp_audio",
                        event_id,
                        result_type=str,
                        start_to_close_timeout=timedelta(minutes=3),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )
                except Exception:
                    pass  # The submitted state prevents a second paid call.
                try:
                    await workflow.execute_child_workflow(
                        ContentCandidateWorkflow.run,
                        event_id,
                        id=f"content-candidate/{event_id}",
                        task_queue=workflow.info().task_queue,
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )
                except Exception:
                    pass  # The failed child remains visible in Temporal; stored material is not rolled back.
            return result
        except Exception:
            return cast(
                str,
                await workflow.execute_activity(
                    "fail_whatsapp_material",
                    event_id,
                    result_type=str,
                    start_to_close_timeout=timedelta(seconds=30),
                    schedule_to_close_timeout=timedelta(minutes=3),
                ),
            )
