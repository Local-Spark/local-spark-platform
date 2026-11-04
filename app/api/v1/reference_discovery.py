"""Private, explicitly simulated reference discovery."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import Actor
from app.schemas.reference_discovery import (
    DiscoveryFixtureRead,
    DiscoveryRead,
    DiscoveryRequest,
    FixtureSelectionRead,
    FixtureSelectionRequest,
    FixtureSelectionState,
)
from app.services.reference_cycles import FixtureSelectionService
from app.services.reference_discovery import ReferenceDiscoveryService

reference_discovery_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/reference-discoveries",
    tags=["reference-discovery"],
)


@reference_discovery_router.post("/fixture-selection", response_model=FixtureSelectionRead)
async def confirm_fixture_selection(
    tenant_id: UUID, business_id: UUID, payload: FixtureSelectionRequest, request: Request, actor: Actor
) -> FixtureSelectionRead:
    return await FixtureSelectionService(request.app.state.settings, request.app.state.database).confirm(
        tenant_id, business_id, actor, payload
    )


@reference_discovery_router.get("/fixture-selection", response_model=FixtureSelectionState)
async def get_fixture_selection(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor
) -> FixtureSelectionState:
    return await FixtureSelectionService(request.app.state.settings, request.app.state.database).current(
        tenant_id, business_id, actor
    )


@reference_discovery_router.post("", response_model=DiscoveryRead)
async def request_discovery(
    tenant_id: UUID, business_id: UUID, payload: DiscoveryRequest, request: Request, actor: Actor
) -> DiscoveryRead:
    return await ReferenceDiscoveryService(request.app.state.settings, request.app.state.database).request(
        tenant_id, business_id, actor, payload.operation_id
    )


@reference_discovery_router.get("", response_model=list[DiscoveryRead])
async def list_discoveries(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> list[DiscoveryRead]:
    return await ReferenceDiscoveryService(request.app.state.settings, request.app.state.database).list_discoveries(
        tenant_id, business_id, actor
    )


@reference_discovery_router.get("/{discovery_id}", response_model=DiscoveryRead)
async def get_discovery(
    tenant_id: UUID, business_id: UUID, discovery_id: UUID, request: Request, actor: Actor
) -> DiscoveryRead:
    return await ReferenceDiscoveryService(request.app.state.settings, request.app.state.database).read(
        tenant_id, business_id, actor, discovery_id
    )


@reference_discovery_router.get("/{discovery_id}/fixtures", response_model=list[DiscoveryFixtureRead])
async def get_discovery_fixtures(
    tenant_id: UUID, business_id: UUID, discovery_id: UUID, request: Request, actor: Actor
) -> list[DiscoveryFixtureRead]:
    return await ReferenceDiscoveryService(request.app.state.settings, request.app.state.database).fixtures(
        tenant_id, business_id, actor, discovery_id
    )
