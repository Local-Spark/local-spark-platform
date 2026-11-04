"""An owner identifies their own listing only when automatic matching is ambiguous."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.reference_own_review import OwnBusinessReviewConfirm, OwnBusinessReviewRead
from app.services.reference_own_review import ReferenceOwnReviewService

reference_own_review_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/reference-results/searches/{search_id}/own-business-review",
    tags=["references"],
)


@reference_own_review_router.get("", response_model=OwnBusinessReviewRead)
async def read_own_review(
    tenant_id: UUID, business_id: UUID, search_id: UUID, request: Request, actor: Actor
) -> OwnBusinessReviewRead:
    return await ReferenceOwnReviewService(request.app.state.database).read(tenant_id, business_id, actor, search_id)


@reference_own_review_router.post("", response_model=OwnBusinessReviewRead)
async def confirm_own_review(
    tenant_id: UUID,
    business_id: UUID,
    search_id: UUID,
    payload: OwnBusinessReviewConfirm,
    request: Request,
    actor: Actor,
) -> OwnBusinessReviewRead:
    return await ReferenceOwnReviewService(request.app.state.database).confirm(
        tenant_id, business_id, actor, search_id, payload
    )
