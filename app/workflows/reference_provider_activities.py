"""The discovery activity loads all private context after entering the worker."""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.reference_provider_execution import ReferenceProviderExecution
from app.workflows.contracts import BusinessEvent


class ReferenceProviderActivities:
    def __init__(self, executor: ReferenceProviderExecution) -> None:
        self.executor = executor

    @activity.defn
    async def execute_reference_provider_discovery(self, event: BusinessEvent) -> str:
        try:
            return await self.executor.run(event)
        except Exception:
            raise ApplicationError("Reference discovery unavailable", type="ReferenceDiscoveryUnavailable") from None
