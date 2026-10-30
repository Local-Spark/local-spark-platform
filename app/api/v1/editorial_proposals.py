"""Owner requests and reviews draft ideas; no publication action is exposed."""

from uuid import UUID

from fastapi import APIRouter, Query, Request, Response

from app.api.deps import Actor
from app.schemas.editorial_proposals import (
    EditorialAIConsent,
    EditorialAIStatus,
    ProposalRead,
    ProposalRequest,
    ScriptEdit,
    ScriptReview,
    ScriptVersionRead,
)
from app.services.editorial_proposals import EditorialProposalService
from app.services.jev_consent import JevConsentService

proposals_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-proposals",
    tags=["editorial-proposals"],
)


def service(request: Request) -> EditorialProposalService:
    return EditorialProposalService(request.app.state.settings, request.app.state.database)


@proposals_router.get("/jev-consent", response_model=EditorialAIStatus)
async def jev_consent_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, bool]:
    return await JevConsentService(request.app.state.settings, request.app.state.database).status(
        tenant_id, business_id, actor
    )


@proposals_router.put("/jev-consent", response_model=EditorialAIStatus)
async def set_jev_consent(
    tenant_id: UUID, business_id: UUID, body: EditorialAIConsent, request: Request, actor: Actor
) -> dict[str, bool]:
    return await JevConsentService(request.app.state.settings, request.app.state.database).set(
        tenant_id, business_id, actor, body.accepted
    )


@proposals_router.get("/consent", response_model=EditorialAIStatus)
async def consent_status(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> dict[str, bool]:
    return await service(request).consent_status(tenant_id, business_id, actor)


@proposals_router.put("/consent", response_model=EditorialAIStatus)
async def set_consent(
    tenant_id: UUID, business_id: UUID, body: EditorialAIConsent, request: Request, actor: Actor
) -> dict[str, bool]:
    return await service(request).set_consent(tenant_id, business_id, actor, body.accepted)


@proposals_router.post("", response_model=ProposalRead, status_code=202)
async def request_proposal(
    tenant_id: UUID, business_id: UUID, body: ProposalRequest, request: Request, actor: Actor
) -> ProposalRead:
    return await service(request).request(tenant_id, business_id, actor, body)


@proposals_router.get("", response_model=list[ProposalRead])
async def list_proposals(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, limit: int = Query(default=30, ge=1, le=100)
) -> list[ProposalRead]:
    return await service(request).list(tenant_id, business_id, actor, limit)


@proposals_router.get("/{proposal_id}/request-trace")
async def editorial_request_trace(
    tenant_id: UUID, business_id: UUID, proposal_id: UUID, request: Request, response: Response, actor: Actor
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    return await service(request).get_request_trace(tenant_id, business_id, actor, proposal_id)


@proposals_router.post("/{proposal_id}/script-review", response_model=ProposalRead)
async def review_script(
    tenant_id: UUID, business_id: UUID, proposal_id: UUID, body: ScriptReview, request: Request, actor: Actor
) -> ProposalRead:
    return await service(request).review_script(tenant_id, business_id, actor, proposal_id, body)


@proposals_router.post("/{proposal_id}/script-versions", response_model=ScriptVersionRead)
async def edit_script(
    tenant_id: UUID, business_id: UUID, proposal_id: UUID, body: ScriptEdit, request: Request, actor: Actor
) -> ScriptVersionRead:
    return await service(request).edit_script(tenant_id, business_id, actor, proposal_id, body)


@proposals_router.get("/{proposal_id}/script-versions", response_model=list[ScriptVersionRead])
async def list_script_versions(
    tenant_id: UUID, business_id: UUID, proposal_id: UUID, request: Request, actor: Actor
) -> list[ScriptVersionRead]:
    return await service(request).script_versions(tenant_id, business_id, actor, proposal_id)
