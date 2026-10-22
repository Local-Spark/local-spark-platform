"""Owner consent and private WhatsApp material library."""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.adapters.material_media import MaterialStore
from app.api.deps import Actor
from app.services.whatsapp_materials import WhatsAppMaterialsService

materials_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-materials",
    tags=["whatsapp-materials"],
)


class ConsentRequest(BaseModel):
    accepted: Literal[True]


def service(request: Request) -> WhatsAppMaterialsService:
    return WhatsAppMaterialsService(request.app.state.settings, request.app.state.database)


@materials_router.get("/consent")
async def consent_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, bool]:
    return await service(request).consent_status(tenant_id, business_id, actor)


@materials_router.post("/consent")
async def accept_consent(
    tenant_id: UUID, business_id: UUID, body: ConsentRequest, request: Request, actor: Actor
) -> dict[str, bool]:
    return await service(request).accept_consent(tenant_id, business_id, actor)


@materials_router.delete("/consent")
async def revoke_consent(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, bool]:
    return await service(request).revoke_consent(tenant_id, business_id, actor)


@materials_router.get("")
async def list_materials(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, limit: int = Query(default=30, ge=1, le=100)
) -> dict[str, list[dict[str, Any]]]:
    return {"items": await service(request).list_materials(tenant_id, business_id, actor, limit)}


@materials_router.get("/{event_id}/download-link")
async def download_link(
    tenant_id: UUID, business_id: UUID, event_id: UUID, request: Request, actor: Actor
) -> dict[str, str]:
    key, mime_type = await service(request).file_key(tenant_id, business_id, actor, event_id)
    return {"url": await MaterialStore(request.app.state.settings).signed_url(key, mime_type)}


@materials_router.delete("/{event_id}", status_code=202)
async def delete_material(
    tenant_id: UUID, business_id: UUID, event_id: UUID, request: Request, actor: Actor
) -> dict[str, str]:
    return await service(request).delete_material(tenant_id, business_id, actor, event_id)
