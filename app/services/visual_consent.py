"""Owner consent to send authorized visual references to the image provider."""

from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.whatsapp_materials import WhatsAppMaterialsService


class VisualConsentService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM visual_ai_consents
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            return {"accepted": bool(accepted), "provider_enabled": self.settings.visual_ai_mode == "openai"}

    async def set(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            params = {"tenant": tenant, "business": business, "actor": actor}
            if accepted:
                changed = await session.scalar(
                    text("""INSERT INTO visual_ai_consents(tenant_id,business_id,actor_id)
                      VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                        actor_id=:actor,accepted_at=now(),revoked_at=NULL
                      WHERE visual_ai_consents.revoked_at IS NOT NULL RETURNING 1"""),
                    params,
                )
            else:
                changed = await session.scalar(
                    text("""UPDATE visual_ai_consents SET actor_id=:actor,revoked_at=now()
                      WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL RETURNING 1"""),
                    params,
                )
            if changed:
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,:action,:business)"""),
                    {
                        **params,
                        "operation": uuid4(),
                        "action": "visual.ai_accepted" if accepted else "visual.ai_revoked",
                    },
                )
            return {"accepted": accepted, "provider_enabled": self.settings.visual_ai_mode == "openai"}
