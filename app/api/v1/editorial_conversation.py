"""Local-only editorial conversation rehearsal endpoints."""

from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.deps import Actor
from app.schemas.editorial_conversation import ConversationDecision, DecideMessage, SimulateMessage
from app.services.editorial_conversation import EditorialConversationService

conversation_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-conversation",
    tags=["editorial-conversation"],
)


@conversation_router.get("", response_model=list[ConversationDecision])
async def list_decisions(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor, limit: int = Query(20, ge=1, le=50)
) -> list[ConversationDecision]:
    return await EditorialConversationService(request.app.state.settings, request.app.state.database).list(
        tenant_id, business_id, actor, limit
    )


@conversation_router.post("/simulate", response_model=ConversationDecision)
async def simulate(
    tenant_id: UUID, business_id: UUID, payload: SimulateMessage, request: Request, actor: Actor
) -> ConversationDecision:
    return await EditorialConversationService(request.app.state.settings, request.app.state.database).simulate(
        tenant_id, business_id, actor, payload
    )


@conversation_router.post("/{decision_id}/decide", response_model=ConversationDecision)
async def decide(
    tenant_id: UUID, business_id: UUID, decision_id: UUID, payload: DecideMessage, request: Request, actor: Actor
) -> ConversationDecision:
    return await EditorialConversationService(request.app.state.settings, request.app.state.database).decide(
        tenant_id, business_id, actor, decision_id, payload.confirmed
    )
