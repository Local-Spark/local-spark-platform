"""Owner-only brand kit selection, edits and private logo upload."""

import json
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.api.deps import Actor
from app.schemas.brand_kits import (
    BrandKitCatalog,
    BrandKitConfirmRequest,
    BrandKitDraftRequest,
    BrandKitLogoRead,
    BrandKitLogoUpload,
    BrandKitLogoUrl,
    BrandKitState,
    BrandKitVersion,
)
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService

brand_kits_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/brand-kit",
    tags=["brand-kits"],
)


def service(request: Request) -> BrandKitService:
    return BrandKitService(request.app.state.settings, request.app.state.database)


@brand_kits_router.get("/catalog", response_model=BrandKitCatalog)
async def kit_catalog(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> BrandKitCatalog:
    return await service(request).catalog(tenant_id, business_id, actor)


@brand_kits_router.get("", response_model=BrandKitState)
async def kit_read(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> BrandKitState:
    return await service(request).read(tenant_id, business_id, actor)


@brand_kits_router.put("/draft", response_model=BrandKitState)
async def kit_draft(
    tenant_id: UUID, business_id: UUID, body: BrandKitDraftRequest, request: Request, actor: Actor
) -> BrandKitState:
    return await service(request).draft(tenant_id, business_id, actor, body)


@brand_kits_router.post("/confirm", response_model=BrandKitState)
async def kit_confirm(
    tenant_id: UUID, business_id: UUID, body: BrandKitConfirmRequest, request: Request, actor: Actor
) -> BrandKitState:
    return await service(request).confirm(tenant_id, business_id, actor, body)


@brand_kits_router.get("/history", response_model=list[BrandKitVersion])
async def kit_history(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> list[BrandKitVersion]:
    return await service(request).history(tenant_id, business_id, actor)


@brand_kits_router.post(
    "/logo",
    response_model=BrandKitLogoRead,
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": BrandKitLogoUpload.model_json_schema()}},
        }
    },
)
async def logo_upload(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> BrandKitLogoRead:
    limit = 3_000_000
    declared = request.headers.get("content-length")
    if declared is not None and (not declared.isdigit() or int(declared) > limit):
        raise AuthError("BRAND_KIT_LOGO_SIZE", 413)
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise AuthError("BRAND_KIT_LOGO_INVALID", 415)
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > limit:
            raise AuthError("BRAND_KIT_LOGO_SIZE", 413)
        data.extend(chunk)
    try:
        body = BrandKitLogoUpload.model_validate(json.loads(data))
    except (ValidationError, ValueError, UnicodeDecodeError) as exc:
        raise AuthError("BRAND_KIT_LOGO_INVALID", 422) from exc
    return await service(request).upload_logo(tenant_id, business_id, actor, body)


@brand_kits_router.post("/logo/reconcile", response_model=dict[str, int])
async def logo_reconcile(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, int]:
    return {"reconciled": await service(request).reconcile_pending_logos(tenant_id, business_id, actor)}


@brand_kits_router.get("/logo/{logo_id}", response_model=BrandKitLogoUrl)
async def logo_url(
    tenant_id: UUID, business_id: UUID, logo_id: UUID, request: Request, actor: Actor
) -> BrandKitLogoUrl:
    return await service(request).logo_url(tenant_id, business_id, actor, logo_id)
