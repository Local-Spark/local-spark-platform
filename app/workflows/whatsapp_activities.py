"""Short material activities with a restricted DB login."""

from uuid import UUID

from temporalio import activity

from app.services.whatsapp_processing import MaterialProcessor


class WhatsAppMaterialActivities:
    def __init__(self, processor: MaterialProcessor) -> None:
        self.processor = processor

    @activity.defn
    async def process_whatsapp_material(self, event_id: str) -> str:
        return await self.processor.process(UUID(event_id))

    @activity.defn
    async def fail_whatsapp_material(self, event_id: str) -> str:
        return await self.processor.fail(UUID(event_id))
