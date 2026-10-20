from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Response

from app.api.deps import Actor, Session, Tenant
from app.schemas.business import BusinessCreate, BusinessCreated, BusinessPage
from app.services.business import create_business, list_businesses

api_router = APIRouter(prefix="/api/v1")


@api_router.post("/businesses", response_model=BusinessCreated, status_code=201, tags=["businesses"])
async def business_create(
    payload: BusinessCreate,
    response: Response,
    session: Session,
    actor: Actor,
    x_tenant_id: Tenant,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=128, pattern=r"^[\w.-]+$")
    ],
) -> BusinessCreated:
    result = await create_business(session, x_tenant_id, actor, idempotency_key, payload)
    if result.replayed:
        response.status_code = 200
    return result


@api_router.get("/businesses", response_model=BusinessPage, tags=["businesses"])
async def business_list(
    session: Session,
    actor: Actor,
    x_tenant_id: Tenant,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    after: UUID | None = None,
) -> BusinessPage:
    return await list_businesses(session, x_tenant_id, actor, limit, after)
