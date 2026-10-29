"""Narrow financial-expiry exception for durable visual work and private review."""

from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.services.editorial_consent_scope import current_visual_run


async def admitted_or_preserved(
    session: Any, tenant: UUID, business: UUID, actor: UUID, source: UUID, preview: UUID | None
) -> bool:
    params = {"tenant": tenant, "business": business, "actor": actor, "source": source}
    if preview is not None:
        return bool(
            await session.scalar(
                text("""SELECT 1 FROM media_previews p
              JOIN visual_consent_runs r ON r.tenant_id=p.tenant_id AND r.business_id=p.business_id
                AND r.preview_id=p.id AND r.fence=p.dispatch_fence AND r.actor_id=p.actor_id
              WHERE p.tenant_id=:tenant AND p.business_id=:business AND p.id=:preview
                AND p.source_asset_id=:source AND p.state='completed' AND p.generation_mode='visual_fake'
                AND p.sha256 IS NOT NULL AND p.object_key IS NOT NULL AND r.state='finished'"""),
                {**params, "preview": preview},
            )
        )
    scope = current_visual_run()
    if scope is None or (scope.tenant, scope.business, scope.actor) != (tenant, business, actor):
        return False
    # Expiry is different from an explicit financial block or revoked sponsorship.
    return bool(
        await session.scalar(
            text("""SELECT 1 FROM visual_consent_runs r
          JOIN media_previews p ON p.id=r.preview_id AND p.tenant_id=r.tenant_id AND p.business_id=r.business_id
          WHERE r.tenant_id=:tenant AND r.business_id=:business AND r.actor_id=:actor
            AND r.operation_id=:operation AND r.fence=:fence AND r.state='in_flight'
            AND p.source_asset_id=:source AND p.dispatch_fence=r.fence AND p.state='rendering'
            AND p.generation_mode='visual_fake'
            AND NOT EXISTS(SELECT 1 FROM billing_accounts b WHERE b.tenant_id=:tenant AND b.blocked)
            AND NOT EXISTS(SELECT 1 FROM billing_sponsorships s WHERE s.tenant_id=:tenant
              AND s.revoked_at IS NOT NULL AND s.revoked_at>=r.created_at)"""),
            {**params, "operation": scope.operation, "fence": scope.fence},
        )
    )
