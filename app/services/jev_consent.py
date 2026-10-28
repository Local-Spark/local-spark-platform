"""Owner approval specifically for sharing message text with TypeSafe."""

from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.service_agreement_scope import accepted_agreement_sql, service_agreement_accepted
from app.services.whatsapp_materials import WhatsAppMaterialsService


class JevConsentService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM intent_jev_consents
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
                {"tenant": tenant, "business": business},
            )
            return {"accepted": bool(accepted), "provider_enabled": self.settings.intent_ai_mode == "jev"}

    async def set(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        from app.services.visual_consent_gate import VisualConsentGate

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            params = {"tenant": tenant, "business": business, "actor": actor, "accepted": accepted}
            changed = await session.scalar(
                text("""INSERT INTO intent_jev_consents(tenant_id,business_id,actor_id,revoked_at)
                  VALUES(:tenant,:business,:actor,CASE WHEN :accepted THEN NULL ELSE now() END)
                  ON CONFLICT(tenant_id,business_id) DO UPDATE SET actor_id=:actor,
                    accepted_at=CASE WHEN :accepted THEN now() ELSE intent_jev_consents.accepted_at END,
                    revoked_at=CASE WHEN :accepted THEN NULL ELSE now() END
                  WHERE (intent_jev_consents.revoked_at IS NULL) <> :accepted RETURNING 1"""),
                params,
            )
            if changed:
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,:action,:business)"""),
                    {
                        **params,
                        "operation": uuid4(),
                        "action": "intent.jev_accepted" if accepted else "intent.jev_revoked",
                    },
                )
            return {"accepted": accepted, "provider_enabled": self.settings.intent_ai_mode == "jev"}
