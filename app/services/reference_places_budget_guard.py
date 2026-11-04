"""Restricted durable Places reservation; no provider is enabled here.

The caller must load this context from a verified intent and pass it only to an
activity. Its executor token never belongs in a workflow result or log.
"""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.google_places import PlacesChargeableRequest
from app.db.session import Database
from app.services.reference_places_request_mac import places_request_mac


@dataclass(frozen=True, repr=False)
class PlacesGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    search: UUID
    effect: UUID
    pilot: UUID
    event: UUID
    context_version: int
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int


class PlacesGuardStateError(Exception):
    """Stable internal error, without request parameters or credentials."""


class DatabasePlacesBudgetGuard:
    """One instance belongs to one executor; successful reservation commits first."""

    def __init__(self, database: Database, context: PlacesGuardContext) -> None:
        self._database = database
        self._context = context
        self._attempted = False
        self._intent_validated = False
        self._executor_token: UUID | None = None

    async def claim(self, operation_id: UUID, request: PlacesChargeableRequest) -> bool | Literal["completed_empty"]:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        context = self._context
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
        async with self._database.transaction(context.tenant, context.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_google_claim(:effect,:event,:mac,:business,:search,:pilot,
                  :amount,:key_version,:tariff_version,:credential_version,:field_mask)"""),
                {
                    "effect": context.effect,
                    "event": context.event,
                    "mac": mac,
                    "business": context.business,
                    "search": context.search,
                    "pilot": context.pilot,
                    "amount": context.reserved_usd_micros,
                    "key_version": context.key_version,
                    "tariff_version": context.tariff_version,
                    "credential_version": context.credential_version,
                    "field_mask": request.field_mask,
                },
            )
        self._intent_validated = True
        if result["created"] is not True:
            if result["state"] == "completed_empty":
                return "completed_empty"
            return False
        self._executor_token = UUID(result["executor_token"])
        return True

    def intent_validated(self) -> bool:
        """Whether the ledger verified the exact request, including its credential."""
        return self._intent_validated

    async def uncertain(self) -> None:
        if self._executor_token is None:
            raise PlacesGuardStateError("PLACES_EXECUTOR_NOT_CLAIMED")
        context = self._context
        async with self._database.transaction(context.tenant, context.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": context.effect, "token": self._executor_token},
            )

    def execution_token(self) -> UUID:
        """Return the in-memory fence to the trusted effect coordinator only."""
        if self._executor_token is None:
            raise PlacesGuardStateError("PLACES_EXECUTOR_NOT_CLAIMED")
        return self._executor_token

    async def complete_empty(self) -> None:
        if self._executor_token is None:
            raise PlacesGuardStateError("PLACES_EXECUTOR_NOT_CLAIMED")
        context = self._context
        async with self._database.transaction(context.tenant, context.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_complete_empty(:effect,:event,:token)"),
                {"effect": context.effect, "event": context.event, "token": self._executor_token},
            )
