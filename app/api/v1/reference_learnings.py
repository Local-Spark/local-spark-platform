"""Owner access to analysis status and derived creative learnings."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.reference_learnings import ReferenceLearningsRead
from app.services.reference_learnings import ReferenceLearningsService

reference_learnings_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/reference-learnings", tags=["references"]
)


@reference_learnings_router.get("", response_model=ReferenceLearningsRead)
async def read_learnings(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> ReferenceLearningsRead:
    return await ReferenceLearningsService(request.app.state.database).read(tenant_id, business_id, actor)
