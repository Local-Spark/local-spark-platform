"""Admit a Jev intent only from a live Google executor and bound batch.

The request body and credentials are authenticated in memory. They must never
be passed to Temporal or persisted in an intent, audit record, event or log.
"""

from dataclasses import replace
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.db.session import Database
from app.services.reference_jev_budget_guard import JevGuardContext
from app.services.reference_jev_request_mac import jev_request_mac


class JevIntentError(Exception):
    """A stable error without request data or credentials."""


def jev_effect_id(google_effect: UUID) -> UUID:
    return uuid5(google_effect, "reference-jev-similarity-v1")


async def create_jev_intent(
    database: Database,
    context: JevGuardContext,
    google_event: UUID,
    request: JevChargeableRequest,
) -> JevGuardContext:
    """Commit intent and event before a guard can reserve or send the request."""
    if context.effect != jev_effect_id(context.parent_google_effect):
        raise JevIntentError("JEV_EFFECT_ID_INVALID")
    mac = jev_request_mac(
        context.key,
        key_version=context.key_version,
        tariff_version=context.tariff_version,
        credential_version=context.credential_version,
        tenant=context.tenant,
        business=context.business,
        actor=context.actor,
        search=context.search,
        effect=context.effect,
        pilot=context.pilot,
        parent_google_effect=context.parent_google_effect,
        source_batch_mac=context.source_batch_mac,
        context_version=context.context_version,
        reserved_usd_micros=context.reserved_usd_micros,
        request=request,
    )
    async with database.transaction(context.tenant, context.actor) as session:
        event_id = await session.scalar(
            text("""SELECT public.reference_jev_intent(:business,:search,:google,:google_event,:google_token,
              :jev,:jev_event,:mac,:key,:tariff,:credential,:charge,:amount,:batch,:context_version)"""),
            {
                "business": context.business,
                "search": context.search,
                "google": context.parent_google_effect,
                "google_event": google_event,
                "google_token": context.parent_executor_token,
                "jev": context.effect,
                "jev_event": context.event,
                "mac": mac,
                "key": context.key_version,
                "tariff": context.tariff_version,
                "credential": context.credential_version,
                "charge": f"jev-model:{request.model}",
                "amount": context.reserved_usd_micros,
                "batch": context.source_batch_mac,
                "context_version": context.context_version,
            },
        )
    return replace(context, event=event_id)
