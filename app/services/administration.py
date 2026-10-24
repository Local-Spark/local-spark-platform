"""Audited administrative projections; platform staff is distinct from tenant ownership."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthError
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


async def editorial_operations(session: AsyncSession, actor: UUID, tenant: UUID | None, limit: int) -> dict[str, Any]:
    """Only operational fields cross the admin boundary; no prompts or drafts."""
    await require_staff(session, actor, "admin.editorial_operations.read")
    rows = (
        (
            await session.execute(
                text("SELECT * FROM public.admin_editorial_operations(:tenant,:limit)"),
                {"tenant": tenant, "limit": limit},
            )
        )
        .mappings()
        .all()
    )
    return {"items": [dict(row) | {"estimated_cost_minor": None} for row in rows]}


async def editorial_operation_events(session: AsyncSession, actor: UUID, proposal: UUID) -> dict[str, Any]:
    """Return persisted stage transitions only; legacy events may be incomplete."""
    await require_staff(session, actor, "admin.editorial_operation_events.read")
    rows = (
        (
            await session.execute(
                text("SELECT * FROM public.admin_editorial_operation_events(:proposal)"),
                {"proposal": proposal},
            )
        )
        .mappings()
        .all()
    )
    return {"items": [dict(row) for row in rows]}


async def editorial_usage_today(
    session: AsyncSession, actor: UUID, tenant: UUID | None, limit: int, token_limit: int
) -> dict[str, Any]:
    """Summarize quota reservations; observed tokens may be incomplete and are not money."""
    await require_staff(session, actor, "admin.editorial_usage.read")
    rows = (
        (
            await session.execute(
                text("SELECT * FROM public.admin_editorial_usage_today(:tenant,:limit)"),
                {"tenant": tenant, "limit": limit},
            )
        )
        .mappings()
        .all()
    )
    day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    items = []
    for row in rows:
        item = dict(row)
        reserved = item["reserved_tokens"]
        if token_limit == 0:
            state = "unconfigured"
        elif reserved >= token_limit:
            state = "exhausted"
        elif reserved * 5 >= token_limit * 4:
            state = "warning"
        else:
            state = "normal"
        items.append(item | {"quota_state": state, "estimated_cost_minor": None})
    return {
        "period_start": day_start,
        "period_end": day_start + timedelta(days=1),
        "daily_token_limit": token_limit,
        "items": items,
    }


async def whatsapp_reply_issues(session: AsyncSession, actor: UUID, tenant: UUID | None, limit: int) -> dict[str, Any]:
    """Staff-only metadata for uncertain or failed delivery; no phone or message body."""
    await require_staff(session, actor, "admin.whatsapp_replies.read")
    rows = (
        (
            await session.execute(
                text("SELECT * FROM public.admin_whatsapp_replies(:tenant,:limit)"),
                {"tenant": tenant, "limit": limit},
            )
        )
        .mappings()
        .all()
    )
    return {"items": [dict(row) for row in rows]}


async def review_whatsapp_reply(session: AsyncSession, actor: UUID, reply: UUID, outcome: str) -> dict[str, str]:
    await require_staff(session, actor, "admin.whatsapp_replies.review")
    found = await session.scalar(
        text("SELECT public.admin_review_whatsapp_reply(:reply,:outcome)"),
        {"reply": reply, "outcome": outcome},
    )
    if not found:
        raise AuthError("WHATSAPP_REPLY_NOT_FOUND", 404)
    return {"review_outcome": outcome}
