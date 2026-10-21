"""Operator invitation and revocation endpoints."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from app.api.deps import Actor, Principal
from app.schemas.auth import ActionInput, EmailInput
from app.services.staff import StaffService

staff_router = APIRouter(prefix="/api/v1", tags=["operators"])
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128, pattern=r"^[\w.-]+$")]


def service(request: Request) -> StaffService:
    return StaffService(request.app.state.settings, request.app.state.auth_database)


@staff_router.get("/admin/staff")
async def staff_overview(request: Request, actor: Actor) -> dict[str, Any]:
    return await service(request).overview(actor)


@staff_router.post("/admin/staff/invitations", status_code=202)
async def invite_staff(
    payload: EmailInput, request: Request, response: Response, actor: Actor, idempotency_key: Key
) -> dict[str, Any]:
    result = await service(request).invite(actor, payload.email, idempotency_key)
    if result["replayed"]:
        response.status_code = 200
    return result


@staff_router.post("/staff/invitations/accept")
async def accept_staff_invitation(payload: ActionInput, request: Request, identity: Principal) -> dict[str, str]:
    await service(request).accept(identity, payload.token.get_secret_value())
    return {"message": "Convite aceito. Entre novamente e configure seu autenticador."}


@staff_router.get("/staff/invitations/pending")
async def pending_staff_invitation(request: Request, identity: Principal) -> dict[str, bool]:
    return await service(request).access_state(identity)


@staff_router.delete("/admin/staff/invitations/{invitation_id}", status_code=204)
async def revoke_staff_invitation(invitation_id: UUID, request: Request, actor: Actor) -> None:
    await service(request).revoke_invitation(actor, invitation_id)


@staff_router.delete("/admin/staff/{operator_id}", status_code=204)
async def revoke_operator(operator_id: UUID, request: Request, actor: Actor) -> None:
    await service(request).revoke_operator(actor, operator_id)
