"""Owner reads and confirmation of existing, privately published suggestions."""

import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import Settings
from app.db.session import Database
from app.schemas.reference_results import (
    ReferenceOccurrenceRead,
    ReferenceResultsRead,
    ReferenceSearchRead,
    ReferenceSelectionRead,
    ReferenceSelectionRequest,
)
from app.services.auth import AuthError
from app.services.reference_published_read import PublishedOccurrence, read_published_references

_CONFLICTS = (
    "REFERENCE_SELECTION_OPERATION_CONFLICT",
    "REFERENCE_SELECTION_CYCLE_STALE",
    "REFERENCE_SELECTION_RESULT_PENDING",
    "REFERENCE_SELECTION_INVALID_CANDIDATE",
    "REFERENCE_SELECTION_DUPLICATE_ENTITY",
    "REFERENCE_CYCLE_DECISION_INCOMPLETE",
    "REFERENCE_CYCLE_DECISION_SELECTION_MISMATCH",
    "REFERENCE_CYCLE_DECISION_NOT_REQUIRED",
)


def _occurrence(item: PublishedOccurrence) -> ReferenceOccurrenceRead:
    return ReferenceOccurrenceRead(
        cycle_id=item.cycle_id,
        result_id=item.result_id,
        candidate_id=item.candidate_id,
        place_identity=item.place_identity,
        place_id=item.place_id,
        position=item.position,
        reputation_score=item.score,
        reputation_formula_version=item.score_version,
        jev_recommendation_rank=item.recommendation_rank,
        instagram_handle=item.instagram_handle,
        profile_source=item.profile_source,
        profile_version=item.profile_version,
    )


class ReferenceResultsService:
    def __init__(self, database: Database, settings: Settings | None = None) -> None:
        self.database, self.settings = database, settings

    async def read(self, tenant: UUID, business: UUID, actor: UUID) -> ReferenceResultsRead:
        snapshot = await read_published_references(self.database, tenant, business, actor)
        return ReferenceResultsRead(
            discovery_available=bool(self.settings and self.settings.reference_discovery_ready()),
            cycle_id=snapshot.cycle_id,
            locked_until=snapshot.locked_until,
            searches=tuple(
                ReferenceSearchRead(
                    search_id=search.search_id,
                    radius_km=search.radius_km,
                    state=search.state,
                    published=search.published,
                    recommendation_status=search.recommendation_status,
                    execution_status=search.execution_status,
                    family_root_id=search.family_root_id,
                    family_current_search_id=search.family_current_search_id,
                    family_status=search.family_status,
                    can_retry_family=search.can_retry_family,
                    candidates=tuple(_occurrence(item) for item in search.candidates),
                )
                for search in snapshot.searches
            ),
            selected=tuple(_occurrence(item) for item in snapshot.selected),
            cycle_review=snapshot.cycle_review,
        )

    async def confirm(
        self, tenant: UUID, business: UUID, actor: UUID, payload: ReferenceSelectionRequest
    ) -> ReferenceSelectionRead:
        try:
            async with self.database.transaction(tenant, actor) as session:
                value = await session.scalar(
                    text("""SELECT public.reference_confirm_published_selection(
                      :business,:operation,:cycle,:results,:candidates,:first,CAST(:decisions AS jsonb))"""),
                    {
                        "business": business,
                        "operation": payload.operation_id,
                        "cycle": payload.cycle_id,
                        "results": [item.result_id for item in payload.selection],
                        "candidates": [item.candidate_id for item in payload.selection],
                        "first": payload.first_result_id,
                        "decisions": json.dumps({str(item.place_identity): item.action for item in payload.decisions}),
                    },
                )
        except DBAPIError as error:
            message = str(error.orig)
            if "REFERENCE_OWNER_INACTIVE" in message:
                raise AuthError("BUSINESS_OWNER_REQUIRED", 403) from None
            for code in _CONFLICTS:
                if code in message:
                    raise AuthError(code, 409) from None
            raise
        return ReferenceSelectionRead.model_validate(value)
