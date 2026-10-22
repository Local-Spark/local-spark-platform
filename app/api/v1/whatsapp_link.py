"""Owner-facing, one-time WhatsApp channel proof."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.services.whatsapp_link import WhatsAppLinkService

whatsapp_link_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-link",
    tags=["whatsapp-link"],
)


def service(request: Request) -> WhatsAppLinkService:
    return WhatsAppLinkService(request.app.state.settings, request.app.state.database, request.app.state.meta_database)


@whatsapp_link_router.get("")
async def link_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, Any]:
    return await service(request).status(tenant_id, business_id, actor)


@whatsapp_link_router.post("", status_code=201)
async def link_start(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, str]:
    return await service(request).start(tenant_id, business_id, actor)


@whatsapp_link_router.post("/confirm")
async def link_confirm(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, str]:
    return await service(request).confirm(tenant_id, business_id, actor)
