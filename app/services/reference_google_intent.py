"""Admit a Places intent against an existing private search; no provider IO."""

from dataclasses import replace
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.google_places import PlacesChargeableRequest
from app.db.session import Database
from app.services.reference_places_budget_guard import PlacesGuardContext
from app.services.reference_places_request_mac import places_request_mac


class GoogleIntentError(Exception):
    """A stable error that contains no request parameters or credentials."""


def google_effect_id(search: UUID) -> UUID:
    return uuid5(search, "reference-google-nearby-v1")


async def create_google_intent(
    database: Database, context: PlacesGuardContext, request: PlacesChargeableRequest
) -> PlacesGuardContext:
    """Commit a single intention and outbox event before reserving or sending."""
    if context.effect != google_effect_id(context.search):
        raise GoogleIntentError("GOOGLE_EFFECT_ID_INVALID")
    mac = places_request_mac(
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
        context_version=context.context_version,
        reserved_usd_micros=context.reserved_usd_micros,
        request=request,
    )
    async with database.transaction(context.tenant, context.actor) as session:
        event = await session.scalar(
            text("""SELECT public.reference_google_intent(:business,:search,:effect,:event,:pilot,:mac,
              :key,:tariff,:credential,:mask,:amount,:context_version)"""),
            {
                "business": context.business,
                "search": context.search,
                "effect": context.effect,
                "event": context.event,
                "pilot": context.pilot,
                "mac": mac,
                "key": context.key_version,
                "tariff": context.tariff_version,
                "credential": context.credential_version,
                "mask": request.field_mask,
                "amount": context.reserved_usd_micros,
                "context_version": context.context_version,
            },
        )
    return replace(context, event=event)
