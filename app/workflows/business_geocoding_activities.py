"""Charged address resolution with sanitized failures and identifier-only results."""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.business_geocoding import BusinessGeocodingRunner
from app.workflows.contracts import BusinessEvent


class BusinessGeocodingActivities:
    def __init__(self, runner: BusinessGeocodingRunner):
        self.runner = runner

    @activity.defn(name="resolve_business_address")
    async def resolve(self, event: BusinessEvent) -> str:
        try:
            return await self.runner.run(event)
        except Exception:
            raise ApplicationError("Address resolution unavailable", type="BusinessGeocodingUnavailable") from None
