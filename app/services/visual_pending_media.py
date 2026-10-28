"""Apply previously validated owner requests after visual work finishes.

The caller holds the business gate and applies these mutations in its existing
transaction. No object-store or provider calls are made here.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brand_kits import BrandKitConfirmRequest
from app.schemas.business_collection import CollectionPhotoUpdate
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.business_catalog import require_catalog_owner
from app.services.business_collection import BusinessCollectionService


class _PhotoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_id: UUID
    body: CollectionPhotoUpdate


class _PhotoDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_id: UUID
    operation_id: UUID
    expected_version: int = Field(ge=1)


class _PhotoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_id: UUID


async def apply_kit_pending_in_session(
    session: Any, tenant: UUID, business: UUID, actor: UUID, kind: str, payload: Any
) -> None:
    if kind != "kit_confirm":
        raise AuthError("VISUAL_PENDING_KIND_INVALID", 409)
    await BrandKitService._owner(session, tenant, business, actor)
    body = BrandKitConfirmRequest.model_validate(payload)
    await BrandKitService._confirm_in_session(session, tenant, business, actor, body)


async def apply_photo_pending_in_session(
    session: Any, tenant: UUID, business: UUID, actor: UUID, kind: str, payload: Any
) -> None:
    await require_catalog_owner(session, tenant, business, actor)
    if kind == "photo_create":
        creation = _PhotoCreate.model_validate(payload)
        await BusinessCollectionService._activate_staged_in_session(session, tenant, business, actor, creation.photo_id)
    elif kind == "photo_update":
        update = _PhotoUpdate.model_validate(payload)
        await BusinessCollectionService._update_in_session(
            session, tenant, business, actor, update.photo_id, update.body
        )
    elif kind == "photo_delete":
        deletion = _PhotoDelete.model_validate(payload)
        await BusinessCollectionService._delete_in_session(
            session, tenant, business, actor, deletion.photo_id, deletion.operation_id, deletion.expected_version
        )
    else:
        raise AuthError("VISUAL_PENDING_KIND_INVALID", 409)
