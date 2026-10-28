"""Private business collection photo contracts; no provider URLs in snapshots."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SpaceKind = Literal["facade", "counter", "room", "environment"]


class CollectionPhotoMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)
    item_id: UUID | None = None
    space_kind: SpaceKind | None = None
    sort_order: int = Field(default=0, ge=0, le=9999)

    @model_validator(mode="after")
    def one_destination(self) -> Self:
        if (self.item_id is None) == (self.space_kind is None):
            raise ValueError("Choose an item or a space category")
        return self


class CollectionPhotoUpload(CollectionPhotoMetadata):
    operation_id: UUID
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    content_base64: str = Field(min_length=1, max_length=2_800_000)
    rights_confirmed: Literal[True]


class CollectionPhotoPromotion(CollectionPhotoMetadata):
    operation_id: UUID
    material_id: UUID
    rights_confirmed: Literal[True]
    keep_in_collection: Literal[True]


class CollectionPhotoUpdate(CollectionPhotoMetadata):
    operation_id: UUID
    expected_version: int = Field(ge=1)
    status: Literal["active", "archived"]


class CollectionPhoto(BaseModel):
    id: UUID
    version: int
    title: str
    item_id: UUID | None
    space_kind: SpaceKind | None
    sort_order: int
    status: Literal["active", "archived", "deleted"]
    source: Literal["upload", "whatsapp"]
    source_material_id: UUID | None
    mime_type: str | None
    sha256: str | None
    source_sha256: str | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime
    pending_change: bool = False
    pending_change_error: str | None = None
    pending_activation: bool = False
    pending_recovery: bool = False
    pending_cancelable: bool = False
    pending_uncertain: bool = False
    pending_quarantined: bool = False


class CollectionPhotoVersion(BaseModel):
    version: int
    action: str
    photo: CollectionPhoto
    created_at: datetime


class CollectionPhotoUrl(BaseModel):
    url: str
    expires_in_seconds: Literal[120] = 120


class CollectionPhotoDeletion(BaseModel):
    status: Literal["deleted", "deleting", "waiting_for_generation", "quarantined"]
