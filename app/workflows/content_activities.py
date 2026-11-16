"""Temporal adapters delegate creation rules to the productive application service."""

from uuid import UUID

from temporalio import activity

from app.services.content_creation import ContentCreationService
from app.services.content_deliveries import publish_fake

# Keep the service identities available to existing callers of this module.
from app.services.content_deliveries import ContentDeliveryService as ContentDeliveryService
from app.services.editorial_proposals import EditorialProposalService as EditorialProposalService
from app.services.media_previews import MediaPreviewService as MediaPreviewService


class ContentCandidateActivities(ContentCreationService):
    @activity.defn
    async def request_message_creation(self, event_id: str) -> str:
        from app.services.message_creation_whatsapp import enqueue_message

        return await enqueue_message(self.settings, self.app_database, self.worker_database, event_id)

    @activity.defn
    async def request_candidate_proposal(self, event_id: str) -> str:
        return await super().request_candidate_proposal(event_id)

    @activity.defn
    async def candidate_proposal_state(self, proposal_id: str) -> str:
        return await super().candidate_proposal_state(proposal_id)

    @activity.defn
    async def request_candidate_preview(self, ids: list[str]) -> str:
        return await super().request_candidate_preview(ids)

    @activity.defn
    async def candidate_preview_state(self, preview_id: str) -> str:
        return await super().candidate_preview_state(preview_id)

    @activity.defn
    async def deliver_candidate_clarification(self, event_id: str) -> str:
        return await super().deliver_candidate_clarification(event_id)

    @activity.defn
    async def deliver_briefing_clarification(self, event_id: str) -> str:
        return await super().deliver_briefing_clarification(event_id)

    @activity.defn
    async def deliver_candidate_preview(self, ids: list[str]) -> str:
        return await super().deliver_candidate_preview(ids)

    @activity.defn
    async def publish_fake_content(self, ids: list[str | int]) -> str:
        return await publish_fake(
            self.settings, self.app_database, self.worker_database, UUID(str(ids[0])), int(ids[1])
        )
