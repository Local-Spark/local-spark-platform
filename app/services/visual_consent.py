"""Owner consent to send authorized visual references to the image provider."""

from uuid import UUID

from app.core.config import Settings
from app.db.session import Database
from app.services.visual_consent_gate import VisualConsentGate


class VisualConsentService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool | str]:
        state = await VisualConsentGate(self.database).status(tenant, business, actor)
        return {
            "accepted": state == "active",
            "state": state,
            "provider_enabled": self.settings.visual_ai_mode == "openai",
        }

    async def set(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool | str]:
        gate = VisualConsentGate(self.database)
        state = await (
            gate.enable(tenant, business, actor) if accepted else gate.request_withdrawal(tenant, business, actor)
        )
        return {
            "accepted": state == "active",
            "state": state,
            "provider_enabled": self.settings.visual_ai_mode == "openai",
        }
