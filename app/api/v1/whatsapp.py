"""Meta callback boundary: authentication first, durable persistence before 200."""

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.adapters.meta_whatsapp import MetaWebhookError, extract_events, verify_challenge, verify_signature
from app.services.whatsapp_ingest import save_events

whatsapp_router = APIRouter(prefix="/api/v1/webhooks/whatsapp", tags=["whatsapp"])


@whatsapp_router.get("")
async def whatsapp_verify(request: Request) -> PlainTextResponse:
    params = request.query_params
    challenge = verify_challenge(
        request.app.state.settings, params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")
    )
    return PlainTextResponse(challenge)


@whatsapp_router.post("")
async def whatsapp_receive(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 262144:
            raise MetaWebhookError("WEBHOOK_TOO_LARGE", 413)
    raw = bytes(body)
    verify_signature(settings, raw, request.headers.get("x-hub-signature-256"))
    events = extract_events(settings, raw)
    database = request.app.state.meta_database
    if database is None:
        raise MetaWebhookError("WHATSAPP_UNAVAILABLE", 503)
    await save_events(database, settings, events)
    return {"status": "accepted"}
