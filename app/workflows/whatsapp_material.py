"""Deterministic material workflow; provider and database IO remain in activities."""

from datetime import timedelta
from typing import cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class WhatsAppMaterialWorkflow:
    @workflow.run
    async def run(self, event_id: str) -> str:
        try:
            return cast(
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
