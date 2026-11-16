"""Private pieces, exact-version owner review and download without publication."""

from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.api.deps import Actor
from app.schemas.content_pieces import PieceDecision, PieceDecisionRead, PieceFromPreview, PieceRead
from app.schemas.piece_feedback import PieceFeedbackWrite
from app.services.content_pieces import ContentPieceService

pieces_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/content-pieces",
    tags=["content-pieces"],
)


def service(request: Request) -> ContentPieceService:
    return ContentPieceService(request.app.state.settings, request.app.state.database)


@pieces_router.post("/from-preview", response_model=PieceRead, status_code=201)
async def from_preview(
    tenant_id: UUID, business_id: UUID, body: PieceFromPreview, request: Request, response: Response, actor: Actor
) -> PieceRead:
    response.headers["Cache-Control"] = "no-store"
    return await service(request).from_preview(tenant_id, business_id, actor, body)


@pieces_router.get("", response_model=list[PieceRead])
async def list_pieces(
    tenant_id: UUID, business_id: UUID, request: Request, response: Response, actor: Actor
) -> list[PieceRead]:
    response.headers["Cache-Control"] = "no-store"
    return await service(request).list(tenant_id, business_id, actor)


@pieces_router.get("/message-receipts")
async def message_receipts(tenant_id: UUID, business_id: UUID, request: Request, response: Response, actor: Actor):
    from app.services.message_creation_delivery import list_product_messages

    response.headers["Cache-Control"] = "no-store"
    return await list_product_messages(
        request.app.state.settings, request.app.state.database, tenant_id, business_id, actor
    )


@pieces_router.get("/{piece_id}", response_model=PieceRead)
async def get_piece(
    tenant_id: UUID, business_id: UUID, piece_id: UUID, request: Request, response: Response, actor: Actor
) -> PieceRead:
    response.headers["Cache-Control"] = "no-store"
    return await service(request).get(tenant_id, business_id, actor, piece_id)


@pieces_router.post("/{piece_id}/decisions", response_model=PieceDecisionRead)
async def decide_piece(
    tenant_id: UUID,
    business_id: UUID,
    piece_id: UUID,
    body: PieceDecision,
    request: Request,
    response: Response,
    actor: Actor,
) -> PieceDecisionRead:
    response.headers["Cache-Control"] = "no-store"
    return await service(request).decide(tenant_id, business_id, actor, piece_id, body)


@pieces_router.get("/{piece_id}/versions/{version_id}/artifacts/{artifact_id}/download-link")
async def download_link(
    tenant_id: UUID,
    business_id: UUID,
    piece_id: UUID,
    version_id: UUID,
    artifact_id: UUID,
    request: Request,
    response: Response,
    actor: Actor,
) -> dict[str, str]:
    response.headers["Cache-Control"] = "no-store"
    return {"url": await service(request).download(tenant_id, business_id, actor, piece_id, version_id, artifact_id)}


@pieces_router.get("/feedback/history")
async def feedback_history(tenant_id: UUID, business_id: UUID, request: Request, response: Response, actor: Actor):
    from app.services.piece_feedback import PieceFeedbackService

    response.headers["Cache-Control"] = "no-store"
    return await PieceFeedbackService(request.app.state.settings, request.app.state.database).list(
        tenant_id, business_id, actor
    )


@pieces_router.get("/{piece_id}/feedback")
async def piece_feedback_list(
    tenant_id: UUID, business_id: UUID, piece_id: UUID, request: Request, response: Response, actor: Actor
):
    from app.services.piece_feedback import PieceFeedbackService

    response.headers["Cache-Control"] = "no-store"
    return await PieceFeedbackService(request.app.state.settings, request.app.state.database).list(
        tenant_id, business_id, actor, piece_id
    )


@pieces_router.post("/{piece_id}/feedback", status_code=201)
async def piece_feedback_write(
    tenant_id: UUID,
    business_id: UUID,
    piece_id: UUID,
    body: PieceFeedbackWrite,
    request: Request,
    response: Response,
    actor: Actor,
):
    from app.services.piece_feedback import PieceFeedbackService

    response.headers["Cache-Control"] = "no-store"
    return await PieceFeedbackService(request.app.state.settings, request.app.state.database).record(
        tenant_id, business_id, actor, piece_id, body
    )


@pieces_router.delete("/feedback/{feedback_id}", status_code=204)
async def piece_feedback_remove(tenant_id: UUID, business_id: UUID, feedback_id: UUID, request: Request, actor: Actor):
    from app.services.piece_feedback import PieceFeedbackService

    await PieceFeedbackService(request.app.state.settings, request.app.state.database).remove(
        tenant_id, business_id, actor, feedback_id
    )
