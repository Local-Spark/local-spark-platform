from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    timezone: str = "America/Sao_Paulo"

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class BusinessRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    created_at: datetime


class BusinessCreated(BaseModel):
    business: BusinessRead
    operation_id: UUID
    replayed: bool = False


class BusinessPage(BaseModel):
    items: list[BusinessRead]
    next_cursor: UUID | None
