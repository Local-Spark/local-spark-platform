"""Editorial activity adapter for Temporal."""

from uuid import UUID

from temporalio import activity

from app.services.editorial_proposals import EditorialProposalService


class EditorialActivities:
    def __init__(self, service: EditorialProposalService) -> None:
        self.service = service

    @activity.defn
    async def generate_editorial_proposal(self, proposal_id: str) -> str:
        return await self.service.run(UUID(proposal_id))
