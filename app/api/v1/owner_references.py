"""Owner-only indication of Instagram profiles; no external access."""

from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.api.deps import Actor
from app.schemas.owner_references import ReferenceCreate, ReferenceRead, ReferenceRemove
from app.services.owner_references import OwnerReferencesService

owner_references_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/references", tags=["owner-references"]
)


@owner_references_router.get("", response_model=list[ReferenceRead])
async def list_references(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> list[ReferenceRead]:
    return await OwnerReferencesService(request.app.state.database).list(tenant_id, business_id, actor)


@owner_references_router.post("", response_model=ReferenceRead)
async def create_reference(
    tenant_id: UUID, business_id: UUID, payload: ReferenceCreate, request: Request, actor: Actor
) -> ReferenceRead:
    return await OwnerReferencesService(request.app.state.database).create(tenant_id, business_id, actor, payload)


@owner_references_router.delete("/{reference_id}", status_code=204)
async def remove_reference(
    tenant_id: UUID, business_id: UUID, reference_id: UUID, payload: ReferenceRemove, request: Request, actor: Actor
) -> Response:
    await OwnerReferencesService(request.app.state.database).remove(
        tenant_id, business_id, actor, reference_id, payload.operation_id
    )
    return Response(status_code=204)
