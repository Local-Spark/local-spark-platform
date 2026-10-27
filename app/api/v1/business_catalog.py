"""Owner-only business catalog, independent of billing and visual kit selection."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Request

from app.api.deps import Actor
from app.schemas.business_catalog import CatalogHistoryItem, CatalogRead, CatalogUpdate
from app.services.business_catalog import BusinessCatalogService

catalog_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/catalog", tags=["business-catalog"]
)


def service(request: Request) -> BusinessCatalogService:
    return BusinessCatalogService(request.app.state.database)


@catalog_router.get("", response_model=CatalogRead)
async def catalog_read(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> CatalogRead:
    return await service(request).read(tenant_id, business_id, actor)


@catalog_router.put("", response_model=CatalogRead)
async def catalog_update(
    tenant_id: UUID, business_id: UUID, payload: CatalogUpdate, request: Request, actor: Actor
) -> CatalogRead:
    return await service(request).update(tenant_id, business_id, actor, payload)


@catalog_router.get("/history", response_model=list[CatalogHistoryItem])
async def catalog_history(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor
) -> list[CatalogHistoryItem]:
    return await service(request).history(tenant_id, business_id, actor)


@catalog_router.get("/versions/{version}", response_model=CatalogRead)
async def catalog_version(
    tenant_id: UUID, business_id: UUID, version: Annotated[int, Path(ge=1)], request: Request, actor: Actor
) -> CatalogRead:
    return await service(request).read(tenant_id, business_id, actor, version)
