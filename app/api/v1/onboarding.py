from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import Actor, ActorSession, Principal
from app.schemas.onboarding import OnboardingCreate, OnboardingResult, SessionRead
from app.services import administration
from app.services.onboarding import provision_initial_business, session_context, sync_identity

onboarding_router = APIRouter(prefix="/api/v1")


@onboarding_router.post("/session", response_model=SessionRead, tags=["identity"])
async def synchronize_session(identity: Principal, session: ActorSession) -> SessionRead:
    await sync_identity(session, identity)
    return await session_context(session, identity)


@onboarding_router.get("/me", response_model=SessionRead, tags=["identity"])
async def me(identity: Principal, session: ActorSession) -> SessionRead:
    return await session_context(session, identity)


@onboarding_router.post("/onboarding", response_model=OnboardingResult, status_code=201, tags=["onboarding"])
async def onboard(
    payload: OnboardingCreate, response: Response, identity: Principal, session: ActorSession
) -> OnboardingResult:
    result = await provision_initial_business(session, identity, payload)
    if result.replayed:
        response.status_code = 200
    return result


@onboarding_router.get("/admin/overview", tags=["administration"])
async def admin_overview(actor: Actor, session: ActorSession) -> dict[str, Any]:
    return await administration.overview(session, actor)


@onboarding_router.get("/admin/organizations", tags=["administration"])
async def admin_organizations(
    actor: Actor,
    session: ActorSession,
    q: Annotated[str, Query(max_length=100)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    after: UUID | None = None,
) -> dict[str, Any]:
    return await administration.organizations(session, actor, q, limit, after)


@onboarding_router.get("/admin/editorial-operations", tags=["administration"])
async def admin_editorial_operations(
    actor: Actor,
    session: ActorSession,
    tenant_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, Any]:
    return await administration.editorial_operations(session, actor, tenant_id, limit)


@onboarding_router.get("/admin/editorial-operations/{proposal_id}/events", tags=["administration"])
async def admin_editorial_operation_events(proposal_id: UUID, actor: Actor, session: ActorSession) -> dict[str, Any]:
    return await administration.editorial_operation_events(session, actor, proposal_id)
