"""Administrative laboratory discovery; generation is wired separately."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import StreamingResponse

from app.adapters.material_media import MAX_BYTES
from app.api.deps import Actor, ActorSession
from app.schemas.creation_lab import LabCollectionSelection, LabContinuation, LabDraft, LabFeedback, LabStart
from app.services.auth import AuthError
from app.services.business import AccessDenied
from app.services.creation_lab_access import lab_businesses, require_lab_access
from app.services.creation_lab_attachments import CreationLabAttachments
from app.services.creation_lab_collection import CreationLabCollection
from app.services.creation_lab_context import CreationLabContext
from app.services.creation_lab_drafts import CreationLabDrafts
from app.services.creation_lab_export import CreationLabExport
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_results import CreationLabResults
from app.schemas.motion_preparation import MotionCheckpointDecision
from app.services.creation_lab_motion_requests import LabMotionRequests
from app.services.creation_lab_checkpoints import LabCheckpoints

creation_lab_router = APIRouter(prefix="/api/v1/admin/creation-lab", tags=["creation-lab"])


@creation_lab_router.get("/runs/{run_id}/results")
async def lab_results(request: Request, response: Response, actor: Actor, run_id: UUID) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabResults(request.app.state.settings, request.app.state.database).list(actor, run_id)


@creation_lab_router.post("/runs/{run_id}/feedback", status_code=201)
async def lab_feedback(
    request: Request, response: Response, actor: Actor, run_id: UUID, body: LabFeedback
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabResults(request.app.state.settings, request.app.state.database).feedback(
        actor, run_id, body
    )


@creation_lab_router.get("/runs/{run_id}/results/{version_id}/download")
async def lab_result_download(request: Request, actor: Actor, run_id: UUID, version_id: UUID) -> Response:
    mime, data = await CreationLabResults(request.app.state.settings, request.app.state.database).download(
        actor, run_id, version_id
    )
    suffix = {"video/mp4": "mp4", "image/png": "png", "image/jpeg": "jpg"}[mime]
    return Response(
        data,
        media_type=mime,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'attachment; filename="{version_id}.{suffix}"',
        },
    )


@creation_lab_router.get("/budget")
async def administrative_budget(request: Request, response: Response, actor: Actor) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabExecution(request.app.state.settings, request.app.state.database).budget(actor)


@creation_lab_router.get("/runs/{run_id}/trace/{trace_id}")
async def trace_detail(
    request: Request, response: Response, actor: Actor, run_id: UUID, trace_id: UUID
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabExecution(request.app.state.settings, request.app.state.database).trace(
        actor, run_id, trace_id
    )


@creation_lab_router.get("/access")
async def access(request: Request, response: Response, session: ActorSession, actor: Actor) -> dict[str, Any]:
    await require_lab_access(session, request.app.state.settings, actor, "admin.creation_lab.access")
    response.headers["Cache-Control"] = "no-store"
    return {"allowed": True, "trace_retention_days": 7}


@creation_lab_router.get("/businesses")
async def businesses(
    request: Request,
    response: Response,
    session: ActorSession,
    actor: Actor,
    query: str = Query(default="", max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    after: UUID | None = None,
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await lab_businesses(session, request.app.state.settings, actor, query, limit, after)


def drafts(request: Request) -> CreationLabDrafts:
    return CreationLabDrafts(request.app.state.settings, request.app.state.database)


@creation_lab_router.post("/drafts", status_code=201)
async def save_draft(request: Request, response: Response, actor: Actor, body: LabDraft) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await drafts(request).create(actor, body)


@creation_lab_router.get("/drafts")
async def history(
    request: Request, response: Response, actor: Actor, tenant_id: UUID, business_id: UUID
) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = "no-store"
    return await drafts(request).history(actor, tenant_id, business_id)


def attachments(request: Request) -> CreationLabAttachments:
    return CreationLabAttachments(request.app.state.settings, request.app.state.database)


@creation_lab_router.get("/runs/{run_id}/context")
async def business_context(
    request: Request, response: Response, actor: Actor, run_id: UUID, after: UUID | None = None
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabContext(request.app.state.settings, request.app.state.database).read(actor, run_id, after)


@creation_lab_router.put("/runs/{run_id}/collection")
async def select_collection(
    request: Request, response: Response, actor: Actor, run_id: UUID, body: LabCollectionSelection
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await CreationLabCollection(request.app.state.settings, request.app.state.database).select(
        actor, run_id, body
    )


@creation_lab_router.get("/runs/{run_id}/attachments")
async def list_attachments(request: Request, response: Response, actor: Actor, run_id: UUID) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = "no-store"
    return await attachments(request).list(actor, run_id)


@creation_lab_router.post("/runs/{run_id}/attachments", status_code=201)
async def upload_attachment(
    request: Request,
    response: Response,
    actor: Actor,
    run_id: UUID,
    operation_id: UUID,
    name: str = Query(min_length=1, max_length=200, pattern=r"^[^\x00-\x1f\x7f]+$"),
    rights_confirmed: bool = False,
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    service = attachments(request)
    await service.authorize(actor, run_id, "admin.creation_lab.attachment.upload")
    if not rights_confirmed:
        raise AuthError("CREATION_LAB_MATERIAL_RIGHTS_REQUIRED", 422)
    mime = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    maximum = MAX_BYTES[service.media_kind(mime)]
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > maximum:
            raise AuthError("CREATION_LAB_MEDIA_TOO_LARGE", 413)
        data.extend(chunk)
    return await service.upload(actor, run_id, operation_id, name, mime, bytes(data))


@creation_lab_router.get("/runs/{run_id}/attachments/{attachment_id}/download")
async def download_attachment(request: Request, actor: Actor, run_id: UUID, attachment_id: UUID) -> Response:
    metadata, data = await attachments(request).download(actor, run_id, attachment_id)
    return Response(
        data,
        media_type=metadata["mime_type"],
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'attachment; filename="{attachment_id}"',
        },
    )


@creation_lab_router.get("/runs/{run_id}/package")
@creation_lab_router.get("/runs/{run_id}/draft-package", include_in_schema=False)
async def download_draft_package(request: Request, actor: Actor, run_id: UUID) -> Response:
    data = await CreationLabExport(request.app.state.settings, request.app.state.database).download(actor, run_id)
    return Response(
        data,
        media_type="application/zip",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'attachment; filename="ensaio-{run_id}.zip"',
        },
    )


@creation_lab_router.get("/runs/{run_id}/events")
async def stream_events(
    request: Request,
    actor: Actor,
    run_id: UUID,
    last_event_id: Annotated[str, Header(pattern=r"^[0-9]{1,18}$")] = "0",
) -> StreamingResponse:
    service = drafts(request)
    cursor = int(last_event_id)
    pending = await service.events(actor, run_id, cursor)
    token = request.headers["authorization"].split(" ", 1)[1]

    async def stream() -> AsyncIterator[str]:
        nonlocal cursor, pending
        # Short transactions per poll; no row locks or DB session held across yield.
        # Bound each connection so the client periodically refreshes authentication.
        for _ in range(12):
            if await request.is_disconnected():
                return
            try:
                identity = await request.app.state.identity_verifier.authenticate(token)
                if identity.actor_id != actor:
                    raise AccessDenied
                # Recheck access before releasing any prefetched event after a wait.
                pending = await service.events(actor, run_id, cursor)
            except jwt.ExpiredSignatureError:
                yield "event: session.expired\ndata: {}\n\n"
                return
            except (jwt.InvalidTokenError, AuthError, AccessDenied):
                yield "event: access.revoked\ndata: {}\n\n"
                return
            for event in pending:
                cursor = event["sequence"]
                yield f"id: {cursor}\nevent: stage\ndata: {json.dumps(event, default=str)}\n\n"
            yield ": keep-alive\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@creation_lab_router.get("/runs/{run_id}")
async def lab_run(request: Request, response: Response, actor: Actor, run_id: UUID) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await drafts(request).get(actor, run_id)


@creation_lab_router.post("/runs/{run_id}/start", status_code=202)
async def start_run(request: Request, response: Response, actor: Actor, run_id: UUID, body: LabStart) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await (await execution_requests(request, actor, run_id)).start(actor, body)


@creation_lab_router.get("/runs/{run_id}/checkpoints")
async def lab_checkpoints(request: Request, response: Response, actor: Actor, run_id: UUID) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = "no-store"
    return await LabCheckpoints(await execution_requests(request, actor, run_id)).list(actor)


@creation_lab_router.post("/runs/{run_id}/checkpoints/{stage}/decision")
async def checkpoint_decision(
    request: Request, response: Response, actor: Actor, run_id: UUID, stage: str, body: MotionCheckpointDecision
) -> dict[str, str]:
    response.headers["Cache-Control"] = "no-store"
    return await LabCheckpoints(await execution_requests(request, actor, run_id)).decide(actor, stage, body)


@creation_lab_router.get("/runs/{run_id}/storyboard/frames/{index}")
async def lab_storyboard_frame(request: Request, actor: Actor, run_id: UUID, index: int) -> Response:
    from app.services.creation_lab_checkpoints import storyboard_frame

    data = await storyboard_frame(
        LabMotionRequests(request.app.state.settings, request.app.state.database, run_id), actor, index
    )
    return Response(
        data, media_type="image/png", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    )


@creation_lab_router.post("/runs/{run_id}/cancel")
async def cancel_lab_run(request: Request, response: Response, actor: Actor, run_id: UUID) -> dict[str, Any]:
    from app.services.creation_lab_drafts import ZERO

    service = CreationLabExecution(request.app.state.settings, request.app.state.database)
    async with service.database.transaction(ZERO, actor) as session:
        row = await service.guard(session, actor, run_id, "admin.creation_lab.run.cancel")
        if row["finished_at"] is None:
            await service.finish_locked(session, row, "cancelled", "CREATION_LAB_CANCELLED_BY_ADMIN")
    response.headers["Cache-Control"] = "no-store"
    return await drafts(request).get(actor, run_id)


async def execution_requests(request: Request, actor: UUID, run_id: UUID) -> LabMotionRequests:
    from app.services.creation_lab_images import LabImageRequests

    row = await drafts(request).get(actor, run_id)
    adapter = LabMotionRequests if row["format"] == "reel" else LabImageRequests
    return adapter(request.app.state.settings, request.app.state.database, run_id)


@creation_lab_router.post("/runs/{run_id}/continuations", status_code=201)
async def continue_run(
    request: Request, response: Response, actor: Actor, run_id: UUID, body: LabContinuation
) -> dict[str, Any]:
    from app.services.creation_lab_continuations import CreationLabContinuations

    response.headers["Cache-Control"] = "no-store"
    return await CreationLabContinuations(request.app.state.settings, request.app.state.database).create(
        actor, run_id, body
    )
