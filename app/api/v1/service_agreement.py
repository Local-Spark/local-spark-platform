"""Business-scoped notice and agreement state."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.services.service_agreement import ServiceAgreementService

agreement_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/service-agreement",
    tags=["service-agreement"],
)


@agreement_router.get("")
async def agreement_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, Any]:
    return await ServiceAgreementService(request.app.state.settings, request.app.state.database).status(
        tenant_id, business_id, actor
    )
