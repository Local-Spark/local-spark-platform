from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from app.adapters.stripe_billing import verify_webhook
from app.api.deps import Actor, ActorSession, Principal
from app.schemas.billing import SponsorshipCreate
from app.services import billing
from app.services.billing_processor import enqueue_webhook

billing_router = APIRouter(prefix="/api/v1", tags=["billing"])
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128, pattern=r"^[\w.-]+$")]


@billing_router.get("/billing/{tenant_id}")
async def billing_status(tenant_id: UUID, request: Request, actor: Actor, session: ActorSession) -> dict[str, Any]:
    return await billing.status(session, request.app.state.settings, tenant_id, actor)


@billing_router.post("/billing/{tenant_id}/checkout", status_code=202)
async def checkout(
    tenant_id: UUID, request: Request, identity: Principal, session: ActorSession, idempotency_key: Key
) -> dict[str, Any]:
    return await billing.request_checkout(session, request.app.state.settings, tenant_id, identity, idempotency_key)


@billing_router.get("/admin/billing")
async def billing_overview(actor: Actor, session: ActorSession) -> dict[str, Any]:
    return await billing.overview(session, actor)


@billing_router.get("/admin/organizations/{tenant_id}/billing")
async def admin_billing_status(
    tenant_id: UUID, request: Request, actor: Actor, session: ActorSession
) -> dict[str, Any]:
    return await billing.status(session, request.app.state.settings, tenant_id, actor, administrative=True)


@billing_router.post("/admin/organizations/{tenant_id}/sponsorship", status_code=201)
async def grant_sponsorship(
    tenant_id: UUID,
    payload: SponsorshipCreate,
    response: Response,
    actor: Actor,
    session: ActorSession,
    idempotency_key: Key,
) -> dict[str, Any]:
    result = await billing.sponsor(session, tenant_id, actor, idempotency_key, payload.reason)
    if result["replayed"]:
        response.status_code = 200
    return result


@billing_router.delete("/admin/organizations/{tenant_id}/sponsorship", status_code=204)
async def revoke_sponsorship(tenant_id: UUID, actor: Actor, session: ActorSession) -> None:
    await billing.revoke_sponsorship(session, tenant_id, actor)


@billing_router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> dict[str, str]:
    body = await request.body()
    if len(body) > 262144:
        raise billing.BillingError("WEBHOOK_TOO_LARGE", 413)
    event = verify_webhook(request.app.state.settings, body, request.headers.get("stripe-signature", ""))
    if event is not None:
        database = request.app.state.billing_database
        if database is None:
            raise billing.BillingError("BILLING_UNAVAILABLE", 503)
        await enqueue_webhook(database, request.app.state.settings, event)
    return {"status": "accepted"}
