"""Exact contract evidence shared by owner and worker services.

SQL expressions come only from application-owned query definitions. This module
has no provider configuration and cannot enable or execute an external effect.
"""

import hashlib
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthError

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


def accepted_agreement_sql(tenant_expr: str = ":tenant", business_expr: str = ":business") -> str:
    """Build a predicate for static application SQL, never client expressions."""
    return (
        "EXISTS(SELECT 1 FROM service_agreement_acceptances service_agreement "
        f"WHERE service_agreement.tenant_id={tenant_expr} AND service_agreement.business_id={business_expr} "
        f"AND service_agreement.version='{SERVICE_AGREEMENT_VERSION}' "
        f"AND service_agreement.notice_hash='{SERVICE_AGREEMENT_HASH}')"
    )


def accepted_agreement_at_sql(tenant_expr: str = ":tenant", business_expr: str = ":business") -> str:
    """Read owner-visible acceptance time; worker roles cannot select this column."""
    return (
        "(SELECT service_agreement.accepted_at FROM service_agreement_acceptances service_agreement "
        f"WHERE service_agreement.tenant_id={tenant_expr} AND service_agreement.business_id={business_expr} "
        f"AND service_agreement.version='{SERVICE_AGREEMENT_VERSION}' "
        f"AND service_agreement.notice_hash='{SERVICE_AGREEMENT_HASH}')"
    )


def editorial_agreement_generation_sql() -> str:
    """Separate new contract jobs from every nonnegative legacy consent epoch."""
    generation = -int(SERVICE_AGREEMENT_HASH[:15], 16)
    return (
        f"SELECT CASE WHEN {accepted_agreement_sql()} THEN {generation} "
        "ELSE coalesce((SELECT generation FROM editorial_ai_consents "
        "WHERE tenant_id=:tenant AND business_id=:business), 0) END"
    )


async def agreement_worker_scope(session: AsyncSession, tenant: UUID) -> None:
    """Set one transaction-local worker scope without switching an existing tenant."""
    current = await session.scalar(text("SELECT current_setting('app.tenant_id',true)"))
    if current and current != str(tenant):
        raise AuthError("SERVICE_AGREEMENT_TENANT_MISMATCH", 403)
    if not current:
        await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(tenant)})


async def service_agreement_accepted(
    session: AsyncSession, tenant: UUID, business: UUID, *, worker: bool = False
) -> bool:
    """Read actual evidence, independently of the rollout enforcement setting."""
    if worker:
        await agreement_worker_scope(session, tenant)
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
