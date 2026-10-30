"""Owner requests and inspects private image/video previews; no publishing action."""

from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.adapters.material_media import MaterialStore
from app.api.deps import Actor
from app.schemas.media_previews import PreviewRead, PreviewRequest, VisualAIConsent, VisualAIStatus
from app.services.media_previews import MediaPreviewService
from app.services.visual_consent import VisualConsentService
from app.services.visual_request_trace import VisualRequestTraceService

previews_router = APIRouter(
    prefix="/api/v1/organizations/{tenant_id}/businesses/{business_id}/media-previews",
    tags=["media-previews"],
)


def service(request: Request) -> MediaPreviewService:
    return MediaPreviewService(request.app.state.settings, request.app.state.database)


@previews_router.get("/visual-consent", response_model=VisualAIStatus)
async def visual_consent_status(
    tenant_id: UUID, business_id: UUID, request: Request, actor: Actor
) -> dict[str, bool | str]:
    return await VisualConsentService(request.app.state.settings, request.app.state.database).status(
        tenant_id, business_id, actor
    )


@previews_router.put("/visual-consent", response_model=VisualAIStatus)
async def set_visual_consent(
    tenant_id: UUID, business_id: UUID, body: VisualAIConsent, request: Request, actor: Actor
) -> dict[str, bool | str]:
    return await VisualConsentService(request.app.state.settings, request.app.state.database).set(
        tenant_id, business_id, actor, body.accepted
    )


@previews_router.post("", response_model=PreviewRead, status_code=202)
async def request_preview(
    tenant_id: UUID, business_id: UUID, body: PreviewRequest, request: Request, actor: Actor
) -> PreviewRead:
    return await service(request).request(tenant_id, business_id, actor, body)


@previews_router.get("", response_model=list[PreviewRead])
async def list_previews(tenant_id: UUID, business_id: UUID, request: Request, actor: Actor) -> list[PreviewRead]:
    return await service(request).list(tenant_id, business_id, actor)


@previews_router.get("/{preview_id}/download-link")
async def download_link(
    tenant_id: UUID, business_id: UUID, preview_id: UUID, request: Request, actor: Actor
) -> dict[str, str]:
    key = await service(request).file_key(tenant_id, business_id, actor, preview_id, review=True)
    mime_type = "video/mp4" if key.endswith(".mp4") else "image/jpeg"
    return {"url": await MaterialStore(request.app.state.settings).signed_url(key, mime_type)}


@previews_router.get("/{preview_id}/request-trace")
async def visual_request_trace(
    tenant_id: UUID, business_id: UUID, preview_id: UUID, request: Request, response: Response, actor: Actor
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    return await VisualRequestTraceService(request.app.state.settings, request.app.state.database).read(
        tenant_id, business_id, actor, preview_id
    )
