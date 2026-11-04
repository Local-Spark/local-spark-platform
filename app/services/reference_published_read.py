"""One owner-scoped snapshot of published lists, selections and cycle review."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import text

from app.db.session import Database
from app.schemas.reference_results import ReferenceCycleReviewRead
from app.services.auth import AuthError


@dataclass(frozen=True, repr=False)
class PublishedOccurrence:
    cycle_id: UUID
    result_id: UUID
    candidate_id: UUID
    place_identity: UUID
    place_id: str
    position: int
    score: Decimal
    score_version: str
    recommendation_rank: int | None = None
    instagram_handle: str | None = None
    profile_source: Literal["apify", "owner"] | None = None
    profile_version: int = 0


@dataclass(frozen=True, repr=False)
class PublishedSearch:
    search_id: UUID
    radius_km: int
    state: str
    published: bool
    candidates: tuple[PublishedOccurrence, ...]
    recommendation_status: Literal["completed", "unavailable"] = "unavailable"
    execution_status: str = "pending"
    family_root_id: UUID | None = None
    family_current_search_id: UUID | None = None
    family_status: str = "pending"
    can_retry_family: bool = False


@dataclass(frozen=True, repr=False)
class PublishedReferences:
    cycle_id: UUID | None
    locked_until: datetime | None
    searches: tuple[PublishedSearch, ...]
    selected: tuple[PublishedOccurrence, ...]
    cycle_review: ReferenceCycleReviewRead | None = None


_QUERY = text("""SELECT h.cycle_id AS current_cycle,coalesce(h.cycle_id,terminal.cycle_id) AS display_cycle,
  cy.locked_until,
  CASE WHEN s.id IS NOT NULL THEN public.reference_read_search_family(:business,s.id) END AS family,
  review.first_result_id,review.required_place_ids,review.resolved_operation_id,
  s.id AS search_id,s.cycle_id,s.radius_km,s.state AS search_state,s.created_at,s.execution_status,
  (pub.result_id IS NOT NULL) AS published,
  r.id AS result_id,c.id AS candidate_id,c.place_id AS place_identity,
  p.place_id,c.position,c.reputation_score,c.reputation_formula_version,
  c.jev_recommendation_rank,coalesce(overridden.instagram_handle,profile.instagram_handle) AS instagram_handle,
  CASE WHEN overridden.version IS NOT NULL THEN 'owner'
    WHEN profile.instagram_handle IS NOT NULL THEN 'apify' END AS profile_source,
  coalesce(overridden.version,0) AS profile_version,r.recommendation_status,
  (sel.candidate_id IS NOT NULL) AS selected
FROM (SELECT CAST(:tenant AS uuid) AS tenant_id,CAST(:business AS uuid) AS business_id
  WHERE EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id AND u.active
    JOIN business_profiles bp ON bp.tenant_id=m.tenant_id AND bp.business_id=:business
    WHERE m.tenant_id=:tenant AND m.actor_id=:actor AND m.active AND m.role='owner')) anchor
LEFT JOIN reference_real_heads h ON (h.tenant_id,h.business_id)=(anchor.tenant_id,anchor.business_id)
LEFT JOIN LATERAL (SELECT old.cycle_id FROM reference_provider_searches old
  WHERE old.tenant_id=anchor.tenant_id AND old.business_id=anchor.business_id
    AND old.execution_status='empty_exhausted' ORDER BY old.created_at DESC,old.id DESC LIMIT 1) terminal
  ON h.cycle_id IS NULL
LEFT JOIN reference_real_cycles cy ON (cy.tenant_id,cy.business_id,cy.id)=(h.tenant_id,h.business_id,h.cycle_id)
LEFT JOIN reference_cycle_reviews review ON (review.tenant_id,review.business_id,review.cycle_id)
  =(h.tenant_id,h.business_id,h.cycle_id)
LEFT JOIN reference_provider_searches s ON s.tenant_id=h.tenant_id AND s.business_id=h.business_id
  AND s.radius_km IN (5,20,50) AND (
    (s.cycle_id=coalesce(h.cycle_id,terminal.cycle_id)
      AND (s.radius_occupied OR s.execution_status='type_mapping_unavailable')) OR EXISTS(
      SELECT 1 FROM reference_provider_results old_result
      JOIN reference_real_selected old_selection ON
        (old_selection.tenant_id,old_selection.business_id,old_selection.result_id)
        =(old_result.tenant_id,old_result.business_id,old_result.id)
      WHERE (old_result.tenant_id,old_result.business_id,old_result.search_id)=(s.tenant_id,s.business_id,s.id)))
LEFT JOIN reference_provider_results r ON (r.tenant_id,r.business_id,r.search_id)=(s.tenant_id,s.business_id,s.id)
  AND s.state='completed'
LEFT JOIN reference_real_published_results pub ON (pub.tenant_id,pub.business_id,pub.result_id)
  =(r.tenant_id,r.business_id,r.id)
LEFT JOIN reference_provider_result_candidates c ON (c.tenant_id,c.business_id,c.result_id)
  =(pub.tenant_id,pub.business_id,pub.result_id)
LEFT JOIN reference_provider_places p ON (p.tenant_id,p.business_id,p.id)=(c.tenant_id,c.business_id,c.place_id)
LEFT JOIN reference_profile_override_heads oh ON (oh.tenant_id,oh.business_id,oh.place_identity)
  =(c.tenant_id,c.business_id,c.place_id)
LEFT JOIN reference_profile_overrides overridden ON
  (overridden.tenant_id,overridden.business_id,overridden.place_identity,overridden.version)
  =(oh.tenant_id,oh.business_id,oh.place_identity,oh.version)
LEFT JOIN LATERAL (SELECT po.instagram_handle FROM reference_provider_profile_options po
  WHERE (po.tenant_id,po.business_id,po.result_id,po.candidate_id)=(c.tenant_id,c.business_id,c.result_id,c.id)
  ORDER BY po.is_primary DESC,po.source_position LIMIT 1) profile ON true
LEFT JOIN reference_real_selected sel ON (sel.tenant_id,sel.business_id,sel.result_id,sel.candidate_id)
  =(c.tenant_id,c.business_id,c.result_id,c.id)
ORDER BY s.created_at,s.id,c.position""")


async def read_published_references(
    database: Database, tenant: UUID, business: UUID, actor: UUID
) -> PublishedReferences:
    """Read one database snapshot; never return unpublished or raw provider data."""
    async with database.transaction(tenant, actor) as session:
        rows = (
            (await session.execute(_QUERY, {"tenant": tenant, "business": business, "actor": actor})).mappings().all()
        )
    if not rows:
        raise AuthError("BUSINESS_OWNER_REQUIRED", 403)
    first = rows[0]
    current_cycle, locked_until = first["current_cycle"], first["locked_until"]
    display_cycle = first.get("display_cycle", current_cycle)
    families = {}
    searches: dict[
        UUID, tuple[int, str, bool, list[PublishedOccurrence], Literal["completed", "unavailable"], str]
    ] = {}
    selected: list[PublishedOccurrence] = []
    for row in rows:
        if row["search_id"] is None:
            continue
        families[row["search_id"]] = row.get("family") or {}
        if row["cycle_id"] == display_cycle:
            search = searches.setdefault(
                row["search_id"],
                (
                    row["radius_km"],
                    row["search_state"],
                    row["published"],
                    [],
                    row.get("recommendation_status") or "unavailable",
                    row.get("execution_status") or "pending",
                ),
            )
        if row["candidate_id"] is None or (row["cycle_id"] != display_cycle and not row["selected"]):
            continue
        item = PublishedOccurrence(
            cycle_id=row["cycle_id"],
            result_id=row["result_id"],
            candidate_id=row["candidate_id"],
            place_identity=row["place_identity"],
            place_id=row["place_id"],
            position=row["position"],
            score=row["reputation_score"],
            score_version=row["reputation_formula_version"],
            recommendation_rank=row.get("jev_recommendation_rank"),
            instagram_handle=row.get("instagram_handle"),
            profile_source=row.get("profile_source"),
            profile_version=row.get("profile_version", 0),
        )
        if row["selected"]:
            selected.append(item)
        if row["cycle_id"] == display_cycle:
            search[3].append(item)
    return PublishedReferences(
        cycle_id=current_cycle,
        locked_until=locked_until,
        searches=tuple(
            PublishedSearch(
                search_id,
                radius,
                state,
                published,
                tuple(items),
                recommendation_status,
                execution_status,
                UUID(families[search_id]["family_root_id"]) if families[search_id].get("family_root_id") else None,
                UUID(families[search_id]["family_current_search_id"])
                if families[search_id].get("family_current_search_id")
                else None,
                families[search_id].get("family_status", "pending"),
                families[search_id].get("can_retry_family", False),
            )
            for search_id, (
                radius,
                state,
                published,
                items,
                recommendation_status,
                execution_status,
            ) in searches.items()
        ),
        selected=tuple(selected),
        cycle_review=ReferenceCycleReviewRead(
            cycle_id=current_cycle,
            first_result_id=first["first_result_id"],
            required_place_ids=first["required_place_ids"],
        )
        if first.get("required_place_ids") and first.get("resolved_operation_id") is None
        else None,
    )
