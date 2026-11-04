"""Durable submission budget and recovery of the same provider run."""

from dataclasses import dataclass
from uuid import UUID, uuid5

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.apify_place_contacts import ContactsInspectionIntent
from app.db.session import Database
from app.schemas.reference_contacts_effect import ContactsChargeableRequest
from app.services.reference_contacts_request_mac import contacts_request_mac


class ContactsGuardError(Exception):
    """Stable failure without Place ID, provider content or credentials."""


@dataclass(frozen=True, repr=False)
class ContactsGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    cycle: UUID
    batch: UUID
    candidate: UUID
    place_id: str
    lookup: UUID
    effect: UUID
    event: UUID
    pilot: UUID
    context_version: int
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int
    build: str
    provider_actor_id: str


class DatabaseContactsBudgetGuard:
    """One paid submission per effect; polling never starts another collection."""

    def __init__(self, database: Database, context: ContactsGuardContext) -> None:
        self._database = database
        self._context = context
        self._attempted = False
        self._token: UUID | None = None
        self._mac: str | None = None

    def _request_mac(self, request: ContactsChargeableRequest) -> str:
        c = self._context
        if request.provider_actor_id != c.provider_actor_id:
            raise ContactsGuardError("CONTACTS_ACTOR_BINDING_INVALID")
        return contacts_request_mac(
            c.key,
            key_version=c.key_version,
            tariff_version=c.tariff_version,
            credential_version=c.credential_version,
            tenant=c.tenant,
            business=c.business,
            actor=c.actor,
            cycle=c.cycle,
            batch=c.batch,
            candidate=c.candidate,
            place_id=c.place_id,
            effect=c.effect,
            pilot=c.pilot,
            context_version=c.context_version,
            reserved_usd_micros=c.reserved_usd_micros,
            build=c.build,
            request=request,
        )

    async def claim_submission(self, operation_id: UUID, request: ContactsChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        c = self._context
        mac = self._request_mac(request)
        async with self._database.transaction(c.tenant, c.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_contacts_claim(
              :business,:lookup,:effect,:event,:mac,:pilot,:amount,:key,:tariff,:credential,:class)"""),
                {
                    "business": c.business,
                    "lookup": c.lookup,
                    "effect": c.effect,
                    "event": c.event,
                    "mac": mac,
                    "pilot": c.pilot,
                    "amount": c.reserved_usd_micros,
                    "key": c.key_version,
                    "tariff": c.tariff_version,
                    "credential": c.credential_version,
                    "class": "apify-place-contacts:" + c.build,
                },
            )
        if result["created"] is not True:
            return False
        self._token = UUID(result["executor_token"])
        self._mac = mac
        return True

    async def submission_uncertain(self, operation_id: UUID, request: ContactsChargeableRequest) -> None:
        if self._token is None or operation_id != self._context.effect or self._request_mac(request) != self._mac:
            raise ContactsGuardError("CONTACTS_EXECUTOR_FENCE_INVALID")
        c = self._context
        async with self._database.transaction(c.tenant, c.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": c.effect, "token": self._token},
            )

    async def claim_inspection(self, operation_id: UUID, intent: ContactsInspectionIntent) -> bool:
        # Import here to keep the shared typed context independent of recovery.
        from app.services.reference_contacts_runs import load_contacts_run

        if operation_id != uuid5(self._context.effect, "contacts-inspection-v1"):
            return False
        existing = await load_contacts_run(self._database, self._context)
        if existing is None or existing[0] != intent.submission:
            return False
        self._token = existing[1]
        return True

    async def inspection_uncertain(self, operation_id: UUID, intent: ContactsInspectionIntent) -> None:
        if not await self.claim_inspection(operation_id, intent):
            raise ContactsGuardError("CONTACTS_EXECUTOR_FENCE_INVALID")
        async with self._database.transaction(self._context.tenant, self._context.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": self._context.effect, "token": self._token},
            )

    def execution_token(self) -> UUID:
        if self._token is None:
            raise ContactsGuardError("CONTACTS_EXECUTOR_FENCE_INVALID")
        return self._token
