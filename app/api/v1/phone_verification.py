"""Business phone possession checks; no code is accepted without provider approval."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.api.deps import Actor
from app.services.phone_verification import PhoneVerificationService

phone_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/phone-verification",
    tags=["phone-verification"],
)


class PhoneCode(BaseModel):
    code: str = Field(pattern=r"^\d{4,10}$")


def service(request: Request) -> PhoneVerificationService:
    return PhoneVerificationService(
        request.app.state.settings, request.app.state.database, request.app.state.phone_provider
    )


@phone_router.get("")
async def phone_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, Any]:
    return await service(request).status(tenant_id, business_id, actor)


@phone_router.post("", status_code=202)
async def phone_start(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, str]:
    return await service(request).start(tenant_id, business_id, actor)


@phone_router.post("/confirm")
async def phone_confirm(
    tenant_id: UUID, business_id: UUID, payload: PhoneCode, request: Request, actor: Actor
) -> dict[str, str]:
    return await service(request).confirm(tenant_id, business_id, actor, payload.code)
