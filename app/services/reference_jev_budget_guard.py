"""Durable Jev reservation bound to a live Google executor and private batch."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.db.session import Database
from app.services.reference_jev_request_mac import jev_request_mac


@dataclass(frozen=True, repr=False)
class JevGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    search: UUID
    effect: UUID
    pilot: UUID
    event: UUID
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int
    parent_google_effect: UUID
    parent_executor_token: UUID
    source_batch_mac: str
    context_version: int


class JevGuardStateError(Exception):
    """Stable error without effect contents or credentials."""


class DatabaseJevBudgetGuard:
    """A single executor obtains a committed reservation before Jev HTTP."""

    def __init__(self, database: Database, context: JevGuardContext) -> None:
        self._database = database
        self._context = context
        self._attempted = False
        self._executor_token: UUID | None = None

    async def claim(self, operation_id: UUID, request: JevChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        context = self._context
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
        async with self._database.transaction(context.tenant, context.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_jev_claim(:effect,:event,:mac,:business,:search,:pilot,
                  :amount,:key_version,:tariff_version,:credential_version,:charge_class,
                  :parent,:parent_token,:batch_mac,:context_version)"""),
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
                    "charge_class": f"jev-model:{request.model}",
                    "parent": context.parent_google_effect,
                    "parent_token": context.parent_executor_token,
                    "batch_mac": context.source_batch_mac,
                    "context_version": context.context_version,
                },
            )
        if result["created"] is not True:
            return False
        self._executor_token = UUID(result["executor_token"])
        return True

    async def uncertain(self) -> None:
        if self._executor_token is None:
            raise JevGuardStateError("JEV_EXECUTOR_NOT_CLAIMED")
        context = self._context
        async with self._database.transaction(context.tenant, context.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": context.effect, "token": self._executor_token},
            )

    def execution_token(self) -> UUID:
        """Return the in-memory fence to the trusted effect coordinator only."""
        if self._executor_token is None:
            raise JevGuardStateError("JEV_EXECUTOR_NOT_CLAIMED")
        return self._executor_token
