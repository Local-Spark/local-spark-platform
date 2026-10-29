"""One authorization rule for literal visual copy and its factual time window.

The request builder and the final effect guard share this owner-scoped SQL-only
check. A deadline is authorization for use, never a retention or approval policy.
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.schemas.brand_kits import BrandKitOverrides
from app.schemas.editorial_context import ContextContent
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_proposals import _COMMERCIAL_CLAIM, _catalog_fact


@dataclass(frozen=True)
class VisualCopyAuthorization:
    statement: str = field(repr=False)
    cta: str = field(repr=False)
    valid_until: datetime
    product_name: str = field(repr=False)
    kit: BrandKitOverrides = field(repr=False)


def _end_of_day(day: date, timezone: str) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, ZoneInfo(timezone)).astimezone(UTC)


async def authorize_visual_copy(
    session: AsyncSession,
    settings: Settings,
    database: Database,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    proposal: UUID,
    briefing: UUID,
) -> VisualCopyAuthorization:
    started_at = datetime.now(UTC)
    status, catalog = await EditorialBriefingService(settings, database).read_valid(
        session, tenant, business, actor, briefing
    )
    row = (
        (
            await session.execute(
                text("""SELECT brand_kit_document,document,context_version,expires_at FROM editorial_proposals
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:proposal"""),
                {"tenant": tenant, "business": business, "proposal": proposal},
            )
        )
        .mappings()
        .one_or_none()
    )
    if status != "prepared" or catalog is None or row is None or row["brand_kit_document"] is None:
        raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
    kit = BrandKitOverrides.model_validate(row["brand_kit_document"]["overrides"])
    draft = ProposalDraft.model_validate(row["document"])
    offering: Any = catalog["offering"]
    product_name = offering["name"]
    facts = [scene for scene in draft.script if scene.role == "fact"]
    ctas = [scene for scene in draft.script if scene.role == "cta"]
    if len(facts) != 1 or len(facts[0].fact_ids) != 1 or len(ctas) != 1:
        raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
    scene = facts[0]
    statement = None
    timezone = None
    deadline = row["expires_at"]
    catalog_fact = _catalog_fact(catalog)
    if catalog_fact is not None and str(scene.fact_ids[0]) == catalog_fact["id"]:
        statement = str(catalog_fact["statement"]).rstrip(". ") + "."
    elif row["context_version"]:
        params = {"tenant": tenant, "business": business, "version": row["context_version"]}
        document = await session.scalar(
            text("""SELECT document FROM business_context_versions
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
            params,
        )
        timezone = await session.scalar(
            text("SELECT timezone FROM businesses WHERE tenant_id=:tenant AND id=:business"), params
        )
        if document is not None and timezone is not None:
            context = ContextContent.model_validate(document)
            today = datetime.now(UTC).astimezone(ZoneInfo(timezone)).date()
            fact = next((item for item in context.facts if item.id == scene.fact_ids[0]), None)
            if fact is not None and (fact.valid_until is None or fact.valid_until >= today):
                statement = fact.statement.rstrip(". ") + "."
                if fact.valid_until is not None:
                    deadline = min(deadline, _end_of_day(fact.valid_until, timezone))
    if statement is None or scene.on_screen_text != statement or scene.voiceover != statement:
        raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
    cta = ctas[0].on_screen_text
    if _COMMERCIAL_CLAIM.search(cta):
        raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
    price = offering.get("price")
    if isinstance(price, dict) and price.get("status") == "valid" and price.get("valid_until"):
        if timezone is None:
            timezone = await session.scalar(
                text("SELECT timezone FROM businesses WHERE tenant_id=:tenant AND id=:business"),
                {"tenant": tenant, "business": business},
            )
        if timezone is None:
            raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
        deadline = min(deadline, _end_of_day(date.fromisoformat(price["valid_until"]), timezone))
    promotions = catalog.get("promotions")
    if isinstance(promotions, list):
        for promotion in promotions:
            deadline = min(deadline, datetime.fromisoformat(promotion["ends_at"]))
        # A newly active promotion would also invalidate this prepared snapshot.
        # Its start is a known time boundary even without a writer during the run.
        next_start = await session.scalar(
            text("""SELECT min(starts_at) FROM business_offering_promotions WHERE tenant_id=:tenant
              AND business_id=:business AND offering_id=:item AND state='active'
              AND starts_at>=:started_at"""),
            {"tenant": tenant, "business": business, "item": UUID(offering["id"]), "started_at": started_at},
        )
        if next_start is not None:
            deadline = min(deadline, next_start)
    if deadline <= datetime.now(UTC):
        raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
    return VisualCopyAuthorization(statement, cta, deadline, product_name, kit)
