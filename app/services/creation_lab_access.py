"""Exclusive, audited laboratory discovery; never impersonates a business owner."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.administration import require_staff
from app.services.auth import AuthError


async def require_lab_access(session: AsyncSession, settings: Settings, actor: UUID, action: str) -> None:
    if settings.creation_lab_actor_id != actor:
        raise AuthError("CREATION_LAB_ACCESS_DENIED", 403)
    await require_staff(session, actor, action)


async def lab_businesses(
    session: AsyncSession, settings: Settings, actor: UUID, query: str, limit: int, after: UUID | None
) -> dict[str, Any]:
    await require_lab_access(session, settings, actor, "admin.creation_lab.businesses.read")
    rows = (
        (
            await session.execute(
                text("""SELECT b.id,b.tenant_id,b.name,t.name AS organization_name
                  FROM businesses b JOIN tenants t ON t.id=b.tenant_id
                  WHERE (b.name ILIKE :query ESCAPE '!' OR t.name ILIKE :query ESCAPE '!')
                    AND (CAST(:after AS uuid) IS NULL OR b.id>:after)
                  ORDER BY b.id LIMIT :limit"""),
                {
                    "query": "%" + query.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%",
                    "limit": limit + 1,
                    "after": after,
                },
            )
        )
        .mappings()
        .all()
    )
    items = [dict(row) for row in rows[:limit]]
    return {"items": items, "next_cursor": str(items[-1]["id"]) if len(rows) > limit else None}
