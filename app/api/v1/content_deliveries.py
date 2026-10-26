"""Owner review of locally delivered content candidates."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.content_deliveries import ContentDecision, ContentDeliveryRead
from app.services.content_deliveries import ContentDeliveryService

deliveries_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/content-deliveries",
    tags=["content-deliveries"],
)


def service(request: Request) -> ContentDeliveryService:
    return ContentDeliveryService(request.app.state.settings, request.app.state.database, request.app.state.database)


@deliveries_router.get("", response_model=list[ContentDeliveryRead])
async def list_deliveries(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor
) -> list[ContentDeliveryRead]:
    return await service(request).list(tenant_id, business_id, actor)


@deliveries_router.post("/{delivery_id}/decision", response_model=ContentDeliveryRead)
async def decide_delivery(
    tenant_id: UUID, business_id: UUID, delivery_id: UUID, body: ContentDecision, request: Request, actor: Actor
) -> ContentDeliveryRead:
    return await service(request).decide(tenant_id, business_id, actor, delivery_id, body)
