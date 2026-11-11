"""Owner request and status; material paths and provider payloads are server-only."""

from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from app.api.deps import Actor
from app.schemas.motion_production import MotionRequest, MotionRequestRead
from app.schemas.motion_storyboards import StoryboardDecision, StoryboardRead
from app.services.motion_requests import MotionRequestService
from app.services.motion_storyboards import MotionStoryboards

motion_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/motion-requests", tags=["motion"]
)


@motion_router.get("", response_model=list[MotionRequestRead])
async def list_motion(
    tenant_id: UUID, business_id: UUID, request: Request, response: Response, actor: Actor
) -> list[MotionRequestRead]:
    response.headers["Cache-Control"] = "no-store"
    return await MotionRequestService(request.app.state.settings, request.app.state.database).list(
        tenant_id, business_id, actor
    )


@motion_router.post("", response_model=MotionRequestRead, status_code=202)
async def request_motion(
    tenant_id: UUID, business_id: UUID, body: MotionRequest, request: Request, response: Response, actor: Actor
) -> MotionRequestRead:
    response.headers["Cache-Control"] = "no-store"
    return await MotionRequestService(request.app.state.settings, request.app.state.database).create(
        tenant_id, business_id, actor, body
    )


@motion_router.get("/{request_id}", response_model=MotionRequestRead)
async def read_motion(
    tenant_id: UUID, business_id: UUID, request_id: UUID, request: Request, response: Response, actor: Actor
) -> MotionRequestRead:
    response.headers["Cache-Control"] = "no-store"
    return await MotionRequestService(request.app.state.settings, request.app.state.database).get(
        tenant_id, business_id, actor, request_id
    )


def boards(request: Request) -> MotionStoryboards:
    from app.adapters.material_media import MaterialStore
    from app.services.motion_storyboards import MotionStoryboards

    settings = request.app.state.settings
    return MotionStoryboards(MotionRequestService(settings, request.app.state.database), MaterialStore(settings))


@motion_router.get("/{request_id}/storyboard", response_model=StoryboardRead)
async def read_storyboard(
    tenant_id: UUID, business_id: UUID, request_id: UUID, request: Request, response: Response, actor: Actor
) -> StoryboardRead:
    response.headers["Cache-Control"] = "no-store"
    service = boards(request)
    _, board, payload = await service.load(tenant_id, business_id, actor, request_id)
    return service.present(board, payload)


@motion_router.get("/{request_id}/storyboard/gallery", response_class=HTMLResponse)
async def storyboard_gallery(
    tenant_id: UUID, business_id: UUID, request_id: UUID, request: Request, actor: Actor
) -> HTMLResponse:
    content = await boards(request).gallery(tenant_id, business_id, actor, request_id)
    return HTMLResponse(
        content,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; img-src data:; style-src 'unsafe-inline'; frame-ancestors 'none'"
            ),
        },
    )


@motion_router.post("/{request_id}/storyboard/decisions")
async def decide_storyboard(
    tenant_id: UUID,
    business_id: UUID,
    request_id: UUID,
    body: StoryboardDecision,
    request: Request,
    response: Response,
    actor: Actor,
) -> dict[str, str]:
    response.headers["Cache-Control"] = "no-store"
    return await boards(request).decide(tenant_id, business_id, actor, request_id, body)
