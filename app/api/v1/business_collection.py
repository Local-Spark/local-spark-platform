"""Owner-only progressive collection photos and explicit durable WhatsApp copies."""

import json
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import ValidationError

from app.api.deps import Actor
from app.schemas.business_collection import (
    CollectionPhoto,
    CollectionPhotoDeletion,
    CollectionPhotoPromotion,
    CollectionPhotoUpdate,
    CollectionPhotoUpload,
    CollectionPhotoUrl,
    CollectionPhotoVersion,
)
from app.services.auth import AuthError
from app.services.business_collection import BusinessCollectionService

collection_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/collection/photos",
    tags=["business-collection"],
)


def service(request: Request) -> BusinessCollectionService:
    return BusinessCollectionService(request.app.state.settings, request.app.state.database)


@collection_router.get("", response_model=list[CollectionPhoto])
async def photo_list(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> list[CollectionPhoto]:
    return await service(request).list_photos(tenant_id, business_id, actor)


@collection_router.post(
    "",
    response_model=CollectionPhoto,
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": CollectionPhotoUpload.model_json_schema()}},
        }
    },
)
async def photo_upload(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> CollectionPhoto:
    limit = 3_000_000
    declared = request.headers.get("content-length")
    if declared is not None and (not declared.isdigit() or int(declared) > limit):
        raise AuthError("COLLECTION_PHOTO_SIZE", 413)
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise AuthError("COLLECTION_PHOTO_INVALID", 415)
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > limit:
            raise AuthError("COLLECTION_PHOTO_SIZE", 413)
        data.extend(chunk)
    try:
        body = CollectionPhotoUpload.model_validate(json.loads(data))
    except (ValidationError, ValueError, UnicodeDecodeError) as exc:
        raise AuthError("COLLECTION_PHOTO_INVALID", 422) from exc
    return await service(request).upload(tenant_id, business_id, actor, body)


@collection_router.post("/from-whatsapp", response_model=CollectionPhoto, status_code=201)
async def photo_promote(
    tenant_id: UUID,
    business_id: UUID,
    body: CollectionPhotoPromotion,
    request: Request,
    actor: Actor,
) -> CollectionPhoto:
    return await service(request).promote(tenant_id, business_id, actor, body)


@collection_router.get("/removals", response_model=dict[str, int])
async def photo_removals(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, int]:
    return await service(request).removals(tenant_id, business_id, actor)


@collection_router.post("/reconcile", response_model=dict[str, int])
async def photo_reconcile(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, int]:
    return {"reconciled": await service(request).reconcile(tenant_id, business_id, actor)}


@collection_router.patch("/{photo_id}", response_model=CollectionPhoto)
async def photo_update(
    tenant_id: UUID,
    business_id: UUID,
    photo_id: UUID,
    body: CollectionPhotoUpdate,
    request: Request,
    actor: Actor,
) -> CollectionPhoto:
    return await service(request).update(tenant_id, business_id, actor, photo_id, body)


@collection_router.get("/{photo_id}/url", response_model=CollectionPhotoUrl)
async def photo_url(
    tenant_id: UUID,
    business_id: UUID,
    photo_id: UUID,
    request: Request,
    actor: Actor,
) -> CollectionPhotoUrl:
    return await service(request).url(tenant_id, business_id, actor, photo_id)


@collection_router.post("/{photo_id}/resume", response_model=CollectionPhoto)
async def photo_resume(
    tenant_id: UUID, business_id: UUID, photo_id: UUID, request: Request, actor: Actor
) -> CollectionPhoto:
    return await service(request).resume_upload(tenant_id, business_id, actor, photo_id)


@collection_router.get("/{photo_id}/history", response_model=list[CollectionPhotoVersion])
async def photo_history(
    tenant_id: UUID,
    business_id: UUID,
    photo_id: UUID,
    request: Request,
    actor: Actor,
) -> list[CollectionPhotoVersion]:
    return await service(request).history(tenant_id, business_id, actor, photo_id)


@collection_router.delete("/{photo_id}", response_model=CollectionPhotoDeletion, status_code=202)
async def photo_delete(
    tenant_id: UUID,
    business_id: UUID,
    photo_id: UUID,
    request: Request,
    actor: Actor,
    operation_id: UUID = Query(),
    expected_version: int = Query(ge=0),
) -> CollectionPhotoDeletion:
    return await service(request).delete(tenant_id, business_id, actor, photo_id, operation_id, expected_version)
