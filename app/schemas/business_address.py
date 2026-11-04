"""The owner's declared shop address, independent of a search origin."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.editorial_context import ReferenceAddress, StateCode


class ShopAddress(ReferenceAddress):
    street: str = Field(min_length=1, max_length=120)
    number: str = Field(min_length=1, max_length=30)
    city: str = Field(min_length=1, max_length=120)
    state_code: StateCode


class BusinessAddressWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_version: int = Field(ge=0, le=9_223_372_036_854_775_806, strict=True)
    address: ShopAddress


class BusinessAddressRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    address: ShopAddress | None
    updated_at: datetime | None
