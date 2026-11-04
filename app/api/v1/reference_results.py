"""Owner access to published suggestions; no provider effect can be submitted here."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.reference_execution import ReferenceSearchRetried, ReferenceSearchStart, ReferenceSearchStarted
from app.schemas.reference_profiles import ReferenceProfileRead, ReferenceProfileWrite
from app.schemas.reference_results import ReferenceResultsRead, ReferenceSelectionRead, ReferenceSelectionRequest
from app.services.reference_profiles import ReferenceProfilesService
from app.services.reference_results import ReferenceResultsService
from app.services.reference_search_start import ReferenceSearchStartService

reference_results_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/reference-results",
    tags=["references"],
)


@reference_results_router.get("", response_model=ReferenceResultsRead)
async def read_results(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> ReferenceResultsRead:
    return await ReferenceResultsService(request.app.state.database, request.app.state.settings).read(
        tenant_id, business_id, actor
    )


@reference_results_router.post("/searches", response_model=ReferenceSearchStarted)
async def start_search(
    tenant_id: UUID, business_id: UUID, payload: ReferenceSearchStart, request: Request, actor: Actor
) -> ReferenceSearchStarted:
    return await ReferenceSearchStartService(request.app.state.database, request.app.state.settings).start(
        tenant_id, business_id, actor, payload
    )


@reference_results_router.post("/selection", response_model=ReferenceSelectionRead)
async def confirm_selection(
    tenant_id: UUID, business_id: UUID, payload: ReferenceSelectionRequest, request: Request, actor: Actor
) -> ReferenceSelectionRead:
    return await ReferenceResultsService(request.app.state.database).confirm(tenant_id, business_id, actor, payload)


@reference_results_router.put("/profiles/{place_identity}", response_model=ReferenceProfileRead)
async def correct_profile(
    tenant_id: UUID,
    business_id: UUID,
    place_identity: UUID,
    payload: ReferenceProfileWrite,
    request: Request,
    actor: Actor,
) -> ReferenceProfileRead:
    return await ReferenceProfilesService(request.app.state.database).save(
        tenant_id, business_id, actor, place_identity, payload
    )


@reference_results_router.post("/searches/{search_id}/retry", response_model=ReferenceSearchRetried)
async def retry_search(
    tenant_id: UUID, business_id: UUID, search_id: UUID, payload: ReferenceSearchStart, request: Request, actor: Actor
) -> ReferenceSearchRetried:
    return await ReferenceSearchStartService(request.app.state.database, request.app.state.settings).retry(
        tenant_id, business_id, actor, search_id, payload
    )
