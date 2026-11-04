"""Owner-managed shop address; saving never calls a geocoding provider."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.business_address import BusinessAddressRead, BusinessAddressWrite
from app.schemas.business_geocoding import GeocodeConfirmation, GeocodeRead, GeocodeRequest
from app.services.business_address import BusinessAddressService
from app.services.business_geocoding import BusinessGeocodingService

business_address_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/address", tags=["business-address"]
)


@business_address_router.get("", response_model=BusinessAddressRead)
async def read_address(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> BusinessAddressRead:
    return await BusinessAddressService(request.app.state.database).read(tenant_id, business_id, actor)


@business_address_router.put("", response_model=BusinessAddressRead)
async def save_address(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, payload: BusinessAddressWrite
) -> BusinessAddressRead:
    return await BusinessAddressService(request.app.state.database).save(tenant_id, business_id, actor, payload)


@business_address_router.get("/geocoding", response_model=GeocodeRead)
async def read_geocoding(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> GeocodeRead:
    return await BusinessGeocodingService(request.app.state.database, request.app.state.settings).read(
        tenant_id, business_id, actor
    )


@business_address_router.post("/geocoding", response_model=GeocodeRead, status_code=202)
async def request_geocoding(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, payload: GeocodeRequest
) -> GeocodeRead:
    return await BusinessGeocodingService(request.app.state.database, request.app.state.settings).request(
        tenant_id, business_id, actor, payload
    )


@business_address_router.post("/geocoding/confirm", response_model=GeocodeRead)
async def confirm_geocoding(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, payload: GeocodeConfirmation
) -> GeocodeRead:
    return await BusinessGeocodingService(request.app.state.database, request.app.state.settings).confirm(
        tenant_id, business_id, actor, payload
    )
