"""Owner-only editorial context API."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.editorial_context import ContextHistoryItem, ContextRead, ContextRestore, ContextUpdate
from app.services.editorial_context import EditorialContextService

context_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-context",
    tags=["editorial-context"],
)


def service(request: Request) -> EditorialContextService:
    return EditorialContextService(request.app.state.database)


@context_router.get("", response_model=ContextRead)
async def context_read(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> ContextRead:
    return await service(request).read(tenant_id, business_id, actor)


@context_router.put("", response_model=ContextRead)
async def context_update(
    tenant_id: UUID, business_id: UUID, payload: ContextUpdate, request: Request, actor: Actor
) -> ContextRead:
    return await service(request).update(tenant_id, business_id, actor, payload)


@context_router.get("/history", response_model=list[ContextHistoryItem])
async def context_history(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor
) -> list[ContextHistoryItem]:
    return await service(request).history(tenant_id, business_id, actor)


@context_router.get("/versions/{version}", response_model=ContextRead)
async def context_version(
    tenant_id: UUID, business_id: UUID, version: int, request: Request, actor: Actor
) -> ContextRead:
    return await service(request).read(tenant_id, business_id, actor, version)


@context_router.post("/restore", response_model=ContextRead)
async def context_restore(
    tenant_id: UUID, business_id: UUID, payload: ContextRestore, request: Request, actor: Actor
) -> ContextRead:
    return await service(request).restore(tenant_id, business_id, actor, payload)
