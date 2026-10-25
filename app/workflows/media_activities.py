"""Temporal activity adapter for private static previews."""

from uuid import UUID

from temporalio import activity

from app.services.media_previews import MediaPreviewService


class MediaPreviewActivities:
    def __init__(self, service: MediaPreviewService) -> None:
        self.service = service

    @activity.defn
    async def render_static_preview(self, preview_id: str, fence: int) -> str:
        return await self.service.render(UUID(preview_id), fence)
