"""Explicit, business-scoped acceptance of the locally published service notice."""

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.service_agreement_scope import (
    SERVICE_AGREEMENT_HASH as SERVICE_AGREEMENT_HASH,
)
from app.services.service_agreement_scope import (
    SERVICE_AGREEMENT_NOTICE as SERVICE_AGREEMENT_NOTICE,
)
from app.services.service_agreement_scope import (
    SERVICE_AGREEMENT_VERSION as SERVICE_AGREEMENT_VERSION,
)
from app.services.service_agreement_scope import (
    agreement_worker_scope,
    service_agreement_accepted,
)
from app.services.whatsapp_materials import WhatsAppMaterialsService


async def service_agreement_allowed(
    session: AsyncSession, settings: Settings, tenant: UUID, business: UUID, *, worker: bool = False
) -> bool:
    """Check the agreement in the tenant-local transaction, never switching actors."""
    if worker:
        await agreement_worker_scope(session, tenant)
    if not settings.service_agreement_required:
        return settings.environment != "production"
    return await service_agreement_accepted(session, tenant, business)


class ServiceAgreementService:
    """Record one contract decision without changing provider configuration or history."""

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
                "review_required": False,
                "enforcement_enabled": self.settings.service_agreement_required,
                "acceptance_enabled": True,
            }

    async def accept(self, tenant: UUID, business: UUID, actor: UUID, version: str, notice_hash: str) -> dict[str, Any]:
        """Record this exact notice once, preserving all prior permission decisions."""
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
                    AND withdrawal_requested_at IS NOT NULL
                  UNION ALL SELECT 1 FROM visual_consent_runs WHERE tenant_id=:tenant AND business_id=:business
                    AND state='in_flight')"""),
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
        return await self.status(tenant, business, actor)
