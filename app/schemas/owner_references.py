"""Unverified Instagram profiles explicitly indicated by the owner."""

import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def instagram_handle(value: str) -> str:
    value = value.strip()
    if "://" in value:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.netloc.lower() not in {"instagram.com", "www.instagram.com"}
            or url.query
            or url.fragment
        ):
            raise ValueError("Informe uma URL de perfil do Instagram")
        value = url.path.strip("/")
        if value.lower() in {"p", "reel", "reels", "stories", "explore", "accounts"}:
            raise ValueError("Informe um perfil, não uma página do Instagram")
    else:
        value = value.removeprefix("@")
    if not re.fullmatch(r"[A-Za-z0-9_](?:[A-Za-z0-9_.]{0,28}[A-Za-z0-9_])?", value) or ".." in value:
        raise ValueError("Informe um @ válido do Instagram")
    return value.lower()


class ReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    operation_id: UUID
    instagram: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("instagram")
    @classmethod
    def normalize_handle(cls, value: str) -> str:
        return instagram_handle(value)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return value or None


class ReferenceRemove(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


class ReferenceRead(BaseModel):
    id: UUID
    instagram_handle: str
    instagram_url: str
    note: str | None
    source: Literal["owner"] = "owner"
    access_status: Literal["not_checked"] = "not_checked"
    selected: Literal[True] = True
    created_at: datetime
