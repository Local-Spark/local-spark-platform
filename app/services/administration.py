"""Audited administrative projections; platform staff is distinct from tenant ownership."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.business import AccessDenied


async def require_staff(session: AsyncSession, actor: UUID, action: str) -> None:
    if not await session.scalar(text("SELECT public.is_platform_staff()")):
        raise AccessDenied
    await session.execute(
        text("INSERT INTO platform_audit(actor_id,action) VALUES (:actor,:action)"), {"actor": actor, "action": action}
    )


async def overview(session: AsyncSession, actor: UUID) -> dict[str, Any]:
    await require_staff(session, actor, "admin.overview.read")
    totals = (
        (
            await session.execute(
                text("""SELECT
      (SELECT count(*) FROM tenants) AS organizations,
      (SELECT count(*) FROM user_accounts WHERE active) AS users,
      (SELECT count(*) FROM businesses) AS businesses,
      (SELECT count(DISTINCT tenant_id) FROM business_profiles WHERE completed) AS onboarded""")
            )
        )
        .mappings()
        .one()
    )
    series = (
        (
            await session.execute(
                text("""SELECT days.day::date AS day,count(t.id) AS count
      FROM generate_series((current_timestamp AT TIME ZONE 'America/Sao_Paulo')::date-6,
        (current_timestamp AT TIME ZONE 'America/Sao_Paulo')::date,interval '1 day') days(day)
      LEFT JOIN tenants t ON (t.created_at AT TIME ZONE 'America/Sao_Paulo')::date=days.day::date
      GROUP BY days.day ORDER BY days.day""")
            )
        )
        .mappings()
        .all()
    )
    return {
        "totals": dict(totals),
        "registrations": [dict(row) for row in series],
        "timezone": "America/Sao_Paulo",
        "billing_available": False,
        "social_metrics_available": False,
    }


async def organizations(
    session: AsyncSession, actor: UUID, query: str, limit: int, after: UUID | None
) -> dict[str, Any]:
    await require_staff(session, actor, "admin.organizations.read")
    rows = (
        (
            await session.execute(
                text("""SELECT t.id,t.name,t.created_at,
      (SELECT count(*) FROM businesses b WHERE b.tenant_id=t.id) AS business_count,
      EXISTS(SELECT 1 FROM business_profiles p WHERE p.tenant_id=t.id AND p.completed) AS onboarding_completed
      FROM tenants t WHERE t.name ILIKE :query AND (CAST(:after AS uuid) IS NULL OR t.id>:after)
      ORDER BY t.id LIMIT :limit"""),
                {"query": f"%{query}%", "after": after, "limit": limit + 1},
            )
        )
        .mappings()
        .all()
    )
    items = [dict(row) for row in rows[:limit]]
    return {"items": items, "next_cursor": str(items[-1]["id"]) if len(rows) > limit else None}
