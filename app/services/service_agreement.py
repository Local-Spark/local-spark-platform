"""Read-only, tenant-scoped verification of the locally published AI notice."""

import hashlib
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService

SERVICE_AGREEMENT_VERSION = "2026-10-ai-v1"
SERVICE_AGREEMENT_NOTICE = (
    "Ao aceitar, você autoriza o Meu Braço Direito a receber e processar mensagens e materiais do seu negócio "
    "pelo WhatsApp, transcrever áudios e usar inteligência artificial e fornecedores para interpretar pedidos "
    "e criar textos e imagens. A criação de imagens com IA ainda está em preparação. A conexão do canal, "
    "os direitos sobre "
    "os materiais, a conexão de redes sociais, a publicação e o uso de voz ou avatar continuam sujeitos "
    "às respectivas etapas e autorizações. Esta versão é destinada à validação local e não é um documento "
    "comercial definitivo."
)
SERVICE_AGREEMENT_HASH = hashlib.sha256(SERVICE_AGREEMENT_NOTICE.encode("utf-8")).hexdigest()


async def service_agreement_allowed(
    session: AsyncSession, settings: Settings, tenant: UUID, business: UUID, *, worker: bool = False
) -> bool:
    """Check the agreement in the tenant-local transaction, never switching actors."""
    if not settings.service_agreement_required:
        return settings.environment != "production"
    if worker:
        current = await session.scalar(text("SELECT current_setting('app.tenant_id',true)"))
        if current and current != str(tenant):
            raise AuthError("SERVICE_AGREEMENT_TENANT_MISMATCH", 403)
        if not current:
            await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(tenant)})
    return bool(
        await session.scalar(
            text("""SELECT 1 FROM service_agreement_acceptances WHERE tenant_id=:tenant AND business_id=:business
              AND version=:version AND notice_hash=:hash"""),
            {
                "tenant": tenant,
                "business": business,
                "version": SERVICE_AGREEMENT_VERSION,
                "hash": SERVICE_AGREEMENT_HASH,
            },
        )
    )


class ServiceAgreementService:
    """Expose the exact notice and existing state; activation is not yet available."""

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, Any]:
        from app.services.editorial_proposals import _access_sql

        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            params = {"tenant": tenant, "business": business, "version": SERVICE_AGREEMENT_VERSION}
            agreement = (
                (
                    await session.execute(
                        text("""SELECT notice_hash,accepted_at FROM service_agreement_acceptances
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if agreement is not None and agreement["notice_hash"] != SERVICE_AGREEMENT_HASH:
                raise AuthError("SERVICE_AGREEMENT_VERSION_CONFLICT", 409)
            states = (
                (
                    await session.execute(
                        text("""SELECT
              (SELECT CASE WHEN revoked_at IS NULL THEN 'active' ELSE 'revoked' END FROM editorial_ai_consents
                WHERE tenant_id=:tenant AND business_id=:business) AS editorial,
              (SELECT CASE WHEN revoked_at IS NULL THEN 'active' ELSE 'revoked' END FROM intent_jev_consents
                WHERE tenant_id=:tenant AND business_id=:business) AS jev,
              (SELECT CASE WHEN revoked_at IS NULL THEN 'active' ELSE 'revoked' END FROM visual_ai_consents
                WHERE tenant_id=:tenant AND business_id=:business) AS visual,
              (SELECT CASE WHEN revoked_at IS NULL THEN 'active' ELSE 'revoked' END FROM whatsapp_processing_consents
                WHERE tenant_id=:tenant AND business_id=:business) AS whatsapp,
              (SELECT CASE WHEN revoked_at IS NULL AND audio_transcription_accepted_at IS NOT NULL
                THEN 'active' ELSE 'inactive' END FROM whatsapp_processing_consents
                WHERE tenant_id=:tenant AND business_id=:business) AS audio,
              (SELECT state FROM visual_consent_gates WHERE tenant_id=:tenant AND business_id=:business) AS visual_gate
            """),
                        params,
                    )
                )
                .mappings()
                .one()
            )
            capabilities = {
                name: states[name] or "missing" for name in ("editorial", "jev", "visual", "whatsapp", "audio")
            }
            if states["visual_gate"] == "revocation_pending":
                capabilities["visual"] = "revocation_pending"
            accepted = agreement is not None
            return {
                "version": SERVICE_AGREEMENT_VERSION,
                "notice": SERVICE_AGREEMENT_NOTICE,
                "notice_hash": SERVICE_AGREEMENT_HASH,
                "accepted": accepted,
                "accepted_at": agreement["accepted_at"] if agreement is not None else None,
                "access_active": bool(
                    await session.scalar(
                        text(_access_sql()), {"tenant": tenant, "live": self.settings.environment == "production"}
                    )
                ),
                "review_required": accepted and any(value != "active" for value in capabilities.values()),
                "enforcement_enabled": self.settings.service_agreement_required,
                "acceptance_enabled": False,
            }

    async def accept(self, tenant: UUID, business: UUID, actor: UUID, version: str, notice_hash: str) -> dict[str, Any]:
        """Record this exact notice and initialize absent permissions in one transaction.

        Existing revocations are not proof that earlier effects finished; they
        remain untouched and are surfaced as requiring review.
        """
        if version != SERVICE_AGREEMENT_VERSION or notice_hash != SERVICE_AGREEMENT_HASH:
            raise AuthError("SERVICE_AGREEMENT_VERSION_CONFLICT", 409)
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_pending_changes import VisualPendingChanges

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            params = {"tenant": tenant, "business": business, "actor": actor}
            existing = await session.scalar(
                text("""SELECT notice_hash FROM service_agreement_acceptances
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
                {**params, "version": version},
            )
            if existing is not None:
                if existing != notice_hash:
                    raise AuthError("SERVICE_AGREEMENT_VERSION_CONFLICT", 409)
            else:
                if await VisualPendingChanges.has_pending_in_session(session, tenant, business):
                    raise AuthError("SERVICE_AGREEMENT_CHANGE_PENDING", 409)
                pending = await session.scalar(
                    text("""SELECT EXISTS(
                  SELECT 1 FROM visual_consent_gates WHERE tenant_id=:tenant AND business_id=:business
                    AND state='revocation_pending'
                  UNION ALL SELECT 1 FROM editorial_ai_consents WHERE tenant_id=:tenant AND business_id=:business
                    AND withdrawal_requested_at IS NOT NULL)"""),
                    params,
                )
                if pending:
                    raise AuthError("SERVICE_AGREEMENT_CHANGE_PENDING", 409)
                await session.execute(
                    text("""INSERT INTO service_agreement_acceptances
                  (tenant_id,business_id,version,actor_id,notice_hash)
                  VALUES(:tenant,:business,:version,:actor,:hash)"""),
                    {**params, "version": version, "hash": notice_hash},
                )
                operation = uuid5(NAMESPACE_URL, f"service-agreement:{tenant}:{business}:{version}:{notice_hash}")
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,:action,:business)"""),
                    {**params, "operation": operation, "action": f"service.agreement.accepted:{version}:{notice_hash}"},
                )
                await self._initialize_absent_consents(session, params, operation)
        return await self.status(tenant, business, actor)

    async def _initialize_absent_consents(
        self, session: AsyncSession, params: dict[str, UUID], operation: UUID
    ) -> None:
        """Never overwrite a prior permission, including its withdrawal or audio choice."""
        for table, action in (
            ("editorial_ai_consents", "editorial.ai_consent_accepted"),
            ("intent_jev_consents", "intent.jev_accepted"),
        ):
            inserted = await session.scalar(
                text(f"""INSERT INTO {table}(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO NOTHING RETURNING 1"""),
                params,
            )
            if inserted:
                await self._audit_consent(session, params, operation, action)
        whatsapp = await session.scalar(
            text("""INSERT INTO whatsapp_processing_consents
          (tenant_id,business_id,actor_id,audio_transcription_accepted_at)
          VALUES(:tenant,:business,:actor,clock_timestamp())
          ON CONFLICT(tenant_id,business_id) DO NOTHING RETURNING 1"""),
            params,
        )
        if whatsapp:
            await self._audit_consent(session, params, operation, "whatsapp.consent_accepted")
            await self._audit_consent(session, params, operation, "whatsapp.audio_consent_accepted")
        visual_gate = await session.scalar(
            text("""SELECT state FROM visual_consent_gates
          WHERE tenant_id=:tenant AND business_id=:business"""),
            params,
        )
        if visual_gate != "revoked":
            visual = await session.scalar(
                text("""INSERT INTO visual_ai_consents(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO NOTHING RETURNING 1"""),
                params,
            )
            if visual:
                await session.execute(
                    text("""INSERT INTO visual_consent_gates(tenant_id,business_id,state)
                  VALUES(:tenant,:business,'active') ON CONFLICT(tenant_id,business_id) DO NOTHING"""),
                    params,
                )
                await self._audit_consent(session, params, operation, "visual.ai_accepted")

    @staticmethod
    async def _audit_consent(session: AsyncSession, params: dict[str, UUID], operation: UUID, action: str) -> None:
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:business)"""),
            {**params, "operation": operation, "action": action},
        )
